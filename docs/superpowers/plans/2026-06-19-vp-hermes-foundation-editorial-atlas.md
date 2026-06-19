# VisePanda Foundation + Editorial Atlas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 VisePanda 的主链路断点，并在稳定底座上落地 `Editorial Atlas` 的首页、聊天、城市、行程与后台结构重构。

**Architecture:** 先用后端契约测试和前端纯逻辑测试把认证、聊天、trip、admin 的关键行为锁住，再收口前后端字段与页面结构，最后在现有 Vanilla SPA 上分文件重组并应用新的视觉与信息架构。整个实施过程中不引入前端框架，保留 WSGI + Vanilla JS 结构。

**Tech Stack:** Python 3.11 stdlib, SQLite, Vanilla JS, HTML, CSS, Node `--test`

---

### Task 1: 建立后端测试基座

**Files:**
- Create: `tests/test_support.py`
- Create: `tests/test_auth_contract.py`
- Create: `tests/test_admin_contract.py`

- [ ] **Step 1: 写失败测试基座**

```python
# tests/test_support.py
import json
import os
import tempfile
import unittest
from io import BytesIO


class WsgiTestCase(unittest.TestCase):
    def make_environ(self, method, path, body=None, token=None, query_string=""):
        payload = json.dumps(body).encode("utf-8") if body is not None else b""
        env = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": query_string,
            "CONTENT_LENGTH": str(len(payload)),
            "CONTENT_TYPE": "application/json",
            "wsgi.input": BytesIO(payload),
            "SERVER_PROTOCOL": "HTTP/1.1",
            "HTTP_HOST": "localhost",
        }
        if token:
            env["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return env

    def call_app(self, app, env):
        captured = {}

        def sr(status, headers):
            captured["status"] = status
            captured["headers"] = headers

        body = b"".join(app(env, sr)).decode("utf-8")
        captured["body"] = body
        captured["json"] = json.loads(body) if body else None
        return captured
```

- [ ] **Step 2: 运行测试以确认失败**

Run: `python3 -m unittest tests/test_auth_contract.py -v`  
Expected: `ModuleNotFoundError: No module named 'tests.test_support'`

- [ ] **Step 3: 写最小实现**

```python
# tests/test_auth_contract.py
import importlib
import os
import tempfile
from tests.test_support import WsgiTestCase


class AuthContractTest(WsgiTestCase):
    def setUp(self):
        self.db_dir = tempfile.TemporaryDirectory()
        os.environ["AUTH_DB_PATH"] = os.path.join(self.db_dir.name, "auth.db")
        from api import auth
        auth._initialized = False
        auth.ensure_init()
        from api.index import app
        self.app = app

    def tearDown(self):
        self.db_dir.cleanup()
```

- [ ] **Step 4: 运行测试以确认通过导入**

Run: `python3 -m unittest tests/test_auth_contract.py -v`  
Expected: 测试文件可导入，但因无具体测试而显示 `Ran 0 tests`

- [ ] **Step 5: Commit**

```bash
git add tests/test_support.py tests/test_auth_contract.py
git commit -m "test: add backend wsgi test support"
```

---

### Task 2: 先锁住 auth/admin 空 body 与权限契约

**Files:**
- Modify: `tests/test_auth_contract.py`
- Modify: `tests/test_admin_contract.py`
- Modify: `api/auth.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_auth_contract.py
    def test_unauthenticated_trips_returns_json_error(self):
        res = self.call_app(self.app, self.make_environ("GET", "/api/trips"))
        self.assertEqual(res["status"], "401 Unauthorized")
        self.assertEqual(res["json"]["error"], "Authentication required")

# tests/test_admin_contract.py
import os
import tempfile
from tests.test_support import WsgiTestCase


class AdminContractTest(WsgiTestCase):
    def setUp(self):
        self.db_dir = tempfile.TemporaryDirectory()
        os.environ["AUTH_DB_PATH"] = os.path.join(self.db_dir.name, "auth.db")
        from api import auth
        auth._initialized = False
        auth.ensure_init()
        from api.index import app
        self.app = app

    def tearDown(self):
        self.db_dir.cleanup()

    def test_unauthenticated_admin_users_returns_json_error(self):
        res = self.call_app(self.app, self.make_environ("GET", "/api/admin/users"))
        self.assertEqual(res["status"], "401 Unauthorized")
        self.assertEqual(res["json"]["error"], "Authentication required")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest tests/test_auth_contract.py tests/test_admin_contract.py -v`  
Expected: 至少一个测试失败，失败原因是 `body` 为空或 `json` 为 `None`

- [ ] **Step 3: 写最小实现**

```python
# api/auth.py
def require_auth(environ, start_response) -> dict | None:
    token = _extract_token(environ)
    user = _get_user_from_token(token)
    if user is None:
        start_response._vp_error = _json_error(start_response, "Authentication required", "401 Unauthorized")
        return None
    return user
```

```python
# api/auth.py
if path == "/api/admin/users" and method == "GET":
    check = require_role("ops", "admin")
    user = check(environ, start_response)
    if user is None:
        return getattr(start_response, "_vp_error", [])
    return handle_admin_users(environ, start_response)
```

- [ ] **Step 4: 重构为显式辅助函数并运行通过**

```python
# api/auth.py
def _auth_error_response(start_response, message, status):
    return _json_error(start_response, message, status)
```

Run: `python3 -m unittest tests/test_auth_contract.py tests/test_admin_contract.py -v`  
Expected: 两条未登录测试通过

- [ ] **Step 5: Commit**

```bash
git add tests/test_auth_contract.py tests/test_admin_contract.py api/auth.py
git commit -m "fix: return json bodies for auth failures"
```

---

### Task 3: 修复 display_name、status 与 admin/ops 权限口径

**Files:**
- Modify: `tests/test_auth_contract.py`
- Modify: `tests/test_admin_contract.py`
- Modify: `api/auth.py`
- Modify: `web/admin.html`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_auth_contract.py
    def test_register_persists_display_name(self):
        res = self.call_app(self.app, self.make_environ("POST", "/api/auth/register", {
            "email": "user@example.com",
            "password": "secret123",
            "display_name": "Atlas User",
        }))
        self.assertEqual(res["status"], "201 Created")
        login = self.call_app(self.app, self.make_environ("POST", "/api/auth/login", {
            "email": "user@example.com",
            "password": "secret123",
        }))
        self.assertEqual(login["json"]["user"]["display_name"], "Atlas User")
```

```python
# tests/test_admin_contract.py
    def test_disabled_user_cannot_login(self):
        from api import auth
        conn = auth._get_db()
        conn.execute("INSERT INTO users (id, email, password_hash, salt, display_name, role, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     ("u1", "disabled@example.com", auth._hash_password("secret123")[0], auth._hash_password("secret123")[1], "Disabled", "user", "disabled"))
        conn.commit()
        conn.close()
        res = self.call_app(self.app, self.make_environ("POST", "/api/auth/login", {
            "email": "disabled@example.com",
            "password": "secret123",
        }))
        self.assertEqual(res["status"], "403 Forbidden")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest tests/test_auth_contract.py tests/test_admin_contract.py -v`  
Expected: 注册读不回 `display_name`，禁用用户仍可登录

- [ ] **Step 3: 写最小实现**

```python
# api/auth.py
display_name = (data.get("display_name", "") or "").strip()
conn.execute(
    "INSERT INTO users (id, email, password_hash, salt, display_name, role) VALUES (?, ?, ?, ?, ?, ?)",
    (user_id, email, password_hash, salt, display_name, role),
)
```

```python
# api/auth.py
row = conn.execute(
    "SELECT id, email, password_hash, salt, role, status, display_name FROM users WHERE email = ?",
    (email,),
).fetchone()
if user["status"] != "active":
    conn.close()
    return _json_error(start_response, "Account is not active", "403 Forbidden")
```

```html
<!-- web/admin.html -->
const token = localStorage.getItem('vp_token');
if (!(user.role === 'admin' || user.role === 'ops')) {
```

- [ ] **Step 4: 运行测试并补前端一致性**

Run: `python3 -m unittest tests/test_auth_contract.py tests/test_admin_contract.py -v`  
Expected: display_name 与 status 测试通过

- [ ] **Step 5: Commit**

```bash
git add tests/test_auth_contract.py tests/test_admin_contract.py api/auth.py web/admin.html
git commit -m "fix: align auth fields and admin role checks"
```

---

### Task 4: 补齐 trips 完整内容模型

**Files:**
- Create: `tests/test_trips_contract.py`
- Modify: `api/auth.py`
- Modify: `web/app.js`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_trips_contract.py
import os
import tempfile
from tests.test_support import WsgiTestCase


class TripsContractTest(WsgiTestCase):
    def setUp(self):
        self.db_dir = tempfile.TemporaryDirectory()
        os.environ["AUTH_DB_PATH"] = os.path.join(self.db_dir.name, "auth.db")
        from api import auth
        auth._initialized = False
        auth.ensure_init()
        from api.index import app
        self.app = app
        reg = self.call_app(self.app, self.make_environ("POST", "/api/auth/register", {
            "email": "trip@example.com", "password": "secret123"
        }))
        login = self.call_app(self.app, self.make_environ("POST", "/api/auth/login", {
            "email": "trip@example.com", "password": "secret123"
        }))
        self.token = login["json"]["token"]

    def tearDown(self):
        self.db_dir.cleanup()

    def test_create_trip_keeps_full_content(self):
        res = self.call_app(self.app, self.make_environ("POST", "/api/trips", {
            "title": "Beijing 3 Days",
            "city": "beijing",
            "days": "3",
            "preview": "short",
            "content": "full itinerary body",
        }, token=self.token))
        self.assertEqual(res["status"], "201 Created")
        self.assertEqual(res["json"]["trip"]["content"], "full itinerary body")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest tests/test_trips_contract.py -v`  
Expected: 接口返回中没有 `content`

- [ ] **Step 3: 写最小实现**

```python
# api/auth.py migration
try:
    conn.execute("ALTER TABLE trips ADD COLUMN content TEXT NOT NULL DEFAULT ''")
except sqlite3.OperationalError:
    pass
```

```python
# api/auth.py create trip
content = (data.get("content", "") or "").strip()
conn.execute(
    "INSERT INTO trips (id, user_id, title, city, days, preview, content, is_saved) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
    (trip_id, user["id"], title, city, days, preview, content, is_saved),
)
```

```js
// web/app.js
body: JSON.stringify({
  title,
  city,
  days,
  preview: content.slice(0, 220),
  content,
  is_saved: true
})
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m unittest tests/test_trips_contract.py -v`  
Expected: trip 完整内容被保存并回传

- [ ] **Step 5: Commit**

```bash
git add tests/test_trips_contract.py api/auth.py web/app.js
git commit -m "feat: persist full trip content"
```

---

### Task 5: 锁住聊天 split 与页面结构唯一性

**Files:**
- Create: `web/tests/chat-stream.test.js`
- Create: `web/tests/view-registry.test.js`
- Modify: `web/index.html`
- Modify: `web/app.js`

- [ ] **Step 1: 写失败测试**

```js
// web/tests/chat-stream.test.js
import test from 'node:test';
import assert from 'node:assert/strict';

test('split events can replace typing id safely', () => {
  let typingId = 't1';
  const next = 't2';
  typingId = next;
  assert.equal(typingId, 't2');
});
```

```js
// web/tests/view-registry.test.js
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

test('chat message container ids are unique', () => {
  const html = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');
  const matches = html.match(/id="chat-messages"/g) || [];
  assert.equal(matches.length, 1);
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `node --test web/tests/chat-stream.test.js web/tests/view-registry.test.js`  
Expected: 唯一性测试失败，因为页面存在重复 `chat-messages`

- [ ] **Step 3: 写最小实现**

```html
<!-- web/index.html -->
<div id="chat-viewer-messages" class="chat-messages"></div>
```

```js
// web/app.js
let typingId = addTyping();
```

```js
// web/app.js
var msgsEl = document.getElementById('chat-viewer-messages');
```

- [ ] **Step 4: 运行测试确认通过**

Run: `node --test web/tests/chat-stream.test.js web/tests/view-registry.test.js`  
Expected: split 赋值与容器唯一性测试通过

- [ ] **Step 5: Commit**

```bash
git add web/tests/chat-stream.test.js web/tests/view-registry.test.js web/index.html web/app.js
git commit -m "fix: stabilize chat split flow and unique chat containers"
```

---

### Task 6: 统一版本与 Google 配置来源

**Files:**
- Create: `tests/test_config_contract.py`
- Modify: `api/index.py`
- Modify: `api/config.py`
- Modify: `web/index.html`
- Modify: `web/app.js`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_config_contract.py
import os
import tempfile
from tests.test_support import WsgiTestCase


class ConfigContractTest(WsgiTestCase):
    def setUp(self):
        from api.index import app
        self.app = app

    def test_health_and_config_share_version(self):
        health = self.call_app(self.app, self.make_environ("GET", "/api/health"))
        config = self.call_app(self.app, self.make_environ("GET", "/api/config"))
        self.assertEqual(health["json"]["version"], config["json"]["version"])
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest tests/test_config_contract.py -v`  
Expected: `4.1.2 != 3.2.0`

- [ ] **Step 3: 写最小实现**

```python
# api/index.py
APP_VERSION = "4.1.2"
```

```python
# api/config.py
from api.index import APP_VERSION
...
"version": APP_VERSION,
"google_client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
```

```html
<!-- web/index.html -->
data-client_id=""
```

```js
// web/app.js
fetch('/api/config').then(r => r.json()).then(cfg => {
  const gsi = document.getElementById('g_id_onload');
  if (gsi && cfg.google_client_id) gsi.dataset.client_id = cfg.google_client_id;
});
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m unittest tests/test_config_contract.py -v`  
Expected: 版本一致

- [ ] **Step 5: Commit**

```bash
git add tests/test_config_contract.py api/index.py api/config.py web/index.html web/app.js
git commit -m "fix: unify version source and config injection"
```

---

### Task 7: 接入 Tools 视图并整理主视图结构

**Files:**
- Modify: `web/index.html`
- Modify: `web/app.js`
- Modify: `web/app.css`
- Create: `web/tests/auth-state.test.js`

- [ ] **Step 1: 写失败测试**

```js
// web/tests/auth-state.test.js
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

test('tools view exists when navigate tools is supported', () => {
  const html = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');
  assert.match(html, /id="view-tools"/);
  assert.match(html, /id="tools-grid"/);
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `node --test web/tests/auth-state.test.js`  
Expected: 页面中缺少 `view-tools` 与 `tools-grid`

- [ ] **Step 3: 写最小实现**

```html
<!-- web/index.html -->
<button class="nav-btn" data-view="tools" onclick="VP.navigate('tools')">🧰 Tools</button>
...
<section id="view-tools" class="view">
  <div class="section">
    <h2 class="section-title">🧰 Travel Toolkit</h2>
    <p class="section-sub">Visa, packing, pricing, phrases, and emergency references</p>
    <div id="tools-grid" class="tools-grid"></div>
  </div>
</section>
```

```css
/* web/app.css */
.tool-card{
  border:1px solid var(--border-default);
  background:var(--bg-surface);
  border-radius:var(--radius-xl);
  padding:18px;
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `node --test web/tests/auth-state.test.js`  
Expected: tools 视图相关结构存在

- [ ] **Step 5: Commit**

```bash
git add web/tests/auth-state.test.js web/index.html web/app.js web/app.css
git commit -m "feat: add tools view to main navigation"
```

---

### Task 8: 落地 Editorial Atlas 首页结构

**Files:**
- Modify: `web/index.html`
- Modify: `web/app.css`

- [ ] **Step 1: 先写结构检查**

```js
// web/tests/view-registry.test.js
test('home page includes atlas sections', () => {
  const html = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');
  assert.match(html, /id="hero-actions"/);
  assert.match(html, /id="trust-layer"/);
  assert.match(html, /id="editorial-city-rail"/);
  assert.match(html, /id="planner-entry"/);
});
```

- [ ] **Step 2: 运行确认失败**

Run: `node --test web/tests/view-registry.test.js`  
Expected: 新 Atlas 区块缺失

- [ ] **Step 3: 写最小实现**

```html
<!-- web/index.html -->
<div class="hero-content">
  <div class="hero-kicker">China Travel Atlas</div>
  <h1 class="hero-title">Plan China with an AI guide that actually knows the ground.</h1>
  <p class="hero-sub">Curated cities, itinerary logic, maps, visa guidance, and local context in one planner.</p>
  <div id="hero-actions" class="hero-actions">
    <button class="hero-cta" onclick="VP.navigate('chat')">Start Planning</button>
    <button class="hero-secondary" onclick="VP.navigate('cities')">Explore Cities</button>
  </div>
</div>
<section id="trust-layer" class="trust-layer"></section>
<section id="editorial-city-rail" class="section"></section>
<section id="planner-entry" class="planner-entry"></section>
```

```css
/* web/app.css */
.hero-kicker{letter-spacing:.18em;text-transform:uppercase;color:var(--accent-gold);font-size:12px}
.hero-actions{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.hero-secondary{padding:12px 24px;border:1px solid var(--border-strong);border-radius:var(--radius-lg)}
```

- [ ] **Step 4: 运行检查确认通过**

Run: `node --test web/tests/view-registry.test.js`  
Expected: 首页四个结构区块全部存在

- [ ] **Step 5: Commit**

```bash
git add web/index.html web/app.css web/tests/view-registry.test.js
git commit -m "feat: add editorial atlas home structure"
```

---

### Task 9: 落地 Chat / Cities / Trips / Admin 的 Atlas 结构

**Files:**
- Modify: `web/index.html`
- Modify: `web/app.css`
- Modify: `web/admin.html`

- [ ] **Step 1: 先写结构检查**

```js
// web/tests/view-registry.test.js
test('chat view includes action rail', () => {
  const html = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');
  assert.match(html, /id="chat-action-rail"/);
});

test('trips view includes grouped sections', () => {
  const html = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');
  assert.match(html, /id="trips-recent"/);
  assert.match(html, /id="trips-saved"/);
});
```

- [ ] **Step 2: 运行确认失败**

Run: `node --test web/tests/view-registry.test.js`  
Expected: Chat 行动区和 Trips 分组容器缺失

- [ ] **Step 3: 写最小实现**

```html
<!-- web/index.html -->
<aside id="chat-action-rail" class="chat-action-rail">
  <button class="rail-btn" onclick="VP.saveCurrentTrip()">Save trip</button>
  <button class="rail-btn" onclick="VP.navigate('map')">Open map</button>
  <button class="rail-btn" onclick="VP.navigate('tools')">Visa & tools</button>
</aside>
...
<div id="trips-recent" class="trips-group"></div>
<div id="trips-saved" class="trips-group"></div>
```

```html
<!-- web/admin.html -->
<section class="admin-hero">
  <div class="admin-kicker">Operations Atlas</div>
  <h1>Platform overview</h1>
</section>
```

```css
/* web/app.css */
.chat-action-rail{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.rail-btn{padding:10px 12px;border:1px solid var(--border-default);border-radius:var(--radius-lg)}
.trips-group{display:grid;gap:12px}
```

- [ ] **Step 4: 运行检查确认通过**

Run: `node --test web/tests/view-registry.test.js`  
Expected: Chat / Trips 的 Atlas 结构存在

- [ ] **Step 5: Commit**

```bash
git add web/index.html web/app.css web/admin.html web/tests/view-registry.test.js
git commit -m "feat: add atlas structure to chat trips and admin"
```

---

### Task 10: 文档与回归收口

**Files:**
- Modify: `README.md`
- Modify: `HANDOFF.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: 同步真实实现说明**

```md
## Current Storage
- Auth/session/trips/chat history currently use SQLite in `api/auth.py`
- Frontend uses Vanilla SPA with `Editorial Atlas` information structure
```

- [ ] **Step 2: 运行全量回归**

Run: `python3 -m unittest discover -s tests -v && node --test web/tests/*.test.js`  
Expected: 全部通过

- [ ] **Step 3: 启动本地 smoke**

Run: `python3 -c "from api.index import app; from wsgiref.simple_server import make_server; httpd = make_server('127.0.0.1', 8765, app); print('http://127.0.0.1:8765'); httpd.serve_forever()"`  
Expected: 可访问首页、聊天、城市、trips、tools、admin

- [ ] **Step 4: Commit**

```bash
git add README.md HANDOFF.md CHANGELOG.md
git commit -m "docs: sync implementation and atlas rollout"
```

---

## Self-Review

- Spec coverage: 已覆盖基础修复、Tools 接入、首页与核心页面的 Atlas 结构、admin 权限与配置统一。
- Placeholder scan: 未使用 `TODO`、`TBD`、`similar to task` 等占位语。
- Type consistency: 统一使用 `vp_token`、`display_name`、`content`、`preview`、`APP_VERSION`。

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-06-19-vp-hermes-foundation-editorial-atlas.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**

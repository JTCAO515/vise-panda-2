# VisePanda v3.1.0 — 用户系统 + 管理后台 技术交付说明

> **版本:** v3.1.0 | **交付日期:** 2026-06-18
> **技术栈:** Python WSGI (stdlib only) + Vanilla JS SPA + SQLite
> **前置依赖:** v3.0.8（现有 auth.py + index.py + SPA）

---

## 一、架构变更

### 1.1 总览

```
v3.0.8                     v3.1.0
─────                      ─────
api/index.py        →    api/index.py          (+ 路由分发扩展)
api/auth.py         →    api/auth.py           (+ chat_history 表 + 管理API)
                         api/admin.py          [新] 管理后台 WSGI 模块
web/index.html      →    web/index.html        (+ 登录/注册 modal + 用户菜单)
web/app.js          →    web/app.js            (+ auth 状态管理 + API 调用)
web/app.css         →    web/app.css           (+ auth 相关样式)
                         web/admin.html        [新] 管理后台页面（纯静态 SPA）
                         web/admin.js          [新] 管理后台 JS 逻辑
                         web/admin.css         [新] 管理后台样式
                         docs/PRD_USER_SYSTEM.md  [新] 产品需求文档
```

### 1.2 后端架构变化

```
api/index.py (WSGI handler)
├── 现有路由 /api/health, /api/chat, /api/cities, ...
├── ── Auth routes (委派到 auth.py)
│   ├── POST /api/auth/register
│   ├── POST /api/auth/login
│   ├── POST /api/auth/logout
│   ├── POST /api/auth/verify-email
│   ├── POST /api/auth/forgot-password
│   ├── POST /api/auth/reset-password
│   ├── GET  /api/auth/me
│   ├── GET  /api/auth/chat-history     ← 新增：用户的对话列表
│   ├── GET  /api/auth/chat/:id         ← 新增：单条对话详情
│   └── POST /api/auth/chat/save        ← 新增：保存对话
├── ── Admin routes (委派到 auth.py 或独立模块)
│   ├── GET  /api/admin/stats           ← 新增：Dashboard 统计
│   ├── GET  /api/admin/users           ← 已有：用户列表
│   ├── GET  /api/admin/users/:id       ← 已有：用户详情
│   ├── PATCH /api/admin/users/:id      ← 新增：编辑用户
│   ├── GET  /api/admin/users/:id/chat  ← 新增：用户对话列表
│   └── GET  /api/admin/chat/:id        ← 新增：查看对话详情
└── ── Static / Admin SPA
    ├── /admin/  → web/admin.html       ← 新增：管理后台入口
    └── /*       → web/ or static/      ← 现有：静态文件服务
```

---

## 二、数据库 Schema

### 2.1 现有表（auth.py 已有）

```sql
-- users 表（已有）
CREATE TABLE users (
    id            TEXT PRIMARY KEY,           -- UUID
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,              -- SHA-256 (现有，可升级)
    salt          TEXT NOT NULL,
    display_name  TEXT NOT NULL DEFAULT '',
    role          TEXT NOT NULL DEFAULT 'user',  -- user | ops | admin
    status        TEXT NOT NULL DEFAULT 'active', -- pending | active | disabled
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- sessions 表（已有）
CREATE TABLE sessions (
    token       TEXT PRIMARY KEY,             -- 64 hex
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at  TEXT NOT NULL
);
```

### 2.2 新增表

```sql
-- chat_conversations 表（新增）
CREATE TABLE chat_conversations (
    id          TEXT PRIMARY KEY,             -- UUID
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL DEFAULT '',     -- 首条消息前50字
    message_count INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- chat_messages 表（新增）
CREATE TABLE chat_messages (
    id              TEXT PRIMARY KEY,         -- UUID
    conversation_id TEXT NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,            -- 'user' | 'assistant' | 'system'
    content         TEXT NOT NULL,
    token_count     INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 索引
CREATE INDEX idx_conversations_user ON chat_conversations(user_id);
CREATE INDEX idx_messages_conversation ON chat_messages(conversation_id, created_at);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_status ON users(status);
```

### 2.3 密码哈希升级（可选）

当前使用 `hashlib.sha256(password + salt).hexdigest()` → 建议升级为：

```python
import hashlib, os
def hash_password(password: str) -> tuple[str, str]:
    salt = os.urandom(16).hex()
    # 1000 次迭代 SHA-256（stdlib only，不用 bcrypt）
    h = password.encode()
    for _ in range(1000):
        h = hashlib.sha256(h + salt.encode()).digest()
    return h.hex(), salt
```

MVP 阶段可保留现有 SHA-256 方案，后续再升级。

---

## 三、API 详细设计

### 3.1 新增 API

| 方法 | 路径 | 认证 | 角色 | 说明 |
|------|------|:----:|:----:|------|
| POST | `/api/auth/chat/save` | ✅ | user+ | 保存当前对话（批量插入 messages） |
| GET | `/api/auth/chat-history` | ✅ | user+ | 当前用户的对话列表（分页） |
| GET | `/api/auth/chat/:id` | ✅ | user+ | 单条对话的完整消息 |
| GET | `/api/admin/stats` | ✅ | ops+ | Dashboard 统计 |
| GET | `/api/admin/users` | ✅ | ops+ | 用户列表（搜索/筛选/分页） |
| GET | `/api/admin/users/:id` | ✅ | ops+ | 用户详情 |
| PATCH | `/api/admin/users/:id` | ✅ | admin | 编辑用户（role/status/display_name） |
| GET | `/api/admin/users/:id/chat` | ✅ | ops+ | 指定用户的所有对话 |
| GET | `/api/admin/chat/:id` | ✅ | ops+ | 查看对话详情 |

### 3.2 请求/响应示例

```json
// POST /api/auth/chat/save
// Request
{
  "conversation_id": "uuid-...",       // 新建传 null，续传传已有 id
  "messages": [
    {"role": "user", "content": "Help me plan 3 days in Beijing"},
    {"role": "assistant", "content": "Here's your 3-day Beijing itinerary..."}
  ]
}
// Response
{
  "conversation_id": "uuid-...",
  "saved": 12,
  "updated_at": "2026-06-18T12:00:00"
}

// GET /api/auth/chat-history?page=1&limit=20
// Response
{
  "conversations": [
    {
      "id": "uuid-...",
      "title": "Help me plan 3 days in Beijing",
      "message_count": 24,
      "created_at": "2026-06-18T10:00:00",
      "updated_at": "2026-06-18T10:30:00"
    }
  ],
  "total": 5,
  "page": 1
}

// GET /api/auth/chat/:id
// Response
{
  "id": "uuid-...",
  "title": "Help me plan 3 days in Beijing",
  "messages": [
    {"role": "user", "content": "...", "created_at": "..."},
    {"role": "assistant", "content": "...", "created_at": "..."}
  ]
}

// GET /api/admin/stats
// Response
{
  "total_users": 42,
  "users_by_role": {"user": 38, "ops": 3, "admin": 1},
  "users_by_status": {"active": 40, "disabled": 2},
  "total_conversations": 156,
  "today_conversations": 8,
  "today_active_users": 5
}

// PATCH /api/admin/users/:id
// Request
{
  "display_name": "New Name",
  "role": "ops",
  "status": "active"
}
// Response: 200 OK with updated user
```

---

## 四、前端实现方案

### 4.1 Auth 状态管理

在 `app.js` 中新增 `VP.auth` 模块：

```javascript
VP.auth = {
  token: localStorage.getItem('vp_token'),
  user: JSON.parse(localStorage.getItem('vp_user') || 'null'),

  isLoggedIn() { return !!this.token; },
  isAdmin() { return this.user?.role === 'admin' || this.user?.role === 'ops'; },
  isOps() { return this.user?.role === 'ops'; },

  async login(email, password) {
    const res = await fetch('/api/auth/login', { method:'POST',
      body: JSON.stringify({email, password}),
      headers: {'Content-Type':'application/json'}
    });
    if (!res.ok) throw new Error((await res.json()).error);
    const data = await res.json();
    this.token = data.access_token;
    localStorage.setItem('vp_token', this.token);
    // 获取用户信息
    const me = await this.getMe();
    this.user = me;
    localStorage.setItem('vp_user', JSON.stringify(me));
    return me;
  },

  async getMe() {
    const res = await fetch('/api/auth/me', {
      headers: {'Authorization': 'Bearer ' + this.token}
    });
    return res.ok ? await res.json() : null;
  },

  logout() {
    this.token = null;
    this.user = null;
    localStorage.removeItem('vp_token');
    localStorage.removeItem('vp_user');
    location.reload();
  },

  authHeader() {
    return this.token ? {'Authorization': 'Bearer ' + this.token} : {};
  }
};
```

### 4.2 前端组件

**登录/注册弹窗（Modal）：**
- 触发按钮：顶部导航右侧「Sign In」
- 两个 Tab：Login / Register
- 表单字段有限，三两步完成
- 成功后自动关闭，更新导航显示

**用户下拉菜单：**
- 显示：用户昵称/邮箱缩写
- 选项：My Chats / My Trips / 管理后台（ops/admin 可见）/ Sign Out

**Chat 对话保存：**
- 已登录用户：每条消息发送后自动触发 `/api/auth/chat/save`
- 使用防抖（3s 无新消息后保存）
- 打开 Chat 时：检查是否有未完成的对话 → 加载历史

**管理后台页面（独立 SPA）：**
- 路径 `/admin` → 返回静态 `web/admin.html`
- 独立 JS/CSS，不与主 SPA 冲突
- 侧边栏 + 内容区布局
- 所有 API 调用带 JWT header
- token 过期 → 跳转登录

### 4.3 登录/注册 UI 设计

**登录表单：**
```
┌─ Sign In ──────────────┐
│                         │
│  Email                  │
│  [________________]     │
│                         │
│  Password               │
│  [________________]     │
│                         │
│  [Sign In]              │
│                         │
│  Don't have an account? │
│  Create one →           │
│                         │
│  Forgot password?       │
└─────────────────────────┘
```

**注册表单：**
```
┌─ Create Account ───────┐
│                         │
│  Email                  │
│  [________________]     │
│                         │
│  Nickname (optional)    │
│  [________________]     │
│                         │
│  Password               │
│  [________________]     │
│                         │
│  [Create Account]       │
│                         │
│  Already have an acount?│
│  Sign in →              │
└─────────────────────────┘
```

---

## 五、实现顺序（迭代计划）

### Iter 1：Auth 后端完善 + 前端口（~2h）

**后端：**
- [ ] auth.py: 新增 `handle_chat_save()`, `handle_chat_history()`, `handle_chat_detail()`
- [ ] auth.py: 新增 `handle_admin_stats()`, `handle_admin_user_update()`, `handle_admin_user_chat()`
- [ ] auth.py: 新增 `require_role()` 装饰器
- [ ] auth.py: 创建 `chat_conversations` 和 `chat_messages` 表（`init_db()` 中）
- [ ] index.py: 新增路由分发

**前端：**
- [ ] app.js: `VP.auth` 模块（登录/登出/token管理）
- [ ] index.html: 登录/注册 Modal HTML
- [ ] app.css: Modal 样式
- [ ] index.html: 用户菜单 + 导航变化

### Iter 2：Chat 持久化 + 对话列表（~2h）

- [ ] Chat 保存逻辑（SSE done → 触发 save）
- [ ] 「My Chats」对话历史页面（列表 + 加载）
- [ ] 打开 Chat 时恢复上次对话
- [ ] 保存行程时检查登录态（未登录弹引导）

### Iter 3：管理后台（~3h）

- [ ] `web/admin.html` — 完整后台页面
- [ ] `web/admin.js` — Dashboard + 用户管理 + 对话查询
- [ ] `web/admin.css` — 后台样式
- [ ] 角色校验：admin vs ops 可见不同内容

### Iter 4：完善与部署（~1h）

- [ ] 错误处理：网络故障/token 过期/权限不足
- [ ] 移动端适配：管理后台手机可用
- [ ] 配置 Vercel env vars（如有需要）
- [ ] 推送到 GitHub → 自动部署

---

## 六、文件变更清单

| 文件 | 操作 | 说明 |
|------|:----:|------|
| `api/auth.py` | 🔧 修改 | 新增 chat_history 表 + 管理 API |
| `api/index.py` | 🔧 修改 | 新增路由分发 (admin + auth chat) |
| `api/admin.py` | ✨ 新建 | 管理后台 WSGI handler（可选，或合入 auth.py） |
| `web/index.html` | 🔧 修改 | 登录 Modal + 用户菜单 + 导航变化 |
| `web/app.js` | 🔧 修改 | VP.auth 模块 + Chat 保存逻辑 |
| `web/app.css` | 🔧 修改 | Modal + 用户菜单样式 |
| `web/admin.html` | ✨ 新建 | 管理后台 SPA 入口 |
| `web/admin.js` | ✨ 新建 | 管理后台 JS 逻辑 |
| `web/admin.css` | ✨ 新建 | 管理后台样式 |
| `docs/PRD_USER_SYSTEM.md` | ✨ 新建 | 产品需求文档 |
| `vercel.json` | 🔍 可能无需修改 | 所有路由已走 index.py |

---

## 七、风险与边界条件

### 7.1 已知风险

| 风险 | 概率 | 影响 | 应对 |
|------|:----:|:----:|------|
| Vercel 冷启动重置 SQLite | 高 | 对话数据丢失 | MVP 接受，标注"对话仅在当前会话内持久"；后续切换到外部 DB |
| auth.py 已近 500 行，新增代码超 300 行 | 中 | 维护性下降 | 将管理 API 拆到独立模块 `api/admin.py` |
| 管理后台表单验证 | 低 | UX 体验 | 前后端双重校验 |
| token 过期场景 | 中 | 用户无感知丢失登录态 | 所有 API 返回 401 → 前端自动清除 token 并跳转 |

### 7.2 性能考虑

- Chat 保存：SSE 完成后一次性批量插入，不要每条消息单独 insert
- 对话历史列表：分页（默认 20 条/页），倒序排列
- 管理后台用户列表：支持搜索（邮箱 LIKE）和筛选（role/status）

### 7.3 数据库兼容

当前 `auth.py` 已支持 `AUTH_DB_PATH` 环境变量覆盖 DB 路径。Vercel 上默认写 `/tmp/users.db`（之前已修复），本地开发写 `data/users.db`。新增的 chat 表自动建在同一 DB 文件中。

注意：`init_db()` 必须在模块加载时调用，确保表存在。

# VisePanda — China Travel AI Agent

> **项目代号**: VisePanda  
> **一句话**: 用 AI 对话帮外国游客规划中国旅行——聊天即行程。  
> **目标用户**: 来华旅游的外国人（英语为主，支持多语种）  
> **商业模式**: 免费规划 → 酒店/导游/门票预订抽佣  
> **当前阶段**: MVP v1 — 能聊天、能登录、能存行程

---

## 用户旅程

1. 用户打开网站 → 看到着陆页（深色中国风，有搜索框）
2. 输入目的地+天数（如 "Beijing 5 days"）→ 点击 Start
3. 进入聊天页面 → AI 回复行程建议（带 Markdown 格式）
4. 可登录 Google 账号 → 行程跨设备同步
5. 后续迭代：拖拽排日程、预订酒店、PDF 导出、语音输入

---

## 技术栈

| 层 | 选型 | 原因 |
|----|------|------|
| 后端 | FastAPI (Python) | 轻量、异步、LLM 生态好 |
| 前端 | 后端直出 HTML (Jinja2 或不依赖模板引擎的 f-string) | 避免静态文件路径问题 |
| LLM | GLM 5.1 (智谱) | OpenAI 兼容 API |
| 认证 | Supabase Auth (Google OAuth) | 免费、自带用户管理 |
| 数据库 | SQLite (本地) / Supabase Postgres (生产) | 零配置本地开发 |
| 部署 | Vercel Serverless Function | 免费、自动 HTTPS |
| 域名 | go2china.space | 已购买 |

---

## GLM 5.1 配置

```
LLM_BASE_URL = https://open.bigmodel.cn/api/paas/v4
LLM_MODEL = glm-5.1
LLM_API_KEY = f8deeed9d23b43c8a891f72dd99d8d10.tErLZfXyLsq5wFzc
```

API 格式是 OpenAI 兼容的 `/chat/completions`，直接 `httpx.post()` 调用。

---

## Supabase 配置

```
SUPABASE_URL = https://jdlinmdhmulozrjeseyc.supabase.co
SUPABASE_ANON_KEY = sb_publishable_GDZz-hDv6m-GTzRwsAt7Lw_BaU7CQYM
```

Supabase 后台已配好 Google OAuth（Client ID + Secret）。回调地址需设为 `https://域名/auth/callback`。

---

## 数据库表

只需 3 张表（SQLite / Supabase Postgres 通用）：

```sql
-- 用户（与 Supabase auth.users 一对一）
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    profile JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 行程
CREATE TABLE trips (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    title TEXT,
    cities JSON DEFAULT '[]',
    start_date TEXT,
    end_date TEXT,
    constraints JSON DEFAULT '{}',
    current_itinerary JSON DEFAULT '{}',
    itinerary_versions JSON DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 聊天消息
CREATE TABLE chat_messages (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    trip_id TEXT REFERENCES trips(id),
    role TEXT,  -- 'user' | 'assistant'
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## API 端点

所有端点在 `/api/*` 路径下（Vercel 通过 vercel.json rewrite 到 api/index.py）：

| 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|
| GET | /api/health | 健康检查，返回 `{ok:true}` | 无 |
| GET | / | 着陆页 HTML（内嵌 Supabase 配置） | 无 |
| GET | /chat | 聊天页 HTML（内嵌 Supabase 配置） | 无 |
| GET | /auth/callback | OAuth 回调页 | 无 |
| POST | /api/chat | 发送消息，返回 AI 回复 | 需要 Bearer token 或 guest_id |
| GET | /api/trips | 行程列表 | 需要 Bearer token |
| GET | /api/trips/{id} | 单个行程详情 | 需要 Bearer token |

---

## 认证逻辑

1. 用户访问任何页面 → HTML 中嵌入 `window.__SUPABASE_CONFIG__ = {url, anon_key}`（服务端直接注入，不走 fetch）
2. 前端用 `@supabase/supabase-js` CDN 初始化客户端
3. Google 登录 → Supabase 回调到 `/auth/callback` → 解析 session → 存 localStorage → 重定向到 `/chat`
4. 游客模式：无需登录，用 `localStorage` 存最近 3 个行程

**⚠️ 旧项目踩坑**: 不要在 HTML 里硬编码 `window.__API_BASE__ = "http://localhost:8000"`。本地开发时用 `.env` 区分环境，生产环境所有请求走相对路径 `/api/*`。

---

## 前端架构 (无框架纯 HTML)

总共 3 个页面，全部由后端 FastAPI 端点直接返回 HTML 字符串：

1. **着陆页** (`GET /`): 
   - 深色中国风背景（CSS 渐变 + SVG）
   - 搜索框 + Start 按钮
   - Google 登录链接
   - 内嵌 Supabase 配置

2. **聊天页** (`GET /chat`):
   - 三栏布局：左侧行程列表 / 中间聊天区 / 右侧详情面板
   - 聊天用 SSE 流式（`/api/chat` 端点返回 stream）
   - 支持 Markdown 渲染（粗体/列表/链接）
   - 快捷回复按钮
   - 语音输入（Web Speech API）
   - 内嵌 Supabase 配置

3. **OAuth 回调页** (`GET /auth/callback`):
   - 处理 Supabase 回调
   - 解析 URL hash 中的 access_token
   - 存到 localStorage
   - 重定向到 `/chat`

**⚠️ 关键原则**: 
- Supabase URL 和 Anon Key 由后端直接注入 HTML，不通过 `/api/public-config` 端点 fetch
- 这避免了"先有鸡还是先有蛋"的问题——页面加载时就能初始化 Supabase

---

## Vercel 部署注意事项

### 项目结构（非常重要）

```
vise-panda-2/
├── api/
│   ├── main.py          # 所有 FastAPI 代码（单文件）
│   ├── index.py         # from main import app
│   └── requirements.txt # Python 依赖
├── vercel.json          # 路由配置
└── .gitignore
```

### vercel.json

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/api/index.py" }
  ]
}
```

### 环境变量（Vercel Settings → Environment Variables）

```
SUPABASE_URL=https://jdlinmdhmulozrjeseyc.supabase.co
SUPABASE_ANON_KEY=sb_publishable_GDZz-hDv6m-GTzRwsAt7Lw_BaU7CQYM
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-5.1
LLM_API_KEY=f8deeed9d23b43c8a891f72dd99d8d10.tErLZfXyLsq5wFzc
LLM_ENABLED=1
HOTEL_PROVIDER=seed
AUTH_TEST_BYPASS=0
```

### ⚠️ 常见部署错误

1. **functions 块报错**: 不要写 `functions` 配置，Vercel Python 自动检测 `api/` 目录
2. **ModuleNotFoundError**: 确保所有 Python 代码在 `api/` 目录下
3. **Supabase 未配置**: 确保环境变量已加 + Redeploy 后生效 + HTML 中服务端注入配置

---

## 用户（猪猪微）的想法和偏好

- 项目名字叫 VisePanda，域名 go2china.space
- 风格是深色中国风（山水画背景）
- 首页要简洁大气，一个搜索框一句话
- 聊天体验要好，AI 回复要有 Markdown 格式
- 支持多语种（英语为主，以后加中文/俄语/西语/阿语/韩语/日语/法语/德语）
- 先做能用的 MVP，再迭代
- 代码要简洁，不要过度设计
- 部署要稳定，不要再出"Supabase 未配置"这种低级问题
- 用 GLM 5.1 因为 DeepSeek 国内连不上

---

## 当前状态

- GitHub 仓库: `JTCAO515/vise-panda-2`
- 域名: `go2china.space`（在 Vercel 上配了 DNS）
- Supabase: 已配好 Google OAuth
- LLM: GLM 5.1 API key 已就绪

---

## 第一步（现在就做）

1. 创建单文件 `api/main.py`，包含：
   - FastAPI app
   - SQLite 数据库（3 张表）
   - Supabase JWT 认证中间件
   - GLM 5.1 聊天端点（支持流式 SSE）
   - 着陆页 HTML（内嵌 Supabase 配置）
   - 聊天页 HTML（内嵌 Supabase 配置）
   - OAuth 回调页 HTML

2. 创建 `api/index.py` — `from main import app`

3. 创建 `api/requirements.txt`：
   ```
   fastapi
   uvicorn
   httpx
   sqlalchemy
   python-jose[cryptography]
   ```

4. 创建 `vercel.json` — 一条 rewrite 规则

5. 本地启动测试：
   ```bash
   cd api && uvicorn main:app --reload
   ```

6. 测试通过后 push → Vercel 部署

---

## 关键代码说明（给 GLM 的提示）

### 认证中间件

用户通过 `Authorization: Bearer <supabase_jwt>` 发请求。后端用 Supabase 的 JWKS 端点验证 JWT：

```python
# Supabase 的 JWKS 在 {SUPABASE_URL}/auth/v1/certs
# 用 python-jose 库解析 JWT，验证 kid/iss/aud
# 开发模式：AUTH_TEST_BYPASS=1 时，支持 Authorization: Bearer test:<user_id>
```

### HTML 注入 Supabase 配置

在返回的 HTML `<head>` 里直接写：

```html
<script>
window.__SUPABASE_CONFIG__ = {
  supabase_url: "实际的 SUPABASE_URL",
  supabase_anon_key: "实际的 SUPABASE_ANON_KEY"
};
</script>
```

然后在 `<script>` 里加载 `@supabase/supabase-js` CDN 并初始化。**不要通过 fetch('/api/public-config') 获取配置**。

### 聊天端点

```
POST /api/chat
Body: { "trip_id": "...", "text": "...", "guest_id": "..." }
Response (SSE): data: {"token": "..."}\n\n ... data: [DONE]\n\n
```

调用 GLM 5.1 时设置 `stream: true`，逐 token 返回给前端。

### 游客模式

如果没有 Bearer token，用 `guest_id` 识别。行程存在 localStorage（最近 3 个），登录后迁移到服务器。

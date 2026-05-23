# VisePanda 迭代档案

> 每次迭代记录做了什么、为什么、学到了什么、下一步做什么。

---

## 📋 总览

| 项 | 值 |
|---|-----|
| 项目 | VisePanda — AI 中国旅游助手 |
| 域名 | www.go2china.space |
| 仓库 | JTCAO515/vise-panda-2 |
| LLM | 智谱 GLM 5.1 |
| 部署 | Vercel (Serverless) |
| DB | Supabase (Postgres) / SQLite fallback |
| Auth | Supabase (Google OAuth) |

---

## 🏗️ 架构决策记录 (ADR)

### ADR-001: 单文件应用
**决策**：全部逻辑放在 `api/main.py` 一个文件里，无前端 JS 模块分离。

**原因**：
- 旧版 VisePanda-New 前端多层文件 + `__API_BASE__` 硬编码 `localhost:8000`，部署后全站 API 请求打到用户本地
- 服务端渲染注入 Supabase 配置，彻底消除客户端配置 fetch 链
- 参考 Streamlit 模式：服务端负责一切，客户端只需极简脚本

**代价**：文件会变大（目前 ~400 行），需要良好分段。当超过 800 行时考虑拆分。

### ADR-002: GLM 5.1 作为默认 LLM
**决策**：用智谱 GLM 5.1 替代 DeepSeek。

**原因**：中文能力更强，成本更低，API 稳定。

### ADR-003: Vercel Serverless
**决策**：用 Vercel 部署，rewrite 规则将全部请求转发给 `api/index.py`。

**原因**：免运维、自动扩容、免费额度够用。Serverless 的限制（冷启动、无状态）对当前阶段无影响。

---

## 🔁 迭代记录

### Iteration 0 — 从零重写 (2026-05-24)

**做了什么**：
- 放弃旧仓库 `china-travel-agent`（前端架构问题无法简单修复）
- 新建 `vise-panda-2` 仓库
- 单文件 `api/main.py`（~395行）：
  - 首页 `/`：Landing page，服务端注入 Supabase 配置
  - 聊天页 `/chat`：SSE 流式聊天
  - OAuth 回调 `/auth/callback`：Google 登录回调
  - API `POST /api/chat`：流式 SSE 聊天接口
  - API `GET /api/health`：健康检查
- 数据库模型：User, Trip, ChatMessage（SQLAlchemy）
- Auth：Supabase JWT 验证 + 游客模式 + 开发测试 bypass
- CSS：深色主题，山水 SVG 背景
- 本地测试 5/5 全通过
- GitHub SSH 密钥配置完成

**待验证**：
- Vercel 部署是否成功（用户未反馈结果）
- 环境变量是否在 Vercel 配置完整

**遗留问题**：
- requirements.txt 里缺少 `python-jose[cryptography]` 的完整依赖，Vercel 可能安装失败

---

### Iteration 1 — 部署修复 ✅ (2026-05-24)

**问题**：Vercel 部署后 `FUNCTION_INVOCATION_FAILED / 500`，所有路由不可用。

**根因**（按发现顺序）：
1. **SQLite 路径**：`sqlite:///data.sqlite3` 写到 Vercel 只读文件系统，lifespan 直接崩溃
2. **依赖未安装**：Vercel uv 构建器只读根目录 `requirements.txt`，`api/requirements.txt` 被忽略
3. **跨文件导入**：`api/index.py → from main import app` 在 Vercel Python runtime 中不稳定

**修复**：
- SQLite → `/tmp/data.sqlite3`
- 新增根级 `requirements.txt`（含 `python-jose[cryptography]`）
- `api/index.py` 内联完整应用代码（不再 import 外部文件）
- lifespan 加 try/except 容错
- `.python-version` 固定 Python 3.12
- Vercel CLI 登录 + 环境变量一键配置 + 自动部署

**教训**：
- Vercel 文件系统除 `/tmp` 外只读
- Vercel uv 构建器需要根级依赖声明
- `api/` 目录下的 Python 函数尽量自包含，避免跨文件导入
- `.python-version` + `.vercelignore` 是好习惯

**状态**：✅ 已部署，首页可访问

---
- [ ] **流式聊天断线恢复**：当前 SSE 断线后消息丢失
- [ ] **对话历史**：加载历史消息到聊天界面
- [ ] **错误处理**：LLM 超时/失败的用户友好提示
- [ ] **移动端适配**：首页表单、聊天页面的响应式
- [ ] **API rate limiting**：防止滥用

#### 🥉 P2 — 旅游功能
- [ ] **行程生成**：LLM 根据城市/天数/偏好输出结构化行程
- [ ] **酒店搜索**：对接酒店数据源
- [ ] **景点推荐**：抓取或接入 POI 数据
- [ ] **地图集成**：行程可视化

#### P3 — 增强
- [ ] 游客模式持久化（localStorage → Supabase 匿名用户）
- [ ] 多语言界面
- [ ] 行程分享链接
- [ ] PDF 行程导出

---

## 📐 当前架构

```
vise-panda-2/
├── api/
│   ├── index.py         # Vercel 入口 + 完整应用 (~400行)
│   ├── main.py          # 本地开发用 (index.py 的副本)
│   └── requirements.txt # api 层依赖 (Vercel 不用，仅本地)
├── requirements.txt     # 根级依赖 (Vercel uv 构建器用)
├── vercel.json          # rewrite /* → /api/index.py
├── .python-version      # 3.12
├── .vercelignore
├── .gitignore
└── docs/
    └── ITERATIONS.md    # 👈 本文件
```

**数据流**：
```
用户 → Vercel → api/main.py
                ├── HTML: 服务端注入 SUPABASE_CONFIG → 浏览器
                ├── SSE: POST /api/chat → GLM 5.1 流式返回
                └── DB: SQLAlchemy → Supabase Postgres
```

---

## ⚠️ 已知问题

1. **Vercel Serverless 冷启动**：首次请求可能 2-5 秒延迟
2. **SQLite 仅限 /tmp**：Serverless 实例重启后数据丢失，生产用 Supabase Postgres
3. **LLM 无上下文**：当前每次请求只传 system prompt + 当前消息，没有对话历史
4. **未配置 DATABASE_URL**：目前走 SQLite fallback，需接 Supabase Postgres

---

*最后更新: 2026-05-24*

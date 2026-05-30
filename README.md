# VisePanda（YS Panda Logo）— AI 中国旅行规划助手

VisePanda 是一个部署在 Vercel Serverless 上的 FastAPI 应用：英文原生 UI，支持流式对话（SSE），默认使用 **DeepSeek（OpenAI-compatible）** 的 `/chat/completions`。

---

## 1) 本地开发

```bash
pip install -r requirements.txt --break-system-packages

# 启动（可选：本地不接 LLM 时关闭）
export LLM_ENABLED=0
uvicorn api.main:app --reload --port 8000
```

打开：`http://localhost:8000`

> 线上部署入口为 `api/index.py`（Vercel 会走 `vercel.json` rewrite 到该文件）。

---

## 2) 关键环境变量（Vercel）

### 必需（LLM）

- `LLM_API_KEY`：DeepSeek 的 API Key（必填）

### 可选（LLM）

- `LLM_BASE_URL`：默认 `https://api.deepseek.com/v1`
- `LLM_MODEL`：默认 `deepseek-v4-flash`
- `LLM_ENABLED`：默认 `1`

### 可选（数据库）

> 现在支持 fallback：优先 `DATABASE_URL`，否则在无 Supabase 凭据时使用 `/tmp/visepanda.sqlite3`（适配 Vercel）。

- `DATABASE_URL`：Postgres/SQLite 等 SQLAlchemy 连接串
- `SUPABASE_URL` / `SUPABASE_ANON_KEY`：仅当你需要 Supabase Auth/OAuth 时配置
- `SUPABASE_PAT`：仅当你使用 Supabase Management API（HTTP）模式时配置

---

## 3) 诊断与排障

### 3.1 Health

`GET /api/health` 会返回：
- 当前 DB 类型（postgres/sqlite/supabase_mgmt）
- LLM 配置是否存在（不会泄露 key）
- 启动自检 warnings

### 3.2 LLM 诊断

- `GET /api/llm/diag`：查看 LLM 配置状态（不泄露密钥）
- `GET /api/llm/diag?test=1`：发起最小化请求测试连通性（返回 status 和错误摘要）

### 3.3 request_id

每个请求都会返回 `X-Request-Id`，前端错误气泡也会显示 `request_id`。  
你可以在 Vercel Function Logs 里用 request_id 快速定位同一次请求的后端日志。

---

## 4) 迭代记录

详见：`docs/ITERATION_LOG.md`


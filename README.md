# VisePanda · v3.0.1

> AI China Travel Platform — 熊猫中国风 · AI 聊天规划 · 33 城知识库

## 产品一句话

**一个让想来中国的旅行者像跟本地朋友聊天一样，获得个性化行程规划的 AI 平台。** 基于 DeepSeek V4 Flash 大模型 + 33 城精选知识库，覆盖目的地推荐、Day-by-day 行程生成、本地美食/住宿/交通建议、旅行工具箱。

**不是通用 AI 问答，是懂中国的 AI 旅行规划师。**

## 最新版本 v3.0.1

| 模块 | 状态 |
|------|------|
| 🐼 熊猫中国风前端（暗色/亮色双主题） | ⬜ 待建 |
| 💬 SSE 流式聊天（DeepSeek V4 Flash） | ⬜ 待建 |
| 📚 33 城知识库（景点/美食/酒店/贴士） | ✅ 已有资产 |
| 🧰 旅行工具箱（打包/价格/签证/语言/紧急） | ✅ 已有资产 |
| 🏗️ WSGI 零依赖后端（stdlib only） | ⬜ 待建 |
| 🚀 Vercel 部署 | ⬜ 待建 |

## 技术栈

- **后端**：Python WSGI（纯 stdlib，零 pip 依赖）
- **前端**：纯 HTML + CSS + JS（单页应用，熊猫 × 水墨中国风）
- **LLM**：DeepSeek V4 Flash（OpenAI 兼容 SSE 流式）
- **部署**：Vercel Serverless（@vercel/python）
- **数据**：33 城知识库 JSON + 项目数据库 JSON
- **设计参考**：popular-web-designs（54 套真实设计系统）

## 前端功能

| Tab | 功能 |
|-----|------|
| 💬 Chat | SSE 流式 AI 聊天，生成个性化行程 |
| 🏙 Cities | 33 城目的地卡片网格，按季节/特色推荐 |
| 🧳 Tools | 打包清单 / 价格估算 / 签证指南 / 语言急救 / 紧急信息 |
| 📋 Trips | 行程历史与持久化（Phase 2） |

## 快速启动（本地测试）

```bash
# 本地 WSGI 测试
python3 -c "
from api.index import app
from wsgiref.simple_server import make_server
httpd = make_server('', 8765, app)
print('→ http://127.0.0.1:8765')
httpd.serve_forever()
"

# 测试 API
curl http://127.0.0.1:8765/api/health
```

## API 端点

| 端点 | 说明 |
|------|------|
| `GET /api/health` | 健康检查 |
| `POST /api/chat` | AI 聊天（SSE 流式） |
| `GET /api/cities` | 城市列表 |
| `GET /api/cities/:city` | 城市详情（景点/美食/贴士） |
| `GET /api/tools/:name` | 工具箱数据 |
| `/*` | 前端静态文件 |

## 数据来源

| 来源 | 类型 | 用途 |
|------|------|------|
| 33 城知识库 | 精选景点/美食/酒店/贴士 | 对话知识 |
| 旅行工具箱 | 打包/价格/签证/语言/紧急 | 工具模块 |
| DeepSeek V4 Flash | AI 大模型 | 对话+行程生成 |

## 项目结构

```
├── api/
│   └── index.py          Vercel WSGI handler（所有路由，~500 行）
├── web/
│   ├── index.html        前端入口（单页应用）
│   ├── app.css           熊猫中国风样式
│   └── app.js            前端逻辑（聊天/导航/主题）
├── data/
│   ├── cities.json       33 城知识库
│   ├── food.json         美食数据
│   ├── hotels.json       酒店数据
│   ├── tips.json         本地人贴士
│   ├── tools.json        工具箱（打包/价格/签证/语言/紧急）
│   └── projects/         项目数据库（行程持久化）
├── static/
│   └── img/              城市图片素材
├── vercel.json           部署配置
├── PRD_PRODUCT_ANALYSIS.md 产品分析文档
├── PLAN.md               迭代路线图
└── DESIGN.md              设计系统参考
```

## 迭代路线图

详见 [PLAN.md](PLAN.md) — 3 个 Phase × 15 轮迭代：

- **Phase 1（Iter 1-6）**：骨架搭建 — WSGI/前端/聊天/知识库就位
- **Phase 2（Iter 7-11）**：体验打磨 — 设计精修/响应式/多轮对话
- **Phase 3（Iter 12-15）**：深度增强 — 行程持久化/地图/分享/智能工具

## 与 v2.x 相比的变化

| 维度 | v2.x | v3.0.1 |
|------|------|--------|
| 架构 | FastAPI + 8 个外部依赖 | WSGI + stdlib only |
| LLM | GLM-5.1 | DeepSeek V4 Flash |
| 前端 | 7 个 JS 文件 | 单页应用（1 个 JS） |
| 后端 | 2,388 行单文件 | ~500 行 WSGI |
| 数据库 | Supabase Postgres | 项目数据库 JSON |
| 部署 | 易故障（依赖链长） | 零故障（零依赖） |
| 设计 | 水墨暗色 | 熊猫 × 中国风双主题 |


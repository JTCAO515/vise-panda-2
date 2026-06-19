# VisePanda · v5.0.7

> AI China Travel Platform — Panda Chinese Style · AI Chat Planning · 36-City Knowledge Base

## Product in One Line

**An AI platform that lets travelers to China get personalized trip plans by chatting like with a local friend.** Powered by DeepSeek V4 Flash + 36-city curated knowledge base — covers destination recommendations, day-by-day itineraries, local food/hotel/transport tips, and travel toolkit.

**Not a generic AI assistant — a China-specialized AI travel planner.**

## Latest Version v5.0.7

| Module | Status |
|--------|--------|
| 🏗️ Foundation contracts (auth/admin/trips/config) | ✅ 已落地到 `tests/` + `web/tests/` |
| 🔐 Auth/Admin consistency (`vp_token` / `display_name` / `status`) | ✅ 已收口 |
| 📋 Trips full-content model (`preview` + `content`) | ✅ 已落地 |
| 🧰 Tools main-nav integration | ✅ 已接入主站 |
| 🏠 Editorial Atlas 首页骨架 (`hero-actions` / `trust-layer` / `editorial-city-rail` / `planner-entry`) | ✅ 已落地并深化 |
| 💬 Chat Atlas action rail | ✅ 已落地 |
| 📋 Trips recent / saved 分组结构 | ✅ 已落地并补充 atlas note |
| 🏙 Cities filter rail / editorial lead | ✅ 已落地 |
| 📱 竖屏移动端体验优化（首页 / Chat / Cities / Trips / Tools / bottom nav） | ✅ 已落地 |
| 🤳 手机端细化（Chat 快捷滚动 / Trips 单手操作 / Tools gallery / Cities 轻说明） | ✅ 已落地 |
| 🇬🇧 English-native website pass（UI + runtime city/food/hotel data） | ✅ 已落地 |
| 🛠️ Admin Atlas overview hero | ✅ 已落地 |
| 🧪 Regression commands (`python3 -m unittest discover -s tests -v` / `node --test`) | ✅ 已纳入回归流程 |

## Tech Stack

- **Backend**: Python WSGI (pure stdlib, zero pip dependencies)
- **Frontend**: Pure HTML + CSS + JS (Vanilla SPA, Panda × Chinese design + Editorial Atlas information structure)
- **LLM**: DeepSeek V4 Flash (OpenAI-compatible SSE streaming)
- **Map**: AMap (Gaode) — Leaflet fallback when AMap key not configured
- **Deployment**: Vercel Serverless (@vercel/python)
- **Storage**: SQLite for auth / session / trips / chat history via `api/auth.py`
- **Data**: 36-city knowledge base JSON + toolkit / visa / FAQ datasets
- **Design**: Panda × Chinese aesthetic, dark/light dual themes

## Current Frontend Structure

| Tab | Feature |
|-----|---------|
| 🏠 Home | Editorial Atlas Hero + Trust Layer + City Rail + Planner Entry |
| 💬 Chat | SSE streaming AI chat + Atlas action rail |
| 🗺️ Map | Full China overview with 36 city markers |
| 📋 Trips | Recent / Saved archive grouped structure |
| 🏙 Cities | 36 city detail cards with food/hotel/tips data |
| 🧰 Tools | Packing / pricing / visa / phrases / emergency toolkit |
| 👥 Admin | Ops/Admin overview hero + user management table |

## Quick Start (Local Test)

```bash
python3 -c "
from api.index import app
from wsgiref.simple_server import make_server
httpd = make_server('', 8765, app)
print('→ http://127.0.0.1:8765')
httpd.serve_forever()
"

curl http://127.0.0.1:8765/api/health
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check + version |
| `POST /api/chat` | AI chat (SSE streaming) |
| `GET /api/cities` | City list |
| `GET /api/cities/:city` | City detail (attractions/food/tips) |
| `GET /api/map` | All city map coordinates (36 cities) |
| `GET /api/config` | Client config (AMap key, etc.) |
| `GET /api/estimate` | Price estimates by city |
| `POST /api/validate` | Trip plan validation |
| `GET /api/tools/:name` | Tool data |
| `/*` | Static frontend files |

## Project Structure

```
├── api/
│   └── index.py          Vercel WSGI handler (all routes)
├── web/
│   ├── index.html        SPA entry point
│   ├── app.css           Panda Chinese style system
│   ├── app.js            Frontend logic (chat/nav/map/trips/tools/auth)
│   └── tests/            Node structure tests for Atlas/foundation
├── tests/
│   └── *.py              Python unittest contract coverage
├── data/
│   ├── cities.json       36-city knowledge base
│   ├── food.json         Food data
│   ├── hotels.json       Hotel data
│   ├── tips.json         Local tips
│   ├── faq.json          FAQ knowledge base (10 categories)
│   └── tools.json        Travel toolkit
├── static/
│   └── img/              City images
├── vercel.json           Deployment config
├── CHANGELOG.md          Version history
├── PLAN.md               Iteration roadmap
├── PRD_PRODUCT_ANALYSIS.md  Product strategy
├── README.md             This file
└── HANDOFF.md            Project handoff doc
```

## Version History

See [CHANGELOG.md](CHANGELOG.md) for full version history.

## Current Implementation Notes

- Foundation phase has already landed in code: auth/admin/trips/config contract tests live under `/workspace/VP-Hermes-Web/tests`.
- Main-page Atlas rollout is at the structural layer: homepage, chat, trips, tools, and admin all have the new containers and entry points.
- Current persistence is SQLite-backed in `/workspace/VP-Hermes-Web/api/auth.py`; this repo is no longer documented as relying on Supabase for the active auth/trip/chat path.

## Iteration Roadmap

See [PLAN.md](PLAN.md) for detailed iteration plan.

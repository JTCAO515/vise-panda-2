# VisePanda · v3.2.0

> AI China Travel Platform — Panda Chinese Style · AI Chat Planning · 36-City Knowledge Base

## Product in One Line

**An AI platform that lets travelers to China get personalized trip plans by chatting like with a local friend.** Powered by DeepSeek V4 Flash + 36-city curated knowledge base — covers destination recommendations, day-by-day itineraries, local food/hotel/transport tips, and travel toolkit.

**Not a generic AI assistant — a China-specialized AI travel planner.**

## Latest Version v3.1.0

| Module | Status |
|--------|--------|
| 🐼 Panda Chinese Style Frontend (Dark/Light) | ✅ v3.0.1 |
| 💬 SSE Streaming Chat (DeepSeek V4 Flash) | ✅ v3.0.1 |
| 📚 36-City Knowledge Base (Attractions/Food/Hotels/Tips/Pricing) | ✅ v3.0.1 |
| 🗺️ Map Tab (Full China Overview + City Markers) | ✅ v3.0.3 |
| 🔍 FAQ Smart Matching (10 categories, query expansion) | ✅ v3.0.2 |
| 🧰 Travel Toolkit (Packing/Price/Visa/Phrases/Emergency) | ✅ v3.0.1 |
| 🏷️ Dynamic Version Badge | ✅ v3.0.2 |
| 🇬🇧 English-Native System Prompt | ✅ v3.0.4 |
| 🗺️ AMap (Gaode) Dual Engine | ✅ v3.0.4 |
| 📱 Mobile App-Style UX (bottom nav, chat overlay, safe area) | ✅ v3.0.5 |
| 👥 Admin Panel (User Management) | ✅ v3.1.0 |
| 🔒 Security Hardening (input validation, XSS, UTF-8 safety) | ✅ v3.0.8 |
| 🧩 Multi-Bubble Responses (split sections into separate bubbles) | ✅ v3.0.6 |
| 🖼️ Rich Media Support (inline city images between bubbles) | ✅ v3.0.7 |
| 🎯 Precision Output (structured, data-citing answers) | ✅ v3.0.6 |
| 🌏 27-City Photo Gallery (Wikimedia Commons images) | ✅ v3.0.7 |
| 🏗️ WSGI Zero-Dependency Backend (stdlib only) | ✅ v3.0.1 |
| 🚀 Vercel Deployment | ✅ v3.0.1 |

## Tech Stack

- **Backend**: Python WSGI (pure stdlib, zero pip dependencies)
- **Frontend**: Pure HTML + CSS + JS (SPA, Panda × Chinese design)
- **LLM**: DeepSeek V4 Flash (OpenAI-compatible SSE streaming)
- **Map**: AMap (Gaode) — Leaflet fallback when AMap key not configured
- **Deployment**: Vercel Serverless (@vercel/python)
- **Data**: 36-city knowledge base JSON
- **Design**: Panda × Chinese aesthetic, dark/light dual themes

## Frontend Tabs

| Tab | Feature |
|-----|---------|
| 🏠 Home | City cards grid, hero section |
| 💬 Chat | SSE streaming AI chat, personalized itineraries |
| 🗺️ Map | Full China overview with 36 city markers |
| 📋 Trips | Trip history, save/load/share |
| 🏙 Cities | 36 city detail cards with food/hotel/tips data |

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
│   └── app.js            Frontend logic (chat/nav/map/trips)
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

## Iteration Roadmap

See [PLAN.md](PLAN.md) for detailed iteration plan.


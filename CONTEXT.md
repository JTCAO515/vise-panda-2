# VisePanda · Context

> AI China Travel Platform

## Domain Vocabulary

| Term | Definition |
|------|-----------|
| **VisePanda** | The product: an AI platform that lets travelers to China get personalized trip plans by chatting like with a local friend. |
| **Panda Chinese Style** | The visual design system: dark bamboo-green + gold accent theme, Chinese ink-wash aesthetics, panda mascot. |
| **36-City Knowledge Base** | Curated JSON dataset covering 36 Chinese cities with attractions, food, hotels, tips, pricing, and transport info per city. |
| **SSE Streaming Chat** | Server-Sent Events based AI chat using DeepSeek V4 Flash. Messages stream token-by-token with real-time rendering. |
| **Travel Toolkit** | In-app tools: packing checklist, price estimator, visa guide, phrase cards, emergency info. |
| **Trip Plan** | AI-generated day-by-day itinerary combining knowledge base data + LLM recommendations. |
| **WSGI Backend** | Pure Python stdlib WSGI server (no pip dependencies). Single `api/index.py` handles routing + API logic. |
| **AMap (Gaode)** | Primary map provider. Leaflet.js fallback when AMap API key is absent. |
| **Vercel Serverless** | Deployment target. Pure static frontend + Python WSGI via @vercel/python. |

## Architecture

```
api/index.py          ← WSGI router: health, chat (SSE), cities, map, config, tools, static files
web/                  ← Pure static SPA (HTML+CSS+JS)
  ├── index.html      ← Main app shell (bottom nav, overlays)
  ├── app.js          ← App logic + chat client + map rendering
  ├── style.css       ← Panda Chinese design system (dark/light)
  └── data/           ← City data, knowledge base JSON files
```

## Key Design Decisions

- **Zero external pip dependencies** — eliminates Vercel cold-start issues, simplifies deployment
- **English-native interface** — target users are international travelers, not Chinese domestic
- **AI chat as primary interaction** — not a search engine, not a form — conversational trip planning
- **Curated knowledge base over RAG** — 36 hand-crafted city datasets instead of real-time web search
- **Single-page app** — bottom tab navigation mimicking mobile app UX

## Known Constraints

- Vercel Hobby plan: 10s cold start, 60s function timeout, 1M requests/month
- No database — trip history stored in localStorage
- Content is English-only (Chinese terms/phrases available in language tools)

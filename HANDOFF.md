# VisePanda (VP-Hermes-Web) v5.0.9 — Handoff Document

> **Last Updated:** 2026-06-20
> **Status:** ✅ Active — foundation contracts are in place, the Editorial Atlas interface has been refined, the Production Stability Pass has landed, and the current release is aligned at v5.0.9
> **Repo:** `https://github.com/JTCAO515/VP-Hermes-Web.git` (HTTPS, PAT auth)
> **Live URL:** https://www.go2china.space (Vercel auto-deploy on push)
> **Vercel Project:** `vise-panda-2` (custom domain `www.go2china.space`)
> **Agent Memory Key:** `VP-Hermes-Web`, `vise-panda-2`, `go2china`, `VisePanda`

---

## 1. Product Overview

**AI China Travel Planner** — Specialized AI travel planner for international travelers visiting China.

Powered by DeepSeek V4 Flash + 36-city curated knowledge base (English-native, Chinese proper nouns in parentheses). Provides city recommendations, day-by-day itineraries, local food/hotel/transport tips, visa guides, packing lists, and expense estimates. SPA with auth system for trip persistence and chat history.

Target user: Non-Chinese tourists planning trips to China (English interface, China-specific content).

---

## 2. Architecture

```
┌─ Frontend (Vanilla SPA) ─────────────────────┐
│  web/index.html + web/app.js + web/app.css    │
│  Panda Chinese Style, Dark/Light themes       │
│  Leaflet (fallback) / AMap (Gaode)            │
│  SSE streaming chat → multi-bubble rendering  │
│  Auth: Google OAuth + Email/Password          │
│  Trip timeline: drag-drop day-by-day planner  │
│  50 inline city images                        │
└────────┬────────────────┬─────────────────────┘
         │ fetch/SSE      │ static files
         ▼                ▼
┌─ Vercel WSGI (Python stdlib) ─────────────────┐
│  api/index.py → route dispatcher              │
│  api/auth.py → user auth + trips + chat       │
│  api/chat.py → SSE stream (DeepSeek)          │
│  api/cities.py → city data + compare          │
│  api/tools.py → travel toolkit                │
│  api/visa.py → visa policy + letter gen       │
│  api/config.py → map config                   │
│  api/common.py → shared utils                 │
└────────┬──────────────────────────────────────┘
         │ LLM call
         ▼
┌─ DeepSeek V4 Flash ───────────────────────────┐
│  deepseek-chat model, SSE streaming           │
│  temp=0.7, max_tokens=2048                    │
│  English system prompt + contextual KB inject │
└───────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Backend | Python WSGI (stdlib only) | Zero pip deps, fast cold start on Vercel |
| Frontend | Vanilla JS SPA | No framework overhead, direct DOM control |
| LLM | DeepSeek V4 Flash | Cost-effective, fast streaming, China travel expertise |
| Auth | SQLite-backed email/password + Google OAuth + JWT | The active auth/session/trips path is concentrated in `api/auth.py`, which keeps local and test regression simple |
| Maps | AMap (Gaode) + Leaflet fallback | AMap for China (better data), Leaflet when no key |
| Session | localStorage + JWT tokens | Simple persistence, no full DB needed |
| Images | Static JPEGs from Wikimedia | Zero API cost, fast loading, CC-licensed |
| i18n | English-native (data layer) | Target users = international tourists |
| Deploy | Vercel auto-deploy from GitHub | One push → live, zero infra maintenance |

---

## 3. Current State

### ✅ Completed (v5.0.9)

| Phase | Feature | Version |
|-------|---------|:-------:|
| 🏗️ Core | WSGI backend, SPA frontend, routing | v3.0.1 |
| 🧪 Foundation | Python `unittest` + Node `--test` contract/structure regression | v5.0.1 → v5.0.3 |
| 💬 Chat | SSE streaming, DeepSeek, multi-bubble rendering | v3.0.1 → v3.0.6 |
| 🗺️ Maps | Leaflet dark maps, POI markers, AMap integration | v3.0.1 → v3.0.4 |
| 🔍 FAQ | 10-category matching engine, query expansion | v3.0.2 |
| 📚 Knowledge | 36 cities, food/hotels/tips/attractions/packing/phrases/emergency | v3.0.1 |
| 🎨 Design | Panda × Chinese aesthetic, dark/light dual themes | v3.0.1 |
| 📱 Mobile | Bottom nav, chat overlay, safe-area, dvh | v3.0.5 |
| 🖼️ Images 50 | 36 city + 5 food + 4 inspiration + 2 logo + 3 landmark | v3.0.7 |
| 🔒 Security | Input validation, XSS protection, abort fix | v3.0.8 |
| 🔐 Auth | Google OAuth + email/password, JWT session, admin panel | v4.0.0 |
| 🗂️ Trips | Save/load/delete trips, day-by-day timeline | v4.0.1 |
| 💬 Chat History | Save conversations, full history browser | v4.0.6 |
| 🇬🇧 English-native | All UI/text in English, CN proper nouns parenthesised | v4.1.0 → v4.1.2 |
| 🏛️ Admin | User list, chat logs, stats dashboard, user detail | v4.0.4 |
| 🛂 Visa tools | Visa policy lookup, visa letter generation | v4.0.3 |
| 🏠 Editorial Atlas Home | Hero / Trust Layer / City Rail / Planner Entry structure + hero metrics / editorial lead | v5.0.4 |
| 🧭 Main-page Atlas Structure | Chat action rail / Trips recent+saved / Tools view / Admin hero | v5.0.3 |
| 🏙 Editorial Browsing | Cities filter rail / editorial lead / Trips atlas note | v5.0.4 |
| 📱 Portrait Mobile UX | Compressed hero rhythm / Chat safe-area shell / swipeable filter rail / one-hand card browsing | v5.0.5 |
| 🤳 Mobile Detail Pass | Chat quick scroll / Trips thumb-first actions / Tools mobile gallery / Cities card caption | v5.0.6 |
| 🇬🇧 English-native Website | UI copy + city / food / hotel runtime data localized into natural English with `English（中文）` proper nouns | v5.0.7 |
| 🧰 Toolkit Detail Sheets | Expandable English-first toolkit sheets + English-only compatibility i18n layer | v5.0.8 |
| 🛡️ Production Stability Pass | Bootstrap hardening / image fallback / loading-state shell / mobile nav recovery | v5.0.9 |
| 🚀 Deploy | Vercel WSGI auto-deploy from GitHub | v3.0.1 |

### 🟡 Known Quirks / Gotchas

| # | Issue | Impact | Workaround |
|---|-------|--------|------------|
| 1 | **SSH git push deprecated** — Using HTTPS with PAT now. Vercel imports from public repo | Low | Push via HTTPS, Vercel builds automatically |
| 2 | **ESTIMATE_DATA only covers 7/36 cities** — Beijing, Shanghai, Chengdu, Guangzhou, Xi'an, Guilin, Hangzhou have pricing | Low | Other cities show blank estimates in pricing tool |
| 3 | **MAP_DATA POIs only for 8 cities** — Shenzhen onward have coordinates but no POI list | Low | Map markers still work |
| 4 | **Vercel cold start** — First request after idle takes ~3-5s | Acceptable | Warm-up via cron possible |
| 5 | **Admin login** — Admin can't login via Google OAuth (must use email/password registered separately) | Very Low | Documented in admin workflow |
| 6 | **Weather API** — `api/weather.py` exists but is still not wired into any UI feature | Very Low | Keep it as a future option; it is not active today |
| 7 | **Weather API** — api/weather.py exists but not wired into any UI feature | Very Low | Not used |
| 8 | **Legacy static modules** — `static/*` files are mostly compatibility artifacts, not the active SPA shell | Very Low | Safe to keep for now; revisit only if a cleanup pass is needed |

---

## 4. File Structure

```
VP-Hermes-Web/
├── api/                          # Python WSGI backend (stdlib only)
│   ├── index.py                  WSGI entry point, route dispatcher (~100 lines)
│   ├── auth.py                   Auth, trips, chat history, admin (~1100 lines)
│   ├── chat.py                   SSE streaming chat handler (~250 lines)
│   ├── cities.py                 City data, compare, estimate, validate (~260 lines)
│   ├── common.py                 Shared utils (JSON, static serving, CORS) (~80 lines)
│   ├── config.py                 Map config, client config (~30 lines)
│   ├── tools.py                  Travel toolkit router (~20 lines)
│   ├── visa.py                   Visa policy & letter generation (~140 lines)
│   ├── weather.py                Weather data (unwired) (~50 lines)
│   ├── prompt.py                 English system prompt (~200 lines)
│   ├── ics_export.py             Calendar export (~50 lines)
│   ├── test_auth.py              Auth tests
│   └── .env.example              Environment template
├── web/                          # Frontend SPA
│   ├── index.html                SPA entry (377 lines)
│   ├── app.js                    Core frontend logic (~2420 lines, vanilla JS IIFE)
│   ├── app.css                   Style system (~1200 lines, Panda Chinese theme)
│   ├── admin.html                Admin panel page
│   ├── trip-timeline.js          Day-by-day trip planner (~400 lines)
│   ├── trip-timeline.css         Trip timeline styles (~200 lines)
│   ├── manifest.json             PWA manifest
│   └── sw.js                     Service worker (basic offline)
├── static/                       # Static assets
│   ├── auth.js                   Auth UI module (~150 lines)
│   ├── chat.js                   Chat UI module (~100 lines)
│   ├── i18n.js                   Internationalization (en + zh) (~70 lines)
│   ├── landing.js                Landing page module (~100 lines)
│   ├── map.js                    Map module (~80 lines)
│   ├── profile.js                Profile page module (~50 lines)
│   ├── trips.js                  Trips page module (~80 lines)
│   ├── sw.js                     Service worker
│   ├── icon.svg                  Site icon
│   └── img/                      50 JPEG images (city, food, landmark, inspiration)
├── data/                         # Knowledge base
│   ├── cities.json               36 cities with full data
│   ├── food.json                 Food entries per city
│   ├── hotels.json               Hotel pricing by tier
│   ├── tips.json                 Local travel tips
│   ├── faq.json                  FAQ matching engine data
│   ├── tools.json                Travel toolkit data
│   ├── visa_policies.json        Visa policy rules
│   ├── city_images.json          Image metadata
│   ├── users.db                  SQLite data file (legacy sample path; active DB path also supports `AUTH_DB_PATH`)
│   └── knowledge/                Curated Python knowledge modules
│       ├── cities.py             36 city data (English)
│       ├── food.py               Food descriptions (English+CN)
│       ├── attractions.py        Attractions tips (English+CN)
│       ├── hotels.py             Hotel recommendations
│       ├── tips.py               Travel tips (English)
│       ├── packing.py            Packing list (English)
│       ├── phrases.py            Useful phrases (English+Pinyin+CN)
│       ├── transport.py          Transport guide (English)
│       ├── emergency.py          Emergency info (English)
│       └── __init__.py
├── docs/                         # Documentation
│   ├── adr/                      5 ADR documents
│   ├── agents/                   Agent instructions (AGENTS.md routing)
│   ├── PRD_PRODUCT_ANALYSIS.md   Product strategy
│   ├── PRD_USER_SYSTEM.md        User system PRD (Chinese)
│   └── ...                       Various product docs
├── scripts/                      # Utility scripts
│   └── generate_city_images.sh   Image download script
├── vercel.json                   Vercel deployment config (wsgi + fallback)
├── CHANGELOG.md                  Version history
├── PLAN.md                       Iteration roadmap
├── PRD_PRODUCT_ANALYSIS.md       Product strategy document
├── HANDOFF.md                    THIS FILE
├── DESIGN.md                     Design tokens
├── CONTEXT.md                    Agent context
├── AGENTS.md                     Agent routing instructions
├── README.md                     English product README
├── requirements.txt              Dependencies (stdlib only — empty)
└── .vercelignore                 Vercel build exclusions
```

---

## 5. API / Interface

### Backend Routes

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|:----:|
| GET | `/api/health` | Health check + version | No |
| POST | `/api/chat` | SSE streaming chat | No |
| GET | `/api/cities` | List all 36 cities | No |
| GET | `/api/cities/:city` | City detail | No |
| GET | `/api/cities/compare?cities=a,b` | Side-by-side city comparison | No |
| GET | `/api/map` | City coordinates + POIs | No |
| GET | `/api/config` | Client config (AMap keys, version) | No |
| GET | `/api/estimate` | Price estimates (7 cities) | No |
| POST | `/api/validate` | Trip validation | No |
| GET | `/api/tools` | List travel tools | No |
| GET | `/api/tools/:name` | Tool detail (packing/pricing/visa/phrases/emergency) | No |
| GET | `/api/visa/info?nationality=X&destination=China` | Visa policy lookup | No |
| POST | `/api/visa/generate` | Generate visa invitation letter | No |
| GET | `/api/visa/countries` | List supported nationalities | No |
| POST | `/api/auth/register` | Email/password registration | No |
| POST | `/api/auth/login` | Email/password login | No |
| POST | `/api/auth/logout` | Logout (invalidate token) | Yes |
| GET | `/api/auth/me` | Current user profile | Yes |
| POST | `/api/auth/google` | Google OAuth login | No |
| POST | `/api/auth/forgot-password` | Password reset email | No |
| POST | `/api/auth/reset-password` | Password reset confirm | Token |
| PUT | `/api/auth/profile` | Update user profile | Yes |
| GET | `/api/auth/trips` | List user trips | Yes |
| POST | `/api/auth/trips` | Create/save trip | Yes |
| DELETE | `/api/auth/trips/:id` | Delete trip | Yes |
| GET | `/api/auth/chat` | List chat conversations | Yes |
| POST | `/api/auth/chat` | Save chat conversation | Yes |
| GET | `/api/auth/chat/:id` | Chat detail | Yes |
| GET | `/api/admin/users` | List all users | Admin |
| GET | `/api/admin/users/:id` | User detail | Admin |
| DELETE | `/api/admin/users/:id` | Delete user | Admin |
| GET | `/api/admin/stats` | Platform stats | Admin |
| GET | `/api/admin/chat/:id` | Admin view chat detail | Admin |
| GET | `/*` | Static files (web/ then static/) | No |

### SSE Chat Event Types

| Event | Payload | Description |
|-------|---------|-------------|
| `message` | `{"token": "..."}` | Streamed text token |
| `message` | `{"split": true}` | Multi-bubble boundary |
| `message` | `{"image": {"key": "..", "url": "..", "label": ".."}}` | Inline city/theme image |
| `message` | `{"faq": {...}}` | FAQ match badge |
| `message` | `{"done": true}` | Stream complete |
| `error` | `{"error": "..."}` | Stream error |

---

## 6. Key Config

| Variable | Description | Source |
|----------|-------------|-------|
| `LLM_API_KEY` | DeepSeek API key | Vercel env |
| `LLM_MODEL` | Model name (default: `deepseek-chat`) | Vercel env |
| `LLM_BASE_URL` | API base (default: `https://api.deepseek.com/v1`) | Vercel env |
| `AMAP_KEY` | Gaode (AMap) JS API key | Vercel env |
| `AMAP_SECURITY_CODE` | Gaode security JS code | Vercel env |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Vercel env |
| `SESSION_SECRET` | JWT signing secret | Vercel env |
| `PORT` | Dev server port (default: 8080) | Local |

Fallback env vars: `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL`.

---

## 7. Core Logic / Data Flow

### Chat Flow

```
User Input → detectCity() + setPandaMood() → addMessage(user)
  → POST /api/chat {messages: [...], city: detected}
  → Backend: _handle_chat()
    → _match_faq(user_text) — optional FAQ expansion
    → _build_system_prompt(city, faq_match) — inject knowledge base
    → POST DeepSeek API (SSE stream with _yield_with_images)
      → ---SPLIT--- markers → split event (new bubble)
      → [img:city_key] markers → image event (inline city/food photo)
      → regular text → token event (streamed characters)
      → Backend "done" → done event
  → Frontend: SSE reader
    → token → currentBubble.innerHTML += token
    → split → commit + append new bubble div
    → image → render inline image bubble
    → faq → append faq badge bubble
    → done → finalize, enable input
```

### Auth Flow

```
Login via Google OAuth / Email+Password → POST /api/auth/google or /api/auth/login
  → Backend verifies with Google, creates/retrieves user
  → Returns JWT token + user profile
  → Frontend stores in localStorage('vp_token')
→ All /api/auth/* requests include Authorization: Bearer <token>
→ Token validated on each request; user/trip/chat data persist in SQLite via api/auth.py
→ Expired token → 401 → redirect to login
```

### Image Resolution

AI outputs `[img:beijing]` or `[img:food-chengdu]` in stream. Backend resolves:
1. `{key}.jpg` (exact match)
2. `city-{key}.jpg` (city photo)
3. `food-{key}.jpg` (food photo)
→ Found: emit `image` SSE event → Frontend renders inline
→ Not found: emit `token` with `[Label]` text fallback

---

## 8. Frontend / UI Component Map

```
App (VP IIFE — web/app.js)
├── Header
│   ├── Logo + Panda avatar (mood-reactive)
│   ├── Nav: Home / Chat / Map / Cities / Trips / Tools
│   ├── Version badge (reads from /api/health)
│   ├── Auth: Sign In button / User menu (avatar + logout)
│   └── Theme toggle (🌙/☀️)
├── Views
│   ├── view-home: Atlas Hero + Trust Layer + City Rail + Planner Entry
│   ├── view-chat: Full chat container + multi-bubble rendering + action rail
│   ├── view-map: Full China overview (AMap or Leaflet)
│   ├── view-trips: Recent / Saved grouped itineraries + timeline editor
│   ├── view-cities: All 36 city cards grid
│   └── view-tools: Travel toolkit cards (packing/visa/pricing/phrases/emergency)
├── Overlays
│   ├── chat-overlay (mobile): Slide-up chat panel
│   ├── city-detail: City modal with tabs (overview/food/hotels/map/tips)
│   ├── auth-modal: Sign In / Register / Forgot Password
│   └── admin panel: web/admin.html
├── Chat Container
│   ├── Messages: msg-user, msg-bot, msg-image bubbles
│   ├── Multi-bubble rendering with spacers
│   ├── Typing indicator (panda bouncing) + stop button
│   └── Suggested questions chips
├── Static Modules (loaded via script tags)
│   ├── auth.js — Google Sign-In, token management
│   ├── chat.js — Chat view logic
│   ├── landing.js — Home/landing view logic
│   ├── map.js — Map view logic
│   ├── profile.js — User profile view
│   ├── trips.js — Saved trips view
│   └── i18n.js — Bilingual labels (en/zh)
├── Bottom Nav (mobile): Home / Chat / Map / Trips / Tools
└── Footer: Credits, Clear Chat button
```

### Panda Mood System

Chat response tokens trigger mood-based avatar changes:
| Keyword Match | Mood | Emoji |
|:--------------|:----:|:-----:|
| eat/food/restaurant | food | 😋 |
| price/cost/budget | money | 💰 |
| visit/attraction/tour | sight | 🕶️ |
| tip/advice/remember | tip | 📌 |
| great/nice/perfect | happy | 😊 |
| let me/maybe/option | thinking | 🤔 |
| sorry/error/unable | sorry | 😅 |
| hotel/stay/room | hotel | 🏨 |
| flight/train/transport | transit | 🚄 |

---

## 9. Dependencies

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | Python 3.11 (stdlib only) | — |
| Frontend | Vanilla JS + CSS3 + HTML5 | — |
| LLM | DeepSeek V4 Flash | `deepseek-chat` |
| Auth | SQLite + JWT + Google OAuth | — |
| Maps | AMap JS API v2 / Leaflet + CartoDB dark | — |
| Icons | Google Material Icons + Emoji | — |
| Fonts | Inter + Noto Sans SC (Google Fonts) | — |
| Deployment | Vercel Serverless | `@vercel/python` |
| Images | Wikimedia Commons (CC-licensed) | 50 JPEGs |

**Zero pip dependencies for backend.** Pure Python stdlib: `urllib`, `json`, `os`, `re`, `ssl`, `pathlib`, `sqlite3` (legacy), `hmac`, `base64`, `hashlib`, `datetime`.

Frontend CDN deps: Leaflet.js, Google Sign-In (GSI), Google Fonts.

---

## 10. Next Steps

| Pri | Feature | Complexity | Notes |
|:---:|---------|:----------:|-------|
| 🟡 | **Post-trip feedback** — Review submission, rating, tag system | Medium | PRD_USER_SYSTEM §6.5, Iter 48 |
| 🟡 | **Expand ESTIMATE_DATA to all 36 cities** | Low | Only 7/36 have pricing data |
| 🟡 | **MAP_DATA POIs for all cities** | Low | 8/36 cities have POI lists |
| 🟡 | **Weather API integration** — api/weather.py exists but not used anywhere | Low | Wire into trip timeline |
| 🟢 | **PWA full support** — manifest + sw.js exist but not wired | Medium | Add service worker registration, offline caching |
| 🟢 | **Trip sharing** — Export as shareable link / text card | Medium | Social sharing |
| 🟢 | **Expand knowledge base** — 36 → 50+ cities | High | More coverage = more useful |
| 🟢 | **WeChat Mini Program / Telegram Bot** | High | Cross-platform expansion |

---

## 11. Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Login button not visible | `_updateAuthUI()` not called on page load | Should be fixed in v4.0.5+ |
| Version mismatch between frontend and API | `/api/health` returns hardcoded version | Frontend reads version from API; update `api/index.py` version string |
| Chat response empty | LLM API key missing or expired | Check `LLM_API_KEY` in Vercel env |
| AMap not loading | Missing `AMAP_KEY` or `AMAP_SECURITY_CODE` env vars | Check Vercel env; app falls back to Leaflet |
| City image not showing | AI used `[img:unknown_city]` where no image exists | Backend falls back to text label `[City Name]` |
| Git push fails | HTTPS connection reset | Retry or use `git push -u origin main` |
| Vercel build fails | Usually missing env vars in Vercel dashboard | Go to Vercel → Project → Settings → Environment Variables |
| Admin can't login via Google | Admin must use email/password account | Register separately as email/password user |

---

## 12. References

| Resource | Link |
|----------|------|
| Live site | https://www.go2china.space |
| GitHub repo | https://github.com/JTCAO515/VP-Hermes-Web |
| Vercel dashboard | https://vercel.com/jtcao515/vise-panda-2 |
| DeepSeek Console | https://platform.deepseek.com |
| Product PRD | `./PRD_PRODUCT_ANALYSIS.md` |
| User System PRD | `./docs/PRD_USER_SYSTEM.md` |
| ADR docs | `./docs/adr/` |
| PLAN | `./PLAN.md` |
| Changelog | `./CHANGELOG.md` |
| Hermes skill | `skill_view(name='handoff')` for resume workflow |

---

*End of Handoff.*

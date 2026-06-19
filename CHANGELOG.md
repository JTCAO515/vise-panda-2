# Changelog

## v3.2.0 — 2026-06-19
- ✨ **Trip Persistence** — 登录用户自动同步行程到后端 API
- 匿名用户继续使用 localStorage 降级
- API 保存 + 本地缓存双写，即时反馈

## v3.1.0 — 2026-06-19
- **⚙️ Admin Panel** — New standalone admin page (`/admin`), user management with stats dashboard. Role-based access (admin/ops only). Users table, delete user, real-time stats.
- **🔄 Admin Nav** — Admin link in user dropdown navigates to `/admin` in same tab instead of popup window.
- **🔢 Version Bump** — v3.0.8 → v3.1.0

## v3.0.8 (2026-06-14)
- **🔒 Security Hardening** — `_read_post` now caps request body at 100KB, wraps CONTENT_LENGTH parse in try/except, catches JSON decode errors
- **🛡️ XSS Prevention** — Image bubble URLs and labels sanitized via `escHtml()`, URL whitelist (relative or https only)
- **🧩 Multi-Bubble Abort** — `AbortController` now saves all split bubbles on stop, not just the last one
- **🌐 UTF-8 Safety** — SSE stream decoder uses `errors="replace"` to survive partial multi-byte characters at chunk boundaries
- **♻️ Code Consistency** — `_yield_with_images` uses `STATIC_DIR` constant instead of ad-hoc path construction

## v3.0.7 (2026-06-14)
- **🖼️ City Image Expansion** — 27 destination city photos downloaded from Wikimedia Commons, covering all major MAP_DATA cities
- **🎨 Rich Visual Chat** — AI now inserts `[img:city_key]` markers in responses → real city photos rendered inline between bubbles
- **📸 Zero-Dependency Image Pipeline** — Static JPEGs served from `/static/img/`, auto-detected by backend with city-/food-/exact-match fallback chain
- **🌏 Coverage** — 27/36 cities have high-quality landscape images; graceful text fallback for the remaining 9

## v3.0.6 (2026-06-14)
- **🧩 Multi-Bubble Responses** — AI now splits answers into logical sections (`---SPLIT---`), each rendered as a separate chat bubble with fade-in animation
- **🖼️ Rich Media Support** — `[img:city_key]` markers trigger inline city/food images between bubbles. Backend auto-routes to `city-*.jpg` or `food-*.jpg` from static assets
- **🎯 Accuracy Upgrade** — System prompt rewritten: AI must cite specific names/prices/distances, explicitly reference knowledge base, and avoid vague generalizations
- **💬 Streamlined SSE** — Backend emits `split` and `image` events in the SSE stream for real-time multi-bubble + image rendering
- **✨ Bubble Animations** — New `bubbleIn` CSS animation, bubble-spacer elements, image zoom-on-hover effect
- **📸 Image Fallback** — When no static image exists for a city key, gracefully renders as text label `[City]` instead of broken image
- **📱 Mobile UX Overhaul** — Bottom nav bar (app-style tabs) on phones, replaces header nav
- **💬 Chat Overlay Panel** — Chat opens as a slide-up panel on mobile instead of page switch
- **⌨️ Keyboard-Safe Heights** — Replaced `100vh` with `100dvh` for chat containers
- **🛡️ Safe Area Support** — Added `env(safe-area-inset-*)` for notched phones
- **👆 Larger Touch Targets** — All buttons minimum 44px on mobile, 16px input text prevents iOS zoom
- **🌀 Slide Transitions** — View changes animate with slide-in on mobile
- **🔄 Real-time Overlay Sync** — Chat overlay auto-syncs messages when new ones arrive

## v3.0.4 (2026-06-14)
- **🇬🇧 English-Native System Prompt** — Full system prompt rewritten in English. AI now defaults to English responses, matches user language.
- **🗺️ AMap (Gaode) Integration** — Dual-map engine: AMap with security key config, Leaflet fallback.
- **🔑 AMap Security Config** — `AMAP_KEY` + `AMAP_SECURITY_CODE` env vars via `/api/config` endpoint.
- **📄 Documentation** — Updated CHANGELOG.md, README.md (English-native rewrite), PLAN.md.

## v3.0.3 (2026-06-15)
- **🗺️ Map Tab** — Full China overview map with all 36 cities plotted. Supports AMap (Gaode) when API key configured, with Leaflet fallback.
- **📍 All Cities Coordinates** — Expanded map data from 8 cities to all 36 cities with lat/lng coordinates.
- **📄 Documentation** — Added CHANGELOG.md, updated PLAN.md with version tracking.

## v3.0.2 (2026-06-14)
- **🔍 FAQ Knowledge Base** — 10-category FAQ matching engine. Vague user queries are now expanded with deep keywords and answer guidance injected into the LLM system prompt.
- **🏷️ Version Badge** — Dynamic version number displayed in header top-right corner and footer, fetched from `/api/health`.
- **🎯 FAQ Match Badge** — When a FAQ category is matched, a small badge appears above the AI response showing what was detected.

## v3.0.1 (2026-06-14)
- **Phase 3 Complete** — Map views, price estimates, smart trip validation.
- **Leaflet Maps** — City detail modals with dark-theme Leaflet maps, POI markers by category.
- **Trip Persistence** — Save/load/share itineraries via localStorage.
- **Responsive Design** — Full mobile/tablet/desktop support with dark/light themes.
- **36-City Knowledge Base** — Comprehensive data for 36 Chinese cities (food, hotels, tips, pricing).
- **SSE Streaming Chat** — Real-time streaming with DeepSeek V4 Flash.
- **WC26 Architecture** — Python WSGI + stdlib + Vercel deployment pattern.

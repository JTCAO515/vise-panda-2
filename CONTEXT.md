# VisePanda Context

Last updated: 2026-06-22
Current version: v6.0.8
Repository: https://github.com/JTCAO515/VP-Codex-Web
Domain: https://go2china.space

## Product Definition

VisePanda is an English-language China travel workspace for international visitors. It combines AI travel consultation, city intelligence, entry readiness, practical travel tools, saved trip drafts, and account sync.

The product should feel like a mobile-friendly travel planning app, not a generic marketing site and not a raw chatbot.

## Primary User

The primary user is an international traveler planning a trip to mainland China or Greater China destinations. They need help with:

- Choosing cities and route order
- Understanding visa or transit readiness
- Estimating budget and logistics
- Planning high-speed rail or flight transfers
- Handling payment, translation, maps, and local friction
- Saving a trip draft for later

## Current Product Views

| View | Purpose | Current state |
| --- | --- | --- |
| Plan | First-screen travel planning workspace | Active main entry |
| Ask | Streaming AI consultation workflow | Active, mode-based |
| Cities | Searchable city cards | Active |
| Tools | Practical travel helper cards and details | Active |
| Trips | Guest and authenticated trip drafts | Active |
| Account | Email/password, email verification, optional Google OAuth | Active |
| Admin | Minimal user management | Internal only |

## Domain Vocabulary

| Term | Meaning |
| --- | --- |
| VisePanda | The product and brand |
| Plan | Home/workspace view for starting a trip |
| Ask | AI guide view |
| City fit | Comparing destinations by traveler preferences |
| Entry readiness | Visa, transit, documents, and pre-departure checks |
| Travel tools | Packing, pricing, phrases, emergency, visa helpers |
| Guest trip | Local-only trip draft saved in browser storage |
| Synced trip | Authenticated trip saved through backend persistence |
| Local guide | Deterministic fallback chat provider |
| DeepSeek route | Remote model route when configured |

## Current Architecture

```text
web/index.html + web/app.css + web/app.js
        |
        v
api/index.py
        |
        +-- api/auth.py
        +-- api/chat.py
        +-- api/cities.py
        +-- api/tools.py
        +-- api/visa.py
        +-- api/config.py
        |
        v
data/*.json + SQLite + optional external APIs
```

## Key Decisions

- Keep the frontend lightweight: static HTML, CSS, and vanilla JavaScript.
- Keep the backend simple: Python WSGI with standard-library-first implementation.
- Treat mobile portrait as a primary product surface.
- Keep the interface English-native.
- Use curated JSON datasets before adding complex retrieval infrastructure.
- Hide optional provider features until their environment variables are configured.
- Do not commit secrets or test-only exposed verification codes.

## Current External Providers

| Provider | Use | Required for basic local use |
| --- | --- | --- |
| DeepSeek | Remote AI chat route | No |
| OpenAI-compatible provider | Optional alternate chat route | No |
| Resend | Email verification delivery | No |
| Google OAuth | Optional Google login | No |

## Current Known Constraints

- SQLite is acceptable for the current MVP but should be revisited for scale.
- Chat output is still mostly conversational and needs stronger structured trip conversion.
- `web/app.js` and `api/auth.py` are high-change files and should be edited carefully.
- Real-device mobile QA is still recommended before major production releases.
- Historical docs may mention VP-Hermes, Supabase, or older v5/v3 plans; treat them as archive unless this document or `HANDOFF.md` says otherwise.

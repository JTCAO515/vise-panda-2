# VisePanda / VP-Codex-Web Handoff

Last updated: 2026-06-23
Current version: v6.1.1
Latest commit: pending local commit for verified responsive QA fixes
Repository: https://github.com/JTCAO515/VP-Codex-Web
Production domain: https://go2china.space
Deployment target: Vercel, routed through `api/index.py`

## 1. Project Summary

VisePanda is an English-language China travel workspace for international visitors. It combines destination discovery, visa and entry readiness, saved trips, travel tools, and a streaming AI guide into a lightweight web product.

The product is not a generic chatbot. The intended user journey is:

1. Start directly in the Ask / AI Guide surface.
2. Use quick prompts or type a planning question.
3. Reveal advanced chat settings only after the conversation starts.
4. Browse cities and practical tools as supporting context.
5. Save trip drafts locally as a guest or sync them after signing in.
6. Use account login, email verification, and optional Google OAuth for persisted user state.

The current product is a working MVP-plus foundation. It is suitable for continued iteration, production validation, and gradual commercial hardening. It is not yet a fully mature commercial platform.

## 2. Current Product Surface

### Ask

The first screen is the AI travel guide. It includes:

- A progressive chat welcome state
- First-screen prompt input
- High-value quick prompts
- Mode, provider, and depth controls after the conversation starts
- A viewport-bounded mobile chat shell with internal message scrolling

### Overview

The planning workspace remains available from the top bar. It includes:

- Destination input
- Trip length selector
- Entry / Route / Local snapshot cards
- Featured city strip
- Readiness checklist
- Mobile-first Ask AI shortcut

The latest v6.0.8 iteration focused heavily on this surface, especially mobile portrait usage.

### Ask

The Ask view is the AI guide workspace. It supports:

- Streaming server-sent-event responses
- Professional consultation modes
- Model/provider routing
- Depth controls
- Preset expert prompts

Current chat modes include itinerary, entry/visa, budget, transit, food/culture, safety/readiness, city-fit comparison, and general travel consulting.

### Cities

The Cities view renders searchable city cards from curated JSON data in `data/cities.json`.

It is currently good for discovery and lightweight comparison. It is not yet a full booking or POI product.

### Tools

The Tools view loads practical travel helpers from `data/tools.json`.

Current categories include packing, pricing, phrases, emergency, and visa-related helpers.

### Trips

Trips supports:

- Guest local drafts through browser storage
- Authenticated saved trips through backend persistence
- Basic trip creation and listing

This is usable, but the product loop between generated chat plans and structured trip timelines still needs more work.

### Account

The current account system supports:

- Email/password login
- Registration without collecting a name
- Email verification code flow
- Resend verification code
- Password reset flow
- Optional Google OAuth login
- Profile update
- Logout

Google login is hidden in the UI unless the required Google OAuth environment variables are configured.

### Admin

`web/admin.html` is a minimal admin surface for user management. It is intentionally small and should be treated as an internal operations tool, not a public product surface.

## 3. Current Technical Architecture

The project is intentionally lightweight.

```text
web/index.html
web/app.css
web/app.js
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
data/*.json
SQLite auth/trips storage
optional external model/email/OAuth providers
```

### Frontend

- Static HTML, CSS, and vanilla JavaScript
- Main files:
  - `web/index.html`
  - `web/app.css`
  - `web/app.js`
  - `web/sw.js`
  - `web/admin.html`
- No React, Next.js, or bundler is currently used.
- The app behaves like a small single-page app by switching `data-view-panel` sections.

### Backend

- Python WSGI app
- Standard library focused
- Main router: `api/index.py`
- Auth, users, sessions, trips, password reset, email verification, and admin live mostly in `api/auth.py`.

### Storage

- SQLite is used for local and current backend persistence.
- Auth DB path can be configured with `AUTH_DB_PATH`.
- There is historical documentation mentioning Supabase/Postgres, but the current active implementation should be treated as SQLite-based unless a future migration is explicitly planned.

### Deployment

- Vercel deployment through `vercel.json`
- All API and static routes go through `api/index.py`
- Static app files are served by the backend static response helper

## 4. Important Files

| File | Purpose |
| --- | --- |
| `README.md` | Fast project overview, API list, environment variables |
| `HANDOFF.md` | Current handoff document |
| `CHANGELOG.md` | Release notes |
| `api/index.py` | Main WSGI router and health/config endpoints |
| `api/config.py` | Public app config and version |
| `api/auth.py` | Auth, sessions, users, trips, admin, verification, OAuth |
| `api/chat.py` | Streaming AI chat and provider routing |
| `api/cities.py` | City API and map payload |
| `api/tools.py` | Travel tools API |
| `api/visa.py` | Visa helper API |
| `web/index.html` | Main product UI |
| `web/app.css` | Main responsive visual system |
| `web/app.js` | Main frontend state, data loading, auth, chat, navigation |
| `web/sw.js` | PWA service worker cache shell |
| `web/tests/*.test.js` | Frontend structure and stability tests |
| `tests/*.py` | Python API and contract tests |
| `data/*.json` | Curated product data |
| `static/img/*` | Product image assets |

## 5. Current Version State

### v6.1.1

Latest commit: pending local commit for verified responsive QA fixes

This release verifies the v2 optimization report against the live app before applying fixes:

- Fixed the guest Trips empty state so its action opens Ask instead of the removed dashboard nav target.
- Expanded the desktop chat shell on wide screens to reduce empty space on 27 inch displays.
- Tightened mobile chat after the first message: compact settings, bounded shell height, internal message scrolling, and no automatic post-send input focus on narrow screens.
- Added a mobile composing state that hides the bottom tab bar while the chat input is focused.
- Replaced the root `100vh` minimum with `100dvh`.
- Confirmed the auth dialog is already centered on desktop and the bottom nav is already four tabs.
- Cache busting is updated to `20260623-v611-responsive-qa2`.
- App version is updated to `6.1.1`.

### v6.1.0

This release shifts the product from a planning dashboard toward an AI-first travel agent:

- Ask is the default first screen.
- Primary navigation is now Ask, Cities, Tools, and Trips.
- Overview remains available from the top bar as a secondary planning surface.
- Chat opens with a focused AI agent welcome state, six quick prompts, and first-screen input.
- Mode, provider, depth, and detailed presets reveal after the first user message.
- SSE parsing is protected against malformed `data:` lines.
- Shared API calls and chat calls now use request timeouts.
- Chat sends Authorization headers when a session token exists.
- City cards use image fallback handling.
- Cache busting is updated to `20260623-v610-ai-first3`.
- App version is updated to `6.1.0`.

### v6.0.8

Latest commit: `4a58629 Polish mobile layout and app tabs`

This release improved mobile portrait layout and UI polish:

- Reworked the first screen into a planning-first workspace.
- Added Entry / Route / Local snapshot cards.
- Improved mobile bottom tab logic and visual selected states.
- Added app-style tab semantics with `role="tablist"`, `role="tab"`, `aria-selected`, and `role="tabpanel"`.
- Added a mobile `Ask AI` floating shortcut.
- Refined the visual system with brighter sky-blue surfaces and orange CTA treatment.
- Updated cache busting to `20260622-v608-mobile-ui3`.
- Updated app version to `6.0.8`.

### v6.0.7

Commit: `4d306d2 Modernize auth with email verification and Google OAuth`

This release modernized authentication:

- Registration no longer asks for name.
- Email/password registration requires email verification.
- Unverified users cannot log in by password.
- Added resend verification code endpoint.
- Added optional Resend email delivery.
- Added optional Google OAuth start/callback flow.
- Added `/api/auth/config` to expose auth feature availability.

### v6.0.6

Commit: `75a0954 Configure DeepSeek V4 Flash defaults for v6.0.6`

This release aligned chat defaults around DeepSeek V4 Flash.

### v6.0.5

Commit: `6f19049 Upgrade chat consultation workflow for v6.0.5`

This release upgraded chat into a more professional consultation workflow with modes, presets, provider routes, and depth.

### v6.0.4

Commit: `82ce874 Upgrade visual system for v6.0.4`

This release improved the overall visual system.

### v6.0.3

Commit: `c1e7976 Harden mobile UX states for v6.0.3`

This release hardened mobile UX states.

### v6.0.2

Commit: `230e05d Polish mobile portrait experience`

This release focused on mobile portrait interaction.

### v6.0.1

Commit: `fcd79f1 Rewrite VisePanda from clean foundation`

This was the clean rewrite baseline after moving into the new repository.

## 6. Local Development

Use PowerShell from the repository root.

```powershell
python -c "from api.index import app; from wsgiref.simple_server import make_server; server = make_server('127.0.0.1', 8765, app); print('http://127.0.0.1:8765'); server.serve_forever()"
```

Open:

```text
http://127.0.0.1:8765
```

Health check:

```powershell
curl.exe http://127.0.0.1:8765/api/health
```

Expected current health version:

```json
{"ok":true,"service":"VisePanda","version":"6.1.1"}
```

## 7. Test Commands

Run all Python contract tests:

```powershell
python -m unittest discover -s tests -v
```

Run all frontend structure tests:

```powershell
node --test web/tests/*.test.js
```

Run syntax checks:

```powershell
python -m py_compile api/config.py api/index.py
node --check web/app.js
```

Run whitespace diff check before committing:

```powershell
git diff --check
```

Latest known passing state from v6.1.1:

- Python tests: 18/18 passing
- Frontend tests: 18/18 passing
- `node --check web/app.js`: passing
- `python -m py_compile api/config.py api/index.py`: passing
- `git diff --check`: passing

## 8. Environment Variables

Do not commit real secrets. Configure them only in local shell or deployment environment.

### Required for production-quality AI chat

- `DEEPSEEK_API_KEY`: DeepSeek API key.
- `DEEPSEEK_MODEL`: recommended value is `deepseek-v4-flash`.

If no DeepSeek key is configured, the app falls back to local deterministic guide behavior.

### Optional OpenAI-compatible provider

- `OPENAI_COMPATIBLE_API_KEY`: optional provider key.
- `OPENAI_COMPATIBLE_BASE_URL`: optional provider base URL.
- `OPENAI_COMPATIBLE_MODEL`: optional provider model name.

These enable another OpenAI-compatible chat completions route.

### Google OAuth

- `APP_BASE_URL`: `https://go2china.space`.
- `GOOGLE_CLIENT_ID`: Google OAuth client id.
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret.
- `GOOGLE_REDIRECT_URI`: `https://go2china.space/api/auth/google/callback`.

If `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are not configured, the frontend hides the Google login button.

### Email verification

- `RESEND_API_KEY`: Resend API key.
- `EMAIL_FROM`: verified sender, for example `VisePanda <verified-sender@go2china.space>`.

If `RESEND_API_KEY` is missing, the backend uses development delivery behavior.

### Auth and admin

- `AUTH_DB_PATH`: optional SQLite database path.
- `ADMIN_EMAIL`: explicit admin seed email.
- `ADMIN_PASSWORD`: explicit strong admin seed password.

Weak admin defaults such as `admin123` are ignored.

### Test-only flags

- `AUTH_EXPOSE_EMAIL_CODE=1`
- `AUTH_EXPOSE_RESET_TOKEN=1`

Never enable these in production.

## 9. API Surface

Public:

- `GET /api/health`
- `GET /api/config`
- `GET /api/cities`
- `GET /api/cities/:id`
- `GET /api/map`
- `GET /api/tools`
- `GET /api/tools/:id`
- `GET /api/visa/countries`
- `GET /api/visa/info?nationality=us`
- `POST /api/visa/generate`
- `GET /api/chat`
- `POST /api/chat`

Auth:

- `POST /api/auth/register`
- `POST /api/auth/verify-email`
- `POST /api/auth/resend-verification`
- `GET /api/auth/google/start`
- `GET /api/auth/google/callback`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `POST /api/auth/update-profile`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `GET /api/auth/config`

Trips:

- `GET /api/trips`
- `POST /api/trips`
- `DELETE /api/trips/:id`

Admin:

- `GET /api/admin/users`
- `DELETE /api/admin/users/:id`

## 10. Frontend Interaction Notes

The main app is driven by `web/app.js`.

Important frontend state:

- `state.token`
- `state.user`
- `state.cities`
- `state.tools`
- `state.chat`
- `state.authMode`
- `state.pendingEmail`
- `state.authConfig`

Important frontend functions:

- `setView(view)`: switches Plan / Ask / Cities / Tools / Trips
- `loadCities()`: loads and renders city cards
- `loadTools()`: loads and renders tools
- `loadTrips()`: loads guest or authenticated trips
- `sendChat(message, overrides)`: streams chat output
- `loadChatOptions()`: loads chat modes/providers/depths
- `loadAuthConfig()`: checks Google/email feature availability
- `updateAuthUi()`: controls auth dialog state
- `restoreSession()`: restores authenticated user
- `bindEvents()`: attaches most frontend event handlers
- `boot()`: app startup entrypoint

When editing the frontend, be careful with:

- Mobile bottom navigation safe area
- Chat form and bottom nav overlap
- Service worker cache busting
- `hidden` and `is-hidden` state staying in sync
- Auth dialog mobile bottom sheet layout
- Horizontal overflow on 390px portrait width

## 11. Auth Notes

The auth system is in `api/auth.py`.

Registration flow:

1. User enters email/password.
2. Backend creates or updates an unverified user.
3. Backend creates a six-digit email verification code.
4. If Resend is configured, code is emailed.
5. User submits code to `/api/auth/verify-email`.
6. Backend marks email verified and returns session token.

Password login requires `email_verified_at` to be present.

Google OAuth flow:

1. Frontend links to `/api/auth/google/start`.
2. Backend creates OAuth state and redirects to Google.
3. Google redirects back to `/api/auth/google/callback`.
4. Backend validates state, exchanges code, fetches user info, and creates/links user.
5. Callback page stores token in `sessionStorage` and redirects home.

Do not log or commit auth tokens, verification codes, OAuth secrets, or API keys.

## 12. Chat Notes

Chat is routed through `api/chat.py`.

Important behavior:

- `GET /api/chat` exposes available modes/providers/depths.
- `POST /api/chat` streams SSE tokens.
- Frontend parses `data:` lines and appends streamed tokens into the active AI message.
- If no remote model is configured, local deterministic behavior keeps the app usable.

The current product direction is to make chat more professional and specialized, not just more casual. Future iterations should improve:

- Question quality
- Follow-up interviewing
- Mode-specific system instructions
- Provider routing
- Structured itinerary extraction into Trips
- Tool/city context injection

## 13. Mobile UI Notes

v6.1.1 specifically targets an AI-first mobile portrait flow.

Verified in browser QA at 390x844:

- No horizontal overflow
- Four primary tabs exist: Ask, Cities, Tools, Trips
- Ask is selected by default
- Active tab updates `aria-selected`
- Chat panel is the first visible product surface
- Welcome state, quick prompts, input, and send button fit in the first mobile viewport
- Advanced chat controls reveal after the first message in a compact two-column mobile layout
- The chat shell stays bounded to the mobile viewport after the conversation starts
- The bottom tab bar hides while the chat input is focused
- Browser console had no relevant errors

Known caveat:

- Browser QA used the in-app browser at desktop width and 390x844 mobile width.
- Local service worker/cache can retain old CSS during development; bump cache strings when changing frontend assets.

## 14. Service Worker and Cache

Current service worker cache name:

```js
visepanda-shell-v611-responsive-qa2
```

Current frontend cache busting query:

```text
20260623-v611-responsive-qa2
```

When changing frontend CSS or JS, update:

- `web/index.html`
- `web/admin.html`
- `web/sw.js`
- `web/tests/stability-ui.test.js`

This prevents phones and PWA installs from staying on stale UI.

## 15. Deployment Checklist

Before pushing:

1. Confirm no secrets are in tracked files.
2. Run backend tests.
3. Run frontend tests.
4. Run syntax checks.
5. Run `git diff --check`.
6. Confirm version numbers are aligned if releasing a named version.
7. Confirm service worker cache name and asset query strings changed after frontend edits.

After pushing:

1. Confirm Vercel deployment succeeded.
2. Open `https://go2china.space`.
3. Check `/api/health`.
4. Test mobile portrait layout.
5. Test Sign in / Create account / Verify email.
6. Test Ask preset and manual chat.
7. Test Cities, Tools, and Trips tabs.

## 16. Current Risks and Known Gaps

### Product gaps

- Chat answers are improving, but still need more professional multi-step consultation.
- Chat output is not yet deeply converted into structured trip plans.
- City cards and tools are useful but still mostly informational.
- Trips need stronger integration with Chat and Tools.
- Visa/entry guidance must avoid overclaiming and should encourage verification.

### Engineering gaps

- `web/app.js` is growing and should eventually be split by feature, but do not refactor casually.
- `api/auth.py` owns many responsibilities and should be handled carefully.
- SQLite is fine for current MVP but may need managed Postgres later.
- Admin is functional but minimal.
- No full browser E2E test suite exists yet.

### UX gaps

- Mobile layout is now stronger, but should be tested on real iOS Safari and Android Chrome.
- Headless screenshot tooling showed viewport quirks; real-device visual QA is still recommended.
- The app should eventually add clearer loading states for provider-backed chat latency.

## 17. Recommended Next Iterations

### Next iteration: Chat depth and professionalization

Focus:

- Add more professional preset question trees.
- Make modes ask targeted follow-up questions.
- Route different prompt classes to different providers where configured.
- Add structured response sections: assumptions, questions, route, budget, risks, next actions.
- Add a path from strong chat output to a saved trip draft.

Suggested files:

- `api/chat.py`
- `web/index.html`
- `web/app.js`
- `web/app.css`
- `web/tests/chat-stream.test.js`
- `web/tests/stability-ui.test.js`
- `tests/test_api_contract.py`

### Following iteration: Trip planning loop

Focus:

- Convert AI route output into a saveable trip object.
- Add trip detail view or expandable trip cards.
- Connect trip readiness with tools.

### Following iteration: Production auth/email validation

Focus:

- Test Resend delivery on the real domain.
- Test Google OAuth on `go2china.space`.
- Confirm redirect URI and domain settings.
- Confirm production never exposes verification codes.

### Following iteration: Data quality

Focus:

- Strengthen city data.
- Add practical foreign-traveler details.
- Add payment, SIM/eSIM, maps, rail, and hotel-area guidance.

### Following iteration: Browser E2E tests

Focus:

- Add a small Playwright or equivalent smoke suite.
- Cover Plan -> Ask, Register -> Verify, Cities search, Tools open, Trips guest save.

## 18. Do Not Do These First

- Do not rewrite the frontend stack before the product loop is clearer.
- Do not migrate storage before production auth and Trips behavior are stable.
- Do not commit API keys or OAuth secrets.
- Do not enable `AUTH_EXPOSE_EMAIL_CODE=1` in production.
- Do not treat historical Supabase docs as current implementation truth without checking code.
- Do not make large refactors in `web/app.js` and `api/auth.py` without adding tests first.

## 19. Quick New-Agent Start

If you are a new agent taking over:

1. Read `README.md`.
2. Read this `HANDOFF.md`.
3. Run:

```powershell
python -m unittest discover -s tests -v
node --test web/tests/*.test.js
```

4. Start local server:

```powershell
python -c "from api.index import app; from wsgiref.simple_server import make_server; server = make_server('127.0.0.1', 8765, app); print('http://127.0.0.1:8765'); server.serve_forever()"
```

5. Open `http://127.0.0.1:8765`.
6. Check Plan, Ask, Cities, Tools, Trips.
7. Check mobile portrait at about 390x844.
8. Only then start editing.

## 20. Final Status

The project is in a good continuation state.

The current foundation has:

- Working product shell
- Working AI guide flow
- Working account system with verification
- Optional Google OAuth
- Optional Resend email delivery
- Guest and authenticated trip persistence
- Searchable city data
- Practical tools
- Mobile-first app-style navigation
- Contract and frontend structure tests
- Vercel deployment path

The best next move is not a rewrite. The best next move is to keep strengthening the professional travel-planning loop: better chat questions, better provider routing, better structured trip output, and tighter connection between Chat, Trips, Cities, and Tools.

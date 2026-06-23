# VisePanda

VisePanda is an English-language China travel workspace for international visitors. It combines city discovery, visa readiness, saved trips, practical travel tools, and a streaming AI guide behind a small Vercel + Python WSGI deployment.

Active repository: `https://github.com/JTCAO515/VP-Codex-Web`

## Current Version

`v6.1.1` keeps the AI-first flow and tightens verified responsive issues: Trips empty states return to Ask, wide desktop chat uses more of the screen, and mobile chat keeps the composer and tab bar from fighting the keyboard.

## Documentation

- `HANDOFF.md`: full current handoff and next-agent guide.
- `CONTEXT.md`: product context, active architecture, and constraints.
- `PLAN.md`: active five-round iteration plan.
- `DESIGN.md`: current UI system and mobile interaction rules.
- `docs/ROADMAP.md`: phased product roadmap.
- `docs/PRD_USER_SYSTEM.md`: user-system product requirements.
- `docs/TECH_USER_SYSTEM.md`: user-system technical notes.

## Product Surface

- Ask: default first-screen AI travel guide with quick prompts, consultation modes, progressive settings, model routing, and a deterministic local fallback.
- Overview: secondary planning workspace with destination input, featured cities, and readiness checklist.
- Cities: searchable China destination cards built from the curated city dataset.
- Tools: packing, pricing, phrase, emergency, and visa helper views.
- Trips: authenticated saved trips with a guest local draft mode.
- Admin: minimal user management console gated by explicit admin credentials.

## Tech Stack

- Backend: Python WSGI, standard library only.
- Frontend: static HTML, CSS, and vanilla JavaScript.
- Deployment: Vercel `@vercel/python`, all routes through `api/index.py`.
- Storage: SQLite for users, sessions, password resets, and trips.
- Data: JSON datasets in `data/` plus image assets in `static/img/`.

## Local Run

```powershell
python -c "from api.index import app; from wsgiref.simple_server import make_server; server = make_server('127.0.0.1', 8765, app); print('http://127.0.0.1:8765'); server.serve_forever()"
```

Useful checks:

```powershell
python -m unittest discover -s tests -v
node --test web/tests/*.test.js
```

## Environment

- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`: optional; enables Google OAuth login.
- `GOOGLE_REDIRECT_URI`: optional; defaults to `/api/auth/google/callback` on the app base URL.
- `RESEND_API_KEY` and `EMAIL_FROM`: optional; sends email verification codes through Resend.
- `AUTH_EXPOSE_EMAIL_CODE=1`: test-only verification code exposure.
- `DEEPSEEK_API_KEY`: optional; enables remote AI answers for `/api/chat`.
- `DEEPSEEK_MODEL`: optional; defaults to `deepseek-v4-flash`.
- `OPENAI_COMPATIBLE_API_KEY`: optional key for another OpenAI-compatible chat completions provider.
- `OPENAI_COMPATIBLE_BASE_URL`: optional base URL for the compatible provider, for example a `/v1` endpoint.
- `OPENAI_COMPATIBLE_MODEL`: optional model name for the compatible provider.
- `AUTH_DB_PATH`: optional SQLite path for local or test storage.
- `ADMIN_EMAIL` and `ADMIN_PASSWORD`: optional admin seed. Weak defaults such as `admin123` are ignored.
- `AUTH_EXPOSE_RESET_TOKEN=1`: test-only reset token exposure.

## API

- `GET /api/health`
- `GET /api/config`
- `POST /api/chat`
- `GET /api/cities`
- `GET /api/cities/:id`
- `GET /api/map`
- `GET /api/tools`
- `GET /api/tools/:id`
- `GET /api/visa/countries`
- `GET /api/visa/info?nationality=us`
- `POST /api/visa/generate`
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
- `GET /api/trips`
- `POST /api/trips`
- `DELETE /api/trips/:id`
- `GET /api/admin/users`
- `DELETE /api/admin/users/:id`

## Structure

```text
api/        WSGI router and API modules
data/       JSON knowledge and policy datasets
static/img/ Visual assets used by the app
tests/      Python contract tests
web/        Static app, PWA manifest, service worker, and Node tests
vercel.json Vercel routing configuration
```

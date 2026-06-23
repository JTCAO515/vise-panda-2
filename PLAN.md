# VisePanda Active Plan

Last updated: 2026-06-22
Current version: v6.0.8

## Current Objective

Continue turning VisePanda into a professional China travel planning workspace. The next work should strengthen the product loop rather than rewrite the stack.

The preferred loop is:

```text
Plan -> Ask -> structured answer -> saved Trip -> related Cities/Tools -> refined Ask
```

## Current Baseline

Already shipped in the current repository:

- Clean static frontend foundation
- Mobile-first Plan workspace
- App-style bottom tabs
- Streaming AI Ask workflow
- Professional chat modes and presets
- Email/password auth with email verification
- Optional Google OAuth
- Optional Resend email delivery
- Guest and authenticated trip drafts
- Searchable city cards
- Travel tools
- Minimal admin user management
- Python and Node test coverage

## Five-Round Iteration Plan

### Round 1: Chat Professionalization

Goal: make Ask feel like a professional travel consultant.

Work:

- Add better preset question groups.
- Make each mode ask sharper follow-up questions.
- Add response sections such as assumptions, key questions, itinerary, budget, risks, and next actions.
- Improve provider routing by task type.
- Add tests for mode/depth/provider contracts.

Primary files:

- `api/chat.py`
- `web/index.html`
- `web/app.js`
- `web/app.css`
- `tests/test_api_contract.py`
- `web/tests/chat-stream.test.js`
- `web/tests/stability-ui.test.js`

### Round 2: Structured Trip Output

Goal: convert useful AI answers into saved trip drafts.

Work:

- Detect structured itinerary sections.
- Add "Save as trip" flow from Ask.
- Store route summary, cities, dates, and notes.
- Improve Trips card detail display.

Primary files:

- `api/auth.py`
- `web/app.js`
- `web/index.html`
- `web/app.css`
- `tests/test_trips_contract.py`

### Round 3: Cities and Tools Integration

Goal: make Cities and Tools influence planning instead of being separate content islands.

Work:

- Add "Ask about this city" from city cards.
- Add "Add to readiness" or "Use in plan" from tool detail.
- Pass selected city/tool context into Ask prompts.
- Improve empty and loading states.

Primary files:

- `api/cities.py`
- `api/tools.py`
- `web/app.js`
- `web/app.css`

### Round 4: Production Auth and Email QA

Goal: make the account system production-ready on `go2china.space`.

Work:

- Verify Google OAuth redirect URI on production.
- Verify Resend sender and delivery.
- Confirm production does not expose email codes or reset tokens.
- Add browser smoke tests for register -> verify -> login.

Primary files:

- `api/auth.py`
- `web/app.js`
- `tests/test_auth_contract.py`

### Round 5: Real Mobile Polish and E2E

Goal: reduce mobile release risk.

Work:

- Add a real browser smoke test suite.
- Test 390x844, 430x932, tablet, and desktop.
- Verify no tab/input overlap.
- Verify Ask, Cities, Tools, Trips, and auth bottom sheet.

Primary files:

- `web/tests/*`
- possible future `e2e/` folder
- `web/app.css`
- `web/app.js`

## Near-Term Rules

- Keep changes scoped.
- Keep the current stack unless there is a concrete reason to migrate.
- Add tests when touching shared auth, chat, trips, or navigation behavior.
- Update cache busting when changing frontend CSS or JS.
- Update `README.md`, `HANDOFF.md`, `CHANGELOG.md`, and this plan when shipping a named version.

## Do Not Prioritize Yet

- Full frontend framework migration
- Full database migration
- Payment or subscription features
- Large map/POI rebuild
- Public admin dashboard polish
- Heavy design-system extraction before core workflows settle

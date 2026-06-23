# Active Iteration Plan

Last updated: 2026-06-22
Current version: v6.0.8

## Baseline

The current repository has shipped the v6.0.x rebuild series:

| Version | Focus |
| --- | --- |
| v6.0.1 | Clean rewrite foundation |
| v6.0.2 | Mobile portrait polish |
| v6.0.3 | Mobile UX state hardening |
| v6.0.4 | Visual system upgrade |
| v6.0.5 | Chat consultation workflow |
| v6.0.6 | DeepSeek V4 Flash defaults |
| v6.0.7 | Email verification and Google OAuth |
| v6.0.8 | Mobile layout and app tabs |

## Iteration 1: Professional Chat

Status: next recommended iteration

### Goal

Make Ask more detailed, professional, and mode-aware.

### Scope

- Add more preset questions.
- Make mode labels and prompt behavior more specialized.
- Add structured response instructions.
- Route task types to configured providers.
- Improve frontend prompt grouping for mobile.

### Acceptance Criteria

- Ask view exposes clear professional presets.
- A user can choose mode, provider, and depth without layout breakage.
- Chat still streams token-by-token.
- Local fallback still works.
- Frontend and backend tests pass.

## Iteration 2: Ask to Trip Draft

### Goal

Let users save useful Ask output into Trips.

### Scope

- Add a save-from-chat action.
- Store route title, destination, rough dates or duration, and notes.
- Show saved output in Trips.
- Preserve guest fallback.

### Acceptance Criteria

- Guest can save a local draft.
- Signed-in user can save a synced draft.
- Empty trip states still work.
- Tests cover guest and authenticated behavior.

## Iteration 3: City and Tool Context

### Goal

Connect content surfaces to Ask.

### Scope

- "Ask about this city" action.
- "Use this tool in my plan" action.
- Pass context into the chat prompt.
- Improve status text and toasts.

### Acceptance Criteria

- City context appears in Ask prompt.
- Tool context appears in Ask prompt.
- No tab or mobile overflow regressions.

## Iteration 4: Production Account QA

### Goal

Confirm account flows on production domain.

### Scope

- Google OAuth production redirect test.
- Resend email delivery test.
- Register -> verify -> profile flow.
- Password reset smoke test.

### Acceptance Criteria

- Google button appears only when configured.
- Email verification sends through configured provider.
- Test-only code exposure is not enabled in production.
- User can complete the normal account flow.

## Iteration 5: Browser Smoke Suite

### Goal

Add basic rendered UI regression coverage.

### Scope

- Plan first screen smoke test.
- Mobile tab smoke test.
- Ask preset smoke test.
- Auth dialog smoke test.
- Cities search smoke test.
- Tools open smoke test.
- Trips guest save smoke test.

### Acceptance Criteria

- Smoke suite can run locally.
- It does not require production secrets.
- It catches blank page, tab failure, and major mobile overflow.

## Iteration Hygiene

For every iteration:

1. Keep edits scoped.
2. Update docs when behavior changes.
3. Update cache busting after frontend changes.
4. Run Python tests.
5. Run frontend tests.
6. Run syntax checks.
7. Run `git diff --check`.
8. Commit with a clear message.

# VisePanda Agent Instructions

VisePanda is an English-first China travel planning app for international visitors. The active repository is `JTCAO515/VP-Codex-Web`, deployed for `go2china.space`.

## Start Here

Read these current documents before making broad changes:

1. `HANDOFF.md`
2. `README.md`
3. `CONTEXT.md`
4. `PLAN.md`
5. `DESIGN.md`

For account work, also read:

- `docs/PRD_USER_SYSTEM.md`
- `docs/TECH_USER_SYSTEM.md`

## Current Engineering Rules

- Keep the Python WSGI backend and static frontend structure unless the task explicitly requires migration.
- Treat mobile portrait as the primary UI surface.
- Keep the product English-native.
- Do not commit real API keys, PATs, OAuth secrets, email-provider secrets, or database credentials.
- Update visible version markers and service worker cache names when frontend assets change.
- Prefer small, testable changes over broad rewrites.

## Useful Checks

```powershell
python -m unittest discover -s tests -v
node --test web/tests/*.test.js
```

Documentation-only changes should still pass whitespace checks and secret scans.

## Historical Notes

Older documents may mention `VP-Hermes-Web`, v3.x, v5.x, or previous UI directions. They are archive context, not the current plan, unless a current document points to them directly.

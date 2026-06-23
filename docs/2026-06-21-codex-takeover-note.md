# Codex Takeover Note

Date: 2026-06-21
Updated: 2026-06-22
Current version: v6.0.8

This repository was initialized from the historical `VP-Hermes-Web` v5.0.9 baseline and is now the active Codex working repository.

- Active repository: `https://github.com/JTCAO515/VP-Codex-Web`
- Production domain: `https://go2china.space`
- Historical source baseline: `https://github.com/JTCAO515/VP-Hermes-Web`
- Working branch: `main`

## Current Takeover State

The project is no longer just a copied baseline. It has gone through the v6.0.1 to v6.0.8 Codex iteration path:

- frontend structure was rewritten from scratch while preserving the product idea;
- chat gained professional presets and multi-provider routing;
- auth gained email/password registration, email verification, and Google OAuth hooks;
- mobile portrait UI became the main interaction target;
- documentation has been refreshed so current entry points no longer depend on old v3 or v5 assumptions.

## Source Of Truth

Use these files first:

1. `HANDOFF.md`
2. `README.md`
3. `CONTEXT.md`
4. `PLAN.md`
5. `DESIGN.md`
6. `docs/ROADMAP.md`
7. `docs/ITERATION_PLAN.md`
8. `docs/TECH_USER_SYSTEM.md`
9. `docs/PRD_USER_SYSTEM.md`

Old files under dated archive paths, `docs/superpowers/`, and `docs/adr/` can still explain why earlier choices were made, but they are not the current product plan unless a current entry document links to them explicitly.

## Operating Stance

- Keep VisePanda English-first for international China travel users.
- Preserve the lightweight Python WSGI plus static frontend architecture unless there is a specific migration plan.
- Treat mobile portrait as the primary UX.
- Avoid committing real PATs, API keys, OAuth secrets, or email-provider secrets.
- Update service worker cache names and visible version markers whenever frontend assets change.

## Current Validation

Before handing off a meaningful code change, run:

```powershell
python -m unittest discover -s tests -v
node --test web/tests/*.test.js
```

For documentation-only changes, at minimum run a whitespace check and a secret scan over the changed docs.

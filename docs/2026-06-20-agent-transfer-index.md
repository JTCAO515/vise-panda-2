# VisePanda Documentation Index

Last updated: 2026-06-22
Current version: v6.0.8

This file is the reading map for the next agent. It separates current source-of-truth documents from historical reference material so an incoming agent does not accidentally follow old v3/v5 plans.

## Read First

1. `HANDOFF.md`
   Complete project handoff, current status, architecture, risks, and next work.

2. `README.md`
   Repository overview, local run commands, environment variables, API list, and structure.

3. `CONTEXT.md`
   Product identity, users, app surfaces, architecture, and active constraints.

4. `PLAN.md`
   Active five-round iteration plan after v6.0.8.

5. `DESIGN.md`
   Current visual system and mobile interaction rules.

## Current Product And Engineering Docs

- `docs/ROADMAP.md`: phased product roadmap.
- `docs/ITERATION_PLAN.md`: next five implementation rounds.
- `docs/PRD_USER_SYSTEM.md`: account-system product requirements.
- `docs/TECH_USER_SYSTEM.md`: account-system technical notes.
- `PRD_PRODUCT_ANALYSIS.md`: current product strategy and opportunity framing.
- `CHANGELOG.md`: release history.

## Technical Reference

- `docs/adr/*`: architecture decision records. These explain decisions such as WSGI, DeepSeek, and knowledge-base structure.
- `docs/agents/*`: agent workflow notes, issue labels, and domain conventions.
- `docs/superpowers/*`: older specs and plans from the handoff/restructure period.

These files are useful when changing a specific area, but they should not override the current handoff, plan, design, or roadmap.

## Historical Archive

The repository still contains dated documents from the VP-Hermes and early VisePanda transition period. Many of them mention:

- old versions such as v3.x or v5.x;
- the historical `VP-Hermes-Web` repository;
- older UI directions such as darker panda/ink styling;
- older login assumptions that did not include Google OAuth or real email verification.

Treat those as historical background unless they have been explicitly refreshed in the v6.0.8 documentation set.

## Recommended Workflow For A New Agent

1. Read `HANDOFF.md`, `README.md`, `CONTEXT.md`, and `PLAN.md`.
2. Check `git status` before editing.
3. If touching UI, read `DESIGN.md` and update cache/version markers.
4. If touching auth, read `docs/PRD_USER_SYSTEM.md` and `docs/TECH_USER_SYSTEM.md`.
5. If touching chat, inspect `api/chat.py`, `web/app.js`, and the current tests before changing prompts or model routing.
6. Run the relevant tests before commit.
7. Keep secrets out of commits.

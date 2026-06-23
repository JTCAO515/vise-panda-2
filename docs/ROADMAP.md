# VisePanda Roadmap

Last updated: 2026-06-22
Current version: v6.0.8

## Current Status

VisePanda is now a working lightweight China travel workspace with:

- Mobile-first Plan surface
- Streaming Ask workflow
- Professional chat modes and presets
- Email/password auth with email verification
- Optional Google OAuth
- Optional Resend email delivery
- Cities, Tools, and Trips views
- Basic admin user management
- Python and frontend structure tests

The next roadmap should focus on product depth and workflow integration.

## Phase 1: Chat Professionalization

Priority: highest

Goal: make Ask feel like a professional China travel consultant.

Deliverables:

- Stronger mode-specific prompt handling
- Better expert preset questions
- More follow-up interview behavior
- Structured answer sections
- Provider routing by task type
- Tests for modes, providers, and depth

Why this matters:

Ask is the product's core differentiator. Better chat quality will improve every downstream view.

## Phase 2: Ask to Trips

Priority: high

Goal: convert useful AI output into saved trip drafts.

Deliverables:

- "Save as trip" from Ask
- Structured route summary
- Day or section parsing
- Trips detail expansion
- Guest-to-account upgrade path

Why this matters:

The product needs a stronger loop than one-off chat answers.

## Phase 3: Cities and Tools Integration

Priority: high

Goal: make Cities and Tools influence planning.

Deliverables:

- Ask about this city
- Use this tool in plan
- City/tool context passed into Ask prompts
- Better readiness checklist flow

Why this matters:

The app already has useful data, but the modules need to reinforce each other.

## Phase 4: Production Auth Validation

Priority: medium-high

Goal: make account flows reliable on the real domain.

Deliverables:

- Production Google OAuth test
- Production Resend email test
- Verification-code security confirmation
- Browser smoke coverage for register -> verify -> login

Why this matters:

The account system is now real enough that production behavior must be validated carefully.

## Phase 5: E2E and Real Mobile QA

Priority: medium

Goal: reduce regression risk.

Deliverables:

- Browser smoke test suite
- Mobile viewport coverage
- Auth dialog checks
- Plan -> Ask flow checks
- Cities / Tools / Trips checks

Why this matters:

The project is a mobile-first web app. Structural tests are useful, but real rendered QA is still needed.

## Later Opportunities

- Managed Postgres migration
- Better trip timeline rendering
- Visa document pack generation
- City comparison surface
- More detailed budget model
- Real map/POI layer
- PWA polish
- SEO landing pages
- Payment or subscription model

## Explicit Non-Goals For Now

- Full frontend framework migration
- Large database migration before product loop hardening
- Complex admin dashboard
- Heavy map rebuild
- Payment implementation
- Rewriting historical docs/specs as if they were current commitments

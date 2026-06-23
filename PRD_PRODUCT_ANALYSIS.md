# VisePanda Product Analysis

Last updated: 2026-06-22
Current version: v6.0.8
Domain: `go2china.space`

## One-Line Product

VisePanda is an English-language China travel workspace that combines AI trip planning, curated city knowledge, practical travel tools, saved trips, and lightweight account features.

## Vision

Make planning a China trip feel like asking a precise local travel expert who understands visa readiness, city fit, route logic, budget, language friction, and practical day-by-day tradeoffs.

VisePanda should not feel like a generic chatbot with a travel skin. The product promise is:

- structured China-specific planning;
- fast mobile-first interaction;
- professional travel questions before answers;
- trustworthy city and tool context;
- saved work when users are ready to commit.

## Primary Users

| Segment | Need | Product Fit |
| --- | --- | --- |
| First-time international visitors | Understand where to go, when to go, and how hard the trip will be | Plan workspace, Ask presets, visa/tool readiness |
| High-intent independent travelers | Build a practical itinerary without agency friction | Professional chat, saved trips, city cards |
| Foreign residents in China | Find weekend or short-break ideas | City discovery and quick Ask flows |
| English-speaking planners helping others | Produce a shareable draft quickly | Structured answers and saved trip artifacts |

## Positioning

VisePanda sits between a general LLM and a travel booking platform.

General LLMs can answer broadly, but they do not automatically keep China-specific structure, saved trip state, and curated destination context together.

Booking platforms are strong once a user knows what to buy, but weaker during the early question-heavy planning phase.

VisePanda owns the planning middle:

1. understand traveler intent;
2. ask the right follow-up questions;
3. generate a usable route or decision;
4. connect the answer to cities, tools, and saved trips.

## Current Product Surface

- Plan: first-screen planning workspace with destination entry, readiness cards, featured cities, and mobile Ask access.
- Ask: streaming AI guide with consultation presets, professional context, provider routing, and local fallback.
- Cities: curated China destination cards backed by local JSON data.
- Tools: packing, pricing, phrase, emergency, and visa helper surfaces.
- Trips: authenticated saved trips plus guest local draft behavior.
- Account: email/password registration, email verification, Google OAuth hooks, profile, reset, and session lookup.
- Admin: minimal user-management console for explicit admin users.

## Differentiators

- China-specific travel focus instead of generic global itinerary generation.
- English-native interface for international users.
- Mobile portrait as the primary interaction surface.
- Lightweight architecture that deploys quickly on Vercel.
- Curated JSON knowledge base plus AI responses.
- Account system only appears where it protects user value, such as saving trips.

## Product Loop

```text
Plan -> Ask -> structured answer -> saved Trip -> related Cities/Tools -> refined Ask
```

The next iterations should tighten this loop rather than adding unrelated surfaces.

## Success Metrics

| Metric | Signal |
| --- | --- |
| Ask completion | Users receive a useful answer without retrying many times |
| Follow-up depth | Users answer professional clarification questions instead of bouncing |
| Save rate | Users save an itinerary or draft after a useful Ask session |
| Mobile engagement | Portrait users can navigate and submit without layout friction |
| Verification completion | Email users finish account confirmation |
| Fallback quality | Local fallback answers remain useful when external APIs are unavailable |

## Current Strengths

- Clear v6.0.8 mobile-first UI direction.
- Professional chat presets and multi-provider architecture.
- Practical account system foundation.
- Simple deploy path and low dependency burden.
- Focused travel-domain identity.

## Current Gaps

- AI answers are not yet deeply converted into editable trip objects.
- City and tool context are visible but not deeply woven into the Ask workflow.
- Email and Google flows need real production QA with live provider credentials.
- SQLite is not a durable production user database on serverless hosting.
- Browser-level mobile smoke tests should be expanded before user acquisition.

## Near-Term Strategy

1. Improve chat professionalism with richer trip-intake structure and better model routing.
2. Turn high-quality Ask outputs into saveable trip drafts.
3. Make Cities and Tools context callable inside planning flows.
4. Harden registration, verification, and Google OAuth in production.
5. Add real mobile browser smoke coverage and continue UI polish.

## Non-Goals For The Next Cycle

- Payments.
- Booking engine integrations.
- Multi-language UI.
- Native mobile apps.
- Large backend migration before product flow validation.
- Broad admin analytics.

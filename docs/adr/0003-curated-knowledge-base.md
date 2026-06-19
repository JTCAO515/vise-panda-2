# 0003 — Curated Knowledge Base over RAG

**Status:** Accepted
**Date:** 2026-05-24

## Context

Chat needs accurate, structured China travel data. Options: RAG over web sources vs hand-curated JSON knowledge base.

## Decision

Hand-crafted 36-city JSON knowledge base with attractions, food, hotels, tips, pricing, and transport data per city. No RAG, no vector DB, no web scraping.

## Consequences

- ✅ Deterministic, verifiable data — no hallucination from retrieval
- ✅ Zero external API dependency for data
- ✅ Fast response (no retrieval latency)
- ⚠️ Manual update effort when city data changes
- ⚠️ Coverage limited to 36 cities

## Related

- `CONTEXT.md` — city JSON structure in `web/data/`

# 0001 — Zero-Dependency WSGI Backend

**Status:** Accepted
**Date:** 2026-05-24

## Context

The project needs a Python backend on Vercel Serverless. Vercel's Hobby plan has cold-start latency issues. The previous v2.x used FastAPI + SQLAlchemy + Supabase — heavy dependency chain causing slow cold starts.

## Decision

Switch to pure Python stdlib WSGI (`wsgiref`), zero pip dependencies. All API logic in a single `api/index.py` file.

## Consequences

- ✅ Cold start reduced from ~5s to ~200ms
- ✅ Deployment zero failures (no pip install step)
- ✅ Simplified debugging (no dependency chain)
- ⚠️ No async support, no ORM, no request validation library

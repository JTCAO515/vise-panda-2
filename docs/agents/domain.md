# Domain Docs Layout

- **Layout:** Single-context
- **CONTEXT.md:** Root level — single shared language document for the entire project
- **ADRs:** `docs/adr/` — architecture decision records
- **PRD:** `PRD_PRODUCT_ANALYSIS.md` at root level

This is a single Python WSGI backend + pure HTML/CSS/JS frontend, deployed as a Vercel Serverless app. Not a monorepo — one context covers the whole codebase.

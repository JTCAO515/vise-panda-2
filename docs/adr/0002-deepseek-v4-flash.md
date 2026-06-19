# 0002 — DeepSeek V4 Flash as LLM Provider

**Status:** Accepted
**Date:** 2026-05-24

## Context

Chat feature needs a cost-effective, China-accessible LLM with strong Chinese travel knowledge and high concurrency tolerance.

## Decision

Use DeepSeek V4 Flash via OpenAI-compatible API. SSE streaming for real-time token-by-token responses.

## Consequences

- ✅ Good Chinese travel knowledge
- ✅ Low cost ($0.27/M tokens)
- ✅ Fast response, high rate limits
- ⚠️ Requires proxy for API access from China servers — uses local Xray SOCKS5 for outbound

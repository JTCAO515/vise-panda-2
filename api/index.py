"""VisePanda v5.0.9 — China Travel AI
WSGI entry point. Zero pip dependencies (stdlib only).
Routes are delegated to submodules: cities, chat, tools, config, auth.
"""
from __future__ import annotations

import json
import os
import sys

from api.common import (
    _json, _json_error, _serve_static, STATIC_DIR, WEB_DIR,
)

APP_VERSION = "5.0.9"


# ════════════════════════════════════════════════════════════
# WSGI APPLICATION
# ════════════════════════════════════════════════════════════

def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")

    # ── Health ──
    if path == "/api/health" and method == "GET":
        return _json(start_response, {
            "status": "alive",
            "version": APP_VERSION,
            "build": "2026-06-20",
        })

    # ── Chat SSE ──
    if path == "/api/chat" and method == "POST":
        from api.chat import handle_chat
        return handle_chat(environ, start_response)

    # ── Compare API (must be before /api/cities catch-all) ──
    if path == "/api/cities/compare" and method == "GET":
        from api.cities import handle_cities_compare
        return handle_cities_compare(environ, start_response)

    # ── Cities API ──
    if path.startswith("/api/cities") and method == "GET":
        from api.cities import handle_cities
        return handle_cities(start_response, path)

    # ── Tools API ──
    if path.startswith("/api/tools") and method == "GET":
        from api.tools import handle_tools
        return handle_tools(start_response, path)

    # ── Estimate API ──
    if path == "/api/estimate" and method == "GET":
        from api.cities import handle_estimate
        return handle_estimate(start_response)

    # ── Validate API ──
    if path == "/api/validate" and method == "POST":
        from api.cities import handle_validate
        return handle_validate(environ, start_response)

    # ── Visa API ──
    if path == "/api/visa/countries" and method == "GET":
        from api.visa import handle_visa_countries
        return handle_visa_countries(start_response)
    if path == "/api/visa/info" and method == "GET":
        from api.visa import handle_visa_info
        return handle_visa_info(environ, start_response)
    if path == "/api/visa/generate" and method == "POST":
        from api.visa import handle_visa_generate
        return handle_visa_generate(environ, start_response)

    # ── Map API ──
    if path == "/api/map" and method == "GET":
        from api.config import handle_map
        return handle_map(start_response)

    # ── Config API ──
    if path == "/api/config" and method == "GET":
        from api.config import handle_config
        return handle_config(start_response)

    # ── Auth & Admin routes ──
    from api import auth as _auth
    _auth.ensure_init()
    auth_result = _auth.handle_auth_route(environ, start_response, path, method)
    if auth_result is not None:
        return auth_result

    # ── Admin panel (serve static HTML) ──
    if path in ("/admin", "/admin/") and method == "GET":
        return _serve_static(start_response, "admin.html")

    # ── Static files (web/ + static/) ──
    result = _serve_static(start_response, path)
    if result is not None:
        return result

    # ── 404 fallback ──
    return _json_error(start_response, f"Not found: {path}", "404 Not Found")

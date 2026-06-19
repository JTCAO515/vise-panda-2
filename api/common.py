"""VisePanda — shared utilities for API handlers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
ROOT = THIS_DIR.parent
DATA_DIR = ROOT / "data"
WEB_DIR = ROOT / "web"
STATIC_DIR = ROOT / "static"

# ── MIME types ──
MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".webp": "image/webp",
    ".woff2": "font/woff2",
    ".txt": "text/plain; charset=utf-8",
}
TEXT_SUFFIXES = {".html", ".js", ".css", ".json", ".svg", ".txt"}


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _json(start_response, payload: Any, status: str = "200 OK"):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    start_response(status, [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Access-Control-Allow-Origin", "*"),
    ])
    return [body]


def _json_error(start_response, msg: str, status: str = "500 Internal Server Error"):
    return _json(start_response, {"error": msg}, status=status)


def _read_post(environ) -> dict:
    """Read and parse POST body. Max 100KB to prevent abuse."""
    raw_len = environ.get("CONTENT_LENGTH", "0") or "0"
    try:
        length = min(int(raw_len), 102_400)  # cap at 100KB
    except (ValueError, TypeError):
        length = 0
    if length <= 0:
        return {}
    raw = environ["wsgi.input"].read(length)
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}


def _load_json(path) -> dict | list | None:
    try:
        p = Path(path) if not isinstance(path, Path) else path
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def _serve_static(start_response, request_path: str):
    """Serve files from web/ (frontend) and static/ (assets)."""
    if request_path in ("", "/"):
        rel = "index.html"
    else:
        rel = request_path.lstrip("/")

    for base_dir in (WEB_DIR, STATIC_DIR):
        target = (base_dir / rel).resolve()
        if target.is_file() and _is_relative_to(target, base_dir.resolve()):
            body = target.read_bytes()
            ct = MIME.get(target.suffix, "application/octet-stream")
            headers = [
                ("Content-Type", ct),
                ("Content-Length", str(len(body))),
            ]
            if base_dir == STATIC_DIR or target.suffix not in (".html",):
                headers.append(("Cache-Control", "public, max-age=31536000, immutable"))
            else:
                headers.append(("Cache-Control", "public, max-age=300"))
            if target.suffix in TEXT_SUFFIXES:
                body = body.decode("utf-8").encode("utf-8")
            start_response("200 OK", headers)
            return [body]
    return None


def _sse_event(data: str, event: str = "message") -> bytes:
    """Format a Server-Sent Event."""
    return f"event: {event}\ndata: {data}\n\n".encode("utf-8")

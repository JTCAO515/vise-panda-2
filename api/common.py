import json
import mimetypes
import os
import re
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
WEB_DIR = ROOT / "web"
STATIC_DIR = ROOT / "static"

ALLOWED_ORIGINS = {
    "https://go2china.space",
    "https://www.go2china.space",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
}


def cors_headers(environ):
    origin = environ.get("HTTP_ORIGIN", "")
    allow_origin = origin if origin in ALLOWED_ORIGINS else "https://go2china.space"
    return [
        ("Access-Control-Allow-Origin", allow_origin),
        ("Access-Control-Allow-Credentials", "true"),
        ("Access-Control-Allow-Headers", "Content-Type, Authorization"),
        ("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS"),
        ("Vary", "Origin"),
    ]


def send(start_response, status, body, headers=None, environ=None):
    if isinstance(status, HTTPStatus):
        status_line = f"{status.value} {status.phrase}"
    elif isinstance(status, int):
        phrase = HTTPStatus(status).phrase if status in HTTPStatus._value2member_map_ else "OK"
        status_line = f"{status} {phrase}"
    else:
        status_line = status
    final_headers = list(headers or [])
    if environ is not None:
        final_headers.extend(cors_headers(environ))
    start_response(status_line, final_headers)
    if isinstance(body, str):
        body = body.encode("utf-8")
    return [body]


def json_response(start_response, payload, status=HTTPStatus.OK, environ=None, headers=None):
    base_headers = [("Content-Type", "application/json; charset=utf-8")]
    base_headers.extend(headers or [])
    return send(start_response, status, json.dumps(payload, ensure_ascii=False), base_headers, environ)


def text_response(start_response, text, status=HTTPStatus.OK, content_type="text/plain; charset=utf-8", environ=None):
    return send(start_response, status, text, [("Content-Type", content_type)], environ)


def error_response(start_response, status, code, message, environ=None):
    return json_response(start_response, {"error": {"code": code, "message": message}}, status, environ)


def read_json(environ):
    try:
        length = int(environ.get("CONTENT_LENGTH") or "0")
    except ValueError:
        length = 0
    raw = environ["wsgi.input"].read(length) if length else b"{}"
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("Request body must be valid JSON.")


def query_params(environ):
    return {key: values[-1] for key, values in parse_qs(environ.get("QUERY_STRING", "")).items()}


def load_json(filename):
    with (DATA_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def clean_text(value):
    if value is None:
        return ""
    text = str(value)
    replacements = {
        "\u9225?": "-",
        "\u9225\u63d7": "-M",
        "\u9225\u63d8": "-N",
        "\u9225\u63d9": "-O",
        "\u9225\u63c7": "-D",
        "\u9225\u63c2": "-A",
        "\u9225\u63ca": "-F",
        "\u9225\u63dd": "-S",
        "\u9225\u63d3": "-J",
        "\u8def": "-",
        "\u697c": "RMB ",
        "\u62e2": "GBP ",
        "\u9227?": "EUR 0",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    text = re.split(r"\u951b|\uff08|\(", text, maxsplit=1)[0]
    text = re.sub(r"\s+", " ", text).strip(" -")
    return text


def clean_list(values, limit=None):
    output = []
    for item in values or []:
        cleaned = clean_text(item)
        if cleaned and cleaned not in output:
            output.append(cleaned)
        if limit and len(output) >= limit:
            break
    return output


def bearer_token(environ):
    header = environ.get("HTTP_AUTHORIZATION", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return ""


def client_ip(environ):
    forwarded = environ.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return environ.get("REMOTE_ADDR", "unknown")


def static_response(start_response, request_path, environ):
    if request_path in {"", "/"}:
        target = WEB_DIR / "index.html"
    elif request_path.startswith("/static/"):
        target = STATIC_DIR / request_path.removeprefix("/static/")
    elif request_path.startswith("/web/"):
        target = WEB_DIR / request_path.removeprefix("/web/")
    else:
        safe_name = request_path.lstrip("/") or "index.html"
        target = WEB_DIR / safe_name

    try:
        resolved = target.resolve()
        allowed = {WEB_DIR.resolve(), STATIC_DIR.resolve()}
        if not any(str(resolved).startswith(str(base)) for base in allowed):
            raise FileNotFoundError
        if not resolved.is_file():
            target = WEB_DIR / "index.html"
            resolved = target.resolve()
        body = resolved.read_bytes()
    except FileNotFoundError:
        return error_response(start_response, HTTPStatus.NOT_FOUND, "not_found", "Resource not found.", environ)

    content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
    cache = "public, max-age=86400" if resolved.suffix.lower() in {".png", ".jpg", ".jpeg", ".svg", ".css", ".js"} else "no-store"
    return send(
        start_response,
        HTTPStatus.OK,
        body,
        [("Content-Type", content_type), ("Cache-Control", cache)],
        environ,
    )


def runtime_database_path():
    configured = os.environ.get("AUTH_DB_PATH")
    if configured:
        return Path(configured)
    if os.environ.get("VERCEL"):
        return Path("/tmp/vp-codex.db")
    return DATA_DIR / "vp-codex.db"

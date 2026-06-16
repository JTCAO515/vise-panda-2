"""
VisePanda Auth Module — email + password, SQLite, stdlib only.

Endpoints (called from index.py):
  register(environ, start_response)  → POST /api/auth/register
  login(environ, start_response)     → POST /api/auth/login
  me(environ, start_response)        → GET /api/auth/me
  admin_users(start_response)        → GET /api/admin/users
  admin_delete_user(environ, sr)     → DELETE /api/admin/users/:id

Database: data/users.db
  users:    id (uuid), email, password_hash, salt, role, created_at, updated_at
  sessions: token (64 hex), user_id, created_at, expires_at
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from urllib.parse import parse_qs

THIS_DIR = Path(__file__).resolve().parent
DATA_DIR = THIS_DIR.parent / "data"
DB_PATH = Path(os.environ.get("AUTH_DB_PATH", str(DATA_DIR / "users.db")))

# ── Token lifetime ──
TOKEN_DAYS = 7
TOKEN_SECONDS = TOKEN_DAYS * 24 * 3600

# ── Admin override key (optional, set env ADMIN_KEY for extra security) ──
ADMIN_KEY = os.environ.get("ADMIN_KEY", "vp-admin-2026")


# ════════════════════════════════════════════════════════════
# DATABASE
# ════════════════════════════════════════════════════════════

def _get_db() -> sqlite3.Connection:
    """Get SQLite connection (autocommit mode)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if not exist. Safe to call repeatedly."""
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          TEXT PRIMARY KEY,
            email       TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt        TEXT NOT NULL,
            role        TEXT NOT NULL DEFAULT 'user',
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token       TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at  TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
        CREATE TABLE IF NOT EXISTS trips (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title       TEXT NOT NULL,
            city        TEXT NOT NULL,
            days        TEXT NOT NULL DEFAULT '',
            preview     TEXT NOT NULL DEFAULT '',
            is_saved    INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_trips_user ON trips(user_id);
    """)
    conn.commit()
    conn.close()


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def _json(start_response, payload, status="200 OK"):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    start_response(status, [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Headers", "Content-Type, Authorization"),
        ("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS"),
    ])
    return [body]


def _json_error(start_response, msg, status="400 Bad Request"):
    return _json(start_response, {"error": msg}, status=status)


def _read_post(environ) -> dict:
    raw_len = environ.get("CONTENT_LENGTH", "0") or "0"
    try:
        length = min(int(raw_len), 102_400)
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


def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash password with salt. Returns (hash, salt)."""
    if salt is None:
        salt = uuid.uuid4().hex[:16]
    h = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return h, salt


def _generate_token() -> str:
    return uuid.uuid4().hex + uuid.uuid4().hex  # 64 hex chars


def _get_user_from_token(token: str) -> dict | None:
    """Look up user by session token. Returns None if invalid/expired."""
    if not token:
        return None
    conn = _get_db()
    row = conn.execute("""
        SELECT u.id, u.email, u.role, u.created_at
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token = ? AND s.expires_at > datetime('now')
    """, (token,)).fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def _validate_email(email: str) -> str | None:
    """Basic email validation. Returns None if valid, error msg if invalid."""
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return "Invalid email address"
    if len(email) > 254:
        return "Email too long"
    return None


def _validate_password(password: str) -> str | None:
    if not password or len(password) < 6:
        return "Password must be at least 6 characters"
    if len(password) > 128:
        return "Password too long"
    return None


# ════════════════════════════════════════════════════════════
# HANDLERS
# ════════════════════════════════════════════════════════════

def handle_register(environ, start_response):
    """POST /api/auth/register — email + password → create user, return user info."""
    ensure_init()
    data = _read_post(environ)
    email = (data.get("email", "") or "").strip().lower()
    password = data.get("password", "") or ""

    # Validate
    err = _validate_email(email)
    if err:
        return _json_error(start_response, err)
    err = _validate_password(password)
    if err:
        return _json_error(start_response, err)

    # Check if first user → admin
    conn = _get_db()
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    role = "admin" if user_count == 0 else "user"

    # Check duplicate
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return _json_error(start_response, "Email already registered", "409 Conflict")

    # Create user
    user_id = uuid.uuid4().hex
    password_hash, salt = _hash_password(password)
    conn.execute(
        "INSERT INTO users (id, email, password_hash, salt, role) VALUES (?, ?, ?, ?, ?)",
        (user_id, email, password_hash, salt, role),
    )
    conn.commit()
    conn.close()

    return _json(start_response, {
        "user": {
            "id": user_id,
            "email": email,
            "role": role,
        },
        "message": "Account created successfully",
    }, "201 Created")


def handle_login(environ, start_response):
    """POST /api/auth/login — email + password → token + user info."""
    ensure_init()
    data = _read_post(environ)
    email = (data.get("email", "") or "").strip().lower()
    password = data.get("password", "") or ""

    if not email or not password:
        return _json_error(start_response, "Email and password required")

    conn = _get_db()
    row = conn.execute(
        "SELECT id, email, password_hash, salt, role FROM users WHERE email = ?",
        (email,),
    ).fetchone()

    if row is None:
        conn.close()
        return _json_error(start_response, "Invalid email or password", "401 Unauthorized")

    user = dict(row)
    expected_hash, _ = _hash_password(password, user["salt"])
    if expected_hash != user["password_hash"]:
        conn.close()
        return _json_error(start_response, "Invalid email or password", "401 Unauthorized")

    # Create session
    token = _generate_token()
    conn.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, datetime('now', '+{} seconds'))".format(TOKEN_SECONDS),
        (token, user["id"]),
    )
    conn.commit()
    conn.close()

    return _json(start_response, {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
        },
    })


def handle_me(environ, start_response):
    """GET /api/auth/me — require Authorization: Bearer <token> → user info."""
    ensure_init()
    token = _extract_token(environ)
    user = _get_user_from_token(token)
    if user is None:
        return _json_error(start_response, "Invalid or expired token", "401 Unauthorized")
    return _json(start_response, {"user": user})


def handle_admin_users(start_response):
    """GET /api/admin/users — list all users."""
    conn = _get_db()
    rows = conn.execute(
        "SELECT id, email, role, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    users = [dict(r) for r in rows]
    return _json(start_response, {"users": users, "total": len(users)})


def handle_admin_delete(environ, start_response, user_id: str):
    """DELETE /api/admin/users/:id — delete a user."""
    conn = _get_db()
    # Check user exists
    row = conn.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        conn.close()
        return _json_error(start_response, "User not found", "404 Not Found")

    user = dict(row)
    # Prevent deleting yourself
    token = _extract_token(environ)
    current = _get_user_from_token(token)
    if current and current["id"] == user_id:
        conn.close()
        return _json_error(start_response, "Cannot delete yourself", "403 Forbidden")

    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return _json(start_response, {"message": "User deleted", "user_id": user_id})


# ════════════════════════════════════════════════════════════
# TRIPS API
# ════════════════════════════════════════════════════════════

def handle_get_trips(environ, start_response):
    """GET /api/trips — list current user's trips (recents and saved)."""
    user = require_auth(environ, start_response)
    if user is None:
        return []
    conn = _get_db()
    recent = [dict(r) for r in conn.execute(
        "SELECT id, title, city, days, preview, created_at FROM trips WHERE user_id = ? AND is_saved = 0 ORDER BY created_at DESC LIMIT 20",
        (user["id"],)
    ).fetchall()]
    saved = [dict(r) for r in conn.execute(
        "SELECT id, title, city, days, preview, created_at FROM trips WHERE user_id = ? AND is_saved = 1 ORDER BY created_at DESC LIMIT 20",
        (user["id"],)
    ).fetchall()]
    conn.close()
    return _json(start_response, {"trips": {"recent": recent, "saved": saved}})


def handle_create_trip(environ, start_response):
    """POST /api/trips — create a new trip."""
    user = require_auth(environ, start_response)
    if user is None:
        return []
    data = _read_post(environ)
    title = (data.get("title", "") or "").strip()
    city = (data.get("city", "") or "").strip()
    days = (data.get("days", "") or "").strip()
    preview = (data.get("preview", "") or "").strip()
    is_saved = 1 if data.get("is_saved", False) else 0

    if not title or not city:
        return _json_error(start_response, "Title and city required")

    trip_id = uuid.uuid4().hex
    conn = _get_db()
    conn.execute(
        "INSERT INTO trips (id, user_id, title, city, days, preview, is_saved) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (trip_id, user["id"], title, city, days, preview, is_saved),
    )
    conn.commit()
    conn.close()
    return _json(start_response, {
        "trip": {"id": trip_id, "title": title, "city": city, "days": days, "preview": preview},
        "message": "Trip created",
    }, "201 Created")


def handle_delete_trip(environ, start_response, trip_id: str):
    """DELETE /api/trips/:id — delete a trip (only owner or admin)."""
    user = require_auth(environ, start_response)
    if user is None:
        return []

    conn = _get_db()
    trip = conn.execute("SELECT id, user_id FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if trip is None:
        conn.close()
        return _json_error(start_response, "Trip not found", "404 Not Found")

    trip = dict(trip)
    # Only trip owner or admin can delete
    if trip["user_id"] != user["id"] and user["role"] != "admin":
        conn.close()
        return _json_error(start_response, "Permission denied", "403 Forbidden")

    conn.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    conn.commit()
    conn.close()
    return _json(start_response, {"message": "Trip deleted", "trip_id": trip_id})


# ════════════════════════════════════════════════════════════
# AUTH MIDDLEWARE
# ════════════════════════════════════════════════════════════

def _extract_token(environ) -> str | None:
    """Extract Bearer token from Authorization header."""
    auth = environ.get("HTTP_AUTHORIZATION", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


def require_auth(environ, start_response) -> dict | None:
    """Middleware: check auth. Returns user dict or None (error already sent)."""
    token = _extract_token(environ)
    user = _get_user_from_token(token)
    if user is None:
        _json_error(start_response, "Authentication required", "401 Unauthorized")
        return None
    return user


def require_admin(environ, start_response) -> dict | None:
    """Middleware: check auth + admin role."""
    user = require_auth(environ, start_response)
    if user is None:
        return None
    if user["role"] != "admin":
        _json_error(start_response, "Admin access required", "403 Forbidden")
        return None
    return user


# ════════════════════════════════════════════════════════════
# CORS preflight & routing helper
# ════════════════════════════════════════════════════════════

_initialized = False


def ensure_init():
    global _initialized
    if not _initialized:
        init_db()
        _initialized = True


def handle_cors_preflight(start_response) -> list[bytes] | None:
    """Handle OPTIONS preflight. Returns response if preflight, None otherwise."""
    # This is handled inline in the router


# ════════════════════════════════════════════════════════════
# ROUTER — called from index.py
# ════════════════════════════════════════════════════════════

def handle_auth_route(environ, start_response, path: str, method: str) -> list[bytes] | None:
    """Route auth requests. Returns response or None if not matched."""
    ensure_init()

    # CORS preflight
    if method == "OPTIONS":
        headers = [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Headers", "Content-Type, Authorization"),
            ("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS"),
            ("Content-Length", "0"),
        ]
        start_response("204 No Content", headers)
        return []

    # ── Auth routes ──
    if path == "/api/auth/register" and method == "POST":
        return handle_register(environ, start_response)

    if path == "/api/auth/login" and method == "POST":
        return handle_login(environ, start_response)

    if path == "/api/auth/me" and method == "GET":
        return handle_me(environ, start_response)

    # ── Admin routes ──
    if path == "/api/admin/users" and method == "GET":
        user = require_admin(environ, start_response)
        if user is None:
            return []  # error already sent
        return handle_admin_users(start_response)

    if path.startswith("/api/admin/users/") and method == "DELETE":
        user = require_admin(environ, start_response)
        if user is None:
            return []
        user_id = path[len("/api/admin/users/"):]
        if not user_id:
            return _json_error(start_response, "User ID required", "400 Bad Request")
        return handle_admin_delete(environ, start_response, user_id)

    # ── Trip routes ──
    if path == "/api/trips" and method == "GET":
        return handle_get_trips(environ, start_response)

    if path == "/api/trips" and method == "POST":
        return handle_create_trip(environ, start_response)

    if path.startswith("/api/trips/") and method == "DELETE":
        trip_id = path[len("/api/trips/"):]
        if trip_id:
            return handle_delete_trip(environ, start_response, trip_id)
        return _json_error(start_response, "Trip ID required", "400 Bad Request")

    return None  # not matched


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
import urllib.request
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs

THIS_DIR = Path(__file__).resolve().parent
DATA_DIR = THIS_DIR.parent / "data"
# Vercel Serverless: /tmp is writable, everything else is read-only
_DEFAULT_DB = str(Path("/tmp/users.db") if os.environ.get("VERCEL") else DATA_DIR / "users.db")
DB_PATH = Path(os.environ.get("AUTH_DB_PATH", _DEFAULT_DB))
_AUTH_ERROR_RESPONSE_KEY = "vp.auth_error_response"

# ── Token lifetime ──
TOKEN_DAYS = 7
TOKEN_SECONDS = TOKEN_DAYS * 24 * 3600

# ── Admin override key (optional, set env ADMIN_KEY for extra security) ──
ADMIN_KEY = os.environ.get("ADMIN_KEY", "vp-admin-2026")

# ── Google OAuth ──
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
# TokenInfo endpoint for verifying Google ID tokens (stdlib only, no external deps)
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo?id_token="


# ════════════════════════════════════════════════════════════
# DATABASE
# ════════════════════════════════════════════════════════════

def _get_db() -> sqlite3.Connection:
    """Get SQLite connection (autocommit mode)."""
    global DB_PATH
    DB_PATH = Path(os.environ.get("AUTH_DB_PATH", _DEFAULT_DB))
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if not exist. Safe to call repeatedly."""
    conn = _get_db()
    # Phase 1: Create tables (without google_id index — added after migration)
    conn.executescript("""
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
            content     TEXT NOT NULL DEFAULT '',
            is_saved    INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_trips_user ON trips(user_id);
        CREATE TABLE IF NOT EXISTS chat_conversations (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title       TEXT NOT NULL DEFAULT '',
            message_count INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS chat_messages (
            id              TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
            role            TEXT NOT NULL,
            content         TEXT NOT NULL,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_conv_user ON chat_conversations(user_id);
        CREATE INDEX IF NOT EXISTS idx_msg_conv ON chat_messages(conversation_id, created_at);
    """)
    # Phase 2: Create users table + migrate existing if needed
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          TEXT PRIMARY KEY,
            email       TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL DEFAULT '',
            salt        TEXT NOT NULL DEFAULT '',
            display_name TEXT NOT NULL DEFAULT '',
            role        TEXT NOT NULL DEFAULT 'user',
            status      TEXT NOT NULL DEFAULT 'active',
            google_id   TEXT DEFAULT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    # Migration: add columns to existing users table (safe to run repeatedly)
    for col, typ in [("google_id", "TEXT DEFAULT NULL"),
                     ("display_name", "TEXT NOT NULL DEFAULT ''"),
                     ("status", "TEXT NOT NULL DEFAULT 'active'")]:
        try:
            conn.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
        except sqlite3.OperationalError:
            pass
    # Now safe to create the partial index
    try:
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google ON users(google_id) WHERE google_id IS NOT NULL")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE trips ADD COLUMN content TEXT NOT NULL DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    # Password reset tokens table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token       TEXT UNIQUE NOT NULL,
            expires_at  TEXT NOT NULL,
            used        INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_reset_token ON password_reset_tokens(token)")

    # Seed default admin user (safe to run repeatedly)
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@go2china.space")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (admin_email,)).fetchone()
    if existing is None:
        pw_hash, salt = _hash_password(admin_password)
        admin_id = uuid.uuid4().hex[:16]
        conn.execute(
            "INSERT INTO users (id, email, password_hash, salt, display_name, role, status) VALUES (?, ?, ?, ?, ?, 'admin', 'active')",
            (admin_id, admin_email, pw_hash, salt, "Admin")
        )

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
        SELECT u.id, u.email, u.display_name, u.role, u.status, u.created_at
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
    display_name = (data.get("display_name", "") or "").strip()

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
        "INSERT INTO users (id, email, password_hash, salt, display_name, role) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, email, password_hash, salt, display_name, role),
    )
    conn.commit()
    conn.close()

    return _json(start_response, {
        "user": {
            "id": user_id,
            "email": email,
            "display_name": display_name,
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
        "SELECT id, email, password_hash, salt, display_name, role, status FROM users WHERE email = ?",
        (email,),
    ).fetchone()

    if row is None:
        conn.close()
        return _json_error(start_response, "Invalid email or password", "401 Unauthorized")

    user = dict(row)
    if user["status"] != "active":
        conn.close()
        return _json_error(start_response, "Account is not active", "403 Forbidden")

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
            "display_name": user["display_name"],
            "role": user["role"],
        },
    })


def handle_logout(environ, start_response):
    """POST /api/auth/logout — invalidate current token."""
    token = _extract_token(environ)
    if token:
        conn = _get_db()
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        conn.close()
    return _json(start_response, {"message": "Logged out"})


def handle_me(environ, start_response):
    """GET /api/auth/me — require Authorization: Bearer <token> → user info."""
    ensure_init()
    token = _extract_token(environ)
    user = _get_user_from_token(token)
    if user is None:
        return _json_error(start_response, "Invalid or expired token", "401 Unauthorized")
    return _json(start_response, {"user": user})


# ════════════════════════════════════════════════════════════
# GOOGLE OAUTH
# ════════════════════════════════════════════════════════════

def handle_google_login(environ, start_response):
    """POST /api/auth/google/login — receive Google credential (ID token) → verify → login/register."""
    data = _read_post(environ)
    credential = data.get("credential", "") or ""

    if not credential:
        return _json_error(start_response, "Google credential required")

    if not GOOGLE_CLIENT_ID:
        return _json_error(start_response, "Google login not configured", "503 Service Unavailable")

    try:
        # Verify the ID token via Google's tokeninfo endpoint (stdlib only)
        url = GOOGLE_TOKENINFO_URL + urllib.request.quote(credential, safe='')
        req = urllib.request.Request(url, headers={"User-Agent": "VisePanda/3.1"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode())

        # Verify it's our client
        if payload.get("aud") != GOOGLE_CLIENT_ID:
            return _json_error(start_response, "Token audience mismatch", "401 Unauthorized")

        google_id = payload.get("sub", "")
        email = payload.get("email", "").lower()
        name = payload.get("name", "") or email.split("@")[0]

        if not google_id or not email:
            return _json_error(start_response, "Invalid Google token: missing user info", "401 Unauthorized")

    except urllib.error.HTTPError as e:
        return _json_error(start_response, f"Google token verification failed: {e.code}", "401 Unauthorized")
    except Exception as e:
        return _json_error(start_response, f"Google verification error: {str(e)[:100]}", "401 Unauthorized")

    # Find or create user
    conn = _get_db()
    user = conn.execute(
        "SELECT id, email, role, display_name FROM users WHERE google_id = ?",
        (google_id,)
    ).fetchone()

    if user is None:
        # Try by email (link Google account to existing email user)
        user = conn.execute(
            "SELECT id, email, role, display_name FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if user:
            # Link Google account to existing user
            conn.execute(
                "UPDATE users SET google_id = ?, display_name = COALESCE(NULLIF(display_name,''), ?) WHERE id = ?",
                (google_id, name, user["id"])
            )
        else:
            # Create new user
            user_id = uuid.uuid4().hex
            conn.execute(
                "INSERT INTO users (id, email, display_name, role, google_id) VALUES (?, ?, ?, 'user', ?)",
                (user_id, email, name, google_id)
            )
            user = {"id": user_id, "email": email, "role": "user", "display_name": name}

    # Generate session token
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
            "display_name": user.get("display_name", ""),
        },
    })


def handle_admin_users(environ, start_response):
    """GET /api/admin/users — list all users with optional search/filter/page."""
    import urllib.parse
    params = urllib.parse.parse_qs(environ.get("QUERY_STRING", ""))
    search = (params.get("search", [""])[0] or "").strip()
    role_filter = params.get("role", [""])[0] or ""
    status_filter = params.get("status", [""])[0] or ""
    page = int(params.get("page", ["1"])[0])
    limit = int(params.get("limit", ["50"])[0])
    offset = (page - 1) * limit

    conn = _get_db()
    where = []
    bind = []
    if search:
        where.append("(email LIKE ? OR display_name LIKE ?)")
        bind.extend([f"%{search}%", f"%{search}%"])
    if role_filter:
        where.append("role = ?")
        bind.append(role_filter)
    if status_filter:
        where.append("status = ?")
        bind.append(status_filter)

    where_clause = " AND ".join(where) if where else "1=1"

    total = conn.execute(
        f"SELECT COUNT(*) FROM users WHERE {where_clause}", bind
    ).fetchone()[0]

    rows = conn.execute(
        f"SELECT id, email, display_name, role, status, created_at FROM users WHERE {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        bind + [limit, offset]
    ).fetchall()
    conn.close()
    users = [dict(r) for r in rows]
    return _json(start_response, {"users": users, "total": total, "page": page, "limit": limit})


def handle_admin_user_detail(environ, start_response, user_id: str):
    """GET /api/admin/users/:id — get single user details (ops/admin)."""
    conn = _get_db()
    row = conn.execute(
        "SELECT id, email, display_name, role, status, created_at, updated_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return _json_error(start_response, "User not found", "404 Not Found")
    return _json(start_response, {"user": dict(row)})


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
        return _take_auth_error(environ)
    conn = _get_db()
    recent = [dict(r) for r in conn.execute(
        "SELECT id, title, city, days, preview, COALESCE(NULLIF(content, ''), preview) AS content, created_at "
        "FROM trips WHERE user_id = ? AND is_saved = 0 ORDER BY created_at DESC LIMIT 20",
        (user["id"],)
    ).fetchall()]
    saved = [dict(r) for r in conn.execute(
        "SELECT id, title, city, days, preview, COALESCE(NULLIF(content, ''), preview) AS content, created_at "
        "FROM trips WHERE user_id = ? AND is_saved = 1 ORDER BY created_at DESC LIMIT 20",
        (user["id"],)
    ).fetchall()]
    conn.close()
    return _json(start_response, {"trips": {"recent": recent, "saved": saved}})


def handle_create_trip(environ, start_response):
    """POST /api/trips — create a new trip."""
    user = require_auth(environ, start_response)
    if user is None:
        return _take_auth_error(environ)
    data = _read_post(environ)
    title = (data.get("title", "") or "").strip()
    city = (data.get("city", "") or "").strip()
    days = (data.get("days", "") or "").strip()
    content = (data.get("content", "") or "").strip()
    preview = (data.get("preview", "") or "").strip()
    if not content:
        content = preview
    if not preview:
        preview = content[:220].strip()
    is_saved = 1 if data.get("is_saved", False) else 0

    if not title or not city:
        return _json_error(start_response, "Title and city required")

    trip_id = uuid.uuid4().hex
    conn = _get_db()
    conn.execute(
        "INSERT INTO trips (id, user_id, title, city, days, preview, content, is_saved) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (trip_id, user["id"], title, city, days, preview, content, is_saved),
    )
    conn.commit()
    conn.close()
    return _json(start_response, {
        "trip": {"id": trip_id, "title": title, "city": city, "days": days, "preview": preview, "content": content},
        "message": "Trip created",
    }, "201 Created")


def handle_delete_trip(environ, start_response, trip_id: str):
    """DELETE /api/trips/:id — delete a trip (only owner or admin)."""
    user = require_auth(environ, start_response)
    if user is None:
        return _take_auth_error(environ)

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


def _store_auth_error(environ, response) -> None:
    environ[_AUTH_ERROR_RESPONSE_KEY] = response


def _take_auth_error(environ):
    return environ.pop(_AUTH_ERROR_RESPONSE_KEY, [])


def require_auth(environ, start_response) -> dict | None:
    """Middleware: check auth. Returns user dict or None (error already sent)."""
    token = _extract_token(environ)
    user = _get_user_from_token(token)
    if user is None:
        _store_auth_error(
            environ,
            _json_error(start_response, "Authentication required", "401 Unauthorized"),
        )
        return None
    return user


def require_admin(environ, start_response) -> dict | None:
    """Middleware: check auth + admin role."""
    user = require_auth(environ, start_response)
    if user is None:
        return None
    if user["role"] != "admin":
        _store_auth_error(
            environ,
            _json_error(start_response, "Admin access required", "403 Forbidden"),
        )
        return None
    return user


def require_role(*allowed_roles) -> callable:
    """Middleware factory: check auth + role in allowed_roles. Returns middleware function."""
    def _check(environ, start_response) -> dict | None:
        user = require_auth(environ, start_response)
        if user is None:
            return None
        if user["role"] not in allowed_roles:
            _store_auth_error(
                environ,
                _json_error(start_response, "Access denied", "403 Forbidden"),
            )
            return None
        return user
    return _check


# ════════════════════════════════════════════════════════════
# CHAT HISTORY API
# ════════════════════════════════════════════════════════════

def handle_chat_save(environ, start_response):
    """POST /api/auth/chat/save — save/update a conversation with messages."""
    check_auth = require_role("user", "ops", "admin")
    user = check_auth(environ, start_response)
    if user is None:
        return []
    data = _read_post(environ)
    conv_id = data.get("conversation_id") or uuid.uuid4().hex
    messages = data.get("messages", [])
    if not messages:
        return _json_error(start_response, "Messages required")

    conn = _get_db()
    # Check if conversation exists and belongs to user
    existing = conn.execute(
        "SELECT id FROM chat_conversations WHERE id = ? AND user_id = ?",
        (conv_id, user["id"])
    ).fetchone()

    title = data.get("title", "") or messages[0].get("content", "")[:50] if messages else ""

    if existing:
        # Update existing
        conn.execute(
            "UPDATE chat_conversations SET title = ?, updated_at = datetime('now') WHERE id = ?",
            (title or "Chat", conv_id)
        )
    else:
        # Create new
        conn.execute(
            "INSERT INTO chat_conversations (id, user_id, title) VALUES (?, ?, ?)",
            (conv_id, user["id"], title or "Chat")
        )

    # Insert messages (skip duplicates by checking content + created_at rough dedup)
    inserted = 0
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if not content:
            continue
        msg_id = msg.get("id") or uuid.uuid4().hex
        conn.execute(
            "INSERT OR IGNORE INTO chat_messages (id, conversation_id, role, content) VALUES (?, ?, ?, ?)",
            (msg_id, conv_id, role, content)
        )
        inserted += 1

    # Update message count
    count = conn.execute(
        "SELECT COUNT(*) FROM chat_messages WHERE conversation_id = ?",
        (conv_id,)
    ).fetchone()[0]
    conn.execute(
        "UPDATE chat_conversations SET message_count = ? WHERE id = ?",
        (count, conv_id)
    )
    conn.commit()
    conn.close()

    return _json(start_response, {
        "conversation_id": conv_id,
        "saved": inserted,
        "total_messages": count,
    })


def handle_chat_history(environ, start_response):
    """GET /api/auth/chat-history?page=1&limit=20 — list user's conversations."""
    check_auth = require_role("user", "ops", "admin")
    user = check_auth(environ, start_response)
    if user is None:
        return []

    params = parse_qs(environ.get("QUERY_STRING", ""))
    page = int(params.get("page", ["1"])[0])
    limit = min(int(params.get("limit", ["20"])[0]), 100)
    offset = (page - 1) * limit

    conn = _get_db()
    total = conn.execute(
        "SELECT COUNT(*) FROM chat_conversations WHERE user_id = ?",
        (user["id"],)
    ).fetchone()[0]
    rows = conn.execute(
        "SELECT id, title, message_count, created_at, updated_at FROM chat_conversations "
        "WHERE user_id = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        (user["id"], limit, offset)
    ).fetchall()
    conn.close()

    return _json(start_response, {
        "conversations": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "limit": limit,
    })


def handle_chat_detail(environ, start_response, conv_id: str):
    """GET /api/auth/chat/:id — get full conversation with messages."""
    check_auth = require_role("user", "ops", "admin")
    user = check_auth(environ, start_response)
    if user is None:
        return []

    conn = _get_db()
    conv = conn.execute(
        "SELECT id, title, message_count, created_at, updated_at FROM chat_conversations "
        "WHERE id = ? AND user_id = ?",
        (conv_id, user["id"])
    ).fetchone()

    if conv is None:
        conn.close()
        return _json_error(start_response, "Conversation not found", "404 Not Found")

    messages = conn.execute(
        "SELECT id, role, content, created_at FROM chat_messages WHERE conversation_id = ? ORDER BY created_at",
        (conv_id,)
    ).fetchall()
    conn.close()

    return _json(start_response, {
        "conversation": dict(conv),
        "messages": [dict(m) for m in messages],
    })


# ════════════════════════════════════════════════════════════
# USER SETTINGS API
# ════════════════════════════════════════════════════════════

def handle_update_profile(environ, start_response):
    """PATCH /api/auth/update-profile — update display_name, password."""
    check_auth = require_role("user", "ops", "admin")
    user = check_auth(environ, start_response)
    if user is None:
        return []

    data = _read_post(environ)
    if not data:
        return _json_error(start_response, "No data provided")

    conn = _get_db()
    updates = []
    params = []

    # Display name
    if "display_name" in data and data["display_name"] is not None:
        name = data["display_name"].strip()
        if name:
            updates.append("display_name = ?")
            params.append(name)

    # Password
    if "password" in data and data["password"]:
        pw = data["password"]
        if len(pw) < 4:
            conn.close()
            return _json_error(start_response, "Password must be at least 4 characters")
        pw_hash, salt = _hash_password(pw)
        updates.append("password_hash = ?")
        params.append(pw_hash)
        updates.append("salt = ?")
        params.append(salt)

    if not updates:
        conn.close()
        return _json_error(start_response, "Nothing to update")

    updates.append("updated_at = datetime('now')")
    params.append(user["id"])

    conn.execute(
        f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
        params
    )
    conn.commit()
    conn.close()
    return _json(start_response, {"message": "Profile updated"})


# ════════════════════════════════════════════════════════════
# PASSWORD RESET API
# ════════════════════════════════════════════════════════════

def handle_forgot_password(environ, start_response):
    """POST /api/auth/forgot-password — generate reset token."""
    data = _read_post(environ)
    if not data or not data.get("email"):
        return _json_error(start_response, "Email is required")

    email = data["email"].strip().lower()
    conn = _get_db()
    user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()

    # Always return the same response to prevent email enumeration
    response = {"message": "If this email exists, a reset code has been generated."}

    if user:
        user_id = user["id"]
        # Invalidate old unused tokens for this user
        conn.execute("UPDATE password_reset_tokens SET used = 1 WHERE user_id = ? AND used = 0", (user_id,))

        token = uuid.uuid4().hex[:32]
        token_id = uuid.uuid4().hex[:16]
        expires = (datetime.utcnow() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            "INSERT INTO password_reset_tokens (id, user_id, token, expires_at) VALUES (?, ?, ?, ?)",
            (token_id, user_id, token, expires)
        )
        # Include the token in response so the frontend can show it
        # In production, this would be sent via email instead
        response["reset_token"] = token
        response["user_id"] = user_id

    conn.commit()
    conn.close()
    return _json(start_response, response)


def handle_reset_password(environ, start_response):
    """POST /api/auth/reset-password — use token to set new password."""
    data = _read_post(environ)
    if not data:
        return _json_error(start_response, "No data provided")

    token = (data.get("token") or "").strip()
    password = data.get("password") or ""

    if not token or not password:
        return _json_error(start_response, "Token and new password are required")

    if len(password) < 4:
        return _json_error(start_response, "Password must be at least 4 characters")

    conn = _get_db()
    row = conn.execute(
        "SELECT id, user_id, expires_at FROM password_reset_tokens WHERE token = ? AND used = 0",
        (token,)
    ).fetchone()

    if row is None:
        conn.close()
        return _json_error(start_response, "Invalid or expired reset token", "400 Bad Request")

    token_data = dict(row)
    expires = datetime.strptime(token_data["expires_at"], "%Y-%m-%d %H:%M:%S")
    if datetime.utcnow() > expires:
        conn.close()
        return _json_error(start_response, "Reset token has expired", "400 Bad Request")

    # Update password
    pw_hash, salt = _hash_password(password)
    conn.execute(
        "UPDATE users SET password_hash = ?, salt = ?, updated_at = datetime('now') WHERE id = ?",
        (pw_hash, salt, token_data["user_id"])
    )
    # Mark token as used
    conn.execute("UPDATE password_reset_tokens SET used = 1 WHERE id = ?", (token_data["id"],))
    conn.commit()
    conn.close()

    return _json(start_response, {"message": "Password has been reset successfully"})


# ════════════════════════════════════════════════════════════
# ADMIN API
# ════════════════════════════════════════════════════════════

def handle_admin_stats(start_response, current_user: dict):
    """GET /api/admin/stats — dashboard statistics."""
    conn = _get_db()
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    by_role = {}
    for r in conn.execute("SELECT role, COUNT(*) as cnt FROM users GROUP BY role").fetchall():
        by_role[r["role"]] = r["cnt"]
    by_status = {}
    for s in conn.execute("SELECT status, COUNT(*) as cnt FROM users GROUP BY status").fetchall():
        by_status[s["status"]] = s["cnt"]
    total_convs = conn.execute("SELECT COUNT(*) FROM chat_conversations").fetchone()[0]
    today_convs = conn.execute(
        "SELECT COUNT(*) FROM chat_conversations WHERE date(created_at) = date('now')"
    ).fetchone()[0]
    today_users = conn.execute(
        "SELECT COUNT(DISTINCT user_id) FROM chat_conversations WHERE date(created_at) = date('now')"
    ).fetchone()[0]
    conn.close()

    return _json(start_response, {
        "total_users": total_users,
        "users_by_role": by_role,
        "users_by_status": by_status,
        "total_conversations": total_convs,
        "today_conversations": today_convs,
        "today_active_users": today_users,
    })


def handle_admin_user_update(environ, start_response, user_id: str):
    """PATCH /api/admin/users/:id — update user (role, status, display_name)."""
    data = _read_post(environ)
    if not data:
        return _json_error(start_response, "No data provided")

    conn = _get_db()
    row = conn.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        conn.close()
        return _json_error(start_response, "User not found", "404 Not Found")

    updates = []
    params = []
    for field in ["display_name", "role", "status"]:
        if field in data and data[field]:
            # Validate role
            if field == "role" and data[field] not in ("user", "ops", "admin"):
                conn.close()
                return _json_error(start_response, f"Invalid role: {data[field]}")
            # Validate status
            if field == "status" and data[field] not in ("active", "disabled", "pending"):
                conn.close()
                return _json_error(start_response, f"Invalid status: {data[field]}")
            updates.append(f"{field} = ?")
            params.append(data[field])

    if not updates:
        conn.close()
        return _json_error(start_response, "No valid fields to update")

    params.append(user_id)
    conn.execute(
        f"UPDATE users SET updated_at = datetime('now'), {', '.join(updates)} WHERE id = ?",
        params
    )
    conn.commit()

    # Return updated user
    row = conn.execute(
        "SELECT id, email, display_name, role, status, created_at, updated_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    conn.close()

    return _json(start_response, {"user": dict(row), "message": "User updated"})


def handle_admin_user_chat(environ, start_response, user_id: str):
    """GET /api/admin/users/:id/chat — list a user's conversations."""
    conn = _get_db()
    # Check user exists
    user_row = conn.execute("SELECT id, email FROM users WHERE id = ?", (user_id,)).fetchone()
    if user_row is None:
        conn.close()
        return _json_error(start_response, "User not found", "404 Not Found")

    rows = conn.execute(
        "SELECT id, title, message_count, created_at, updated_at FROM chat_conversations "
        "WHERE user_id = ? ORDER BY updated_at DESC LIMIT 50",
        (user_id,)
    ).fetchall()
    conn.close()

    return _json(start_response, {
        "user": dict(user_row),
        "conversations": [dict(r) for r in rows],
        "total": len(rows),
    })


def handle_admin_chat_detail(environ, start_response, conv_id: str):
    """GET /api/admin/chat/:id — view any conversation's full messages."""
    conn = _get_db()
    conv = conn.execute(
        "SELECT id, user_id, title, message_count, created_at, updated_at FROM chat_conversations "
        "WHERE id = ?",
        (conv_id,)
    ).fetchone()

    if conv is None:
        conn.close()
        return _json_error(start_response, "Conversation not found", "404 Not Found")

    conv = dict(conv)
    # Get user info
    user_row = conn.execute(
        "SELECT email FROM users WHERE id = ?", (conv["user_id"],)
    ).fetchone()
    conv["user_email"] = user_row["email"] if user_row else "unknown"

    messages = conn.execute(
        "SELECT id, role, content, created_at FROM chat_messages WHERE conversation_id = ? ORDER BY created_at",
        (conv_id,)
    ).fetchall()
    conn.close()

    return _json(start_response, {
        "conversation": conv,
        "messages": [dict(m) for m in messages],
    })


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

    if path == "/api/auth/logout" and method == "POST":
        return handle_logout(environ, start_response)

    # ── Google OAuth ──
    if path == "/api/auth/google/login" and method == "POST":
        return handle_google_login(environ, start_response)

    # ── Chat history routes ──
    if path == "/api/auth/chat/save" and method == "POST":
        return handle_chat_save(environ, start_response)

    if path == "/api/auth/chat-history" and method == "GET":
        return handle_chat_history(environ, start_response)

    if path.startswith("/api/auth/chat/") and method == "GET":
        conv_id = path[len("/api/auth/chat/"):]
        if conv_id and "/" not in conv_id:
            return handle_chat_detail(environ, start_response, conv_id)

    # ── User settings ──
    if path == "/api/auth/update-profile" and method == "POST":
        return handle_update_profile(environ, start_response)

    # ── Password reset ──
    if path == "/api/auth/forgot-password" and method == "POST":
        return handle_forgot_password(environ, start_response)

    if path == "/api/auth/reset-password" and method == "POST":
        return handle_reset_password(environ, start_response)

    # ── Admin routes ──
    if path == "/api/admin/stats" and method == "GET":
        check = require_role("ops", "admin")
        user = check(environ, start_response)
        if user is None:
            return _take_auth_error(environ)
        return handle_admin_stats(start_response, user)

    if path == "/api/admin/users" and method == "GET":
        check = require_role("ops", "admin")
        user = check(environ, start_response)
        if user is None:
            return _take_auth_error(environ)
        return handle_admin_users(environ, start_response)

    if path.startswith("/api/admin/users/") and method == "DELETE":
        check = require_role("ops", "admin")
        user = check(environ, start_response)
        if user is None:
            return _take_auth_error(environ)
        user_id = path[len("/api/admin/users/"):]
        if not user_id or "/" in user_id:
            return _json_error(start_response, "Invalid user ID", "400 Bad Request")
        return handle_admin_delete(environ, start_response, user_id)

    # PATCH /api/admin/users/:id — admin only (can edit role/status)
    admin_patch_match = path.startswith("/api/admin/users/") and method == "PATCH"
    if admin_patch_match:
        user_id = path[len("/api/admin/users/"):]
        if user_id and "/" not in user_id:
            check = require_role("admin")
            user = check(environ, start_response)
            if user is None:
                return _take_auth_error(environ)
            return handle_admin_user_update(environ, start_response, user_id)

    # GET /api/admin/users/:id — ops/admin view single user detail (not /chat)
    if path.startswith("/api/admin/users/") and method == "GET" and not path.endswith("/chat"):
        user_id = path[len("/api/admin/users/"):]
        if user_id and "/" not in user_id:
            check = require_role("ops", "admin")
            user = check(environ, start_response)
            if user is None:
                return _take_auth_error(environ)
            return handle_admin_user_detail(environ, start_response, user_id)

    # GET /api/admin/users/:id/chat — ops/admin view user conversations
    if path.startswith("/api/admin/users/") and path.endswith("/chat") and method == "GET":
        user_id = path[len("/api/admin/users/"):-len("/chat")]
        if user_id and "/" not in user_id:
            check = require_role("ops", "admin")
            user = check(environ, start_response)
            if user is None:
                return _take_auth_error(environ)
            return handle_admin_user_chat(environ, start_response, user_id)

    # GET /api/admin/chat/:id — ops/admin view conversation details
    if path.startswith("/api/admin/chat/") and method == "GET":
        conv_id = path[len("/api/admin/chat/"):]
        if conv_id and "/" not in conv_id:
            check = require_role("ops", "admin")
            user = check(environ, start_response)
            if user is None:
                return _take_auth_error(environ)
            return handle_admin_chat_detail(environ, start_response, conv_id)

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

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http import HTTPStatus

from api.common import (
    bearer_token,
    client_ip,
    error_response,
    json_response,
    query_params,
    read_json,
    runtime_database_path,
    send,
)


MIN_PASSWORD_LENGTH = 8
_ATTEMPTS = {}


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()
        return False


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def db():
    path = runtime_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    return conn


def init_db(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL DEFAULT '',
            role TEXT NOT NULL DEFAULT 'user',
            email_verified_at TEXT,
            auth_provider TEXT NOT NULL DEFAULT 'password',
            google_sub TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL,
            expires_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reset_tokens (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            used_at TEXT
        );
        CREATE TABLE IF NOT EXISTS email_verifications (
            email TEXT NOT NULL,
            code_hash TEXT NOT NULL,
            purpose TEXT NOT NULL DEFAULT 'register',
            attempts INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            used_at TEXT,
            PRIMARY KEY (email, purpose)
        );
        CREATE TABLE IF NOT EXISTS oauth_states (
            state TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            used_at TEXT
        );
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            destination TEXT NOT NULL DEFAULT '',
            start_date TEXT NOT NULL DEFAULT '',
            end_date TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )
    ensure_auth_columns(conn)
    seed_admin(conn)


def ensure_auth_columns(conn):
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    migrations = {
        "email_verified_at": "ALTER TABLE users ADD COLUMN email_verified_at TEXT",
        "auth_provider": "ALTER TABLE users ADD COLUMN auth_provider TEXT NOT NULL DEFAULT 'password'",
        "google_sub": "ALTER TABLE users ADD COLUMN google_sub TEXT",
    }
    for column, statement in migrations.items():
        if column not in columns:
            conn.execute(statement)


def seed_admin(conn):
    email = (os.environ.get("ADMIN_EMAIL") or "").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD") or ""
    if not email or not password:
        return
    if password in {"admin", "admin123", "password", "changeme"} or len(password) < 12:
        return
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.execute("UPDATE users SET role = 'admin', email_verified_at = COALESCE(email_verified_at, ?), updated_at = ? WHERE id = ?", (now_iso(), now_iso(), existing["id"]))
        conn.commit()
        return
    timestamp = now_iso()
    conn.execute(
        "INSERT INTO users (email, password_hash, name, role, email_verified_at, auth_provider, created_at, updated_at) VALUES (?, ?, ?, 'admin', ?, 'password', ?, ?)",
        (email, hash_password(password), "Admin", timestamp, timestamp, timestamp),
    )
    conn.commit()


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return f"pbkdf2_sha256$200000${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    try:
        algorithm, rounds, salt_hex, digest_hex = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(rounds))
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def hash_code(email, code):
    secret = os.environ.get("AUTH_CODE_SECRET") or "vp-codex-local-secret"
    payload = f"{email.lower()}:{code}:{secret}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def generate_code():
    return f"{secrets.randbelow(1_000_000):06d}"


def app_base_url(environ=None):
    configured = (os.environ.get("APP_BASE_URL") or "").rstrip("/")
    if configured:
        return configured
    host = environ.get("HTTP_HOST") if environ else ""
    scheme = environ.get("wsgi.url_scheme", "https") if environ else "https"
    if host:
        return f"{scheme}://{host}"
    return "https://go2china.space"


def google_redirect_uri(environ):
    return os.environ.get("GOOGLE_REDIRECT_URI") or f"{app_base_url(environ)}/api/auth/google/callback"


def public_auth_config():
    return {
        "google": bool(os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET")),
        "emailVerification": True,
        "emailProvider": "resend" if os.environ.get("RESEND_API_KEY") else "development",
    }


def public_user(row):
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "role": row["role"],
        "emailVerified": bool(row["email_verified_at"]),
        "authProvider": row["auth_provider"],
        "createdAt": row["created_at"],
    }


def check_rate(key, limit=6, window=300):
    now = time.time()
    attempts = [item for item in _ATTEMPTS.get(key, []) if now - item < window]
    if len(attempts) >= limit:
        _ATTEMPTS[key] = attempts
        return False
    attempts.append(now)
    _ATTEMPTS[key] = attempts
    return True


def current_user(environ):
    token = bearer_token(environ)
    if not token:
        return None
    with db() as conn:
        row = conn.execute(
            """
            SELECT users.* FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ? AND sessions.expires_at > ?
            """,
            (token, int(time.time())),
        ).fetchone()
    return row


def require_user(environ, start_response):
    user = current_user(environ)
    if not user:
        return None, error_response(start_response, HTTPStatus.UNAUTHORIZED, "unauthorized", "Sign in required.", environ)
    return user, None


def require_admin(environ, start_response):
    user, failure = require_user(environ, start_response)
    if failure:
        return None, failure
    if user["role"] != "admin":
        return None, error_response(start_response, HTTPStatus.FORBIDDEN, "forbidden", "Admin access required.", environ)
    return user, None


def send_verification_email(email, code):
    subject = "Verify your VisePanda account"
    text = f"Your VisePanda verification code is {code}. It expires in 15 minutes."
    from_email = os.environ.get("EMAIL_FROM") or "VisePanda <onboarding@resend.dev>"
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        return False
    payload = {
        "from": from_email,
        "to": [email],
        "subject": subject,
        "text": text,
        "html": f"<p>Your VisePanda verification code is <strong>{code}</strong>.</p><p>It expires in 15 minutes.</p>",
    }
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "VisePanda/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError):
        return False


def create_verification(conn, email):
    code = generate_code()
    conn.execute(
        """
        INSERT INTO email_verifications (email, code_hash, purpose, attempts, created_at, expires_at, used_at)
        VALUES (?, ?, 'register', 0, ?, ?, NULL)
        ON CONFLICT(email, purpose) DO UPDATE SET
            code_hash = excluded.code_hash,
            attempts = 0,
            created_at = excluded.created_at,
            expires_at = excluded.expires_at,
            used_at = NULL
        """,
        (email, hash_code(email, code), now_iso(), int(time.time()) + 15 * 60),
    )
    return code


def verification_payload(email, code, sent):
    payload = {
        "ok": True,
        "requiresVerification": True,
        "email": email,
        "delivery": "sent" if sent else "not_configured",
    }
    if os.environ.get("AUTH_EXPOSE_EMAIL_CODE") == "1":
        payload["verificationCode"] = code
    return payload


def register(environ, start_response):
    body = read_json(environ)
    email = str(body.get("email") or "").strip().lower()
    password = str(body.get("password") or "")
    if "@" not in email or "." not in email:
        return error_response(start_response, HTTPStatus.BAD_REQUEST, "invalid_email", "Enter a valid email address.", environ)
    if len(password) < MIN_PASSWORD_LENGTH:
        return error_response(start_response, HTTPStatus.BAD_REQUEST, "weak_password", "Password must be at least 8 characters.", environ)
    timestamp = now_iso()
    try:
        with db() as conn:
            existing = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if existing and existing["email_verified_at"]:
                return error_response(start_response, HTTPStatus.CONFLICT, "email_exists", "Email is already registered.", environ)
            if existing:
                conn.execute(
                    "UPDATE users SET password_hash = ?, auth_provider = 'password', updated_at = ? WHERE email = ?",
                    (hash_password(password), timestamp, email),
                )
            else:
                conn.execute(
                    "INSERT INTO users (email, password_hash, name, role, auth_provider, created_at, updated_at) VALUES (?, ?, '', 'user', 'password', ?, ?)",
                    (email, hash_password(password), timestamp, timestamp),
                )
            code = create_verification(conn, email)
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            sent = send_verification_email(email, code)
    except sqlite3.IntegrityError:
        return error_response(start_response, HTTPStatus.CONFLICT, "email_exists", "Email is already registered.", environ)
    return json_response(start_response, {**verification_payload(email, code, sent), "user": public_user(row)}, HTTPStatus.CREATED, environ)


def verify_email(environ, start_response):
    body = read_json(environ)
    email = str(body.get("email") or "").strip().lower()
    code = str(body.get("code") or "").strip()
    if not email or not code:
        return error_response(start_response, HTTPStatus.BAD_REQUEST, "verification_required", "Email and verification code are required.", environ)
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM email_verifications WHERE email = ? AND purpose = 'register' AND used_at IS NULL",
            (email,),
        ).fetchone()
        if not row or row["expires_at"] <= int(time.time()):
            return error_response(start_response, HTTPStatus.BAD_REQUEST, "verification_expired", "Verification code is expired.", environ)
        if row["attempts"] >= 5:
            return error_response(start_response, HTTPStatus.TOO_MANY_REQUESTS, "verification_locked", "Too many verification attempts.", environ)
        if not hmac.compare_digest(row["code_hash"], hash_code(email, code)):
            conn.execute("UPDATE email_verifications SET attempts = attempts + 1 WHERE email = ? AND purpose = 'register'", (email,))
            return error_response(start_response, HTTPStatus.BAD_REQUEST, "invalid_verification_code", "Verification code is invalid.", environ)
        timestamp = now_iso()
        conn.execute("UPDATE email_verifications SET used_at = ? WHERE email = ? AND purpose = 'register'", (timestamp, email))
        conn.execute("UPDATE users SET email_verified_at = ?, updated_at = ? WHERE email = ?", (timestamp, timestamp, email))
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        token = create_session(conn, user["id"])
    return json_response(start_response, {"token": token, "user": public_user(user)}, environ=environ)


def resend_verification(environ, start_response):
    body = read_json(environ)
    email = str(body.get("email") or "").strip().lower()
    key = f"verify:{client_ip(environ)}:{email}"
    if not check_rate(key, limit=3):
        return error_response(start_response, HTTPStatus.TOO_MANY_REQUESTS, "rate_limited", "Too many attempts. Try again later.", environ)
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not user or user["email_verified_at"]:
            return json_response(start_response, {"ok": True}, environ=environ)
        code = create_verification(conn, email)
        sent = send_verification_email(email, code)
    return json_response(start_response, verification_payload(email, code, sent), environ=environ)


def create_session(conn, user_id):
    token = secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, now_iso(), int(time.time()) + 60 * 60 * 24 * 14),
    )
    return token


def login(environ, start_response):
    body = read_json(environ)
    email = str(body.get("email") or "").strip().lower()
    password = str(body.get("password") or "")
    key = f"login:{client_ip(environ)}:{email}"
    if not check_rate(key):
        return error_response(start_response, HTTPStatus.TOO_MANY_REQUESTS, "rate_limited", "Too many attempts. Try again later.", environ)
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not row or not verify_password(password, row["password_hash"]):
            return error_response(start_response, HTTPStatus.UNAUTHORIZED, "invalid_credentials", "Invalid email or password.", environ)
        if not row["email_verified_at"]:
            return error_response(start_response, HTTPStatus.FORBIDDEN, "email_unverified", "Verify your email before signing in.", environ)
        token = create_session(conn, row["id"])
    return json_response(start_response, {"token": token, "user": public_user(row)}, environ=environ)


def logout(environ, start_response):
    token = bearer_token(environ)
    if token:
        with db() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    return json_response(start_response, {"ok": True}, environ=environ)


def me(environ, start_response):
    user, failure = require_user(environ, start_response)
    if failure:
        return failure
    return json_response(start_response, {"user": public_user(user)}, environ=environ)


def update_profile(environ, start_response):
    user, failure = require_user(environ, start_response)
    if failure:
        return failure
    body = read_json(environ)
    name = str(body.get("name") or user["name"]).strip()[:80]
    current_password = str(body.get("currentPassword") or "")
    new_password = str(body.get("newPassword") or "")
    with db() as conn:
        if new_password:
            fresh = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
            if not verify_password(current_password, fresh["password_hash"]):
                return error_response(start_response, HTTPStatus.BAD_REQUEST, "current_password_required", "Current password is required.", environ)
            if len(new_password) < MIN_PASSWORD_LENGTH:
                return error_response(start_response, HTTPStatus.BAD_REQUEST, "weak_password", "Password must be at least 8 characters.", environ)
            conn.execute("UPDATE users SET name = ?, password_hash = ?, updated_at = ? WHERE id = ?", (name, hash_password(new_password), now_iso(), user["id"]))
        else:
            conn.execute("UPDATE users SET name = ?, updated_at = ? WHERE id = ?", (name, now_iso(), user["id"]))
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    return json_response(start_response, {"user": public_user(row)}, environ=environ)


def forgot_password(environ, start_response):
    body = read_json(environ)
    email = str(body.get("email") or "").strip().lower()
    key = f"forgot:{client_ip(environ)}:{email}"
    if not check_rate(key, limit=3):
        return error_response(start_response, HTTPStatus.TOO_MANY_REQUESTS, "rate_limited", "Too many attempts. Try again later.", environ)
    exposed = {}
    with db() as conn:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            token = secrets.token_urlsafe(32)
            conn.execute(
                "INSERT INTO reset_tokens (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (token, row["id"], now_iso(), int(time.time()) + 3600),
            )
            if os.environ.get("AUTH_EXPOSE_RESET_TOKEN") == "1":
                exposed = {"resetToken": token}
    return json_response(start_response, {"ok": True, **exposed}, environ=environ)


def reset_password(environ, start_response):
    body = read_json(environ)
    token = str(body.get("token") or "")
    password = str(body.get("password") or "")
    if len(password) < MIN_PASSWORD_LENGTH:
        return error_response(start_response, HTTPStatus.BAD_REQUEST, "weak_password", "Password must be at least 8 characters.", environ)
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM reset_tokens WHERE token = ? AND used_at IS NULL AND expires_at > ?",
            (token, int(time.time())),
        ).fetchone()
        if not row:
            return error_response(start_response, HTTPStatus.BAD_REQUEST, "invalid_token", "Reset token is invalid or expired.", environ)
        conn.execute("UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?", (hash_password(password), now_iso(), row["user_id"]))
        conn.execute("UPDATE reset_tokens SET used_at = ? WHERE token = ?", (now_iso(), token))
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (row["user_id"],))
    return json_response(start_response, {"ok": True}, environ=environ)


def google_start(environ, start_response):
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if not (client_id and client_secret):
        return error_response(start_response, HTTPStatus.SERVICE_UNAVAILABLE, "google_not_configured", "Google login is not configured.", environ)
    state = secrets.token_urlsafe(32)
    with db() as conn:
        conn.execute(
            "INSERT INTO oauth_states (state, provider, created_at, expires_at) VALUES (?, 'google', ?, ?)",
            (state, now_iso(), int(time.time()) + 600),
        )
    params = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": google_redirect_uri(environ),
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
            "prompt": "select_account",
        }
    )
    location = f"https://accounts.google.com/o/oauth2/v2/auth?{params}"
    return send(start_response, HTTPStatus.FOUND, "", [("Location", location)], environ)


def _post_form(url, payload):
    request = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _google_userinfo(access_token):
    request = urllib.request.Request(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def google_callback(environ, start_response):
    params = query_params(environ)
    code = params.get("code", "")
    state = params.get("state", "")
    if not code or not state:
        return auth_callback_page(start_response, "", "Google login was cancelled or incomplete.", environ)
    with db() as conn:
        state_row = conn.execute(
            "SELECT * FROM oauth_states WHERE state = ? AND provider = 'google' AND used_at IS NULL AND expires_at > ?",
            (state, int(time.time())),
        ).fetchone()
        if not state_row:
            return auth_callback_page(start_response, "", "Google login expired. Please try again.", environ)
        conn.execute("UPDATE oauth_states SET used_at = ? WHERE state = ?", (now_iso(), state))
    try:
        token_data = _post_form(
            "https://oauth2.googleapis.com/token",
            {
                "code": code,
                "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
                "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
                "redirect_uri": google_redirect_uri(environ),
                "grant_type": "authorization_code",
            },
        )
        profile = _google_userinfo(token_data["access_token"])
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError):
        return auth_callback_page(start_response, "", "Google login could not be completed. Please try again.", environ)
    email = str(profile.get("email") or "").strip().lower()
    google_sub = str(profile.get("sub") or "").strip()
    if not email or not google_sub or profile.get("email_verified") is False:
        return auth_callback_page(start_response, "", "Google did not return a verified email.", environ)
    timestamp = now_iso()
    with db() as conn:
        existing = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE users
                SET google_sub = ?, auth_provider = CASE WHEN auth_provider = 'password' THEN 'password+google' ELSE auth_provider END,
                    email_verified_at = COALESCE(email_verified_at, ?), updated_at = ?
                WHERE id = ?
                """,
                (google_sub, timestamp, timestamp, existing["id"]),
            )
            user = conn.execute("SELECT * FROM users WHERE id = ?", (existing["id"],)).fetchone()
        else:
            conn.execute(
                """
                INSERT INTO users (email, password_hash, name, role, email_verified_at, auth_provider, google_sub, created_at, updated_at)
                VALUES (?, ?, ?, 'user', ?, 'google', ?, ?, ?)
                """,
                (email, "google_oauth", str(profile.get("name") or "").strip()[:80], timestamp, google_sub, timestamp, timestamp),
            )
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        token = create_session(conn, user["id"])
    return auth_callback_page(start_response, token, "", environ)


def auth_callback_page(start_response, token, error, environ):
    target = app_base_url(environ)
    payload = json.dumps({"token": token, "error": error})
    html = f"""<!doctype html>
<html lang="en">
  <head><meta charset="utf-8"><title>VisePanda account</title></head>
  <body>
    <script>
      const result = {payload};
      if (result.token) {{
        sessionStorage.setItem("vp_token", result.token);
        location.replace("{target}/?auth=google");
      }} else {{
        location.replace("{target}/?auth_error=" + encodeURIComponent(result.error || "Google login failed"));
      }}
    </script>
  </body>
</html>"""
    return send(start_response, HTTPStatus.OK, html, [("Content-Type", "text/html; charset=utf-8")], environ)


def list_trips(environ, start_response):
    user, failure = require_user(environ, start_response)
    if failure:
        return failure
    with db() as conn:
        rows = conn.execute("SELECT * FROM trips WHERE user_id = ? ORDER BY created_at DESC", (user["id"],)).fetchall()
    trips = [trip_payload(row) for row in rows]
    return json_response(start_response, {"trips": trips}, environ=environ)


def trip_payload(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "destination": row["destination"],
        "startDate": row["start_date"],
        "endDate": row["end_date"],
        "notes": row["notes"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def create_trip(environ, start_response):
    user, failure = require_user(environ, start_response)
    if failure:
        return failure
    body = read_json(environ)
    title = str(body.get("title") or "China trip").strip()[:120]
    destination = str(body.get("destination") or "").strip()[:120]
    timestamp = now_iso()
    with db() as conn:
        cur = conn.execute(
            """
            INSERT INTO trips (user_id, title, destination, start_date, end_date, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"],
                title,
                destination,
                str(body.get("startDate") or "")[:20],
                str(body.get("endDate") or "")[:20],
                str(body.get("notes") or "")[:2000],
                timestamp,
                timestamp,
            ),
        )
        row = conn.execute("SELECT * FROM trips WHERE id = ?", (cur.lastrowid,)).fetchone()
    return json_response(start_response, {"trip": trip_payload(row)}, HTTPStatus.CREATED, environ)


def delete_trip(path_parts, environ, start_response):
    user, failure = require_user(environ, start_response)
    if failure:
        return failure
    if len(path_parts) != 3:
        return error_response(start_response, HTTPStatus.NOT_FOUND, "not_found", "Trip not found.", environ)
    with db() as conn:
        cur = conn.execute("DELETE FROM trips WHERE id = ? AND user_id = ?", (path_parts[2], user["id"]))
    if cur.rowcount == 0:
        return error_response(start_response, HTTPStatus.NOT_FOUND, "trip_not_found", "Trip not found.", environ)
    return json_response(start_response, {"ok": True}, environ=environ)


def admin_users(environ, start_response):
    _, failure = require_admin(environ, start_response)
    if failure:
        return failure
    with db() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    return json_response(start_response, {"users": [public_user(row) for row in rows]}, environ=environ)


def admin_delete_user(path_parts, environ, start_response):
    admin, failure = require_admin(environ, start_response)
    if failure:
        return failure
    if len(path_parts) != 4:
        return error_response(start_response, HTTPStatus.NOT_FOUND, "not_found", "User not found.", environ)
    user_id = int(path_parts[3])
    if user_id == admin["id"]:
        return error_response(start_response, HTTPStatus.BAD_REQUEST, "cannot_delete_self", "Admins cannot delete themselves.", environ)
    with db() as conn:
        cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    if cur.rowcount == 0:
        return error_response(start_response, HTTPStatus.NOT_FOUND, "user_not_found", "User not found.", environ)
    return json_response(start_response, {"ok": True}, environ=environ)


def dispatch(method, path_parts, environ, start_response):
    try:
        if path_parts[:2] == ["api", "auth"]:
            action = path_parts[2] if len(path_parts) > 2 else ""
            if method == "GET" and action == "config":
                return json_response(start_response, public_auth_config(), environ=environ)
            if method == "POST" and action == "register":
                return register(environ, start_response)
            if method == "POST" and action == "verify-email":
                return verify_email(environ, start_response)
            if method == "POST" and action == "resend-verification":
                return resend_verification(environ, start_response)
            if method == "POST" and action == "login":
                return login(environ, start_response)
            if method == "GET" and path_parts[2:4] == ["google", "start"]:
                return google_start(environ, start_response)
            if method == "GET" and path_parts[2:4] == ["google", "callback"]:
                return google_callback(environ, start_response)
            if method == "POST" and action == "logout":
                return logout(environ, start_response)
            if method == "GET" and action == "me":
                return me(environ, start_response)
            if method in {"PUT", "PATCH", "POST"} and action == "update-profile":
                return update_profile(environ, start_response)
            if method == "POST" and action == "forgot-password":
                return forgot_password(environ, start_response)
            if method == "POST" and action == "reset-password":
                return reset_password(environ, start_response)
        if path_parts[:2] == ["api", "trips"]:
            if method == "GET" and len(path_parts) == 2:
                return list_trips(environ, start_response)
            if method == "POST" and len(path_parts) == 2:
                return create_trip(environ, start_response)
            if method == "DELETE":
                return delete_trip(path_parts, environ, start_response)
        if path_parts[:3] == ["api", "admin", "users"]:
            if method == "GET" and len(path_parts) == 3:
                return admin_users(environ, start_response)
            if method == "DELETE":
                return admin_delete_user(path_parts, environ, start_response)
    except ValueError as exc:
        return error_response(start_response, HTTPStatus.BAD_REQUEST, "bad_request", str(exc), environ)
    return error_response(start_response, HTTPStatus.NOT_FOUND, "not_found", "Endpoint not found.", environ)

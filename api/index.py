"""
VisePanda — China Travel AI Agent
Single-file FastAPI app. No static frontend files.
Supabase config is server-injected into HTML.
LLM: GLM 5.1 (ZhipuAI, OpenAI-compatible).
"""
from __future__ import annotations

import datetime as dt
import random
import re
import string
import time
import hashlib
import json
import os
import secrets
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
import urllib.parse
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from jose import jwt

# ══════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "glm-5.1")
LLM_ENABLED = os.getenv("LLM_ENABLED", "1") == "1"
AUTH_TEST_BYPASS = os.getenv("AUTH_TEST_BYPASS", "0").lower() in ("1", "true", "yes")
IS_DEV = os.getenv("IS_DEV", "0") == "1"

# Rate limiting
_RATE_LIMIT: dict[str, list[float]] = {}
_RATE_WINDOW = 60  # seconds
_RATE_MAX = 20  # requests per window

# ── Database: Supabase Management API (HTTP-based) ──
SUPABASE_PAT = os.getenv("SUPABASE_PAT", "")
SUPABASE_PROJECT_REF = "jdlinmdhmulozrjeseyc"
_SB_HEADERS = {"Authorization": f"Bearer {SUPABASE_PAT}", "Content-Type": "application/json"}
_SB_QUERY_URL = f"https://api.supabase.com/v1/projects/{SUPABASE_PROJECT_REF}/database/query"

class SupabaseDB:
    """Drop-in replacement for SQLAlchemy session using Supabase Management API."""
    
    _http_proxy = os.getenv("SUPABASE_HTTP_PROXY", "")
    _http_client = httpx.Client(
        proxy=_http_proxy if (IS_DEV and _http_proxy) else None,
        timeout=httpx.Timeout(20.0, connect=15.0)
    )
    
    def __init__(self):
        self._pending_inserts = []
        self._pending_deletes = []
        self._pending_updates = []
    
    def _query(self, sql: str) -> list[dict]:
        r = self._http_client.post(_SB_QUERY_URL, headers=_SB_HEADERS, json={"query": sql})
        if r.status_code >= 400:
            raise Exception(f"DB error: {r.text[:200]}")
        return r.json() if r.text.strip() else []
    
    def _val(self, v):
        """Serialize Python value for SQL."""
        if v is None: return "NULL"
        if isinstance(v, bool): return "TRUE" if v else "FALSE"
        if isinstance(v, (int, float)): return str(v)
        if isinstance(v, dt.datetime):
            return f"'{v.isoformat()}'"
        if isinstance(v, (list, dict)):
            return f"'{json.dumps(v)}'"
        return f"'{str(v).replace(chr(39), chr(39)+chr(39))}'"
    
    def _table_name(self, model) -> str:
        return model.__tablename__ if hasattr(model, '__tablename__') else model.__name__.lower()
    
    def query(self, model):
        """Start a SELECT query. Returns QueryBuilder."""
        return _QueryBuilder(self, model)
    
    def add(self, obj):
        """Queue an INSERT."""
        self._pending_inserts.append(obj)
    
    def delete(self, obj):
        """Queue a DELETE."""
        self._pending_deletes.append(obj)
    
    def commit(self):
        """Execute all pending operations."""
        err = None
        for obj in self._pending_inserts:
            try:
                self._insert_one(obj)
            except Exception as e:
                err = e
        for obj in self._pending_deletes:
            try:
                self._delete_one(obj)
            except Exception as e:
                err = e
        self._pending_inserts = []
        self._pending_deletes = []
        if err: raise err
    
    def flush(self):
        self.commit()  # Supabase API doesn't have transactions, commit = flush
    
    def rollback(self):
        self._pending_inserts = []
        self._pending_deletes = []
    
    def close(self):
        pass
    
    def _insert_one(self, obj):
        table = self._table_name(type(obj))
        cols = []
        vals = []
        for col in obj.__table__.columns if hasattr(obj, '__table__') else []:
            val = getattr(obj, col.name, None)
            if col.name == 'id' and val is None:
                import uuid
                val = str(uuid.uuid4())
            cols.append(col.name)
            vals.append(self._val(val))
        sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(vals)})"
        try:
            self._query(sql)
        except Exception as e:
            if "duplicate" in str(e).lower() or "exists" in str(e).lower() or "unique" in str(e).lower():
                pass  # Ignore duplicate inserts (upsert-like behavior)
            raise
    
    def _delete_one(self, obj):
        table = self._table_name(type(obj))
        # Try to identify by primary key
        pk = None
        for col in obj.__table__.columns if hasattr(obj, '__table__') else []:
            if col.primary_key:
                pk = col.name
                break
        if pk:
            val = getattr(obj, pk, None)
            if val:
                self._query(f"DELETE FROM {table} WHERE {pk}={self._val(val)}")

class _QueryBuilder:
    def __init__(self, db, model):
        self._db = db
        self._model = model
        self._table = model.__tablename__
        self._where = []
        self._order = None
        self._limit = None
        self._join = None
    
    def filter(self, *args, **kwargs):
        if args:
            # Handle SQLAlchemy BinaryExpression -> compile to raw SQL
            expr = args[0]
            if hasattr(expr, 'left') and hasattr(expr, 'right'):
                try:
                    import sqlalchemy as sa
                    compiled = expr.compile(compile_kwargs={"literal_binds": True})
                    self._where.append(str(compiled))
                except Exception:
                    self._where.append(str(expr))
            else:
                self._where.append(str(expr))
        for k, v in kwargs.items():
            self._where.append(f"{k}={self._db._val(v)}")
        return self
    
    def filter_by(self, **kwargs):
        for k, v in kwargs.items():
            self._where.append(f"{k}={self._db._val(v)}")
        return self
    
    def order_by(self, col):
        self._order = str(col)
        return self
    
    def limit(self, n):
        self._limit = n
        return self
    
    def _build(self, count=False):
        sql = f"SELECT {'COUNT(*)' if count else '*'} FROM {self._table}"
        if self._join: sql += f" {self._join}"
        if self._where: sql += " WHERE " + " AND ".join(self._where)
        if self._order: sql += f" ORDER BY {self._order}"
        if self._limit: sql += f" LIMIT {self._limit}"
        return sql
    
    def all(self):
        rows = self._db._query(self._build())
        return [_row_to_model(self._model, r) for r in rows]
    
    def one(self):
        rows = self._db._query(self._build())
        if not rows: raise Exception("No row found")
        return _row_to_model(self._model, rows[0])
    
    def one_or_none(self):
        rows = self._db._query(self._build())
        if not rows: return None
        return _row_to_model(self._model, rows[0])
    
    def count(self):
        rows = self._db._query(self._build(count=True))
        return int(rows[0]['count']) if rows else 0

    def delete(self):
        """Execute DELETE WHERE query."""
        sql = f"DELETE FROM {self._table}"
        if self._where:
            sql += " WHERE " + " AND ".join(self._where)
        self._db._query(sql)

class _Row:
    """Minimal row-like object that bypasses SQLAlchemy instrumentation."""
    def __init__(self, data: dict):
        self.__dict__.update(data)

def _row_to_model(model, row: dict):
    """Convert a dict row to a model-like object (bypass SQLAlchemy instrumentation)."""
    return _Row(row)

def get_db():
    return SupabaseDB()

# ══════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════

class Base(DeclarativeBase):
    pass

def _uid(): return str(uuid.uuid4())
def _now(): return dt.datetime.now(dt.timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uid)
    profile: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

# ── Local email/password auth ──

def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"

def _verify_password(password: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split(":", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == h
    except Exception:
        return False

class EmailUser(Base):
    __tablename__ = "email_users"
    email: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, default=_uid)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

# ── Phone number auth (SMS verification) ──

class PhoneVerification(Base):
    __tablename__ = "phone_verifications"
    phone: Mapped[str] = mapped_column(String, primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified: Mapped[bool] = mapped_column(default=False)

class PhoneUser(Base):
    __tablename__ = "phone_users"
    phone: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, default=_uid)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

SMS_PROVIDER = os.getenv("SMS_PROVIDER", "console")
ALIYUN_SMS_ACCESS_KEY = os.getenv("ALIYUN_SMS_ACCESS_KEY", "")
ALIYUN_SMS_SECRET = os.getenv("ALIYUN_SMS_SECRET", "")
ALIYUN_SMS_SIGN_NAME = os.getenv("ALIYUN_SMS_SIGN_NAME", "VisePanda")
ALIYUN_SMS_TEMPLATE_CODE = os.getenv("ALIYUN_SMS_TEMPLATE_CODE", "")
ALIYUN_SMS_TEMPLATE_PARAM = os.getenv("ALIYUN_SMS_TEMPLATE_PARAM", '{"code":"%s"}')

def _send_sms(phone: str, code: str) -> bool:
    """Send SMS via configured provider. Returns True on success."""
    if SMS_PROVIDER == "aliyun":
        try:
            import hmac, base64, hashlib
            # Aliyun SMS API via HTTP
            params = {
                "Action": "SendSms",
                "Format": "JSON",
                "Version": "2017-05-25",
                "AccessKeyId": ALIYUN_SMS_ACCESS_KEY,
                "SignatureMethod": "HMAC-SHA1",
                "Timestamp": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "SignatureVersion": "1.0",
                "SignatureNonce": str(uuid.uuid4()),
                "PhoneNumbers": phone,
                "SignName": ALIYUN_SMS_SIGN_NAME,
                "TemplateCode": ALIYUN_SMS_TEMPLATE_CODE,
                "TemplateParam": ALIYUN_SMS_TEMPLATE_PARAM % code,
            }
            sorted_keys = sorted(params.keys())
            query = "&".join(f"{k}={urllib.parse.quote(str(params[k]), safe='')}" for k in sorted_keys)
            string_to_sign = f"GET&{urllib.parse.quote('/', safe='')}&{urllib.parse.quote(query, safe='')}"
            sig = base64.b64encode(hmac.new(f"{ALIYUN_SMS_SECRET}&".encode(), string_to_sign.encode(), hashlib.sha1).digest()).decode()
            url = f"https://dysmsapi.aliyuncs.com/?{query}&Signature={urllib.parse.quote(sig, safe='')}"
            r = httpx.get(url, timeout=10)
            result = r.json()
            if result.get("Code") == "OK":
                return True
            print(f"[SMS] Aliyun error: {result}", flush=True)
            return False
        except Exception as e:
            print(f"[SMS] Aliyun failed: {e}", flush=True)
            return False
    # Console provider (default) — just log it
    print(f"[SMS] Code for {phone}: {code}", flush=True)
    return True

class UserPreference(Base):
    __tablename__ = "user_preferences"
    id = Column(String, primary_key=True, default=lambda: _uid())
    user_id = Column(String, unique=True, nullable=False)
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: dt.datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: dt.datetime.utcnow(), onupdate=lambda: dt.datetime.utcnow())

class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(String, primary_key=True, default=lambda: _uid())
    user_id = Column(String, nullable=False)
    trip_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: dt.datetime.utcnow())

class Trip(Base):
    __tablename__ = "trips"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    cities: Mapped[list] = mapped_column(JSON, default=list)
    start_date: Mapped[str | None] = mapped_column(String, nullable=True)
    end_date: Mapped[str | None] = mapped_column(String, nullable=True)
    constraints: Mapped[dict] = mapped_column(JSON, default=dict)
    current_itinerary: Mapped[dict] = mapped_column(JSON, default=dict)
    itinerary_versions: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)
    share_id: Mapped[str | None] = mapped_column(String, nullable=True, unique=True, index=True)
    user: Mapped[User] = relationship()

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uid)
    user_id: Mapped[str] = mapped_column(String, index=True)
    trip_id: Mapped[str] = mapped_column(String, ForeignKey("trips.id"), index=True)
    role: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

# ══════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════

_JWKS = {"ts": 0.0, "keys": None}

def _get_jwks():
    now = dt.datetime.now(dt.timezone.utc).timestamp()
    if _JWKS["keys"] and (now - _JWKS["ts"]) < 300:
        return _JWKS["keys"]
    r = httpx.get(f"{SUPABASE_URL}/auth/v1/certs", timeout=10)
    r.raise_for_status()
    _JWKS["keys"] = r.json()["keys"]
    _JWKS["ts"] = now
    return _JWKS["keys"]


def _sanitize(text: str) -> str:
    """Strip HTML, limit length, remove control chars."""
    text = text.strip()[:2000]
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return text

def _get_user_id(request: Request, guest_id: str | None) -> tuple[str, str]:
    """Returns (user_id, mode). mode = 'user' | 'guest'."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        # Local tokens
        # `test:` tokens are dev bypass (require AUTH_TEST_BYPASS)
        if token.startswith("test:"):
            if AUTH_TEST_BYPASS:
                return token.split(":", 1)[1], "user"
            raise HTTPException(401, "Invalid token")
        # `email:` and `phone:` tokens are real user auth (email/phone login)
        if token.startswith("email:") or token.startswith("phone:"):
            return token.split(":", 1)[1], "user"
        # Verify Supabase JWT
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise HTTPException(401, "Invalid token")
        keys = _get_jwks()
        key = next((k for k in keys if k.get("kid") == kid), None)
        if not key:
            raise HTTPException(401, "Unknown signing key")
        claims = jwt.decode(token, key, algorithms=["RS256"], audience="authenticated")
        sub = claims.get("sub")
        if not sub:
            raise HTTPException(401, "Token missing sub")
        return sub, "user"

    if guest_id:
        return f"guest:{guest_id}", "guest"
    raise HTTPException(401, "Login required")




# ══════════════════════════════════════════════════════════
# LLM
# ══════════════════════════════════════════════════════════

from api.prompt import SYSTEM_PROMPT, get_system_prompt, get_proactive_questions
from data.tools.packing import get_packing_list
from data.tools.travel_tools import recommend_destination, generate_caption
from data.tools.pricing import estimate_trip_cost, get_weather_advice
from data.tools.visa_guide import VISA_INFO

async def stream_llm(messages: list[dict]) -> AsyncGenerator[str, None]:
    if not LLM_ENABLED or not LLM_API_KEY:
        yield f"data: {json.dumps({'error': 'LLM not configured'})}\n\n"
        yield "data: [DONE]\n\n"
        return

    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "stream": True,
        "max_tokens": 2048,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{LLM_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {LLM_API_KEY}"},
                json=payload,
            ) as resp:
                if resp.status_code != 200:
                    yield f"data: {json.dumps({'error': f'LLM {resp.status_code}'})}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        yield "data: [DONE]\n\n"
                        return
                    try:
                        obj = json.loads(data)
                        token = obj["choices"][0]["delta"].get("content", "")
                        if token:
                            yield f"data: {json.dumps({'token': token})}\n\n"
                    except (KeyError, json.JSONDecodeError):
                        continue
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

    yield "data: [DONE]\n\n"


# ══════════════════════════════════════════════════════════
# HTML PAGES (server-rendered)
# ══════════════════════════════════════════════════════════

CSS = """
.light-theme,.light{--bg0:#f5f0eb;--bg1:#faf5ef;--line:rgba(0,0,0,.07);--muted:rgba(0,0,0,.45);--text:rgba(0,0,0,.88);--accent:#bc3a2c;--red:#bc3a2c;--red-bright:#c43a2c;--gold:#b8942e;--gold-bright:#c9a96e}
:root{--bg0:#05070b;--bg1:#0e0b14;--line:rgba(255,255,255,.08);--muted:rgba(255,255,255,.58);--text:rgba(255,255,255,.92);--accent:#7dd3fc;--red:#bc3a2c;--red-bright:#dc4a3a;--gold:#d4a84b;--gold-bright:#e8c56a;font-family:'Inter','Noto Sans SC','PingFang SC',ui-sans-serif,system-ui,-apple-system,sans-serif}
body{margin:0;min-height:100vh;background:linear-gradient(175deg,#0e0b14 0,#120f1e 35%,#0a0f17 65%,#05070b 100%);color:var(--text);position:relative;animation:fadeIn .4s ease}
.bg-shanshui{position:fixed;inset:0;background:url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 800"><defs><linearGradient id="mG" cx="50%" cy="40%" r="50%"><stop offset="0%" stop-color="%23ffe9c4" stop-opacity=".7"/><stop offset="100%" stop-color="%23ffe9c4" stop-opacity="0"/></linearGradient></defs><circle cx="1050" cy="140" r="48" fill="%23ffe9c4" opacity=".18"/><circle cx="1050" cy="140" r="60" fill="url(%23mG)" opacity=".12"/><path d="M200 460 L203 460 L203 660 L200 660Z M196 460 L211 460 L211 463 L196 463Z M196 490 L211 490 L211 493 L196 493Z M196 520 L211 520 L211 523 L196 523Z M193 530 L217 530 L217 532 L193 532Z M201 440 L195 460 L207 460Z" fill="%23fff" opacity=".007"/><path d="M350 490 L330 520 L370 520Z M347 520 L353 520 L353 660 L347 660Z" fill="%23fff" opacity=".007"/><path d="M500 470 L503 470 L503 660 L500 660Z M496 470 L511 470 L511 473 L496 473Z M496 500 L511 500 L511 503 L496 503Z M501 450 L495 470 L507 470Z M493 480 L517 480 L517 482 L493 482Z" fill="%23fff" opacity=".006"/><path d="M700 400 L704 400 L704 660 L700 660Z M695 400 L714 400 L714 403 L695 403Z M695 430 L714 430 L714 433 L695 433Z M695 460 L714 460 L714 463 L695 463Z M691 470 L722 470 L722 472 L691 472Z M702 380 L694 400 L710 400Z" fill="%23fff" opacity=".01"/><path d="M850 420 Q870 390 890 420 L890 660 L850 660Z M867 420 L873 420 L873 660 L867 660Z" fill="%23fff" opacity=".009"/><path d="M1050 430 L1054 430 L1054 660 L1050 660Z M1045 430 L1064 430 L1064 433 L1045 433Z M1045 460 L1064 460 L1064 463 L1045 463Z M1052 410 L1044 430 L1060 430Z M1041 470 L1072 470 L1072 472 L1041 472Z" fill="%23fff" opacity=".009"/><path d="M150 500 Q180 460 210 500 L210 660 L150 660Z M155 500 L155 660 M205 500 L205 660 M177 500 L183 500 L183 660 L177 660Z M140 500 Q160 495 180 500 Q200 495 220 500 M145 520 Q165 515 180 520 Q195 515 215 520" fill="%23fff" opacity=".013" stroke="%23fff" stroke-width="1"/><path d="M580 380 L585 380 L585 660 L580 660Z M574 380 L596 380 L596 384 L574 384Z M574 410 L596 410 L596 414 L574 414Z M574 440 L596 440 L596 444 L574 444Z M569 450 L606 450 L606 453 L569 453Z M582 355 L572 380 L592 380Z M567 380 Q574 376 582 380 Q590 376 597 380 M567 410 Q574 406 582 410 Q590 406 597 410 M567 440 Q574 436 582 440 Q590 436 597 440" fill="%23fff" opacity=".016" stroke="%23fff" stroke-width="1"/><path d="M1200 470 Q1230 430 1260 470 L1260 660 L1200 660Z M1205 470 Q1220 450 1235 470 M1225 470 Q1240 450 1255 470 M1227 470 L1233 470 L1233 660 L1227 660Z" fill="%23fff" opacity=".012"/><path d="M300 580 L480 580 L480 660 L300 660Z M300 575 L480 575 L480 580 L300 580Z M300 570 L315 570 L315 580 L300 580Z M330 570 L345 570 L345 580 L330 580Z M360 570 L375 570 L375 580 L360 580Z M390 570 L405 570 L405 580 L390 580Z M420 570 L435 570 L435 580 L420 580Z M450 570 L465 570 L465 580 L450 580Z M370 620 L410 620 L410 660 L370 660Z M380 630 Q390 625 400 630" fill="%23fff" opacity=".008"/><rect x="0" y="680" width="1400" height="120" fill="%23fff" opacity=".005"/></svg>') center/cover;opacity:.35;filter:blur(4px);pointer-events:none;z-index:0}
.bg-shanshui::after{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 1000px 600px at 1080px 140px,rgba(255,233,196,.06) 0%,transparent 70%);pointer-events:none}
.light header,.light-theme header{background:rgba(255,255,255,.7)!important;border-bottom-color:rgba(0,0,0,.06)!important}
header{height:56px;display:flex;align-items:center;justify-content:space-between;padding:0 16px;border-bottom:1px solid rgba(212,168,75,.12);background:rgba(10,8,16,.7);backdrop-filter:blur(14px);position:relative;z-index:1}
.dot{display:none}
.logo-seal{display:inline-flex;align-items:center;gap:12px;text-decoration:none;color:var(--text)}
.logo-seal .seal{display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border:2px solid var(--red-bright);border-radius:6px;background:linear-gradient(135deg,rgba(220,74,58,.12),rgba(220,74,58,.03));font-size:16px;color:var(--red-bright);font-weight:700;font-family:'Songti SC','STSong','Georgia',serif;transform:rotate(-2deg);flex-shrink:0;box-shadow:0 0 12px rgba(220,74,58,.15);transition:all .2s}
.logo-seal .seal:hover{background:linear-gradient(135deg,rgba(220,74,58,.18),rgba(220,74,58,.06));box-shadow:0 0 18px rgba(220,74,58,.25)}
.name{font-weight:650;font-size:15px;letter-spacing:.02em;color:var(--gold)}
.name-ch{font-size:11px;color:var(--gold-bright);margin-left:4px;font-weight:400;opacity:.8}
.btn{font-size:12px;padding:7px 16px;border-radius:6px;border:1px solid var(--line);background:rgba(255,255,255,.04);color:var(--text);cursor:pointer;text-decoration:none;transition:all .2s}
.btn:hover{background:rgba(255,255,255,.1);border-color:rgba(255,255,255,.2)}
.btn-accent{border-color:rgba(212,168,75,.3);background:rgba(212,168,75,.08);color:var(--gold-bright)}
.btn-accent:hover{border-color:rgba(212,168,75,.5);background:rgba(212,168,75,.14);color:%23f0d580}
.btn-red{border-color:var(--red-bright);background:rgba(220,74,58,.12);color:%23fff;font-weight:500}
.btn-red:hover{background:rgba(220,74,58,.22);border-color:%23e86a5a}
.card{border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:18px 16px;background:linear-gradient(160deg,rgba(255,255,255,.03),rgba(255,255,255,.008));cursor:pointer;transition:all .25s;text-align:left;text-decoration:none;display:block;position:relative;overflow:hidden}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--gold-bright),rgba(232,197,106,.06),transparent);opacity:0;transition:opacity .3s}
.card::after{content:'';position:absolute;bottom:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,var(--red-bright),transparent);opacity:0;transition:opacity .3s}
.card:hover{background:linear-gradient(160deg,rgba(255,255,255,.045),rgba(255,255,255,.015));transform:translateY(-3px);box-shadow:0 8px 30px rgba(0,0,0,.4),0 0 20px rgba(212,168,75,.04)}
.card:hover::before,.card:hover::after{opacity:1}
.card-title{font-weight:650;font-size:15px;color:var(--text);margin:0 0 4px}
.card-sub{font-size:11px;color:var(--muted);margin:0}
.card-emoji{font-size:26px;margin-bottom:8px;display:block}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:20px;max-width:530px;margin-left:auto;margin-right:auto}
.lang-switch{font-size:11px;padding:5px 10px;border-radius:4px;border:1px solid var(--line);background:rgba(255,255,255,.03);color:var(--text);cursor:pointer;margin-left:6px;text-decoration:none;transition:all .2s}
.lang-switch:hover{background:rgba(255,255,255,.08);border-color:rgba(212,168,75,.4);color:var(--gold-bright)}
.recent-title{font-size:13px;color:var(--muted);margin-bottom:8px;font-weight:600}
.recent-trip{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border:1px solid var(--line);border-radius:10px;margin-bottom:6px;background:rgba(255,255,255,.02);text-decoration:none;color:var(--text);transition:all .15s}
.recent-trip:hover{border-color:rgba(212,168,75,.3);background:rgba(212,168,75,.06)}
.recent-trip-label{font-size:14px;font-weight:500}
.recent-trip-meta{font-size:11px;color:var(--muted)}
.trip-card{border-left:3px solid var(--accent)!important;background:linear-gradient(135deg,rgba(125,211,252,.06),transparent)!important}
.price-budget{color:%234ade80}
.price-mid{color:%23fbbf24}
.price-luxury{color:%23f87171}
code{background:rgba(0,0,0,.3);padding:2px 6px;border-radius:4px;font-family:'JetBrains Mono','Fira Code','Cascadia Code',monospace;font-size:.9em}
pre{background:rgba(0,0,0,.4);padding:12px 16px;border-radius:10px;border:1px solid var(--line);overflow-x:auto;margin:8px 0}
pre code{background:none;padding:0;border-radius:0}
#quickReplies .chip{background:rgba(255,255,255,.05);border-color:var(--line);color:var(--muted)}
.profile-page{max-width:560px;margin:60px auto;padding:0 20px}.profile-card{border:1px solid var(--line);border-radius:12px;padding:24px;background:linear-gradient(160deg,rgba(255,255,255,.025),rgba(255,255,255,.005));margin-bottom:16px}.profile-card h3{font-size:14px;color:var(--gold);margin:0 0 16px}.profile-field{margin-bottom:16px}.profile-field label{font-size:11px;color:var(--muted);display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.05em}.profile-field input[type=text],.profile-field input[type=email],.profile-field input[type=password],.profile-field select{width:100%;padding:10px 14px;border-radius:8px;border:1px solid var(--line);background:rgba(255,255,255,.03);color:var(--text);outline:none;font-size:14px;box-sizing:border-box}.profile-field input:focus{border-color:var(--gold)}.profile-field select option{background:#1a1f2e;color:var(--text)}.profile-save-btn{width:100%;padding:12px;border-radius:8px;border:1px solid var(--red-bright);background:rgba(220,74,58,.12);color:%23fff;cursor:pointer;font-size:14px;font-weight:600;transition:all .2s}.profile-save-btn:hover{background:rgba(220,74,58,.22);border-color:%23e86a5a}.profile-save-btn:disabled{opacity:.4;cursor:not-allowed}.profile-msg{padding:10px 14px;border-radius:8px;font-size:13px;margin-bottom:12px;display:none}.profile-msg.success{display:block;background:rgba(74,222,128,.1);border:1px solid rgba(74,222,128,.2);color:%234ade80}.profile-msg.error{display:block;background:rgba(248,113,113,.1);border:1px solid rgba(248,113,113,.2);color:%23f87171}.profile-status{font-size:11px;color:var(--muted);margin-top:4px}.profile-divider{border:none;border-top:1px solid var(--line);margin:20px 0}.profile-header{text-align:center;margin-bottom:32px}.profile-avatar{width:64px;height:64px;border-radius:50%;background:linear-gradient(135deg,rgba(220,74,58,.18),rgba(220,74,58,.05));border:2px solid rgba(220,74,58,.2);display:flex;align-items:center;justify-content:center;margin:0 auto 12px;font-size:28px;box-shadow:0 0 20px rgba(220,74,58,.1)}.profile-header h1{font-size:18px;margin:0;color:var(--text)}.profile-header p{color:var(--muted);font-size:13px;margin:4px 0 0}.profile-nav{text-align:center;margin-top:32px;font-size:13px}.profile-nav a{color:var(--muted);text-decoration:none;margin:0 8px}.profile-nav a:hover{color:var(--gold)}.profile-nav a:last-child{margin-left:8px}
input[type=text]{border-radius:6px;border:1px solid var(--line);background:rgba(255,255,255,.03);color:var(--text);padding:12px 16px;outline:none;font-size:16px;transition:all .2s}
input[type=text]:focus{border-color:var(--gold);box-shadow:0 0 0 4px rgba(212,168,75,.08)}
.light footer,.light-theme footer{background:rgba(0,0,0,.03)!important}
footer{border-top:1px solid rgba(212,168,75,.08);background:rgba(10,8,16,.4);color:var(--muted);font-size:12px;padding:10px 16px;text-align:center;position:relative;z-index:1}

/* Landing v2 — Hot routes */
.section-label{font-size:13px;color:var(--gold);margin:20px 0 10px;text-align:left;font-weight:600;letter-spacing:.05em}
.hot-scroll{display:flex;gap:10px;overflow-x:auto;padding-bottom:8px;margin-bottom:4px;scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch}
.hot-scroll::-webkit-scrollbar{display:none}
.hot-card{flex-shrink:0;display:flex;flex-direction:column;align-items:center;gap:4px;border:1px solid var(--line);border-radius:12px;padding:14px 18px;background:linear-gradient(160deg,rgba(255,255,255,.03),rgba(255,255,255,.008));cursor:pointer;text-decoration:none;color:var(--text);transition:all .25s;min-width:100px}
.hot-card:hover{border-color:rgba(212,168,75,.3);background:rgba(212,168,75,.06);transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,.2)}
.hot-emoji{font-size:24px}
.hot-text{font-size:12px;font-weight:600;white-space:nowrap}
.hot-sub{font-size:10px;color:var(--muted)}

/* City chips */
.city-chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}
.city-chip{font-size:12px;padding:6px 14px;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.03);cursor:pointer;text-decoration:none;color:var(--text);transition:all .2s}
.city-chip:hover{border-color:rgba(125,211,252,.35);background:rgba(125,211,252,.08);color:var(--accent)}
@media(max-width:640px){h1{font-size:24px!important}header{padding:0 12px}.btn{padding:6px 12px;font-size:11px}footer{font-size:11px;padding:8px 12px}.bubble{max-width:95%!important;font-size:15px}#msgForm{gap:6px}#msgInput{height:40px;font-size:16px}#sendBtn{height:44px;padding:0 20px;font-size:14px}.chat-footer{padding:10px 12px;padding-bottom:calc(10px + env(safe-area-inset-bottom))}#thread{padding:12px 12px 140px;padding-bottom:calc(140px + env(safe-area-inset-bottom))}input[type=text]{font-size:16px}.welcome-chips{gap:4px!important}.cards{grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px}.card{padding:14px}.card-emoji{font-size:22px}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes scaleIn{from{opacity:0;transform:scale(.93)}to{opacity:1;transform:scale(1)}}
@keyframes brushIn{0%{clip-path:inset(0 100% 0 0)}100%{clip-path:inset(0 0 0 0)}}
@media(prefers-reduced-motion){*,*::before,*::after{animation-duration:0s!important;transition-duration:0s!important}}
/* ── Animate.css inspired entrance animations ── */
@keyframes fadeUp{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
@keyframes fadeInRight{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:translateX(0)}}
@keyframes fadeInLeft{from{opacity:0;transform:translateX(-20px)}to{opacity:1;transform:translateX(0)}}
@keyframes pulseGlow{0%,100%{opacity:.35}50%{opacity:.5}}
@keyframes sealPulse{0%,100%{box-shadow:0 0 12px rgba(220,74,58,.15)}50%{box-shadow:0 0 22px rgba(220,74,58,.3)}}
@keyframes shimmer{0%{background-position:-200% 0}100%{background-position:200% 0}}
@keyframes scaleInRotate{from{opacity:0;transform:scale(.85) rotate(-4deg)}to{opacity:1;transform:scale(1) rotate(-2deg)}}

/* Animated utility classes */
.anim-fade-up{animation:fadeUp .5s ease both}
.anim-fade-right{animation:fadeInRight .4s ease both}
.anim-fade-left{animation:fadeInLeft .4s ease both}
.anim-delay-1{animation-delay:.1s}.anim-delay-2{animation-delay:.2s}.anim-delay-3{animation-delay:.3s}
.anim-delay-4{animation-delay:.4s}.anim-delay-5{animation-delay:.5s}.anim-delay-6{animation-delay:.6s}
.anim-delay-7{animation-delay:.7s}.anim-delay-8{animation-delay:.8s}

/* Background breathing */
.bg-shanshui{animation:pulseGlow 8s ease-in-out infinite}

/* Seal logo pulse */
.logo-seal .seal{animation:scaleInRotate .6s ease both,sealPulse 3s ease-in-out infinite .6s}

/* Message entrance */
.msg{animation:fadeUp .35s ease both}
.msg.user{animation:fadeInRight .35s ease both}
.msg.bot{animation:fadeInLeft .35s ease both}

/* Card stagger for landing */
.card{animation:fadeUp .45s ease both}
.card:nth-child(1){animation-delay:.05s}.card:nth-child(2){animation-delay:.1s}
.card:nth-child(3){animation-delay:.15s}.card:nth-child(4){animation-delay:.2s}
.card:nth-child(5){animation-delay:.25s}.card:nth-child(6){animation-delay:.3s}
.card:nth-child(7){animation-delay:.35s}.card:nth-child(8){animation-delay:.4s}

/* Hero text entrance */
h1{animation:fadeUp .5s ease both}
p{animation:fadeUp .5s ease both;animation-delay:.1s}
form{animation:fadeUp .5s ease both;animation-delay:.15s}
.cat-nav{animation:fadeUp .5s ease both;animation-delay:.2s}

/* Skeleton shimmer */
.skeleton{animation:shimmer 1.5s infinite;background:linear-gradient(90deg,rgba(255,255,255,.04)25%,rgba(255,255,255,.1)50%,rgba(255,255,255,.04)75%);background-size:200% 100%}
.skel-block{padding:4px 0}
.skel-line{height:14px;border-radius:7px;margin:8px 0;background:linear-gradient(90deg,rgba(255,255,255,.04)25%,rgba(255,255,255,.1)50%,rgba(255,255,255,.04)75%);background-size:200% 100%;animation:shimmer 1.5s infinite}
.skel-w-10{width:10%}.skel-w-20{width:20%}.skel-w-30{width:30%}.skel-w-40{width:40%}.skel-w-50{width:50%}.skel-w-60{width:60%}.skel-w-70{width:70%}.skel-w-80{width:80%}.skel-w-90{width:90%}.skel-w-100{width:100%}

/* Button press feedback */
/* ── Micro-interactions ── */
.btn{position:relative;overflow:hidden}
.btn::after,.btn-accent::after,.btn-red::after{content:'';position:absolute;inset:0;background:radial-gradient(circle at var(--mx,50%) var(--my,50%),rgba(255,255,255,.15) 0%,transparent 70%);opacity:0;transition:opacity .3s;pointer-events:none}
.btn:hover::after,.btn-accent:hover::after,.btn-red:hover::after{opacity:1}
.btn:active,.btn-accent:active,.btn-red:active,.cat-tag:active{transform:scale(.96);transition:transform .1s}

/* Link hover underline */
.logo-seal::after{content:'';position:absolute;bottom:-2px;left:36px;right:0;height:1px;background:var(--gold);transform:scaleX(0);transform-origin:left;transition:transform .3s}
.logo-seal:hover::after{transform:scaleX(1)}

/* Card glow float enhancement */
.card{transition:all .35s cubic-bezier(.25,.46,.45,.94)}
.card:hover{transform:translateY(-4px);box-shadow:0 12px 40px rgba(0,0,0,.4),0 0 30px rgba(212,168,75,.06)}
.card:active{transform:scale(.97);transition:all .1s}

/* Cat-tag hover underline */
.cat-tag{position:relative}
.cat-tag::after{content:'';position:absolute;bottom:0;left:20%;right:20%;height:1px;background:var(--gold-bright);transform:scaleX(0);transition:transform .2s}
.cat-tag:hover::after{transform:scaleX(1)}

/* Input focus glow */
input[type=text]:focus{transform:scale(1.01)}

/* Welcome chip hover */
.welcome-chip{transition:all .25s cubic-bezier(.25,.46,.45,.94)}
.welcome-chip:hover{transform:translateY(-2px);box-shadow:0 4px 16px rgba(125,211,252,.1)}

/* ── Chinese Theme Pack ── */
[data-theme="hongjin"]{--bg0:#1A0A0A;--bg1:#2D1212;--line:rgba(212,168,75,.15);--muted:rgba(255,200,150,.5);--text:#F5E6C8;--accent:#C41E1E;--red:#C41E1E;--red-bright:#E83939;--gold:#D4A017;--gold-bright:#F0C848;}
[data-theme="mogreen"]{--bg0:#0A1410;--bg1:#0F1E18;--line:rgba(100,200,150,.12);--muted:rgba(160,210,180,.5);--text:#D4E8D8;--accent:#2D8A4E;--red:#C43A3A;--red-bright:#D85A4A;--gold:#8AB84E;--gold-bright:#A8D86A;}
[data-theme="qinghua"]{--bg0:#080E1A;--bg1:#0E1628;--line:rgba(130,180,220,.12);--muted:rgba(150,190,230,.5);--text:#D4E4F0;--accent:#3A7BBF;--red:#C43A3A;--red-bright:#D85A4A;--gold:#8AB8D4;--gold-bright:#A8D0E8;}
/* Mobile improvements */
.chat-wrapper{padding-bottom:env(safe-area-inset-bottom)}
body{padding-bottom:env(safe-area-inset-bottom)}
.city-chip,.cat-tag,.hot-card,.card{-webkit-tap-highlight-color:transparent;touch-action:manipulation}
/* Accessibility */
:focus-visible{outline:2px solid var(--gold-bright);outline-offset:2px;border-radius:4px}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0}
@media(prefers-contrast:more){:root{--muted:rgba(255,255,255,.75)}.light-theme,.light{--muted:rgba(0,0,0,.65)}}

"""

def _inject_config() -> str:
    """Inject Supabase config into HTML."""
    return f"""<script>
window.__SUPABASE_CONFIG__ = {{
  supabase_url: "{SUPABASE_URL}",
  supabase_anon_key: "{SUPABASE_ANON_KEY}"
}};
// Auto-detect locale via IP (only if no preference stored)
!function(){{if(!localStorage.getItem('vp_lang')){{fetch('/api/locale').then(function(r){{return r.json()}}).then(function(d){{if(d.locale==='zh'){{localStorage.setItem('vp_lang','zh');location.reload()}}}}).catch(function(){{}})}}}}();
</script>"""

def page_landing() -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#bc3a2c">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap" rel="stylesheet">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="VisePanda">
<link rel="apple-touch-icon" href="/static/icon.svg"><title data-i18n="title">VisePanda — AI China Travel Planner</title><meta name="description" data-i18n-content="metaDesc" content="Your AI-powered guide to traveling China. Get personalized day-by-day itineraries, food recommendations, hotel tips, and local insights — just tell us where and how long."><meta property="og:title" content="VisePanda — AI China Travel Planner"><meta property="og:description" content="Personalized China travel itineraries powered by AI — built by travelers, for travelers."><meta property="og:type" content="website"><meta name="twitter:card" content="summary_large_image"><style>{CSS}</style><script defer src='/_vercel/insights/script.js'></script><script defer src='/_vercel/speed-insights/script.js'></script>{_inject_config()}</head><body>
<div class="bg-shanshui"></div>
<header><div><a href="/" class="logo-seal"><span class="seal">熊</span><span class="name">VisePanda</span></a></div><div id="authArea"><a href="#" class="lang-switch" onclick="event.preventDefault();setLang(LANG==='en'?'zh':'en')" data-i18n="langLabel">中</a><a href="#" onclick="event.preventDefault();signIn()" class="btn btn-accent" style="color:var(--gold-bright)" data-i18n="signIn">Sign in</a><a href="#" onclick="event.preventDefault();toggleTheme()" class="lang-switch" id="themeToggle" title="Toggle theme">🌓</a></div></header>
<main style="position:relative;min-height:calc(100vh-56px);display:flex;align-items:center;justify-content:center;padding:24px 16px 90px;z-index:1">
<div style="width:min(680px,96%);text-align:center">
<h1 style="font-size:36px;margin:0 0 6px;letter-spacing:-.02em;font-weight:700" data-i18n="heroTitle">🐼 Your personal guide to China</h1>
<p style="color:var(--gold-bright);font-size:14px;margin:0 0 20px;font-weight:500" data-i18n="heroSub">Just say where and how long — we'll handle the rest. Day-by-day itineraries, local food, hotels, and insider tips.</p>

<form onsubmit="event.preventDefault();const v=document.getElementById('q').value.trim();goChat(v||document.getElementById('q').placeholder)" style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
<input id="q" type="text" placeholder="Beijing 5 days, food + history, mid-range budget…" data-i18n-placeholder="inputPlaceholder" style="width:min(480px,88vw);height:48px;padding:0 16px">
<button type="submit" class="btn btn-red" style="height:48px;padding:0 24px;font-size:14px;font-weight:600" data-i18n="startBtn">🚀 Plan My Trip</button>
</form>
<div class="section-label">🔥 Popular trips</div>
<div class="hot-scroll">
  <a class="hot-card" href="#" onclick="event.preventDefault();goChat('Beijing 3 days, history and culture, mid-range budget')"><span class="hot-emoji">🏯</span><span class="hot-text">Beijing History</span><span class="hot-sub">3 days · ¥1500+</span></a>
  <a class="hot-card" href="#" onclick="event.preventDefault();goChat('Chengdu 4 days, food tour, hotpot and pandas, relaxed')"><span class="hot-emoji">🐼</span><span class="hot-text">Chengdu Food</span><span class="hot-sub">4 days · ¥1200+</span></a>
  <a class="hot-card" href="#" onclick="event.preventDefault();goChat('Yunnan 7 days, Dali Lijiang Shangri-La, nature')"><span class="hot-emoji">🏔️</span><span class="hot-text">Yunnan Explorer</span><span class="hot-sub">7 days · ¥3000+</span></a>
  <a class="hot-card" href="#" onclick="event.preventDefault();goChat('Xi\'an 3 days, Terracotta Warriors, history')"><span class="hot-emoji">🏛️</span><span class="hot-text">Xi'an Ancient</span><span class="hot-sub">3 days · ¥1500+</span></a>
  <a class="hot-card" href="#" onclick="event.preventDefault();goChat('Guangzhou 3 days, dim sum and food culture')"><span class="hot-emoji">🥟</span><span class="hot-text">Guangzhou Eats</span><span class="hot-sub">3 days · ¥1500+</span></a>
  <a class="hot-card" href="#" onclick="event.preventDefault();goChat('Chongqing 3 days, night views and hotpot')"><span class="hot-emoji">🌆</span><span class="hot-text">Chongqing Nights</span><span class="hot-sub">3 days · ¥1000+</span></a>
</div>
<div class="section-label">🏙️ Popular cities</div>
<div class="city-chips">
  <a class="city-chip" href="#" onclick="event.preventDefault();goChat('Beijing')">Beijing</a>
  <a class="city-chip" href="#" onclick="event.preventDefault();goChat('Shanghai')">Shanghai</a>
  <a class="city-chip" href="#" onclick="event.preventDefault();goChat('Chengdu')">Chengdu</a>
  <a class="city-chip" href="#" onclick="event.preventDefault();goChat('Xi\'an')">Xi'an</a>
  <a class="city-chip" href="#" onclick="event.preventDefault();goChat('Guangzhou')">Guangzhou</a>
  <a class="city-chip" href="#" onclick="event.preventDefault();goChat('Hangzhou')">Hangzhou</a>
  <a class="city-chip" href="#" onclick="event.preventDefault();goChat('Chongqing')">Chongqing</a>
  <a class="city-chip" href="#" onclick="event.preventDefault();goChat('Guilin')">Guilin</a>
  <a class="city-chip" href="#" onclick="event.preventDefault();goChat('Kunming')">Kunming</a>
  <a class="city-chip" href="#" onclick="event.preventDefault();goChat('Suzhou')">Suzhou</a>
  <a class="city-chip" href="#" onclick="event.preventDefault();goChat('Zhangjiajie')">Zhangjiajie</a>
  <a class="city-chip" href="#" onclick="event.preventDefault();goChat('Lhasa')">Lhasa</a>
</div>
<div class="cat-nav"><span class="cat-tag active" data-cat="all" onclick="filterCards('all')">🔥 All</span><span class="cat-tag" data-cat="food" onclick="filterCards('food')">🍜 Food</span><span class="cat-tag" data-cat="history" onclick="filterCards('history')">🏯 History</span><span class="cat-tag" data-cat="nature" onclick="filterCards('nature')">🏔️ Nature</span><span class="cat-tag" data-cat="city" onclick="filterCards('city')">🌃 Cities</span></div>
<div class="cards" id="cardGrid">
<a class="card anim-fade-up" data-cat="history" href="#" onclick="event.preventDefault();goChat('Beijing 3 days, Forbidden City Great Wall hutongs, mid-range')"><div class="card-emoji">🏯</div><div class="card-title">Beijing</div><div class="card-sub">Forbidden City · Great Wall · Hutongs</div></a>
<a class="card anim-fade-up" data-cat="food" href="#" onclick="event.preventDefault();goChat('Chengdu 4 days, hotpot street food pandas')"><div class="card-emoji">🐼</div><div class="card-title">Chengdu</div><div class="card-sub">Hotpot · Pandas · Tea Houses</div></a>
<a class="card anim-fade-up" data-cat="nature" href="#" onclick="event.preventDefault();goChat('Yunnan 7 days, Dali Lijiang Shangri-La')"><div class="card-emoji">🏔️</div><div class="card-title">Yunnan</div><div class="card-sub">Dali Old Town · Jade Dragon · Shangri-La</div></a>
<a class="card anim-fade-up" data-cat="city" href="#" onclick="event.preventDefault();goChat('Shanghai 3 days, The Bund Disney French Concession')"><div class="card-emoji">🌃</div><div class="card-title">Shanghai</div><div class="card-sub">The Bund · Disney · Art Deco</div></a>
<a class="card anim-fade-up" data-cat="history" href="#" onclick="event.preventDefault();goChat('Xi\'an 3 days, Terracotta Warriors ancient capital')"><div class="card-emoji">🏛️</div><div class="card-title">Xi'an</div><div class="card-sub">Terracotta Warriors · Muslim Quarter</div></a>
<a class="card anim-fade-up" data-cat="nature" href="#" onclick="event.preventDefault();goChat('Guilin 4 days, Li River Yangshuo rice terraces')"><div class="card-emoji">🛶</div><div class="card-title">Guilin</div><div class="card-sub">Li River · Yangshuo · Rice Terraces</div></a>
<a class="card anim-fade-up" data-cat="food" href="#" onclick="event.preventDefault();goChat('Guangzhou 3 days, dim sum culinary tour')"><div class="card-emoji">🥟</div><div class="card-title">Guangzhou</div><div class="card-sub">Dim Sum · Cantonese · Night Markets</div></a>
<a class="card anim-fade-up" data-cat="city" href="#" onclick="event.preventDefault();goChat('Chongqing 3 days, night views hotpot 8D city')"><div class="card-emoji">🌆</div><div class="card-title">Chongqing</div><div class="card-sub">Night Views · Hotpot · Hongyadong</div></a>
</div>
<div id="recentTrips" style="display:none;margin-top:20px;text-align:left"></div>
<div style="margin-top:16px;font-size:12px;color:var(--muted)" data-i18n="guestHint">✉️ Email · 📱 Phone · 🔑 Google · 👤 Guest mode</div>
</div></main>
<footer data-i18n="footer">🐼 VisePanda · AI-powered China travel planner · Try it without signing up</footer>
<script src="/static/i18n.js"></script>
<script src="/static/landing.js"></script><script src="/static/pwa.js"></script></body></html>"""

def _render_msg(text: str) -> str:
    """Convert LLM markdown to HTML (mirrors chat.js M())."""
    import re
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'\n\n', '</p><p>', text)
    text = text.replace('\n', '<br>')
    if '**Day ' in text:
        text = '<div class=trip-card>' + text + '</div>'
    return text

def page_share(share_id: str) -> str:
    db = get_db()
    try:
        trip = db.query(Trip).filter(Trip.share_id == share_id).one_or_none()
        if not trip:
            return '<html lang=en><head><meta charset=utf-8><title>Not Found</title><style>body{display:flex;align-items:center;justify-content:center;min-height:100vh;background:#0a0f17;color:#fff;font-family:sans-serif;text-align:center;margin:0}h1{font-size:48px}a{color:#7dd3fc}</style><h1>🐼</h1><p>Trip not found</p><a href=/>Back home</a><script src="/static/i18n.js"></script>'
        msgs = db.query(ChatMessage).filter(ChatMessage.trip_id == trip.id).order_by(ChatMessage.created_at.asc()).all()
    finally:
        db.close()
    msgs_html = ''.join(f'<div class="msg {m.role}"><div class=bubble>{_render_msg(m.content)}</div></div>' for m in msgs)
    title = trip.title or 'Shared Trip'
    
    # Build structured summary
    itin = trip.current_itinerary or {}
    cities_str = ', '.join(itin.get('cities', [])) or 'China'
    days_str = f"{itin.get('day_count', '?')} days" if itin.get('day_count') else ''
    budget_str = {'budget': '💰 Budget', 'mid': '💰 Mid-range', 'luxury': '💰 Luxury'}.get(itin.get('budget_tier', ''), '')
    summary_parts = [s for s in [cities_str, days_str, budget_str] if s]
    summary = ' · '.join(summary_parts) if summary_parts else 'AI-planned trip'
    
    tid = trip.id
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#bc3a2c">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&family=Noto+Serif+SC:wght@600;700&display=swap" rel="stylesheet">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="VisePanda">
<link rel="apple-touch-icon" href="/static/icon.svg"><title>{title} · VisePanda</title>
<meta name="description" content="{summary}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{summary}">
<meta property="og:image" content="/api/trips/{tid}/card">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
</style><script defer src='/_vercel/insights/script.js'></script><script defer src='/_vercel/speed-insights/script.js'></script></head><body><div class="bg-shanshui"></div>
<div class="share-header"><h2>🐼 {title}</h2><p data-i18n="shareAI">AI-planned trip · ''' + str(len(msgs)) + ''' messages</p><a href="/" class="btn btn-accent" style="margin-top:16px;display:inline-block" data-i18n="planYourOwn">🚀 Create your own trip</a></div>
<div class="share-thread">''' + msgs_html + '''</div>
<div id="tripMap" class="vp-map-container" style="display:block;height:400px;margin:16px"></div>
<div class="share-footer"><a href="/" class="btn btn-accent" data-i18n="planYourOwn">Plan your own trip</a><script src="/static/i18n.js"></script></div>
<script src="/static/pwa.js"></script><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script src="/static/map.js"></script>
<script>
var _tid="''' + tid + '''";
(function(){
try{
var r=new XMLHttpRequest();
r.open('GET','/api/trips/'+_tid,false);
r.send();
var d=JSON.parse(r.responseText);
if(d.current_itinerary&&d.current_itinerary.cities&&d.current_itinerary.cities.length>0){
VP_MAP.loadItinerary('tripMap',d);
}
}catch(e){}
})();
</script>
</body></html>'''
    return html


def page_trips() -> str:
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#bc3a2c">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&family=Noto+Serif+SC:wght@600;700&display=swap" rel="stylesheet">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="VisePanda">
<link rel="apple-touch-icon" href="/static/icon.svg"><title data-i18n="tripsTitle">My Trips · VisePanda</title><style>{CSS}
.trips-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;padding:20px;max-width:900px;margin:0 auto}}
.trip-item{{border:1px solid var(--line);border-radius:14px;padding:18px;background:rgba(255,255,255,.02);cursor:pointer;transition:all .2s;text-decoration:none;display:block}}
.trip-item:hover{{border-color:rgba(125,211,252,.35);background:rgba(125,211,252,.04)}}
.trip-item h3{{font-size:16px;margin:0 0 6px;color:var(--text)}}
.trip-item .meta{{font-size:12px;color:var(--muted)}}
.empty{{text-align:center;padding:60px 20px;color:var(--muted)}}
.modal-overlay{{position:fixed;inset:0;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;z-index:9998;animation:fadeIn .15s ease}}
.modal-content{{background:#1a1f2e;border:1px solid var(--line);border-radius:16px;padding:24px;max-width:420px;width:90vw;animation:scaleIn .15s ease}}
#toast{{position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,.85);color:#fff;padding:10px 20px;border-radius:999px;font-size:14px;z-index:9999;animation:fadeInOut 1.8s ease forwards;pointer-events:none}}
@keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes scaleIn{{from{{opacity:0;transform:scale(.95)}}to{{opacity:1;transform:scale(1)}}}}
@keyframes fadeInOut{{0%{{opacity:0;transform:translateX(-50%) translateY(8px)}}15%{{opacity:1;transform:translateX(-50%) translateY(0)}}85%{{opacity:1;transform:translateX(-50%) translateY(0)}}100%{{opacity:0;transform:translateX(-50%) translateY(-8px)}}}}
</style><script defer src='/_vercel/insights/script.js'></script><script defer src='/_vercel/speed-insights/script.js'></script></head><body>
<div class="bg-shanshui"></div>
<header><div><a href="/" class="logo-seal"><span class="seal">熊</span><span class="name">VisePanda</span></a></div><div><a href="/" class="btn" data-i18n="homeBtn">Home</a><a href="#" class="lang-switch" onclick="event.preventDefault();setLang(LANG==='en'?'zh':'en')" data-i18n="langLabel">中</a><a href="#" onclick="event.preventDefault();toggleTheme()" class="lang-switch" id="themeToggle" title="Toggle theme">🌓</a></div></header>
<main style="position:relative;z-index:1;min-height:calc(100vh-56px);padding:20px 16px 80px">
<h2 style="text-align:center;color:var(--text);font-size:22px;margin:20px 0" data-i18n="tripsHeading">My Trips</h2>
<div id="tripsList" class="trips-grid"><div class="skeleton" style="height:100px"></div></div>
<div id="emptyMsg" class="empty" style="display:none"><p data-i18n="noTrips">No trips yet.</p><a href="/" class="btn btn-accent" style="display:inline-block;margin-top:12px" data-i18n="startPlanning">Start Planning</a></div>
</main>
<script src="/static/i18n.js"></script>
<script src="/static/trips.js"></script><script src="/static/pwa.js"></script></body></html>'''

def page_chat() -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#bc3a2c">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&family=Noto+Serif+SC:wght@600;700&display=swap" rel="stylesheet">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="VisePanda">
<link rel="apple-touch-icon" href="/static/icon.svg"><title data-i18n="chatTitle">Chat · VisePanda — AI China Travel Planner</title><meta name="description" data-i18n-content="chatMeta" content="Chat with VisePanda AI to plan your China trip. Get day-by-day itineraries, food guides, and practical travel tips."><style>{CSS}
.layout{{display:flex;height:calc(100vh-56px);position:relative;z-index:1}}
#sidebar{{width:280px;flex-shrink:0;background:rgba(10,8,16,.3);border-right:1px solid var(--line);padding:16px;overflow-y:auto;display:none}}
#sidebar.visible{{display:block}}
#sidebar h3{{font-size:11px;color:var(--gold);text-transform:uppercase;letter-spacing:.08em;margin:0 0 10px}}
.sidebar-info{{font-size:13px;color:var(--muted);margin-bottom:12px;line-height:1.5}}
.sidebar-info strong{{color:var(--text)}}
.sidebar-item{{padding:8px 10px;border:1px solid var(--line);border-radius:8px;margin-bottom:6px;font-size:12px;color:var(--text);cursor:pointer;transition:all .15s}}
.sidebar-item:hover{{border-color:rgba(212,168,75,.3);background:rgba(212,168,75,.04)}}
.sidebar-toggle{{display:none;position:fixed;left:0;top:60px;z-index:3;padding:6px 8px;border:1px solid var(--line);border-left:none;border-radius:0 6px 6px 0;background:rgba(10,8,16,.7);color:var(--text);cursor:pointer;font-size:14px}}
.sidebar-toggle.visible{{display:block}}
#thread{{flex:1;overflow:auto;padding:18px 16px 120px}}
@media(max-width:768px){{#sidebar{{position:fixed;left:0;top:56px;bottom:0;z-index:4;width:260px;transform:translateX(-100%);transition:transform .25s}}#sidebar.visible{{transform:translateX(0)}}.sidebar-toggle{{display:block}}}}
.msg{{display:flex;margin:8px 0}}
.msg.user{{justify-content:flex-end}}
.bubble{{max-width:min(700px,88%);border:1px solid var(--line);border-radius:14px;padding:10px 14px;line-height:1.4;background:rgba(255,255,255,.03);white-space:pre-wrap}}
.msg.user .bubble{{background:rgba(125,211,252,.10);border-color:rgba(125,211,252,.18)}}
.msg.bot .bubble p{{margin:0}}
.chip{{font-size:11px;padding:5px 10px;border-radius:999px;border:1px solid rgba(125,211,252,.2);background:rgba(125,211,252,.06);color:rgba(255,255,255,.8);cursor:pointer;white-space:nowrap;margin:4px 4px 0 0;display:inline-block}}
#quickReplies .chip{{background:rgba(255,255,255,.05);border-color:var(--line);color:var(--muted);padding:8px 14px;border-radius:10px;font-size:12px}}
.light .chat-footer,.light-theme .chat-footer{{background:rgba(255,255,255,.7)!important}}
.chat-footer{{position:fixed;bottom:0;left:0;right:0;padding:12px 16px;padding-bottom:calc(12px + env(safe-area-inset-bottom));border-top:1px solid var(--line);background:rgba(8,10,14,.55);backdrop-filter:blur(10px);z-index:2}}
#msgForm{{display:flex;gap:10px;align-items:center;max-width:800px;margin:0 auto}}
#msgInput{{flex:1;height:44px;padding:0 14px;font-size:14px}}
#sendBtn{{height:44px;padding:0 24px;background:rgba(188,58,44,.14);border:1px solid rgba(188,58,44,.35);border-radius:8px;color:var(--text);cursor:pointer;font-size:14px;font-weight:500;transition:all .2s}}
#sendBtn:hover{{background:rgba(188,58,44,.22);border-color:rgba(188,58,44,.55)}}
#quickReplies{{display:flex;flex-wrap:wrap;gap:4px;padding:6px 0;max-width:800px;margin:0 auto 8px}}
.cursor{{animation:blink 1s step-end infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:0}}}}
.vp-map-container{{display:none;height:320px;border:1px solid var(--line);border-radius:12px;margin:8px 12px;overflow:hidden;z-index:1;position:relative}}
.vp-map-label{{background:none!important;border:none!important;box-shadow:none!important;color:rgba(255,255,255,.7)!important;font-size:11px!important;font-weight:600}}
.leaflet-container{{background:#0a0f17!important}}
.leaflet-control-zoom a{{background:rgba(255,255,255,.05)!important;color:rgba(255,255,255,.8)!important;border-color:var(--line)!important}}
.vp-map-controls{{display:flex;gap:4px;padding:6px 12px;background:rgba(10,8,16,.5);border-bottom:1px solid var(--line)}}
.vp-map-controls button{{background:none;border:1px solid var(--line);border-radius:4px;color:rgba(255,255,255,.7);padding:4px 10px;font-size:11px;cursor:pointer;transition:all .15s}}
.vp-map-controls button:hover{{border-color:rgba(212,168,75,.3);color:var(--gold)}}
.skel-block{{padding:4px 0}}.skel-line{{height:14px;border-radius:7px;margin:8px 0}}.skel-w-10{{width:10%}}.skel-w-20{{width:20%}}.skel-w-30{{width:30%}}.skel-w-40{{width:40%}}.skel-w-50{{width:50%}}.skel-w-60{{width:60%}}.skel-w-70{{width:70%}}.skel-w-80{{width:80%}}
@keyframes shimmer{{0%{{background-position:200%0}}100%{{background-position:-200%0}}}}
.trip-card{{border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:12px;padding:14px 14px 14px 11px;margin:6px 0;background:linear-gradient(135deg,rgba(125,211,252,.06),transparent)}}
.trip-card b{{color:var(--accent)}}
.welcome{{text-align:center;padding:40px 20px;color:var(--muted)}}
.welcome h2{{font-size:20px;color:var(--text);margin:0 0 6px}}
.welcome p{{margin:4px 0;font-size:14px}}
.welcome-chips{{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:20px}}
.welcome-chip{{border:1px solid var(--line);border-radius:999px;padding:8px 16px;font-size:13px;color:var(--text);cursor:pointer;background:rgba(255,255,255,.03);transition:all .15s}}
.welcome-chip:hover{{border-color:rgba(125,211,252,.35);background:rgba(125,211,252,.08)}}
.time{{font-size:10px;color:var(--muted);margin-top:4px}}
</style><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><script defer src='/_vercel/insights/script.js'></script><script defer src='/_vercel/speed-insights/script.js'></script>{_inject_config()}</head><body>
<div class="bg-shanshui"></div>
<header><div><a href="/" class="logo-seal"><span class="seal">熊</span><span class="name">VisePanda</span></a></div><div><a href="/trips" class="btn" style="margin-right:8px" data-i18n="tripsBtn">Trips</a><a href="#" onclick="event.preventDefault();clearChat()" class="btn" style="margin-right:8px" data-i18n="clearBtn">Clear</a><a href="/" class="btn" data-i18n="homeBtn">Home</a><a href="#" class="lang-switch" onclick="event.preventDefault();setLang(LANG==='en'?'zh':'en')" data-i18n="langLabel">中</a><a href="#" onclick="event.preventDefault();toggleTheme()" class="lang-switch" id="themeToggle" title="Toggle theme">🌓</a></div></header>
<div class="layout"><button class="sidebar-toggle" id="sidebarToggle" onclick="toggleSidebar()">☰</button>
<aside id="sidebar">
  <h3>📋 行程概况</h3>
  <div class="sidebar-info" id="tripInfo"><strong>目的地</strong><br><span id="tripCities">—</span></div>
  <div class="sidebar-info"><strong>天数</strong><br><span id="tripDays">—</span></div>
  <h3 style="margin-top:16px">💬 最近消息</h3>
  <div id="sidebarMsgs"></div>
</aside>
<main style="flex:1;display:flex;flex-direction:column"><div id="thread"><div class="welcome" id="welcomeMsg"><h2 data-i18n="welcomeTitle">🐼 Explorer</h2><p style="color:var(--gold-bright);font-size:13px;letter-spacing:.12em;margin:0;font-weight:500" data-i18n="welcomeSub">✦ AI 中国旅行规划 · Tell me where ✦</p><p style="font-size:13px;color:var(--muted);margin:8px 0 0" data-i18n="welcomeSub2">Pick a destination or describe your dream trip</p><div class="welcome-chips"><span class="welcome-chip" onclick="document.getElementById('msgInput').value='北京3天深度游,历史文化';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🏯 北京 3天</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='成都4天美食之旅';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🐼 成都 4天</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='云南7天自然风光';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🏔️ 云南 7天</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='上海3天摩登都市';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🌃 上海 3天</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='西安3天兵马俑历史';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🏛️ 西安 3天</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='桂林漓江阳朔4天';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🛶 桂林 4天</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='杭州西湖3天休闲';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🍵 杭州 3天</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='广州3天早茶美食之旅';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🥟 广州 3天</span></div></div></div><div id="tripMap" class="vp-map-container"></div></main></div>
<div class="chat-footer"><div id="quickReplies"></div><form id="msgForm"><input id="msgInput" type="text" placeholder="告诉我你想去哪，玩几天…" data-i18n-placeholder="inputMsgPlaceholder" autofocus><button id="sendBtn" type="submit" class="btn-red" style="height:44px;padding:0 24px;font-size:14px" data-i18n="sendBtn">Send</button></form></div>
<script src="/static/i18n.js"></script>
<script src="/static/chat.js"></script><script src="/static/pwa.js"></script><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script src="/static/map.js"></script></body></html>"""

def page_phrases() -> str:
    """Language Emergency Cards reference page — screenshot-friendly card layout"""
    from data.knowledge.phrases import get_category_list
    cats = get_category_list()
    cat_buttons = "".join(
        f'<button class="cat-btn" data-cat="{c["id"]}" onclick="showCat(\'{c["id"]}\')">'
        f'{c["icon"]} {c["title_en"]}</button>'
        for c in cats
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Language Emergency Cards 🇨🇳 — VisePanda</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;background:#0d1117;color:#e6edf3;min-height:100vh}}
.header{{background:linear-gradient(135deg,#1a1f2e 0%,#0d1117 100%);padding:32px 20px 24px;text-align:center;border-bottom:1px solid #30363d}}
.header h1{{font-size:28px;font-weight:800;background:linear-gradient(135deg,#f0883e,#e05a2a);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.header p{{color:#8b949e;font-size:14px;margin-top:6px}}
.cat-grid{{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;padding:20px 16px 4px}}
.cat-btn{{padding:10px 18px;border-radius:10px;border:1px solid #30363d;background:#161b22;color:#c9d1d9;font-size:13px;font-weight:500;cursor:pointer;transition:all .2s;font-family:inherit}}
.cat-btn:hover{{border-color:#f0883e;background:#1c2128;color:#f0883e}}
.cat-btn.active{{border-color:#f0883e;background:#2d1f12;color:#f0883e}}
.card-container{{max-width:720px;margin:0 auto;padding:16px 16px 40px}}
.card{{display:none;background:#161b22;border-radius:16px;border:1px solid #30363d;overflow:hidden;margin-bottom:16px}}
.card.active{{display:block}}
.card-header{{padding:18px 20px 14px;border-bottom:1px solid #21262d}}
.card-header h2{{font-size:20px;font-weight:700}}
.card-header .sub{{color:#8b949e;font-size:12px;margin-top:2px}}
.phrase{{display:flex;align-items:flex-start;padding:14px 20px;border-bottom:1px solid #21262d;gap:12px}}
.phrase:last-child{{border-bottom:none}}
.phrase-num{{width:28px;height:28px;border-radius:50%;background:#1e2a3a;color:#f0883e;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
.phrase-content{{flex:1;min-width:0}}
.phrase-cn{{font-size:18px;font-weight:600;color:#e6edf3;line-height:1.4}}
.phrase-pinyin{{font-size:13px;color:#8b949e;font-style:italic;margin-top:1px}}
.phrase-en{{font-size:14px;color:#c9d1d9;margin-top:4px}}
.tip{{text-align:center;padding-top:16px;color:#8b949e;font-size:13px}}
.tip a{{color:#58a6ff;text-decoration:none}}
@media(max-width:480px){{.header{{padding:24px 16px 18px}}.header h1{{font-size:24px}}.phrase{{padding:12px 16px}}.phrase-cn{{font-size:16px}}}}
</style></head><body>
<div class=header>
<h1>🇨🇳 Language Emergency Cards</h1>
<p>Chinese travel phrases — tap a category to view cards · Screenshot to save</p>
</div>
<div class=cat-grid>{cat_buttons}</div>
<div class=card-container id=container></div>
<div class=tip>💡 Screenshot a card to save it on your phone · <a href=/>← Back to VisePanda</a></div>
<script>
const DATA={{}};let cur=null;
async function showCat(cat){{
document.querySelectorAll('.cat-btn').forEach(b=>b.classList.toggle('active',b.dataset.cat===cat));
if(DATA[cat]){{render(DATA[cat],cat);return}}
const r=await fetch('/api/phrases/'+cat);const d=await r.json();DATA[cat]=d;render(d,cat)
}}
function render(d,cat){{
const c=document.getElementById('container');c.innerHTML='<div class=card active>'
+'<div class=card-header><h2>'+d.icon+' '+d.title_en+'<span style=color:#8b949e;font-weight:400;margin-left:8px;font-size:14px>'+d.title_zh+'</span>'
+'</h2><div class=sub>'+d.phrases.length+' essential phrases · 截图保存</div></div>';
d.phrases.forEach((p,i)=>{{
c.innerHTML+='<div class=phrase><div class=phrase-num>'+(i+1)+'</div><div class=phrase-content>'
+'<div class=phrase-cn>'+p[0]+'</div><div class=phrase-pinyin>'+p[1]+'</div><div class=phrase-en>'+p[2]+'</div></div></div>'
}});
c.innerHTML+='</div>'
}}
showCat('taxi')
</script></body></html>"""


def page_auth_callback() -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#bc3a2c">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&family=Noto+Serif+SC:wght@600;700&display=swap" rel="stylesheet">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="VisePanda">
<link rel="apple-touch-icon" href="/static/icon.svg"><title data-i18n="signingIn">Signing in…</title><style>body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0a0f17;color:#fff;font-family:sans-serif;text-align:center}}.muted{{color:rgba(255,255,255,.5);font-size:14px}}</style><script defer src='/_vercel/insights/script.js'></script><script defer src='/_vercel/speed-insights/script.js'></script>{_inject_config()}</head><body>
<div><div style="font-size:18px;font-weight:650;margin-bottom:8px" data-i18n="signingIn">Signing in…</div><div class="muted" data-i18n="redirecting">Redirecting…</div></div>
<script src="https://esm.sh/@supabase/supabase-js@2"></script>
<script src="/static/i18n.js"></script>
<script src="/static/auth.js"></script><script src="/static/pwa.js"></script></body></html>"""

def page_profile(user_id: str) -> str:
    db = get_db()
    user = db.query(EmailUser).filter(EmailUser.user_id == user_id).one_or_none()
    if not user:
        pu = db.query(PhoneUser).filter(PhoneUser.user_id == user_id).one_or_none()
        email_display = "—"
        phone_display = pu.phone if pu else "—"
        name = pu.name if (pu and pu.name) else ""
    else:
        email_display = user.email
        phone_display = "—"
        name = user.name or ""
    db.close()
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#bc3a2c">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&family=Noto+Serif+SC:wght@600;700&display=swap" rel="stylesheet">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="VisePanda">
<link rel="apple-touch-icon" href="/static/icon.svg"><title data-i18n="profileTitle">Profile · VisePanda</title><meta name="description" content="Manage your VisePanda profile and preferences."><style>{CSS}</style><script defer src='/_vercel/insights/script.js'></script><script defer src='/_vercel/speed-insights/script.js'></script>{_inject_config()}</head><body>
<div class="bg-shanshui"></div>
<header><div><a href="/" class="logo-seal"><span class="seal">熊</span><span class="name">VisePanda</span></a></div><div><a href="/chat" class="btn" style="margin-right:8px" data-i18n="chatBtn">Chat</a><a href="/trips" class="btn" style="margin-right:8px" data-i18n="tripsBtn">Trips</a><a href="/" class="btn" data-i18n="homeBtn">Home</a><a href="#" class="lang-switch" onclick="event.preventDefault();setLang(LANG==='en'?'zh':'en')" data-i18n="langLabel">中</a><a href="#" onclick="event.preventDefault();toggleTheme()" class="lang-switch" id="themeToggle" title="Toggle theme">🌓</a></div></header>
<div class="profile-page">
<div class="profile-header"><div class="profile-avatar">🐼</div><h1 data-i18n="profileH1">My Profile</h1><p data-i18n="profileSub">Manage your account and preferences</p></div>
<div id="profileMsg" class="profile-msg"></div>
<div class="profile-card">
<h3 data-i18n="generalSection">General</h3>
<div class="profile-field"><label data-i18n="nameLabel">Display Name</label><input id="profileName" type="text" placeholder="Your name" value="{name}" data-i18n-placeholder="namePlaceholder"></div>
<div class="profile-field"><label data-i18n="emailLabel">Email</label><input id="profileEmail" type="email" value="{email_display}" readonly style="opacity:.6;cursor:not-allowed"></div>
<div class="profile-field"><label data-i18n="phoneLabel">Phone</label><input id="profilePhone" type="text" value="{phone_display}" readonly style="opacity:.6;cursor:not-allowed"></div>
<div class="profile-field"><label data-i18n="langLabelPref">Language</label><select id="langSelect"><option value="en">English</option><option value="zh">中文</option></select></div>
</div>
<div class="profile-card">
<h3 data-i18n="passwordSection">Change Password</h3>
<div class="profile-field"><label data-i18n="oldPwLabel">Current Password</label><input id="oldPassword" type="password" data-i18n-placeholder="oldPwPlaceholder" placeholder="Current password"></div>
<div class="profile-field"><label data-i18n="newPwLabel">New Password</label><input id="newPassword" type="password" data-i18n-placeholder="newPwPlaceholder" placeholder="New password (min 6 chars)"></div>
<div class="profile-field"><label data-i18n="confirmPwLabel">Confirm New Password</label><input id="confirmPassword" type="password" data-i18n-placeholder="confirmPwPlaceholder" placeholder="Confirm new password"></div>
</div>
<button id="saveBtn" class="profile-save-btn" data-i18n="saveBtn">Save Changes</button>
<div class="profile-nav"><a href="/chat" data-i18n="chatBtn">Chat</a> · <a href="/trips" data-i18n="tripsBtn">My Trips</a> · <a href="/" data-i18n="homeBtn">Home</a> · <a href="#" id="logoutBtn" style="color:#f87171" data-i18n="logoutBtn">Logout</a></div>
</div>
<script src="/static/i18n.js"></script>
<script src="/static/profile.js"></script><script src="/static/pwa.js"></script></body></html>"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables managed via Supabase Management API
    yield

app = FastAPI(title="VisePanda", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/api/health")
def health():
    return {"ok": True, "version": "0.1.0", "db": "postgres"}

@app.get("/favicon.ico")
@app.get("/favicon.png")
def favicon():
    return Response(status_code=204)


@app.get("/", response_class=HTMLResponse)
def landing():
    return page_landing()


@app.get("/share/{share_id}", response_class=HTMLResponse)
def share_view(share_id: str):
    return page_share(share_id)


@app.get("/api/trips/{trip_id}/card")
@app.post("/api/favorites/toggle")
def toggle_favorite(body: dict):
    user_id = body.get("user_id")
    trip_id = body.get("trip_id")
    if not user_id or not trip_id:
        raise HTTPException(400, "user_id and trip_id required")
    db = get_db()
    try:
        existing = db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.trip_id == trip_id).one_or_none()
        if existing:
            db.delete(existing)
            db.commit()
            return {"favorited": False}
        db.add(Favorite(user_id=user_id, trip_id=trip_id))
        db.commit()
        return {"favorited": True}
    finally:
        db.close()

@app.get("/api/favorites/{user_id}")
def get_favorites(user_id: str):
    db = get_db()
    try:
        favs = db.query(Favorite).filter(Favorite.user_id == user_id).all()
        return [f.trip_id for f in favs]
    finally:
        db.close()

def trip_card_image(trip_id: str):
    """Generate an SVG card image for trip sharing (used as og:image)."""
    db = get_db()
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).one_or_none()
        if not trip:
            return Response(status_code=404)
        itin = trip.current_itinerary or {}
        title = trip.title or "China Trip"
        cities = ', '.join(itin.get('cities', [])) or "Explore China"
        days = itin.get('day_count', 0)
        budget = {'budget': 'Budget', 'mid': 'Mid-range', 'luxury': 'Luxury'}.get(itin.get('budget_tier', ''), '')
        hotels = itin.get('hotels', [])
        hotels_str = ' · '.join(hotels[:3]) if hotels else ''
        
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0a0f17"/>
      <stop offset="50%" style="stop-color:#121826"/>
      <stop offset="100%" style="stop-color:#05070b"/>
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#7dd3fc"/>
      <stop offset="100%" style="stop-color:#38bdf8"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <circle cx="100" cy="500" r="300" fill="rgba(125,211,252,.03)"/>
  <circle cx="1100" cy="100" r="200" fill="rgba(125,211,252,.02)"/>
  <text x="80" y="120" font-family="system-ui,sans-serif" font-size="48" font-weight="700" fill="white">🐼 {self.escape(title) if hasattr(self, 'escape') else title}</text>
  <text x="80" y="180" font-family="system-ui,sans-serif" font-size="24" fill="rgba(255,255,255,.6)">{self.escape(cities) if hasattr(self, 'escape') else cities}</text>
  <rect x="80" y="220" width="1040" height="1" fill="rgba(255,255,255,.08)"/>
  <text x="80" y="290" font-family="system-ui,sans-serif" font-size="72" font-weight="700" fill="url(#accent)">{days}</text>
  <text x="180" y="290" font-family="system-ui,sans-serif" font-size="24" fill="rgba(255,255,255,.5)" dy="-8">days itinerary</text>
  <text x="80" y="400" font-family="system-ui,sans-serif" font-size="20" fill="rgba(255,255,255,.5)">{f'Hotels: {hotels_str}' if hotels_str else ''}</text>
  <text x="80" y="450" font-family="system-ui,sans-serif" font-size="20" fill="rgba(255,255,255,.5)">{f'Budget: {budget}' if budget else ''}</text>
  <text x="80" y="560" font-family="system-ui,sans-serif" font-size="16" fill="rgba(255,255,255,.3)">go2china.space · AI-planned trip by VisePanda</text>
  <circle cx="1130" cy="570" r="20" fill="rgba(125,211,252,.15)"/>
  <text x="1120" y="577" font-family="system-ui,sans-serif" font-size="20" text-anchor="middle" fill="rgba(255,255,255,.5)">🐼</text>
</svg>'''
        return Response(content=svg, media_type="image/svg+xml")
    finally:
        db.close()

@app.get("/trips", response_class=HTMLResponse)
def trips_page():
    return page_trips()

@app.get("/chat", response_class=HTMLResponse)
def chat_page():
    return page_chat()


@app.get("/phrases", response_class=HTMLResponse)
def phrases_page():
    return page_phrases()

@app.get("/api/phrases/{cat}", response_class=JSONResponse)
def api_phrases(cat: str):
    try:
        from data.knowledge.phrases import get_category
        data = get_category(cat)
        if not data:
            raise HTTPException(404, f"Category '{cat}' not found")
        return data
    except ImportError:
        return JSONResponse({"error": "Phrases module not loaded"}, status_code=500)

@app.get("/api/phrases", response_class=JSONResponse)
def api_phrases_list():
    try:
        from data.knowledge.phrases import get_category_list
        return {"categories": get_category_list()}
    except ImportError:
        return JSONResponse({"error": "Phrases module not loaded"}, status_code=500)

@app.get("/auth/callback", response_class=HTMLResponse)
def auth_callback():
    return page_auth_callback()

@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    try:
        user_id, _ = _get_user_id(request, request.query_params.get("guest_id"))
        if not user_id or user_id.startswith("guest:"):
            return HTMLResponse(status_code=302, headers={"Location": "/?login=1"})
        return page_profile(user_id)
    except HTTPException:
        return HTMLResponse(status_code=302, headers={"Location": "/?login=1"})


class EmailSignupIn(BaseModel):
    email: str
    password: str
    name: str | None = None

class EmailLoginIn(BaseModel):
    email: str
    password: str

@app.post("/api/auth/email-signup")
def email_signup(body: EmailSignupIn):
    email = body.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, "Invalid email")
    if len(body.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    db = get_db()
    try:
        existing = db.query(EmailUser).filter(EmailUser.email == email).one_or_none()
        if existing:
            raise HTTPException(409, "Email already registered")
        user_id = _uid()
        eu = EmailUser(email=email, user_id=user_id, password_hash=_hash_password(body.password), name=body.name)
        db.add(eu)
        # Also create entry in users table
        db.add(User(id=f"email:{user_id}", profile={"email": email, "name": body.name or ""}))
        db.commit()
        return {"token": f"email:{user_id}", "user_id": f"email:{user_id}", "email": email}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()

@app.post("/api/auth/email-login")
def email_login(body: EmailLoginIn):
    email = body.email.strip().lower()
    if not email:
        raise HTTPException(400, "Invalid email")
    db = get_db()
    try:
        eu = db.query(EmailUser).filter(EmailUser.email == email).one_or_none()
        if not eu or not _verify_password(body.password, eu.password_hash):
            raise HTTPException(401, "Invalid email or password")
        return {"token": f"email:{eu.user_id}", "user_id": f"email:{eu.user_id}", "email": email, "name": eu.name or ""}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        db.close()

class PhoneSendCodeIn(BaseModel):
    phone: str

class PhoneLoginIn(BaseModel):
    phone: str
    code: str

@app.post("/api/auth/send-code")
def send_code(body: PhoneSendCodeIn):
    phone = body.phone.strip()
    if not phone:
        raise HTTPException(400, "Invalid phone number")
    # Generate 6-digit code
    code = str(random.randint(100000, 999999))
    expires_at = _now() + dt.timedelta(minutes=5)
    db = get_db()
    try:
        # Upsert verification record
        existing = db.query(PhoneVerification).filter(PhoneVerification.phone == phone).one_or_none()
        if existing:
            existing.code = code
            existing.expires_at = expires_at
            existing.verified = False
        else:
            db.add(PhoneVerification(phone=phone, code=code, expires_at=expires_at, verified=False))
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()
    # Send SMS (best-effort)
    ok = _send_sms(phone, code)
    return {"ok": ok, "message": "Code sent" if ok else "Failed to send SMS — check SMS provider config"}

@app.post("/api/auth/phone-login")
def phone_login(body: PhoneLoginIn):
    phone = body.phone.strip()
    code = body.code.strip()
    if not phone or not code:
        raise HTTPException(400, "Invalid phone or code")
    # Verify code
    pu_user_id = None
    db = get_db()
    try:
        record = db.query(PhoneVerification).filter(
            PhoneVerification.phone == phone,
            PhoneVerification.verified == False
        ).one_or_none()
        if not record:
            raise HTTPException(401, "No verification code found. Request a new code.")
        if record.expires_at.replace(tzinfo=dt.timezone.utc) < _now():
            db.delete(record)
            db.commit()
            raise HTTPException(401, "Code expired. Request a new code.")
        if record.code != code:
            raise HTTPException(401, "Invalid code")
        # Mark as verified so it can't be reused
        record.verified = True
        db.commit()
        # Check/create phone user
        pu = db.query(PhoneUser).filter(PhoneUser.phone == phone).one_or_none()
        if not pu:
            pu = PhoneUser(phone=phone, user_id=_uid())
            db.add(pu)
            db.add(User(id=f"phone:{pu.user_id}", profile={"phone": phone}))
            db.commit()
        pu_user_id = pu.user_id
    finally:
        db.close()
    if not pu_user_id:
        raise HTTPException(500, "Failed to create user")
    return {"token": f"phone:{pu_user_id}", "user_id": f"phone:{pu_user_id}", "phone": phone}


class ProfileUpdateIn(BaseModel):
    name: str | None = None

class PasswordChangeIn(BaseModel):
    old_password: str
    new_password: str

class ProfileOut(BaseModel):
    user_id: str
    email: str | None = None
    phone: str | None = None
    name: str | None = None

@app.get("/api/profile")
def get_profile(request: Request):
    user_id, _ = _get_user_id(request, request.query_params.get("guest_id"))
    if not user_id or user_id.startswith("guest:"):
        raise HTTPException(401, "Not logged in")
    db = get_db()
    try:
        # Try email user first, then phone user
        user = db.query(EmailUser).filter(EmailUser.user_id == user_id).one_or_none()
        if user:
            return ProfileOut(user_id=user_id, email=user.email, phone=None, name=user.name or "")
        pu = db.query(PhoneUser).filter(PhoneUser.user_id == user_id).one_or_none()
        if pu:
            return ProfileOut(user_id=user_id, email=None, phone=pu.phone, name=pu.name or "")
        raise HTTPException(404, "User not found")
    finally:
        db.close()

@app.put("/api/profile")
def update_profile(body: ProfileUpdateIn, request: Request):
    user_id, _ = _get_user_id(request, request.query_params.get("guest_id"))
    if not user_id or user_id.startswith("guest:"):
        raise HTTPException(401, "Not logged in")
    if body.name is None:
        return {"ok": True}
    db = get_db()
    try:
        user = db.query(EmailUser).filter(EmailUser.user_id == user_id).one_or_none()
        if user:
            db.query(EmailUser).filter(EmailUser.user_id == user_id).delete()
            db.commit()
            db.add(EmailUser(email=user.email, user_id=user_id, password_hash=user.password_hash, name=body.name))
            db.commit()
            return {"ok": True}
        pu = db.query(PhoneUser).filter(PhoneUser.user_id == user_id).one_or_none()
        if pu:
            db.query(PhoneUser).filter(PhoneUser.user_id == user_id).delete()
            db.commit()
            db.add(PhoneUser(phone=pu.phone, user_id=user_id, name=body.name))
            db.commit()
            return {"ok": True}
        raise HTTPException(404, "User not found")
    finally:
        db.close()

@app.post("/api/auth/change-password")
def change_password(body: PasswordChangeIn, request: Request):
    user_id, _ = _get_user_id(request, request.query_params.get("guest_id"))
    if not user_id or user_id.startswith("guest:"):
        raise HTTPException(401, "Not logged in")
    if len(body.new_password) < 6:
        raise HTTPException(400, "New password must be at least 6 characters")
    db = get_db()
    try:
        user = db.query(EmailUser).filter(EmailUser.user_id == user_id).one_or_none()
        if not user:
            raise HTTPException(401, "Only email users can change password")
        if not _verify_password(body.old_password, user.password_hash):
            raise HTTPException(401, "Current password is incorrect")
        db.query(EmailUser).filter(EmailUser.user_id == user_id).delete()
        db.commit()
        db.add(EmailUser(email=user.email, user_id=user_id, password_hash=_hash_password(body.new_password), name=user.name))
        db.commit()
        return {"ok": True, "message": "Password updated"}
    finally:
        db.close()

@app.get("/api/locale")
def get_locale(request: Request):
    """Detect user locale via IP geolocation. Returns {'locale': 'zh'} for China IPs."""
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host if request.client else ""
    if not ip or ip == "127.0.0.1" or ip.startswith("10.") or ip.startswith("192.168."):
        return {"locale": None}
    try:
        r = httpx.get(f"http://ip-api.com/json/{ip}?fields=countryCode", timeout=3)
        data = r.json()
        if data.get("countryCode") == "CN":
            return {"locale": "zh"}
    except Exception:
        pass
    return {"locale": None}

def _parse_itinerary(text: str) -> dict | None:
    """Detect structured itinerary in LLM response and extract structured data."""
    import re as _re
    
    # Detect day-by-day format
    day_pattern = _re.findall(r'\*\*Day\s+(\d+)\s*[—–-]\s*(.+?)\*\*', text)
    if not day_pattern:
        return None
    
    days = []
    for num, title in day_pattern:
        days.append({"day": int(num), "title": title.strip()})
    
    # Detect cities mentioned
    cn_cities = ["北京", "上海", "广州", "深圳", "成都", "重庆", "杭州", "西安",
                 "桂林", "昆明", "大理", "丽江", "厦门", "三亚", "长沙", "武汉",
                 "南京", "苏州", "青岛", "大连", "哈尔滨", "拉萨", "敦煌", "张家界",
                 "贵阳", "兰州", "西宁", "乌鲁木齐", "呼和浩特"]
    cities = [c for c in cn_cities if c in text]
    
    # Detect budget tier
    budget = "mid"
    if "经济档" in text or "Budget" in text: budget = "budget"
    if "豪华档" in text or "Luxury" in text: budget = "luxury"
    
    # Detect named hotels
    hotel_pattern = _re.findall(r'(?:🏨|Stay|住)[：:]\s*(.+?)(?:[—–—-]|\n|$)', text)
    hotels = [h.strip() for h in hotel_pattern if h.strip()]
    
    # Detect named restaurants
    restaurant_pattern = _re.findall(r'(?:🍜|Eat|吃)[：:]\s*(.+?)(?:[—–—-]|\n|$)', text)
    restaurants = [r.strip() for r in restaurant_pattern if r.strip()]
    
    return {
        "cities": cities[:5],
        "days": days,
        "day_count": len(days),
        "budget_tier": budget,
        "hotels": hotels[:10],
        "restaurants": restaurants[:10],
        "raw_preview": text[:500],
    }


class ChatIn(BaseModel):
    trip_id: str
    text: str
    guest_id: str | None = None


@app.post("/api/chat")
async def chat_endpoint(payload: ChatIn, request: Request):
    # Rate limit check
    ip = request.headers.get("x-forwarded-for", "unknown").split(",")[0].strip()
    now = time.time()
    _RATE_LIMIT.setdefault(ip, [])
    _RATE_LIMIT[ip] = [t for t in _RATE_LIMIT[ip] if now - t < _RATE_WINDOW]
    if len(_RATE_LIMIT[ip]) >= _RATE_MAX:
        raise HTTPException(429, "Too many requests. Please wait.")
    _RATE_LIMIT[ip].append(now)


    """SSE streaming chat with LLM."""
    user_id, mode = _get_user_id(request, payload.guest_id)

    # Save user if new
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).one_or_none()
        if not user:
            user = User(id=user_id)
            db.add(user)
            db.flush()

        trip = db.query(Trip).filter(Trip.id == payload.trip_id).one_or_none()
        if not trip:
            trip = Trip(id=payload.trip_id, user_id=user_id, title=payload.text[:80])
            db.add(trip)
            db.flush()

        db.add(ChatMessage(user_id=user_id, trip_id=trip.id, role="user", content=payload.text))
        db.commit()
    finally:
        db.close()

    # Load conversation history for context
    db_ctx = get_db()
    try:
        recent = db_ctx.query(ChatMessage).filter(
            ChatMessage.trip_id == payload.trip_id
        ).order_by(ChatMessage.created_at.desc()).limit(20).all()[::-1]
        context_msgs = [{"role": m.role, "content": m.content} for m in recent]
        # Context compression: if more than 8 messages, summarize older ones
        if len(context_msgs) > 8:
            keep = context_msgs[-6:]  # Keep last 6 messages verbatim
            older = context_msgs[:-6]
            summary_text = " | ".join(m["content"][:80] for m in older if m["role"] == "user")
            if summary_text:
                summary_msg = {"role": "system", "content": f"[历史摘要] 用户之前提到: {summary_text}..."}
                context_msgs = [summary_msg] + keep
    finally:
        db_ctx.close()

    # Build system prompt with context
    user_ctx = {}
    if payload.trip_id:
        db_trip = get_db()
        try:
            t = db_trip.query(Trip).filter(Trip.id == payload.trip_id).one_or_none()
            if t and t.current_itinerary:
                user_ctx['current_trip'] = t.current_itinerary
        finally:
            db_trip.close()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *context_msgs,
    ]

    async def generate():
        full_text = ""
        event_id = 0
        async for chunk in stream_llm(messages):
            if "token" in chunk:
                try:
                    token = json.loads(chunk.split("data: ")[1].strip())["token"]
                    full_text += token
                    event_id += 1
                    yield f"id: {event_id}\n{chunk}"
                except:
                    yield chunk
            else:
                yield chunk

        # Save assistant message + track preferences
        if full_text:
            # Simple preference extraction from user messages
            user_prefs = db2.query(UserPreference).filter(UserPreference.user_id == user_id).one_or_none()
            if not user_prefs:
                user_prefs = UserPreference(user_id=user_id, preferences={})
                db2.add(user_prefs)
            # Extract budget/style from context
            pref = user_prefs.preferences or {}
            for msg in context_msgs[-3:]:
                if msg["role"] == "user":
                    txt = msg["content"]
                    if "穷游" in txt or "省钱" in txt or "经济" in txt: pref["budget"] = "budget"
                    elif "豪华" in txt or "五星" in txt: pref["budget"] = "luxury"
                    else: pref["budget"] = "mid"
                    if "美食" in txt: pref["style"] = "food"
                    elif "历史" in txt: pref["style"] = "history"
                    elif "自然" in txt: pref["style"] = "nature"
            user_prefs.preferences = pref
            db2.commit()
            db2 = get_db()
            try:
                db2.add(ChatMessage(user_id=user_id, trip_id=payload.trip_id, role="assistant", content=full_text))
                db2.commit()

                # Auto-detect structured itinerary and save to trip
                trip2 = db2.query(Trip).filter(Trip.id == payload.trip_id).one_or_none()
                if trip2 and not trip2.current_itinerary:
                    parsed = _parse_itinerary(full_text)
                    if parsed:
                        trip2.current_itinerary = parsed
                        db2.commit()
                        yield f"data: {json.dumps({'trip_update': True, 'cities': parsed.get('cities', []), 'days': len(parsed.get('days', []))})}\n\n"
            finally:
                db2.close()

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.exception_handler(404)
async def not_found(request, exc):
    path = request.url.path
    if path.startswith("/api/"):
        return JSONResponse({"error": "not found"}, status_code=404)
    return HTMLResponse('<html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><link rel="manifest" href="/static/manifest.json"><meta name="theme-color" content="#bc3a2c"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"><meta name="apple-mobile-web-app-title" content="VisePanda"><link rel="apple-touch-icon" href="/static/icon.svg"><title data-i18n="notFoundTitle">404 — VisePanda</title><style>body{display:flex;align-items:center;justify-content:center;min-height:100vh;background:#0a0f17;color:#fff;font-family:sans-serif;text-align:center;margin:0}h1{font-size:48px;margin:0;letter-spacing:-.02em}p{color:rgba(255,255,255,.5)}a{color:#7dd3fc}</style><h1>🐼</h1><p data-i18n="notFound">Page not found</p><a href=/>Back home</a><script src="/static/i18n.js"></script><script src="/static/pwa.js"></script>', status_code=404)


@app.get("/api/trips")
def list_trips(request: Request, guest_id: str | None = None):
    """List trips for current user."""
    from fastapi import Query
    db = get_db()
    try:
        user_id = None
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            # test: tokens are dev bypass
            if token.startswith("test:"):
                if AUTH_TEST_BYPASS:
                    user_id = token.split(":", 1)[1] or "test_user"
            # email: and phone: tokens are real user auth
            elif token.startswith("email:") or token.startswith("phone:"):
                user_id = token.split(":", 1)[1]
            else:
                try:
                    header = jwt.get_unverified_header(token)
                    kid = header.get("kid")
                    if kid:
                        keys = _get_jwks()
                        key = next((k for k in keys if k.get("kid") == kid), None)
                        if key:
                            claims = jwt.decode(token, key, algorithms=["RS256"], audience="authenticated")
                            user_id = claims.get("sub")
                except:
                    pass
        if not user_id and guest_id:
            user_id = f"guest:{guest_id}"
        if not user_id:
            user_id = "unknown"
        trips = db.query(Trip).filter(Trip.user_id == user_id).order_by(Trip.updated_at.desc()).limit(20).all()
        msgs_count = {}
        for t in trips:
            cnt = db.query(ChatMessage).filter(ChatMessage.trip_id == t.id).count()
            msgs_count[t.id] = cnt
        return [{"id": t.id, "title": t.title or "Untitled Trip", "cities": t.cities or [], "start_date": t.start_date, "updated_at": t.updated_at.isoformat() if t.updated_at else None, "msg_count": msgs_count.get(t.id, 0)} for t in trips]
    finally:
        db.close()


class RenameIn(BaseModel):
    title: str


@app.get("/api/trips/{trip_id}")
def get_trip_detail(trip_id: str):
    """Return trip detail including structured itinerary."""
    db = get_db()
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).one_or_none()
        if not trip:
            raise HTTPException(404, "Trip not found")
        return {
            "id": trip.id,
            "title": trip.title or "Untitled Trip",
            "cities": trip.cities or [],
            "current_itinerary": trip.current_itinerary,
            "start_date": trip.start_date,
            "end_date": trip.end_date,
            "updated_at": trip.updated_at.isoformat() if trip.updated_at else None,
        }
    finally:
        db.close()


@app.put("/api/trips/{trip_id}")
def rename_trip(trip_id: str, body: RenameIn):
    db = get_db()
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).one_or_none()
        if not trip:
            raise HTTPException(404, "Trip not found")
        trip.title = body.title[:100]
        trip.updated_at = _now()
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@app.post("/api/trips/{trip_id}/share")
def share_trip(trip_id: str):
    db = get_db()
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).one_or_none()
        if not trip:
            raise HTTPException(404, "Trip not found")
        if not trip.share_id:
            trip.share_id = "%s" % (''.join(__import__('random').choices(__import__('string').ascii_lowercase + __import__('string').digits, k=8)))
            trip.updated_at = _now()
            db.commit()
        return {"share_id": trip.share_id, "url": f"/share/{trip.share_id}"}
    finally:
        db.close()


@app.get("/api/trips/{trip_id}/share")
def get_share_link(trip_id: str):
    db = get_db()
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).one_or_none()
        if not trip:
            raise HTTPException(404, "Trip not found")
        return {"share_id": trip.share_id, "url": f"/share/{trip.share_id}" if trip.share_id else None}
    finally:
        db.close()


@app.delete("/api/trips/{trip_id}")
def delete_trip(trip_id: str):
    db = get_db()
    try:
        db.query(ChatMessage).filter(ChatMessage.trip_id == trip_id).delete()
        db.query(Trip).filter(Trip.id == trip_id).delete()
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@app.get("/api/trips/{trip_id}/messages")
def get_messages(trip_id: str):
    """Return chat history for a trip."""
    db = get_db()
    try:
        msgs = db.query(ChatMessage).filter(
            ChatMessage.trip_id == trip_id
        ).order_by(ChatMessage.created_at.asc()).limit(50).all()
        return [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in msgs]
    finally:
        db.close()


# ── Weather API (wttr.in) ──
@app.get("/api/weather/{city}")
def weather_route(city: str):
    """GET /api/weather/Beijing → 3-day forecast via wttr.in"""
    try:
        import httpx, time
        _cache = {}
        key = city.lower().strip()
        with httpx.Client(timeout=8) as c:
            r = c.get(f"https://wttr.in/{key}?format=j1")
            if r.status_code != 200:
                return JSONResponse({"error": "Weather unavailable"}, status_code=503)
            d = r.json()
            cur = d.get("current_condition", [{}])[0]
            fc = d.get("weather", [])[:3]
            return JSONResponse({
                "city": city, "temp_c": cur.get("temp_C","?"),
                "description": cur.get("weatherDesc",[{}])[0].get("value",""),
                "forecast": [{"date":day.get("date",""),"max":day.get("maxtempC","?"),"min":day.get("mintempC","?")} for day in fc]
            })
    except Exception as e:
        return JSONResponse({"error": f"Weather failed: {repr(e)}"}, status_code=500)


# ── Calendar export (.ics) ──
@app.post("/api/calendar/export")
async def calendar_export(request: Request):
    """POST trip itinerary JSON → .ics file download"""
    try:
        from ics_export import generate_ics
        body = await request.json()
        ics = generate_ics(body)
        return Response(
            content=ics,
            media_type="text/calendar",
            headers={"Content-Disposition": "attachment; filename=trip.ics"}
        )
    except Exception as e:
        print(f"Calendar error: {e}")
        return JSONResponse({"error": "Calendar generation failed"}, status_code=500)


# ── Currency converter ──
@app.get("/api/fx/{amount}/{from_curr}/{to_curr}")
def fx_route(amount: float, from_curr: str, to_curr: str = "CNY"):
    """GET /api/fx/100/USD/CNY → converted amount (inline, no import)"""
    try:
        _RATES = {"USD":1.0,"CNY":7.24,"EUR":0.92,"GBP":0.79,"JPY":151.5,"KRW":1350,"THB":36.5,"SGD":1.35,"HKD":7.82,"TWD":32.5,"AUD":1.53,"CAD":1.38,"MYR":4.72,"VND":25450,"INR":83.5,"RUB":92.0}
        f, t = from_curr.upper(), to_curr.upper()
        if f == t:
            return JSONResponse({"amount": amount, "from": f, "to": t, "result": amount, "rate": 1.0})
        if f in _RATES and t in _RATES:
            rate = _RATES[t] / _RATES[f]
            return JSONResponse({"amount": amount, "from": f, "to": t, "result": round(amount * rate, 2), "rate": rate})
        return JSONResponse({"error": f"Unknown currency: {f} or {t}"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"FX failed: {repr(e)}"}, status_code=500)


# ── Itinerary validation ──
@app.post("/api/itinerary/validate")
async def validate_route(request: Request):
    """POST itinerary JSON → list of warnings (inline validation)"""
    try:
        body = await request.json()
        warnings = []
        days = body.get("itinerary", body.get("days", []))
        for day in days:
            dn = day.get("day", 0)
            acts = day.get("activities", day.get("items", []))
            if len(acts) > 8:
                warnings.append(f"Day {dn}: 安排了 {len(acts)} 项活动，可能太紧凑")
            elif len(acts) == 0:
                warnings.append(f"Day {dn}: 没有安排任何活动")
            for a in acts:
                t, n = a.get("time", ""), a.get("name", "")
                if "餐" in t or "饭" in t:
                    if any(h in t for h in ["22:", "23:", "00:", "01:", "02:"]):
                        warnings.append(f"Day {dn}: '{n}' 安排在深夜 {t}")
                if "出发" in t or "起" in t:
                    try:
                        if int(t.split(":")[0]) < 5:
                            warnings.append(f"Day {dn}: '{n}' 出发时间 {t} 过早")
                    except: pass
        return JSONResponse({"warnings": warnings, "safe": len(warnings) == 0})
    except Exception as e:
        return JSONResponse({"warnings": [f"Failed: {repr(e)}"], "safe": False}, status_code=500)


# ── Geocode API (Nominatim proxy with cache) ──

_GEOCODE_CACHE: dict[str, list[float]] = {}
_GEOCODE_LAST_CALL = 0.0

class GeocodeIn(BaseModel):
    places: list[str]

@app.post("/api/geocode")
def geocode(body: GeocodeIn):
    """Convert place names to coordinates via Nominatim with caching."""
    import time as _time
    import urllib.request as _req
    import urllib.parse as _parse
    global _GEOCODE_LAST_CALL
    
    results = {}
    for place in body.places:
        place_stripped = place.strip()
        if not place_stripped:
            continue
        
        # Check cache
        if place_stripped in _GEOCODE_CACHE:
            results[place] = _GEOCODE_CACHE[place_stripped]
            continue
        
        # Rate limit: 1 request per 1.2s
        elapsed = _time.time() - _GEOCODE_LAST_CALL
        if elapsed < 1.2:
            _time.sleep(1.2 - elapsed)
        
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={_parse.quote(place_stripped)}&format=json&limit=1"
            req = _req.Request(url, headers={"User-Agent": "VisePanda/1.0 (travel app)"})
            with _req.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                _GEOCODE_LAST_CALL = _time.time()
                if data:
                    coords = [float(data[0]["lat"]), float(data[0]["lon"])]
                    _GEOCODE_CACHE[place_stripped] = coords
                    results[place] = coords
                else:
                    results[place] = None
        except Exception:
            results[place] = None
    
    return results

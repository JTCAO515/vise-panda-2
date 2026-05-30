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
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

# ══════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "glm-5.1")
LLM_ENABLED = os.getenv("LLM_ENABLED", "1") == "1"
AUTH_TEST_BYPASS = os.getenv("AUTH_TEST_BYPASS", "0") == "1"
IS_DEV = os.getenv("IS_DEV", "0") == "1"

# Rate limiting
_RATE_LIMIT: dict[str, list[float]] = {}
_RATE_WINDOW = 60  # seconds
_RATE_MAX = 20  # requests per window

DB_URL = os.getenv("DATABASE_URL")
if DB_URL:
    engine = create_engine(DB_URL, pool_pre_ping=True)
else:
    engine = create_engine("sqlite:////tmp/data.sqlite3", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False)

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
        # Development bypass
        if AUTH_TEST_BYPASS and token.startswith("test:"):
            return token.split(":", 1)[1] or "test_user", "user"
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ══════════════════════════════════════════════════════════
# LLM
# ══════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are VisePanda 🐼, a premium AI travel planner for China.

Your personality: warm, knowledgeable, efficient. Like a local friend who happens to be a professional travel agent.

CRITICAL RULES:
- 🏪 SPECIFIC NAMES REQUIRED: Every restaurant, hotel, attraction, and activity recommendation MUST include the actual business/store name (e.g. "南门涮肉" not "a local hotpot place", "北京嘉里大酒店" not "a nice hotel near the center"). NEVER use vague phrases like "there are many options", "you can find various choices", "numerous restaurants available" — name names.
- 💰 BUDGET TIERS — always match user's budget with explicit tier label:
  · 经济档 (Budget): 青年旅社/如家/汉庭 ≈ ¥50-150/night · 当地小吃/街边摊/沙县小吃 ≈ ¥15-30/meal
  · 中档 (Mid-range): 精品酒店/亚朵/全季 ≈ ¥300-600/night · 网红餐厅/特色菜馆 ≈ ¥80-150/meal
  · 豪华档 (Luxury): 五星酒店/洲际/丽思卡尔顿 ≈ ¥1000+/night · 米其林/黑珍珠餐厅 ≈ ¥300+/meal
  Label each recommendation with its tier so user sees the range.
- 🏠 LOCAL TIPS REQUIRED per recommendation: best photo time (e.g. "故宫16:00后光影最出片"), ticket booking tricks (e.g. "故宫需提前7天在公众号抢票"), metro transfer details (e.g. "天安门东站B出口出，排队最少"), peak avoidance ("周一闭馆，别跑空").
- Structure itineraries with clear day-by-day breakdown, times, and transport tips
- End long responses with ---SUGGESTIONS--- followed by 2-3 follow-up questions on separate lines starting with -
- 🌐 LANGUAGE MATCH: Always respond in the SAME language as the user. If user writes in Chinese, reply entirely in Chinese (Simplified). Never switch to English unless the user does first.

FORMAT for itineraries:
**Day N — [Theme]**
- Morning (8:00-12:00): ...
- Afternoon (12:00-18:00): ...
- Evening (18:00+): ...
- 🍜 Eat: [店名 — 档次 — 推荐理由]
- 🏨 Stay near: [区域/酒店名 — 档次]
- 🚇 Transport: [具体地铁线路+换乘站+出口编号]
- 💡 Tip: [本地人实用贴士 — 拍照/门票/避开排队等]

IMPORTANT: Every single meal, hotel, and activity slot must contain a named establishment. If you don't know a specific name for the city, make reasonable effort to recall real, verifiable businesses in that city — do NOT fall back to "you'll find good food there"."""

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
:root{--bg0:#05070b;--bg1:#0a0f17;--bg2:#0e1520;--line:rgba(255,255,255,.06);--line-hover:rgba(125,211,252,.25);--muted:rgba(255,255,255,.5);--text:rgba(255,255,255,.92);--accent:#7dd3fc;--accent-dim:rgba(125,211,252,.12);--card-bg:rgba(255,255,255,.02);--card-hover:rgba(125,211,252,.04);--font-display:'Geist','Geist Fallback',system-ui,-apple-system,sans-serif;--font-mono:'Geist Mono','JetBrains Mono','Fira Code',monospace}
/* font-display: swap is implicit — Geist loads async via <link preload>
   until loaded, system-ui/sans-serif fallback renders immediately */
*,*::before,*::after{box-sizing:border-box}
body{margin:0;min-height:100dvh;background:radial-gradient(1400px 900px at 30% 10%,#121826 0%,var(--bg1) 45%,var(--bg0) 100%);color:var(--text);font-family:var(--font-display);-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
.bg-shanshui{position:fixed;inset:0;background:url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400"><path d="M0 350 Q200 200 400 280 Q600 360 800 250 L800 400 L0 400Z" fill="%23ffffff" opacity=".06"/></svg>') center/cover;filter:blur(8px);pointer-events:none;will-change:transform}
.bg-glow{position:fixed;top:-30%;right:-20%;width:600px;height:600px;border-radius:50%;background:radial-gradient(circle,rgba(125,211,252,.06),transparent 70%);pointer-events:none;z-index:0;will-change:transform}
header{height:56px;display:flex;align-items:center;justify-content:space-between;padding:0 20px;border-bottom:1px solid var(--line);background:rgba(15,20,30,.45);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);position:relative;z-index:10}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--text)}
.brand-logo{width:22px;height:22px;background:url("data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="rgba(125,211,252,.12)"/><circle cx="50" cy="46" r="28" fill="%23fff"/><ellipse cx="37" cy="42" rx="8" ry="7" fill="%23111"/><ellipse cx="63" cy="42" rx="8" ry="7" fill="%23111"/><circle cx="37" cy="41" r="3" fill="%23fff"/><circle cx="63" cy="41" r="3" fill="%23fff"/><ellipse cx="50" cy="52" rx="4" ry="3" fill="%23111"/><path d="M38 62 Q44 70 50 62 Q56 70 62 62" stroke="%23111" stroke-width="2" fill="none" stroke-linecap="round"/><circle cx="20" cy="20" r="10" fill="rgba(125,211,252,.12)"/><circle cx="80" cy="20" r="10" fill="rgba(125,211,252,.12)"/></svg>") center/contain no-repeat;flex-shrink:0}
.brand-name{font-weight:600;font-size:13px;letter-spacing:-.01em}
.btn{font-size:12px;padding:8px 16px;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.03);color:var(--text);cursor:pointer;text-decoration:none;transition:all .2s cubic-bezier(.16,1,.3,1);display:inline-flex;align-items:center;gap:6px;backface-visibility:hidden}
.btn:hover{background:rgba(255,255,255,.07);border-color:rgba(255,255,255,.12)}
.btn-accent{border-color:rgba(125,211,252,.3);background:rgba(125,211,252,.1)}
.btn-accent:hover{border-color:rgba(125,211,252,.5);background:rgba(125,211,252,.18);box-shadow:0 0 24px rgba(125,211,252,.12)}
.hero{position:relative;z-index:1;min-height:calc(100dvh - 56px);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px 24px 100px;text-align:center}
.hero-inner{max-width:680px;width:100%}
.hero-eyebrow{font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:var(--accent);margin-bottom:16px;font-weight:500;opacity:.8}
.hero h1{font-size:clamp(28px,5vw,44px);font-weight:600;letter-spacing:-.03em;line-height:1.15;margin:0 0 12px;color:var(--text)}
.hero h1 span{background:linear-gradient(135deg,var(--accent),#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero p{font-size:15px;line-height:1.6;color:var(--muted);margin:0 auto 28px;max-width:480px}
.search-box{display:flex;gap:8px;max-width:520px;margin:0 auto;background:rgba(255,255,255,.03);border:1px solid var(--line);border-radius:999px;padding:4px;transition:all .2s}
.search-box:focus-within{border-color:rgba(125,211,252,.35);box-shadow:0 0 0 3px rgba(125,211,252,.08),0 0 30px rgba(125,211,252,.05);background:rgba(255,255,255,.05)}
.search-box input{flex:1;border:none;background:transparent;color:var(--text);padding:0 16px;font-size:14px;outline:none;font-family:var(--font-display)}
.search-box input::placeholder{color:var(--muted)}
.search-box button{height:40px;padding:0 20px;border-radius:999px;border:none;background:rgba(125,211,252,.14);color:var(--text);font-size:13px;cursor:pointer;transition:all .2s;font-weight:500;font-family:var(--font-display);white-space:nowrap}
.search-box button:hover{background:rgba(125,211,252,.24)}
.trust-bar{display:flex;align-items:center;justify-content:center;gap:16px;margin-top:20px;font-size:11px;color:var(--muted)}
.trust-bar .dot-sep{width:3px;height:3px;border-radius:50%;background:var(--line);flex-shrink:0}
.destinations{padding:0 24px 80px;position:relative;z-index:1}
.destinations-inner{max-width:900px;margin:0 auto}
.section-label{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:20px;font-weight:500}
.dest-grid{display:grid;grid-template-columns:2fr 1fr 1fr;gap:10px;content-visibility:auto;contain-intrinsic-size:320px}
.dest-grid .dest-card.featured{grid-row:1/3}
.dest-grid .dest-card.wide{grid-column:1/4;display:flex;align-items:center;gap:16px;padding:14px 20px}
.dest-grid .dest-card.wide .dest-emoji{font-size:32px;margin-bottom:0}
.dest-grid .dest-card.wide .dest-title{font-size:16px}
.dest-grid .dest-card.wide .dest-sub{font-size:12px}
.dest-card{position:relative;border:1px solid var(--line);border-radius:14px;padding:18px;background:var(--card-bg);cursor:pointer;transition:all .25s ease;text-decoration:none;display:block;overflow:hidden}
.dest-card::before{content:'';position:absolute;inset:0;background:linear-gradient(135deg,rgba(125,211,252,.04),transparent 60%);opacity:0;transition:opacity .25s;border-radius:inherit}
.dest-card:hover{border-color:var(--line-hover);background:var(--card-hover);transform:translateY(-3px);backface-visibility:hidden}
.dest-card:hover::before{opacity:1}
.dest-card:hover .dest-emoji{transform:scale(1.1)}
.dest-emoji{font-size:26px;margin-bottom:10px;display:block;transition:transform .25s}
.dest-title{font-weight:600;font-size:14px;color:var(--text);margin:0 0 3px}
.dest-sub{font-size:11px;color:var(--muted);margin:0;line-height:1.4}
.dest-accent{position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,rgba(125,211,252,.3),transparent);opacity:0;transition:opacity .25s}
.dest-card:hover .dest-accent{opacity:1}
.featured-grid{display:grid;grid-template-columns:2fr 1fr;gap:10px;margin-top:10px}
.featured-card{position:relative;border:1px solid var(--line);border-radius:14px;padding:20px;background:linear-gradient(135deg,rgba(125,211,252,.06),transparent);cursor:pointer;transition:all .25s ease;text-decoration:none;display:block}
.featured-card:hover{border-color:var(--line-hover);transform:translateY(-3px)}
.featured-emoji{font-size:28px;margin-bottom:8px;display:block}
.featured-title{font-weight:600;font-size:15px;color:var(--text);margin:0 0 4px}
.featured-sub{font-size:12px;color:var(--muted);margin:0;line-height:1.4}
footer{position:fixed;left:0;right:0;bottom:0;padding:10px 20px;padding-bottom:calc(10px + env(safe-area-inset-bottom));border-top:1px solid var(--line);background:rgba(15,20,30,.35);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);font-size:11px;color:var(--muted);z-index:10;display:flex;align-items:center;gap:12px;justify-content:center}
input[type=text]{border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.03);color:var(--text);padding:12px 16px;outline:none;font-size:16px;font-family:var(--font-display);transition:all .2s}
input[type=text]:focus{border-color:rgba(125,211,252,.35);box-shadow:0 0 0 3px rgba(125,211,252,.08),0 0 24px rgba(125,211,252,.06)}
.recent-title{font-size:12px;color:var(--muted);margin-bottom:8px;font-weight:600;letter-spacing:.05em}
.recent-trip{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border:1px solid var(--line);border-radius:12px;margin-bottom:6px;background:rgba(255,255,255,.02);text-decoration:none;color:var(--text);transition:all .2s}
.recent-trip:hover{border-color:var(--line-hover);background:var(--card-hover)}
.recent-trip-label{font-size:14px;font-weight:500}
.recent-trip-meta{font-size:11px;color:var(--muted)}
.trip-highlight{border-left:2px solid var(--accent)!important;background:linear-gradient(135deg,rgba(125,211,252,.06),transparent)!important}
.price-budget{color:#4ade80}
.price-mid{color:#fbbf24}
.price-luxury{color:#f87171}
code{background:rgba(0,0,0,.3);padding:2px 6px;border-radius:4px;font-family:var(--font-mono);font-size:.9em}
pre{background:rgba(0,0,0,.4);padding:12px 16px;border-radius:10px;border:1px solid var(--line);overflow-x:auto;margin:8px 0}
pre code{background:none;padding:0;border-radius:0}
#quickReplies .chip{font-size:11px;padding:6px 12px;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.04);color:var(--muted);cursor:pointer;white-space:nowrap;margin:4px 4px 0 0;display:inline-block;transition:all .15s}
#quickReplies .chip:hover{border-color:var(--line-hover);color:var(--text)}
.animate-in{animation:fadeUp .6s cubic-bezier(.16,1,.3,1) both}
.animate-in-d1{animation-delay:.1s}
.animate-in-d2{animation-delay:.2s}
.animate-in-d3{animation-delay:.3s}
.animate-in-d4{animation-delay:.4s}
/* Chat message slide-in */
@keyframes slideUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.msg-enter{animation:slideUp .35s cubic-bezier(.16,1,.3,1) both}
/* Card stagger delay */
.stagger-d1{animation-delay:.05s!important}.stagger-d2{animation-delay:.1s!important}.stagger-d3{animation-delay:.15s!important}.stagger-d4{animation-delay:.2s!important}.stagger-d5{animation-delay:.25s!important}.stagger-d6{animation-delay:.3s!important}
/* Breathing bg glow */
@keyframes breathe{0%,100%{opacity:.5}50%{opacity:1}}
@media(prefers-reduced-motion:no-preference){.bg-glow{animation:breathe 6s ease-in-out infinite}}
@keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
@media(max-width:800px){.dest-grid{grid-template-columns:repeat(2,1fr)}.dest-grid .dest-card.featured{grid-row:auto}.dest-grid .dest-card.wide{grid-column:auto;flex-direction:column;text-align:center;padding:18px;gap:8px}.dest-grid .dest-card.wide .dest-emoji{font-size:26px;margin-bottom:10px}.featured-grid{grid-template-columns:1fr}}
/* Hero decorative elements */
.hero-decor{position:absolute;top:50%;right:-5%;width:400px;height:400px;pointer-events:none;z-index:0;opacity:.35}
.hero-decor-circle{position:absolute;top:50%;left:50%;width:300px;height:300px;border-radius:50%;border:1px solid rgba(125,211,252,.12);transform:translate(-50%,-50%);animation:float 8s ease-in-out infinite}
.hero-decor-dot{position:absolute;border-radius:50%;background:var(--accent);opacity:.15}
.hero-decor-dot.dot-1{width:12px;height:12px;top:20%;right:30%;animation:float 6s ease-in-out infinite 1s}
.hero-decor-dot.dot-2{width:8px;height:8px;top:60%;right:10%;animation:float 7s ease-in-out infinite 2s}
.hero-decor-dot.dot-3{width:6px;height:6px;top:40%;left:10%;animation:float 5s ease-in-out infinite .5s}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}
/* Adjust hero position for decor */
.hero{overflow:hidden}
@media(max-width:800px){.hero-decor{display:none}}
@media(max-width:480px){.dest-grid{grid-template-columns:1fr}.hero{padding:30px 16px 80px}.search-box{flex-direction:column;border-radius:16px;background:transparent;border:none;gap:8px;padding:0}.search-box input{border:1px solid var(--line);border-radius:999px;padding:12px 16px;height:44px;background:rgba(255,255,255,.03)}.search-box button{width:100%;height:44px}.hero h1{font-size:26px}.destinations{padding:0 16px 60px}.trust-bar{flex-wrap:wrap;gap:8px}}
"""

def _inject_config() -> str:
    """Inject Supabase config into HTML."""
    return f"""<script>
window.__SUPABASE_CONFIG__ = {{
  supabase_url: "{SUPABASE_URL}",
  supabase_anon_key: "{SUPABASE_ANON_KEY}"
}};
</script>"""


def _font_links() -> str:
    """Async font loading — non-blocking, text renders in fallback immediately."""
    return '''<link rel="preconnect" href="https://fonts.cdnfonts.com">
<link rel="preload" as="style" href="https://fonts.cdnfonts.com/css/geist" onload="this.onload=null;this.rel=\'stylesheet\'">
<noscript><link rel="stylesheet" href="https://fonts.cdnfonts.com/css/geist"></noscript>'''

def page_landing() -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>VisePanda — AI China Travel Planner 🇨🇳</title><meta name="description" content="Plan your China trip with AI. Get personalized itineraries, local food recommendations, hotel tips. Beijing, Shanghai, Chengdu, Yunnan — tell us where and how long."><meta property="og:title" content="VisePanda — AI China Travel Planner"><meta property="og:description" content="Personalized China travel itineraries powered by AI"><meta property="og:type" content="website"><meta name="twitter:card" content="summary">{_font_links()}<style>{CSS}</style>{_inject_config()}<script>navigator.serviceWorker&&navigator.serviceWorker.register("/sw.js")</script></head><body>
<div class="bg-shanshui"></div>
<div class="bg-glow"></div>
<header><a href="/" class="brand"><span class="brand-logo"></span><span class="brand-name">VisePanda</span></a><div id="authArea"><a href="#" onclick="event.preventDefault();signIn()" class="btn btn-accent">Sign in</a></div></header>
<div class="hero">
<div class="hero-inner">
<div class="hero-eyebrow animate-in">AI Travel Planner</div>
<h1 class="animate-in animate-in-d1">Plan your <span>China trip</span> 🐼</h1>
<p class="animate-in animate-in-d2">Just tell me where and how long. I'll craft a personalized itinerary with local tips.</p>
<form onsubmit="event.preventDefault();const v=document.getElementById('q').value.trim();goChat(v||document.getElementById('q').placeholder)" class="search-box animate-in animate-in-d3">
<input id="q" type="text" placeholder="e.g. Beijing 5 days, food+history, relaxed pace…">
<button type="submit">Start Planning →</button>
</form>
<div class="trust-bar animate-in animate-in-d4"><span>No sign-up needed</span><span class="dot-sep"></span><span>AI-powered</span><span class="dot-sep"></span><span>Local insights</span></div>
<div class="hero-decor"><div class="hero-decor-circle"></div><div class="hero-decor-dot dot-1"></div><div class="hero-decor-dot dot-2"></div><div class="hero-decor-dot dot-3"></div></div>
</div>
</div>
<div class="destinations">
<div class="destinations-inner">
<div class="section-label">Popular destinations</div>
<div class="dest-grid">
<a class="dest-card featured" href="#" onclick="event.preventDefault();goChat('北京3天深度游,喜欢历史文化,中等预算')"><div class="dest-accent"></div><span class="dest-emoji">🏯</span><div class="dest-title">Beijing</div><div class="dest-sub">Forbidden City · Wall · Hutongs</div></a>
<a class="dest-card" href="#" onclick="event.preventDefault();goChat('成都4天美食之旅,火锅串串,悠闲逛')"><div class="dest-accent"></div><span class="dest-emoji">🐼</span><div class="dest-title">Chengdu</div><div class="dest-sub">Hotpot · Pandas · Tea houses</div></a>
<a class="dest-card" href="#" onclick="event.preventDefault();goChat('云南7天,大理丽江香格里拉,自然风光')"><div class="dest-accent"></div><span class="dest-emoji">🏔️</span><div class="dest-title">Yunnan</div><div class="dest-sub">Dali · Lijiang · Shangri-La</div></a>
<a class="dest-card" href="#" onclick="event.preventDefault();goChat('上海3天,摩登都市,外滩迪士尼')"><div class="dest-accent"></div><span class="dest-emoji">🌃</span><div class="dest-title">Shanghai</div><div class="dest-sub">Bund · Disney · French Concession</div></a>
<a class="dest-card" href="#" onclick="event.preventDefault();goChat('西安3天历史游,兵马俑古城墙,中等预算')"><div class="dest-accent"></div><span class="dest-emoji">🏛️</span><div class="dest-title">Xi'an</div><div class="dest-sub">Terracotta · City Wall · Muslim Quarter</div></a>
<a class="dest-card wide" href="#" onclick="event.preventDefault();goChat('桂林4天,漓江阳朔,自然风光')"><div class="dest-accent"></div><span class="dest-emoji">🛶</span><div class="dest-title">Guilin</div><div class="dest-sub">Li River · Yangshuo · Karst Mountains</div></a>
</div>
<div id="recentTrips" style="display:none;margin-top:20px;text-align:left"></div>
</div>
</div>
<footer><span>No login required</span><span class="dot-sep"></span><span>Last 3 trips saved locally</span><span class="dot-sep"></span><span>Sign in to sync across devices</span></footer>
<script src="/static/landing.js"></script></body></html>"""

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
    db = SessionLocal()
    try:
        trip = db.query(Trip).filter(Trip.share_id == share_id).one_or_none()
        if not trip:
            return '<html lang=en><head><meta charset=utf-8><title>Not Found</title><style>body{{display:flex;align-items:center;justify-content:center;min-height:100vh;background:#0a0f17;color:#fff;font-family:sans-serif;text-align:center;margin:0}}h1{{font-size:48px}}a{{color:#7dd3fc}}</style><h1>🐼</h1><p>Trip not found</p><a href=/>Back home</a>'
        msgs = db.query(ChatMessage).filter(ChatMessage.trip_id == trip.id).order_by(ChatMessage.created_at.asc()).all()
    finally:
        db.close()
    msgs_html = ''.join(f'<div class="msg {m.role}"><div class=bubble>{_render_msg(m.content)}</div></div>' for m in msgs)
    title = trip.title or 'Shared Trip'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · VisePanda</title><meta name="description" content="AI-planned China trip itinerary"><meta property="og:title" content="{title}">{_font_links()}<style>{CSS}.share-header{{text-align:center;padding:24px 16px 12px;position:relative;z-index:1}}.share-header h2{{font-size:20px;margin:0;color:var(--text)}}.share-header p{{color:var(--muted);font-size:14px;margin:4px 0}}.share-thread{{max-width:700px;margin:0 auto;padding:12px 16px 100px;position:relative;z-index:1}}.share-footer{{text-align:center;padding:20px;position:relative;z-index:1}}.msg{{margin:8px 0}}.msg.assistant .bubble{{border:1px solid var(--line);border-radius:14px;padding:10px 14px;line-height:1.5;background:rgba(255,255,255,.03);white-space:pre-wrap}}.msg.user .bubble{{background:rgba(125,211,252,.10);border-color:rgba(125,211,252,.18)}}.bubble{{max-width:700px}}
</style><script defer src='/_vercel/insights/script.js'></script><script defer src='/_vercel/speed-insights/script.js'></script><script>navigator.serviceWorker&&navigator.serviceWorker.register("/sw.js")</script></head><body><div class="bg-shanshui"></div>
<div class="share-header"><h2>🐼 {title}</h2><p>AI-planned trip · {len(msgs)} messages</p><a href="/" class="btn btn-accent" style="margin-top:16px;display:inline-block">🚀 Create your own trip</a></div>
<div class="share-thread">{msgs_html}</div>
<div class="share-footer"><a href="/" class="btn btn-accent">Plan your own trip</a></div>
</body></html>'''


def page_trips() -> str:
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>My Trips · VisePanda</title>{_font_links()}<style>{CSS}
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
</style><script>navigator.serviceWorker&&navigator.serviceWorker.register("/sw.js")</script></head><body>
<div class="bg-shanshui"></div>
<header><a href="/" class="brand"><span class="brand-logo"></span><span class="brand-name">VisePanda</span></a><div><a href="/" class="btn">Home</a></div></header>
<main style="position:relative;z-index:1;min-height:calc(100vh-56px);padding:20px 16px 80px">
<h2 style="text-align:center;color:var(--text);font-size:22px;margin:20px 0">My Trips</h2>
<div id="tripsList" class="trips-grid"><div class="skeleton" style="height:100px"></div></div>
<div id="emptyMsg" class="empty" style="display:none"><p>No trips yet.</p><a href="/" class="btn btn-accent" style="display:inline-block;margin-top:12px">Start Planning</a></div>
</main>
<script src="/static/trips.js"></script>
</body></html>'''

def page_chat() -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>Chat · VisePanda — AI China Travel Planner</title><meta name="description" content="Chat with VisePanda AI to plan your China trip. Get day-by-day itineraries, food guides, and practical travel tips.">{_font_links()}<style>{CSS}
.layout{{display:flex;height:calc(100vh-56px);position:relative;z-index:1}}
#thread{{flex:1;overflow:auto;padding:18px 16px 120px}}
/* Chat avatars + bubbles */
.avatar{{width:30px;height:30px;border-radius:50%;flex-shrink:0;margin-top:4px}}
.avatar-bot{{background:url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="rgba(125,211,252,.12)"/><circle cx="50" cy="46" r="28" fill="%23fff"/><ellipse cx="37" cy="42" rx="8" ry="7" fill="%23111"/><ellipse cx="63" cy="42" rx="8" ry="7" fill="%23111"/><circle cx="37" cy="41" r="3" fill="%23fff"/><circle cx="63" cy="41" r="3" fill="%23fff"/><ellipse cx="50" cy="52" rx="4" ry="3" fill="%23111"/><path d="M38 62 Q44 70 50 62 Q56 70 62 62" stroke="%23111" stroke-width="2" fill="none" stroke-linecap="round"/></svg>') center/contain no-repeat}}
.avatar-user{{background:linear-gradient(135deg,rgba(125,211,252,.2),rgba(167,139,250,.2));display:flex;align-items:center;justify-content:center}}
.avatar-user span{{font-size:13px;font-weight:600;color:var(--accent)}}
.msg{{display:flex;margin:12px 0;gap:8px}}
.msg.user{{flex-direction:row-reverse}}
.msg-body{{max-width:min(660px,80%)}}
.bubble{{max-width:100%;border:1px solid var(--line);border-radius:14px;padding:10px 14px;line-height:1.4;background:rgba(255,255,255,.03);white-space:pre-wrap}}
.msg.user .msg-body{{display:flex;flex-direction:column;align-items:flex-end}}
.msg.user .bubble{{background:rgba(125,211,252,.10);border-color:rgba(125,211,252,.18)}}
.msg.bot .bubble p{{margin:0}}
/* Typing indicator */
@keyframes typing{{0%,60%,100%{{transform:translateY(0)}}30%{{transform:translateY(-4px)}}}}
.typing-indicator{{display:inline-flex;align-items:center;gap:3px;padding:8px 4px}}
.typing-indicator span{{width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,.3);animation:typing 1.4s ease-in-out infinite}}
.typing-indicator span:nth-child(2){{animation-delay:.2s}}
.typing-indicator span:nth-child(3){{animation-delay:.4s}}
.chip{{font-size:11px;padding:5px 10px;border-radius:999px;border:1px solid rgba(125,211,252,.2);background:rgba(125,211,252,.06);color:rgba(255,255,255,.8);cursor:pointer;white-space:nowrap;margin:4px 4px 0 0;display:inline-block}}
#quickReplies .chip{{background:rgba(255,255,255,.05);border-color:var(--line);color:var(--muted);padding:8px 14px;border-radius:10px;font-size:12px}}
.chat-footer{{position:fixed;bottom:0;left:0;right:0;padding:12px 16px;padding-bottom:calc(12px + env(safe-area-inset-bottom));border-top:1px solid var(--line);background:rgba(8,10,14,.55);backdrop-filter:blur(10px);z-index:2}}
#msgForm{{display:flex;gap:10px;align-items:center;max-width:800px;margin:0 auto}}
#msgInput{{flex:1;height:44px;padding:0 14px;font-size:14px}}
#sendBtn{{height:44px;padding:0 20px;background:rgba(125,211,252,.14);border:1px solid rgba(125,211,252,.35);border-radius:999px;color:var(--text);cursor:pointer;font-size:14px}}
#sendBtn:hover{{background:rgba(125,211,252,.22);transform:scale(1.04);box-shadow:0 0 20px rgba(125,211,252,.15)}}#sendBtn:active{{transform:scale(.96)}}
#quickReplies{{display:flex;flex-wrap:wrap;gap:4px;padding:6px 0;max-width:800px;margin:0 auto 8px}}
.cursor{{animation:blink 1s step-end infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:0}}}}
/* Skeleton v2 — polished shimmer + variants */
.skeleton,.skel-text{height:16px;border-radius:8px;background:linear-gradient(110deg,rgba(255,255,255,.03)30%,rgba(255,255,255,.09)50%,rgba(255,255,255,.03)70%);background-size:200%100%;animation:shimmer 1.8s cubic-bezier(.4,0,.2,1) infinite}
.skel-card{height:120px;border-radius:14px;background:linear-gradient(135deg,rgba(255,255,255,.02),rgba(125,211,252,.04));overflow:hidden;position:relative}
.skel-card::after{content:'';position:absolute;inset:0;background:linear-gradient(110deg,transparent 30%,rgba(125,211,252,.06)50%,transparent 70%);background-size:200%100%;animation:shimmer 1.8s cubic-bezier(.4,0,.2,1) infinite}
.skel-circle{width:36px;height:36px;border-radius:50%;background:linear-gradient(110deg,rgba(255,255,255,.03)30%,rgba(255,255,255,.09)50%,rgba(255,255,255,.03)70%);background-size:200%100%;animation:shimmer 1.8s cubic-bezier(.4,0,.2,1) infinite}
.skel-msg{display:flex;gap:10px;align-items:flex-start;margin:8px 0}
.skel-msg .skel-lines{flex:1}
.skel-msg .skel-lines .skel-text:first-child{width:75%;margin-bottom:6px}
.skel-msg .skel-lines .skel-text:last-child{width:50%}
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
</style><script defer src='/_vercel/insights/script.js'></script><script defer src='/_vercel/speed-insights/script.js'></script>{_inject_config()}<script>navigator.serviceWorker&&navigator.serviceWorker.register("/sw.js")</script></head><body>
<div class="bg-shanshui"></div>
<header><a href="/" class="brand"><span class="brand-logo"></span><span class="brand-name">VisePanda</span></a><div><a href="/trips" class="btn" style="margin-right:8px">Trips</a><a href="#" onclick="event.preventDefault();clearChat()" class="btn" style="margin-right:8px">Clear</a><a href="/" class="btn">Home</a></div></header>
<div class="layout"><main style="flex:1;display:flex;flex-direction:column"><div id="thread"><div class="welcome" id="welcomeMsg"><h2>👋 Welcome to VisePanda</h2><p>Your AI travel planner for China. Ask me anything!</p><div class="welcome-chips"><span class="welcome-chip" onclick="document.getElementById('msgInput').value='Beijing 3-day itinerary';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🏯 Beijing 3 days</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='Chengdu food tour 4 days';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🐼 Chengdu food</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='Yunnan 7 days nature trip';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🏔️ Yunnan 7 days</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='Shanghai weekend guide';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🌃 Shanghai weekend</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='Xi'an terracotta history 3 days';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🏛️ Xi'an history</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='Guilin Li River Yangshuo 4 days';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🛶 Guilin nature</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='Hangzhou West Lake relaxed 3 days';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🍵 Hangzhou relax</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='Guangzhou dimsum food tour 3 days';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🥟 Guangzhou food</span></div></div></div></main></div>
<div class="chat-footer"><div id="quickReplies"></div><form id="msgForm"><input id="msgInput" type="text" placeholder="Type a message…" autofocus><button id="sendBtn" type="submit">Send</button></form></div>
<script src="/static/chat.js"></script></body></html>"""

def page_auth_callback() -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Signing in…</title>{_font_links()}<style>body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0a0f17;color:#fff;font-family:sans-serif;text-align:center}}.muted{{color:rgba(255,255,255,.5);font-size:14px}}</style>{_inject_config()}</head><body>
<div><div style="font-size:18px;font-weight:650;margin-bottom:8px">Signing in…</div><div class="muted">Redirecting…</div></div>
<script src="/static/auth.js"></script></body></html>"""

# ══════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[WARN] DB init failed: {e}", flush=True)
    yield

app = FastAPI(title="VisePanda", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add aggressive caching for static assets."""
    async def dispatch(self, request, call_next):
        resp = await call_next(request)
        path = request.url.path
        if path.startswith("/static/") or path in ("/favicon.ico", "/favicon.png"):
            resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif path.startswith("/sw.js"):
            resp.headers["Cache-Control"] = "no-cache, must-revalidate"
        return resp


app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(CacheControlMiddleware)


@app.get("/api/health")
def health():
    return {"ok": True, "version": "0.1.0", "db": "postgres" if DB_URL else "sqlite"}

@app.get("/favicon.ico")
@app.get("/favicon.png")
def favicon():
    return Response(status_code=204)


SW_JS = open("static/sw.js").read()


@app.get("/sw.js")
def service_worker():
    return Response(SW_JS, media_type="application/javascript",
                    headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"})


@app.get("/", response_class=HTMLResponse)
def landing():
    return page_landing()


@app.get("/share/{share_id}", response_class=HTMLResponse)
def share_view(share_id: str):
    return page_share(share_id)

@app.get("/trips", response_class=HTMLResponse)
def trips_page():
    return page_trips()

@app.get("/chat", response_class=HTMLResponse)
def chat_page():
    return page_chat()


@app.get("/auth/callback", response_class=HTMLResponse)
def auth_callback():
    return page_auth_callback()


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
    db = SessionLocal()
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
    db_ctx = SessionLocal()
    try:
        recent = db_ctx.query(ChatMessage).filter(
            ChatMessage.trip_id == payload.trip_id
        ).order_by(ChatMessage.created_at.desc()).limit(20).all()[::-1]
        context_msgs = [{"role": m.role, "content": m.content} for m in recent]
    finally:
        db_ctx.close()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *context_msgs,
    ]

    async def generate():
        full_text = ""
        async for chunk in stream_llm(messages):
            if "token" in chunk:
                try:
                    full_text += json.loads(chunk.split("data: ")[1].strip())["token"]
                except:
                    pass
            yield chunk

        # Save assistant message
        if full_text:
            db2 = SessionLocal()
            try:
                db2.add(ChatMessage(user_id=user_id, trip_id=payload.trip_id, role="assistant", content=full_text))
                db2.commit()
            finally:
                db2.close()

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.exception_handler(404)
async def not_found(request, exc):
    path = request.url.path
    if path.startswith("/api/"):
        return JSONResponse({"error": "not found"}, status_code=404)
    return HTMLResponse('<html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>404 — VisePanda</title><style>body{display:flex;align-items:center;justify-content:center;min-height:100vh;background:#0a0f17;color:#fff;font-family:sans-serif;text-align:center;margin:0}h1{font-size:48px;margin:0;letter-spacing:-.02em}p{color:rgba(255,255,255,.5)}a{color:#7dd3fc}</style><h1>🐼</h1><p>Page not found</p><a href=/>Back home</a>', status_code=404)


@app.get("/api/trips")
def list_trips(request: Request, guest_id: str | None = None):
    """List trips for current user."""
    from fastapi import Query
    db = SessionLocal()
    try:
        user_id = None
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            if AUTH_TEST_BYPASS and token.startswith("test:"):
                user_id = token.split(":", 1)[1] or "test_user"
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

@app.put("/api/trips/{trip_id}")
def rename_trip(trip_id: str, body: RenameIn):
    db = SessionLocal()
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
    db = SessionLocal()
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
    db = SessionLocal()
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).one_or_none()
        if not trip:
            raise HTTPException(404, "Trip not found")
        return {"share_id": trip.share_id, "url": f"/share/{trip.share_id}" if trip.share_id else None}
    finally:
        db.close()


@app.delete("/api/trips/{trip_id}")
def delete_trip(trip_id: str):
    db = SessionLocal()
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
    db = SessionLocal()
    try:
        msgs = db.query(ChatMessage).filter(
            ChatMessage.trip_id == trip_id
        ).order_by(ChatMessage.created_at.asc()).limit(50).all()
        return [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in msgs]
    finally:
        db.close()

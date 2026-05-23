"""
VisePanda — China Travel AI Agent
Single-file FastAPI app. No static frontend files.
Supabase config is server-injected into HTML.
LLM: GLM 5.1 (ZhipuAI, OpenAI-compatible).
"""
from __future__ import annotations

import datetime as dt
import re
import time
import hashlib
import json
import os
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
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

RULES:
- Recommend specific places, restaurants, hotels — never vague "there are many options"
- Structure itineraries with clear day-by-day breakdown, times, and transport tips
- Adapt to user's style: budget (青年旅社/当地小吃), mid-range (精品酒店/网红餐厅), luxury (五星酒店/米其林)
- Mention practical details: best time to visit spots, ticket booking tips, subway routes
- End long responses with ---SUGGESTIONS--- followed by 2-3 follow-up questions on separate lines starting with -
- Always respond in the same language as the user

FORMAT for itineraries:
**Day N — [Theme]**
- Morning (8:00-12:00): ...
- Afternoon (12:00-18:00): ...
- Evening (18:00+): ...
- 🍜 Eat: ...
- 🏨 Stay near: ...
- 🚇 Transport: ..."""

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
:root{--bg0:#05070b;--bg1:#0a0f17;--line:rgba(255,255,255,.08);--muted:rgba(255,255,255,.62);--text:rgba(255,255,255,.92);--accent:#7dd3fc;font-family:ui-sans-serif,system-ui,-apple-system,sans-serif}
body{margin:0;min-height:100vh;background:radial-gradient(1200px 800px at 30% 15%,#121826 0%,var(--bg1) 55%,var(--bg0) 100%);color:var(--text)}
.bg-shanshui{position:fixed;inset:0;background:url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400"><path d="M0 350 Q200 200 400 280 Q600 360 800 250 L800 400 L0 400Z" fill="%23ffffff" opacity=".03"/></svg>') center/cover;opacity:.15;filter:blur(6px);pointer-events:none}
header{height:56px;display:flex;align-items:center;justify-content:space-between;padding:0 16px;border-bottom:1px solid var(--line);background:rgba(8,10,14,.55);backdrop-filter:blur(10px);position:relative;z-index:1}
.dot{width:10px;height:10px;border-radius:99px;background:var(--accent);box-shadow:0 0 18px rgba(125,211,252,.45);display:inline-block;margin-right:10px}
.name{font-weight:650;font-size:14px}
.btn{font-size:12px;padding:7px 14px;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.03);color:var(--text);cursor:pointer;text-decoration:none}
.btn:hover{background:rgba(255,255,255,.06)}
.btn-accent{border-color:rgba(125,211,252,.35);background:rgba(125,211,252,.12)}
.card{border:1px solid var(--line);border-radius:16px;padding:18px;background:rgba(255,255,255,.02);cursor:pointer;transition:all .2s;text-align:left;text-decoration:none;display:block}
.card:hover{border-color:rgba(125,211,252,.35);background:rgba(125,211,252,.06);transform:translateY(-2px)}
.card-title{font-weight:650;font-size:15px;color:var(--text);margin:0 0 4px}
.card-sub{font-size:12px;color:var(--muted);margin:0}
.card-emoji{font-size:28px;margin-bottom:8px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-top:24px;max-width:560px;margin-left:auto;margin-right:auto}
footer{position:fixed;left:0;right:0;bottom:0;padding:10px 16px;border-top:1px solid var(--line);background:rgba(8,10,14,.55);backdrop-filter:blur(10px);font-size:12px;color:var(--muted);z-index:1}
input[type=text]{border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.03);color:var(--text);padding:12px 16px;outline:none;font-size:14px}
input[type=text]:focus{border-color:rgba(125,211,252,.35);box-shadow:0 0 0 4px rgba(125,211,252,.12)}
@media(max-width:640px){h1{font-size:24px!important}header{padding:0 12px}.btn{padding:6px 12px;font-size:11px}footer{font-size:11px;padding:8px 12px}.bubble{max-width:95%!important;font-size:15px}#msgForm{gap:6px}#msgInput{height:40px;font-size:16px}#sendBtn{height:40px;padding:0 14px;font-size:13px}.chat-footer{padding:10px 12px}#thread{padding:12px 12px 140px}input[type=text]{font-size:16px}}
"""

def _inject_config() -> str:
    """Inject Supabase config into HTML."""
    return f"""<script>
window.__SUPABASE_CONFIG__ = {{
  supabase_url: "{SUPABASE_URL}",
  supabase_anon_key: "{SUPABASE_ANON_KEY}"
}};
</script>"""

def page_landing() -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VisePanda — AI China Travel Planner 🇨🇳</title><meta name="description" content="Plan your China trip with AI. Get personalized itineraries, local food recommendations, hotel tips. Beijing, Shanghai, Chengdu, Yunnan — tell us where and how long."><meta property="og:title" content="VisePanda — AI China Travel Planner"><meta property="og:description" content="Personalized China travel itineraries powered by AI"><meta property="og:type" content="website"><meta name="twitter:card" content="summary"><style>{CSS}</style>{_inject_config()}</head><body>
<div class="bg-shanshui"></div>
<header><div><span class="dot"></span><span class="name">VisePanda</span></div><div id="authArea"><a href="#" onclick="event.preventDefault();signIn()" class="btn btn-accent">Sign in</a></div></header>
<main style="position:relative;min-height:calc(100vh-56px);display:flex;align-items:center;justify-content:center;padding:24px 16px 90px;z-index:1">
<div style="width:min(640px,96%);text-align:center">
<h1 style="font-size:34px;margin:0 0 8px;letter-spacing:-.02em">Plan your China trip 🐼</h1>
<p style="color:var(--muted);margin:0 0 24px;line-height:1.5">Ask less, chat more. Just tell me where and how long.</p>
<form onsubmit="event.preventDefault();const v=document.getElementById('q').value.trim();goChat(v||document.getElementById('q').placeholder)" style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
<input id="q" type="text" placeholder="e.g. Beijing 5 days, food+history, relaxed pace…" style="width:min(480px,88vw);height:48px;padding:0 16px">
<button type="submit" class="btn btn-accent" style="height:48px;padding:0 20px;font-size:14px">Start</button>
</form>
<div class="cards">
<a class="card" href="#" onclick="event.preventDefault();goChat('北京3天深度游,喜欢历史文化,中等预算')"><div class="card-emoji">🏯</div><div class="card-title">Beijing 3 Days</div><div class="card-sub">Forbidden City · Wall · Hutongs</div></a>
<a class="card" href="#" onclick="event.preventDefault();goChat('成都4天美食之旅,火锅串串,悠闲逛')"><div class="card-emoji">🐼</div><div class="card-title">Chengdu Food Tour</div><div class="card-sub">Hotpot · Pandas · Tea houses</div></a>
<a class="card" href="#" onclick="event.preventDefault();goChat('云南7天,大理丽江香格里拉,自然风光')"><div class="card-emoji">🏔️</div><div class="card-title">Yunnan 7 Days</div><div class="card-sub">Dali · Lijiang · Shangri-La</div></a>
</div>
<div style="margin-top:20px;font-size:12px;color:var(--muted)">Open chat · Sign in with Google · Continue as guest</div>
</div></main>
<footer>Try without login — last 3 trips saved locally. Login to sync across devices.</footer>
<script src="https://esm.sh/@supabase/supabase-js@2"></script>
<script>
let sb=null;
function goChat(q){{const id='t_'+crypto.randomUUID();const u=new URL('/chat',location);u.searchParams.set('trip',id);if(q)u.searchParams.set('q',q);location.href=u.toString()}}
async function initSupabase(){{sb=supabase.createClient(window.__SUPABASE_CONFIG__.supabase_url,window.__SUPABASE_CONFIG__.supabase_anon_key)}}
async function signIn(){{if(!sb)await initSupabase();sb.auth.signInWithOAuth({{provider:'google',options:{{redirectTo:location.origin+'/auth/callback'}}}})}}
initSupabase();
</script></body></html>"""

def page_chat() -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Chat · VisePanda — AI China Travel Planner</title><meta name="description" content="Chat with VisePanda AI to plan your China trip. Get day-by-day itineraries, food guides, and practical travel tips."><style>{CSS}
.layout{{display:flex;height:calc(100vh-56px);position:relative;z-index:1}}
#thread{{flex:1;overflow:auto;padding:18px 16px 120px}}
.msg{{display:flex;margin:8px 0}}
.msg.user{{justify-content:flex-end}}
.bubble{{max-width:min(700px,88%);border:1px solid var(--line);border-radius:14px;padding:10px 14px;line-height:1.4;background:rgba(255,255,255,.03);white-space:pre-wrap}}
.msg.user .bubble{{background:rgba(125,211,252,.10);border-color:rgba(125,211,252,.18)}}
.msg.bot .bubble p{{margin:0}}
.chip{{font-size:11px;padding:5px 10px;border-radius:999px;border:1px solid rgba(125,211,252,.2);background:rgba(125,211,252,.06);color:rgba(255,255,255,.8);cursor:pointer;white-space:nowrap;margin:4px 4px 0 0;display:inline-block}}
.chat-footer{{position:fixed;bottom:0;left:0;right:0;padding:12px 16px;border-top:1px solid var(--line);background:rgba(8,10,14,.55);backdrop-filter:blur(10px);z-index:2}}
#msgForm{{display:flex;gap:10px;align-items:center;max-width:800px;margin:0 auto}}
#msgInput{{flex:1;height:44px;padding:0 14px;font-size:14px}}
#sendBtn{{height:44px;padding:0 20px;background:rgba(125,211,252,.14);border:1px solid rgba(125,211,252,.35);border-radius:999px;color:var(--text);cursor:pointer;font-size:14px}}
#sendBtn:hover{{background:rgba(125,211,252,.22)}}
#quickReplies{{display:flex;flex-wrap:wrap;gap:4px;padding:6px 0;max-width:800px;margin:0 auto 8px}}
.cursor{{animation:blink 1s step-end infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:0}}}}
.skeleton{{height:16px;border-radius:8px;background:linear-gradient(90deg,rgba(255,255,255,.04)25%,rgba(255,255,255,.08)50%,rgba(255,255,255,.04)75%);background-size:200%100%;animation:shimmer 1.5s infinite}}
@keyframes shimmer{{0%{{background-position:200%0}}100%{{background-position:-200%0}}}}
.trip-card{{border:1px solid var(--line);border-radius:12px;padding:14px;margin:6px 0;background:rgba(125,211,252,.03)}}
.trip-card b{{color:var(--accent)}}
.welcome{{text-align:center;padding:40px 20px;color:var(--muted)}}
.welcome h2{{font-size:20px;color:var(--text);margin:0 0 6px}}
.welcome p{{margin:4px 0;font-size:14px}}
.welcome-chips{{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:20px}}
.welcome-chip{{border:1px solid var(--line);border-radius:999px;padding:8px 16px;font-size:13px;color:var(--text);cursor:pointer;background:rgba(255,255,255,.03);transition:all .15s}}
.welcome-chip:hover{{border-color:rgba(125,211,252,.35);background:rgba(125,211,252,.08)}}
.time{{font-size:10px;color:var(--muted);margin-top:4px}}
</style>{_inject_config()}</head><body>
<div class="bg-shanshui"></div>
<header><div><span class="dot"></span><span class="name">VisePanda</span></div><div><a href="#" onclick="event.preventDefault();clearChat()" class="btn" style="margin-right:8px">Clear</a><a href="/" class="btn">Home</a></div></header>
<div class="layout"><main style="flex:1;display:flex;flex-direction:column"><div id="thread"><div class="welcome" id="welcomeMsg"><h2>👋 Welcome to VisePanda</h2><p>Your AI travel planner for China. Ask me anything!</p><div class="welcome-chips"><span class="welcome-chip" onclick="document.getElementById('msgInput').value='Beijing 3-day itinerary';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🏯 Beijing 3 days</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='Chengdu food tour 4 days';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🐼 Chengdu food</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='Yunnan 7 days nature trip';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🏔️ Yunnan 7 days</span><span class="welcome-chip" onclick="document.getElementById('msgInput').value='Shanghai weekend guide';document.getElementById('msgForm').dispatchEvent(new Event('submit'))">🌃 Shanghai weekend</span></div></div></div></main></div>
<div class="chat-footer"><div id="quickReplies"></div><form id="msgForm"><input id="msgInput" type="text" placeholder="Type a message…" autofocus><button id="sendBtn" type="submit">Send</button></form></div>
<script src="https://esm.sh/@supabase/supabase-js@2"></script>
<script>
let sb=null,tripId=null;
async function i(){{sb=supabase.createClient(W.__SUPABASE_CONFIG__.supabase_url,W.__SUPABASE_CONFIG__.supabase_anon_key)}}
const W=window,Q=s=>document.querySelector(s),H=s=>s.replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])),M=t=>{{let h=t.replace(/\\*\\*(.+?)\\*\\*/g,'<b>$1</b>').replace(/\\*(.+?)\\*/g,'<i>$1</i>').replace(/\\n\\n/g,'</p><p>').replace(/\\n/g,'<br>');if(t.includes('**Day '))h='<div class=trip-card>'+h+'</div>';return h}}
function msg(r,c){{const d=document.createElement('div');d.className='msg '+r;const t=new Date().toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit'}});d.innerHTML='<div class=bubble>'+M(c)+'</div><div class=time>'+t+'</div>';Q('#thread').appendChild(d);smartScroll();return d}}
async function loadHistory(){{if(!tripId)return;try{{const r=await fetch('/api/trips/'+tripId+'/messages');if(!r.ok)return;const msgs=await r.json();if(msgs.length>0){{const w=Q('#welcomeMsg');if(w)w.remove()}}for(const m of msgs){{msg(m.role==='user'?'user':'bot',m.content)}}}}catch(e){{}}}}
async function send(t){{const sbb=Q('#sendBtn');sbb.disabled=true;sbb.textContent='...';msg('user',t);const w=Q('#welcomeMsg');if(w)w.remove();tripId=tripId||'t_'+crypto.randomUUID();localStorage.setItem('vp_trip',tripId);const b=msg('bot','<div class=skeleton style=width:60%></div><div class=skeleton style=width:40%;margin-top:8px></div><div class=skeleton style=width:50%;margin-top:8px></div>');let f='';try{{
const s=await sb?.auth.getSession();const tok=s?.data?.session?.access_token;const h={{'Content-Type':'application/json'}};if(tok)h['Authorization']='Bearer '+tok;
let r;try{{r=await fetch('/api/chat',{{method:'POST',headers:h,body:JSON.stringify({{trip_id:tripId,text:t}})}});
}}catch(fe){{b.innerHTML='<span style=color:#fca5a5>Connection failed. Check your network.</span> <a href=# onclick="send(\\''+t.replace(/'/g,'\\\\x27')+'\\');return false" style=color:var(--accent);text-decoration:underline>Retry</a>';sbb.disabled=false;sbb.textContent='Send';return}}
const rd=r.body.getReader(),dc=new TextDecoder();let buf='';
while(1){{const{{done,value}}=await rd.read();if(done)break;buf+=dc.decode(value,{{stream:true}});
for(const l of buf.split('\\n')){{if(!l.startsWith('data:'))continue;const d=l.slice(5).trim();if(d==='[DONE]')continue;try{{const j=JSON.parse(d);if(j.token)f+=j.token;b.innerHTML=M(f)}}catch(_){{}}}}
buf=buf.includes('\\n')?buf.split('\\n').pop():buf;smartScroll();}};
const sm=f.split('---SUGGESTIONS---');if(sm[1]){{const sgs=sm[1].split('\\n').filter(l=>l.trim().startsWith('-')).map(l=>l.replace(/^-\\s*/,''));const qr=Q('#quickReplies');qr.innerHTML=sgs.map(s=>'<span class=chip onclick="document.getElementById(\\'msgInput\\').value=\\''+s.replace(/'/g,'\\\\x27')+'\\';document.getElementById(\\'msgForm\\').dispatchEvent(new Event(\\'submit\\'))">'+s+'</span>').join('')}};
}}catch(e){{b.innerHTML='<span style=color:#fca5a5>Error: '+H(e.message)+'</span> <a href=# onclick="send(\\''+t.replace(/'/g,'\\\\x27')+'\\');return false" style=color:var(--accent);text-decoration:underline>Retry</a>'}};sbb.disabled=false;sbb.textContent='Send';
smartScroll();}}
function smartScroll(){{const t=Q('#thread');if(t.scrollHeight-t.scrollTop-t.clientHeight<200)t.scrollTop=t.scrollHeight}}
function clearChat(){{Q('#thread').innerHTML='';localStorage.removeItem('vp_trip')}}
i();setTimeout(()=>{{if(!sb)Q('#thread').innerHTML='<div style=padding:20px;color:var(--muted)>Loading services… please wait or <a href=# onclick=location.reload() style=color:var(--accent)>refresh</a></div>'}},5000);const p=new URL(W.location);tripId=p.searchParams.get('trip')||localStorage.getItem('vp_trip');if(tripId)loadHistory();const q=p.searchParams.get('q');
Q('#msgForm').onsubmit=e=>{{e.preventDefault();const v=Q('#msgInput').value.trim();if(!v)return;Q('#msgInput').value='';Q('#quickReplies').innerHTML='';send(v)}};
if(q){{p.searchParams.delete('q');history.replaceState(null,'',p.toString());send(q)}}
</script></body></html>"""

def page_auth_callback() -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Signing in…</title><style>body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0a0f17;color:#fff;font-family:sans-serif;text-align:center}}.muted{{color:rgba(255,255,255,.5);font-size:14px}}</style>{_inject_config()}</head><body>
<div><div style="font-size:18px;font-weight:650;margin-bottom:8px">Signing in…</div><div class="muted">Redirecting…</div></div>
<script src="https://esm.sh/@supabase/supabase-js@2"></script>
<script>
(async()=>{{
const sb=supabase.createClient(window.__SUPABASE_CONFIG__.supabase_url,window.__SUPABASE_CONFIG__.supabase_anon_key);
const{{data,error}}=await sb.auth.getSession();
if(data?.session){{localStorage.setItem('visepanda_session',JSON.stringify(data.session));location.href='/chat'}}
else{{setTimeout(()=>location.href='/',3000)}}
}})();
</script></body></html>"""

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


@app.get("/api/health")
def health():
    return {"ok": True, "version": "0.1.0", "db": "postgres" if DB_URL else "sqlite"}

@app.get("/favicon.ico")
@app.get("/favicon.png")
def favicon():
    return Response(status_code=204)


@app.get("/", response_class=HTMLResponse)
def landing():
    return page_landing()


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
            trip = Trip(id=payload.trip_id, user_id=user_id)
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
    return HTMLResponse('<html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>404 — VisePanda</title><style>body{display:flex;align-items:center;justify-content:center;min-height:100vh;background:#0a0f17;color:#fff;font-family:sans-serif;text-align:center;margin:0}h1{font-size:48px;margin:0;letter-spacing:-.02em}p{color:rgba(255,255,255,.5)}a{color:#7dd3fc}</style><h1>🐼</h1><p>Page not found</p><a href=/>Back home</a>', status_code=404)


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

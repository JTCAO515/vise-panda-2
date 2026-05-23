"""
VisePanda — China Travel AI Agent
Single-file FastAPI app. No static frontend files.
Supabase config is server-injected into HTML.
LLM: GLM 5.1 (ZhipuAI, OpenAI-compatible).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
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

SYSTEM_PROMPT = """You are VisePanda 🐼, a friendly China travel assistant.
Be concise, helpful, and conversational. Recommend specific places, foods, and practical tips.
When giving itineraries, format them nicely with clear day-by-day structure.
Suggest quick follow-up questions at the end of long responses, prefixed with '---SUGGESTIONS---'.
Always respond in the same language as the user's message."""

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
.btn-accent:hover{background:rgba(125,211,252,.20)}
footer{position:fixed;left:0;right:0;bottom:0;padding:10px 16px;border-top:1px solid var(--line);background:rgba(8,10,14,.55);backdrop-filter:blur(10px);font-size:12px;color:var(--muted);z-index:1}
input[type=text]{border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.03);color:var(--text);padding:12px 16px;outline:none;font-size:14px}
input[type=text]:focus{border-color:rgba(125,211,252,.35);box-shadow:0 0 0 4px rgba(125,211,252,.12)}
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
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VisePanda — China Travel Agent</title><style>{CSS}</style>{_inject_config()}</head><body>
<div class="bg-shanshui"></div>
<header><div><span class="dot"></span><span class="name">VisePanda</span></div><div id="authArea"><a href="#" onclick="event.preventDefault();signIn()" class="btn btn-accent">Sign in</a></div></header>
<main style="position:relative;min-height:calc(100vh-56px);display:flex;align-items:center;justify-content:center;padding:24px 16px 90px;z-index:1">
<div style="width:min(640px,96%);text-align:center">
<h1 style="font-size:34px;margin:0 0 8px;letter-spacing:-.02em">Plan your China trip 🐼</h1>
<p style="color:var(--muted);margin:0 0 24px;line-height:1.5">Ask less, chat more. Just tell me where and how long.</p>
<form onsubmit="event.preventDefault();const t=document.getElementById('q').value.trim();const id='t_'+crypto.randomUUID();const u=new URL('/chat',location);u.searchParams.set('trip',id);if(t)u.searchParams.set('q',t);location.href=u.toString()" style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
<input id="q" type="text" placeholder="e.g. Beijing 5 days, food+history, relaxed pace…" style="width:min(480px,88vw);height:48px;padding:0 16px">
<button type="submit" class="btn btn-accent" style="height:48px;padding:0 20px;font-size:14px">Start</button>
</form>
<div style="margin-top:16px;font-size:12px;color:var(--muted)">
<a href="/chat" style="color:var(--muted);text-decoration:none">Open chat</a>
<span style="opacity:.5;padding:0 8px">·</span>
<a href="#" onclick="event.preventDefault();signIn()" style="color:var(--muted);text-decoration:none">Sign in with Google</a>
<span style="opacity:.5;padding:0 8px">·</span>
<span>Continue as guest</span>
</div></div></main>
<footer>Try without login — last 3 trips saved locally. Login to sync across devices.</footer>
<script src="https://esm.sh/@supabase/supabase-js@2"></script>
<script>
let sb=null;
async function initSupabase(){{sb=supabase.createClient(window.__SUPABASE_CONFIG__.supabase_url,window.__SUPABASE_CONFIG__.supabase_anon_key)}}
async function signIn(){{if(!sb)await initSupabase();sb.auth.signInWithOAuth({{provider:'google',options:{{redirectTo:location.origin+'/auth/callback'}}}})}}
initSupabase();
</script></body></html>"""

def page_chat() -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Chat · VisePanda</title><style>{CSS}
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
</style>{_inject_config()}</head><body>
<div class="bg-shanshui"></div>
<header><div><span class="dot"></span><span class="name">VisePanda</span></div><div><a href="/" class="btn">Home</a></div></header>
<div class="layout"><main style="flex:1;display:flex;flex-direction:column"><div id="thread"></div></main></div>
<div class="chat-footer"><div id="quickReplies"></div><form id="msgForm"><input id="msgInput" type="text" placeholder="Type a message…" autofocus><button id="sendBtn" type="submit">Send</button></form></div>
<script src="https://esm.sh/@supabase/supabase-js@2"></script>
<script>
let sb=null,tripId=null;
async function i(){{sb=supabase.createClient(W.__SUPABASE_CONFIG__.supabase_url,W.__SUPABASE_CONFIG__.supabase_anon_key)}}
const W=window,Q=s=>document.querySelector(s),H=s=>s.replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])),M=t=>t.replace(/\\*\\*(.+?)\\*\\*/g,'<b>$1</b>').replace(/\\*(.+?)\\*/g,'<i>$1</i>').replace(/\\n\\n/g,'</p><p>').replace(/\\n/g,'<br>');
function msg(r,c){{const d=document.createElement('div');d.className='msg '+r;d.innerHTML='<div class=bubble>'+M(c)+'</div>';Q('#thread').appendChild(d);Q('#thread').scrollTop=Q('#thread').scrollHeight;return d}}
async function send(t){{msg('user',t);tripId=tripId||'t_'+crypto.randomUUID();const b=msg('bot','<span class=cursor>▊</span>');let f='';try{{
const s=await sb?.auth.getSession();const tok=s?.data?.session?.access_token;const h={{'Content-Type':'application/json'}};if(tok)h['Authorization']='Bearer '+tok;
const r=await fetch('/api/chat',{{method:'POST',headers:h,body:JSON.stringify({{trip_id:tripId,text:t}})}});
const rd=r.body.getReader(),dc=new TextDecoder();let buf='';
while(1){{const{{done,value}}=await rd.read();if(done)break;buf+=dc.decode(value,{{stream:true}});
for(const l of buf.split('\\n')){{if(!l.startsWith('data:'))continue;const d=l.slice(5).trim();if(d==='[DONE]')continue;try{{const j=JSON.parse(d);if(j.token)f+=j.token;b.innerHTML=M(f)}}catch(_){{}}}}
buf=buf.includes('\\n')?buf.split('\\n').pop():buf;Q('#thread').scrollTop=Q('#thread').scrollHeight;}};
const sm=f.split('---SUGGESTIONS---');if(sm[1]){{const sgs=sm[1].split('\\n').filter(l=>l.trim().startsWith('-')).map(l=>l.replace(/^-\\s*/,''));const qr=Q('#quickReplies');qr.innerHTML=sgs.map(s=>'<span class=chip onclick="document.getElementById(\\'msgInput\\').value=\\''+s.replace(/'/g,'\\\\x27')+'\\';document.getElementById(\\'msgForm\\').dispatchEvent(new Event(\\'submit\\'))">'+s+'</span>').join('')}};
}}catch(e){{b.innerHTML='<span style=color:#fca5a5>Error: '+H(e.message)+'</span>'}};
Q('#thread').scrollTop=Q('#thread').scrollHeight;}}
i();const p=new URL(W.location);tripId=p.searchParams.get('trip');const q=p.searchParams.get('q');
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
    return {"ok": True}


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

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": payload.text},
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

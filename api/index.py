"""
VisePanda v3.0.1 — China Travel AI
WSGI handler. Zero pip dependencies (stdlib only).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

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

# ── LLM config (check multiple env var names for compatibility) ──
DEEPSEEK_API_KEY = (os.environ.get("DEEPSEEK_API_KEY", "")
                    or os.environ.get("LLM_API_KEY", ""))
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL",
                 os.environ.get("LLM_MODEL", "deepseek-chat"))
DEEPSEEK_BASE = (os.environ.get("DEEPSEEK_BASE_URL", "")
                 or os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1"))


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

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
    length = int(environ.get("CONTENT_LENGTH", "0") or "0")
    if length <= 0:
        return {}
    raw = environ["wsgi.input"].read(length)
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw) if raw else {}


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

    # Try web/ first, then static/
    for base_dir in (WEB_DIR, STATIC_DIR):
        target = (base_dir / rel).resolve()
        if target.is_file() and _is_relative_to(target, base_dir.resolve()):
            body = target.read_bytes()
            ct = MIME.get(target.suffix, "application/octet-stream")
            headers = [
                ("Content-Type", ct),
                ("Content-Length", str(len(body))),
            ]
            # Cache static assets aggressively, not HTML
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


# ════════════════════════════════════════════════════════════
# CHAT SSE ENDPOINT
# ════════════════════════════════════════════════════════════

def _handle_chat(environ, start_response):
    """POST /api/chat — SSE streaming chat with DeepSeek V4 Flash."""
    if not DEEPSEEK_API_KEY:
        return _json_error(start_response, "DEEPSEEK_API_KEY not configured", "503 Service Unavailable")

    params = _read_post(environ)
    messages = params.get("messages", [])
    if not messages:
        return _json_error(start_response, "messages required", "400 Bad Request")

    # Build system prompt with knowledge context
    system_prompt = _build_system_prompt(params)

    # Stream response via SSE
    def stream():
        import urllib.request

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        }
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        req = urllib.request.Request(
            f"{DEEPSEEK_BASE}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                buffer = ""
                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break
                    buffer += chunk.decode("utf-8")
                    lines = buffer.split("\n")
                    buffer = lines.pop()  # keep incomplete line

                    for line in lines:
                        line = line.strip()
                        if not line or line == "data: [DONE]":
                            continue
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield _sse_event(json.dumps({"token": content}))
                            except (json.JSONDecodeError, KeyError, IndexError):
                                pass
        except Exception as ex:
            yield _sse_event(json.dumps({"error": str(ex)}), event="error")

        yield _sse_event(json.dumps({"done": True}), event="done")

    headers = [
        ("Content-Type", "text/event-stream"),
        ("Cache-Control", "no-cache"),
        ("Connection", "keep-alive"),
        ("Access-Control-Allow-Origin", "*"),
        ("X-Accel-Buffering", "no"),
    ]
    start_response("200 OK", headers)
    return stream()


def _build_system_prompt(params: dict) -> str:
    """Build system prompt with full knowledge base injection."""
    city = params.get("city", "").lower()
    prompt_parts = [
        "You are VisePanda, an expert AI China travel planner. You have a comprehensive knowledge base of 36 Chinese cities.",
        "",
        "## CORE RULES",
        "- Always use specific, real information from your knowledge base (specific restaurant names, prices, districts)",
        "- When suggesting itineraries, ALWAYS use the structured Day format below",
        "- Be honest: say 'I don't have specific data on that' instead of making things up",
        "- Consider seasonality, weather, and local holidays in your recommendations",
        "- For food recommendations, include specific dish names in both English and Chinese",
        "- Include practical tips: transport options, budget ranges, peak hours to avoid",
        "",
        "## ITINERARY FORMAT",
        "When creating a day-by-day plan, use this exact format:",
        "",
        "**Day 1: [Title]**",
        "- 🕐 Morning: [activity] at [specific location]",
        "- 🕐 Afternoon: [activity] at [specific location]",
        "- 🕐 Evening: [activity] at [specific location]",
        "- 🍽️ Eat: [specific dish] at [restaurant name] (¥[price])",
        "- 🏨 Stay: [recommended area] - [budget/mid/luxury option]",
        "- 💡 Tip: [local insider advice]",
        "",
        "**Day 2: [Title]**",
        "...(same format)...",
        "",
        "## QUICK RECOMMENDATION FORMAT",
        "For quick tips, use:",
        "- 🏙️ **City**: [name] (best season: [season], recommended: [days])",
        "- 🎯 Vibe: [description]",
        "- 🍽️ Must eat: [dish] at [place] (¥[price])",
        "- 💰 Budget tip: [advice]",
        "- 🏨 Stay: [area] - [price range]",
        "",
    ]

    # Inject city-specific knowledge if provided
    if city:
        city_data = _load_json(DATA_DIR / "cities.json") or {}
        food_data = _load_json(DATA_DIR / "food.json") or {}
        hotels_data = _load_json(DATA_DIR / "hotels.json") or {}
        tips_data = _load_json(DATA_DIR / "tips.json") or {}

        info = city_data.get(city)
        if info:
            prompt_parts.append(f"\n## KNOWLEDGE: {city.title()}")
            prompt_parts.append(f"- Name (CN): {info.get('name_cn', '')}")
            prompt_parts.append(f"- Province: {info.get('province', '')}")
            prompt_parts.append(f"- Best season: {info.get('best_season', '')}")
            prompt_parts.append(f"- Recommended stay: {info.get('days', '')}")
            prompt_parts.append(f"- Vibe: {info.get('vibe', '')}")
            prompt_parts.append(f"- Budget tip: {info.get('budget_tip', '')}")
            kw = info.get('keywords', [])
            if kw:
                prompt_parts.append(f"- Keywords: {', '.join(kw[:6])}")

            # Food
            foods = food_data.get(city, [])
            if foods:
                prompt_parts.append(f"\n### Must-eat Foods in {city.title()}")
                for f in foods[:6]:
                    en = f.get('name_en', '')
                    desc = f.get('description', '')
                    price = f.get('price_range', '')
                    must = '⭐ ' if f.get('must_try') else '   '
                    prompt_parts.append(f"{must}{en} ({desc}) {price}")

            # Hotels
            h = hotels_data.get(city, {})
            if h:
                prompt_parts.append(f"\n### Accommodation in {city.title()}")
                b = h.get('budget', {})
                m = h.get('mid', {})
                lx = h.get('luxury', {})
                if b: prompt_parts.append(f"- Budget: {b.get('range','')} — {b.get('desc','')} ({b.get('areas','')})")
                if m: prompt_parts.append(f"- Mid: {m.get('range','')} — {m.get('desc','')} ({m.get('areas','')})")
                if lx: prompt_parts.append(f"- Luxury: {lx.get('range','')} — {lx.get('desc','')} ({lx.get('areas','')})")
                if h.get('tip'): prompt_parts.append(f"- Tip: {h['tip']}")

            # Tips
            tips = tips_data.get(city, [])
            if tips:
                prompt_parts.append(f"\n### Local Tips for {city.title()}")
                for t in tips[:4]:
                    if isinstance(t, dict):
                        prompt_parts.append(f"- {t.get('en','')}: {t.get('tip','')}")
                    else:
                        prompt_parts.append(f"- {t}")

            # Price estimates
            est = ESTIMATE_DATA.get(city)
            if est:
                prompt_parts.append(f"\n### Price Estimates for {city.title()}")
                prompt_parts.append(f"- Budget daily: {est.get('budget_daily', '')}")
                prompt_parts.append(f"- Mid daily: {est.get('mid_daily', '')}")
                prompt_parts.append(f"- Luxury daily: {est.get('luxury_daily', '')}")
                prompt_parts.append(f"- Avg flight: {est.get('flight_avg', '')}")
                prompt_parts.append(f"- Avg meal: {est.get('food_avg', '')}")

    # Add general recommendation guidance
    prompt_parts.append("")
    prompt_parts.append("## POPULAR CITY GUIDE (Quick Reference)")
    prompt_parts.append("Use this to recommend cities based on user preferences:")
    all_cities = _load_json(DATA_DIR / "cities.json") or {}
    for name, info in list(all_cities.items())[:8]:
        vibes = info.get('vibe', '').split('·')[0].strip() if info.get('vibe') else ''
        season = info.get('best_season', '')[:20]
        prompt_parts.append(f"- {name.title()}: {vibes} | Best: {season} | {info.get('days','')}")

    return "\n".join(prompt_parts)


# ════════════════════════════════════════════════════════════
# CITIES API
# ════════════════════════════════════════════════════════════

def _handle_cities(start_response, path: str):
    """GET /api/cities — list all cities. GET /api/cities/:city — city detail."""
    cities = _load_json(DATA_DIR / "cities.json")
    food = _load_json(DATA_DIR / "food.json") or {}
    hotels = _load_json(DATA_DIR / "hotels.json") or {}
    tips = _load_json(DATA_DIR / "tips.json") or {}
    if cities is None:
        return _json_error(start_response, "City data not found")

    parts = path.strip("/").split("/")
    if len(parts) == 2:  # /api/cities
        # Return summary with highlights
        summary = {}
        for name, info in cities.items():
            summary[name] = {
                "name_cn": info.get("name_cn", ""),
                "best_season": info.get("best_season", ""),
                "days": info.get("days", ""),
                "vibe": info.get("vibe", ""),
                "highlights": info.get("highlights", []),
                "image": f"/static/img/city-{name}.jpg" if os.path.exists(
                    os.path.join(os.path.dirname(__file__), "..", "static", "img", f"city-{name}.jpg")
                ) else "",
                "budget_tip": info.get("budget_tip", ""),
            }
        return _json(start_response, {"cities": summary})
    elif len(parts) == 3:  # /api/cities/beijing
        city_name = parts[2]
        if city_name in cities:
            detail = dict(cities[city_name])
            detail["food"] = food.get(city_name, [])
            detail["hotels"] = hotels.get(city_name, {})
            detail["tips"] = tips.get(city_name, [])
            detail["map"] = MAP_DATA.get(city_name, {})
            detail["estimate"] = ESTIMATE_DATA.get(city_name, {})
            return _json(start_response, {"city": detail})
        return _json_error(start_response, f"City '{city_name}' not found", "404 Not Found")
    return _json_error(start_response, "Not found", "404 Not Found")


# ════════════════════════════════════════════════════════════
# TOOLS API
# ════════════════════════════════════════════════════════════

def _handle_tools(start_response, path: str):
    """GET /api/tools — list tools. GET /api/tools/:name — tool detail."""
    parts = path.strip("/").split("/")
    tool_name = parts[2] if len(parts) >= 3 else ""

    tools_index = {
        "packing": "Packing checklist by destination and season",
        "pricing": "Price estimates for transport/accommodation/food",
        "visa": "China visa guide for foreigners",
        "phrases": "Useful Chinese phrases for travelers",
        "emergency": "Emergency contacts and procedures in China",
    }

    if not tool_name:
        return _json(start_response, {"tools": tools_index})

    if tool_name in tools_index:
        data = _load_json(DATA_DIR / "tools.json")
        if data and tool_name in data:
            return _json(start_response, {"tool": data[tool_name]})
        return _json_error(start_response, f"Tool data '{tool_name}' not loaded", "500 Internal Server Error")

    return _json_error(start_response, f"Tool '{tool_name}' not found", "404 Not Found")


# ════════════════════════════════════════════════════════════
# ESTIMATE & VALIDATE API
# ════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════
# MAP & ESTIMATE DATA
# ════════════════════════════════════════════════════════════

MAP_DATA = {
    "beijing": {"lat": 39.9042, "lng": 116.4074, "zoom": 11, "pois": [
        {"name": "Forbidden City", "name_cn": "故宫", "lat": 39.9163, "lng": 116.3972, "type": "history"},
        {"name": "Great Wall (Badaling)", "name_cn": "八达岭长城", "lat": 40.3601, "lng": 116.0114, "type": "landmark"},
        {"name": "Temple of Heaven", "name_cn": "天坛", "lat": 39.8822, "lng": 116.4066, "type": "history"},
        {"name": "Summer Palace", "name_cn": "颐和园", "lat": 39.9999, "lng": 116.2755, "type": "history"},
        {"name": "Wangfujing Night Market", "name_cn": "王府井小吃街", "lat": 39.9133, "lng": 116.4109, "type": "food"},
    ]},
    "shanghai": {"lat": 31.2304, "lng": 121.4737, "zoom": 12, "pois": [
        {"name": "The Bund", "name_cn": "外滩", "lat": 31.2400, "lng": 121.4900, "type": "landmark"},
        {"name": "Yu Garden", "name_cn": "豫园", "lat": 31.2270, "lng": 121.4885, "type": "history"},
        {"name": "Oriental Pearl Tower", "name_cn": "东方明珠", "lat": 31.2400, "lng": 121.5000, "type": "modern"},
        {"name": "Shanghai Disney", "name_cn": "上海迪士尼", "lat": 31.1440, "lng": 121.6590, "type": "entertainment"},
    ]},
    "chengdu": {"lat": 30.5728, "lng": 104.0668, "zoom": 11, "pois": [
        {"name": "Panda Base", "name_cn": "大熊猫繁育基地", "lat": 30.7345, "lng": 104.1442, "type": "nature"},
        {"name": "Jinli Ancient Street", "name_cn": "锦里", "lat": 30.6480, "lng": 104.0470, "type": "culture"},
        {"name": "Kuanzhai Alley", "name_cn": "宽窄巷子", "lat": 30.6680, "lng": 104.0560, "type": "culture"},
        {"name": "Wuhou Shrine", "name_cn": "武侯祠", "lat": 30.6460, "lng": 104.0480, "type": "history"},
    ]},
    "xian": {"lat": 34.3416, "lng": 108.9398, "zoom": 11, "pois": [
        {"name": "Terracotta Warriors", "name_cn": "兵马俑", "lat": 34.3853, "lng": 109.2739, "type": "history"},
        {"name": "Ancient City Wall", "name_cn": "西安城墙", "lat": 34.2610, "lng": 108.9420, "type": "history"},
        {"name": "Muslim Quarter", "name_cn": "回民街", "lat": 34.2620, "lng": 108.9390, "type": "food"},
        {"name": "Big Wild Goose Pagoda", "name_cn": "大雁塔", "lat": 34.2180, "lng": 108.9590, "type": "history"},
    ]},
    "guangzhou": {"lat": 23.1291, "lng": 113.2644, "zoom": 11, "pois": [
        {"name": "Canton Tower", "name_cn": "广州塔", "lat": 23.1065, "lng": 113.3244, "type": "modern"},
        {"name": "Shamian Island", "name_cn": "沙面岛", "lat": 23.1090, "lng": 113.2440, "type": "culture"},
        {"name": "Chen Clan Academy", "name_cn": "陈家祠", "lat": 23.1330, "lng": 113.2570, "type": "history"},
    ]},
    "guilin": {"lat": 25.2736, "lng": 110.2900, "zoom": 11, "pois": [
        {"name": "Li River", "name_cn": "漓江", "lat": 25.2700, "lng": 110.3000, "type": "nature"},
        {"name": "Elephant Trunk Hill", "name_cn": "象鼻山", "lat": 25.2670, "lng": 110.2980, "type": "nature"},
        {"name": "Reed Flute Cave", "name_cn": "芦笛岩", "lat": 25.2870, "lng": 110.2780, "type": "nature"},
    ]},
    "hangzhou": {"lat": 30.2741, "lng": 120.1551, "zoom": 12, "pois": [
        {"name": "West Lake", "name_cn": "西湖", "lat": 30.2590, "lng": 120.1480, "type": "nature"},
        {"name": "Lingyin Temple", "name_cn": "灵隐寺", "lat": 30.2670, "lng": 120.1000, "type": "history"},
        {"name": "Longjing Tea Village", "name_cn": "龙井村", "lat": 30.2240, "lng": 120.1230, "type": "culture"},
    ]},
    "chongqing": {"lat": 29.4316, "lng": 106.9123, "zoom": 11, "pois": [
        {"name": "Hongya Cave", "name_cn": "洪崖洞", "lat": 29.5627, "lng": 106.5810, "type": "culture"},
        {"name": "Yangtze River Cableway", "name_cn": "长江索道", "lat": 29.5650, "lng": 106.5850, "type": "landmark"},
        {"name": "Ciqikou", "name_cn": "磁器口", "lat": 29.5750, "lng": 106.4550, "type": "culture"},
    ]},
}

ESTIMATE_DATA = {
    "beijing": {"budget_daily": "¥300-500", "mid_daily": "¥600-1000", "luxury_daily": "¥1500-3000", "flight_avg": "¥500-1500", "food_avg": "¥30-80/meal"},
    "shanghai": {"budget_daily": "¥350-550", "mid_daily": "¥700-1200", "luxury_daily": "¥2000-4000", "flight_avg": "¥500-1500", "food_avg": "¥35-100/meal"},
    "chengdu": {"budget_daily": "¥200-400", "mid_daily": "¥500-800", "luxury_daily": "¥1200-2500", "flight_avg": "¥400-1200", "food_avg": "¥20-60/meal"},
    "guangzhou": {"budget_daily": "¥250-450", "mid_daily": "¥500-900", "luxury_daily": "¥1500-3000", "flight_avg": "¥400-1200", "food_avg": "¥25-70/meal"},
    "xian": {"budget_daily": "¥200-350", "mid_daily": "¥400-700", "luxury_daily": "¥1000-2000", "flight_avg": "¥400-1000", "food_avg": "¥20-50/meal"},
    "guilin": {"budget_daily": "¥180-300", "mid_daily": "¥350-600", "luxury_daily": "¥800-1800", "flight_avg": "¥400-1000", "food_avg": "¥20-45/meal"},
    "hangzhou": {"budget_daily": "¥250-400", "mid_daily": "¥500-900", "luxury_daily": "¥1500-3000", "flight_avg": "¥400-1200", "food_avg": "¥30-70/meal"},
}


def _handle_estimate(start_response):
    """GET /api/estimate — return price estimates for cities."""
    return _json(start_response, {"estimates": ESTIMATE_DATA})


def _handle_validate(environ, start_response):
    """POST /api/validate — validate a trip plan."""
    try:
        length = int(environ.get("CONTENT_LENGTH", 0))
        body = environ["wsgi.input"].read(length) if length else b"{}"
        data = json.loads(body)
    except (ValueError, json.JSONDecodeError):
        data = {}

    city = data.get("city", "").lower()
    days = data.get("days", 0)

    warnings = []
    tips = []

    # Validate city
    if city and city not in ESTIMATE_DATA:
        warnings.append(f"We don't have detailed pricing data for {city.title()}")

    # Validate days
    if days:
        if days < 1:
            warnings.append("Trip should be at least 1 day")
        elif days > 30:
            warnings.append("Trips over 30 days may need visa planning")

    # Seasonal tips for known cities
    cities_data = _load_json(DATA_DIR / "cities.json") or {}
    if city in cities_data:
        info = cities_data[city]
        season = info.get("best_season", "")
        if season:
            tips.append(f"Best season: {season}")
        if info.get("budget_tip"):
            tips.append(info["budget_tip"])

    return _json(start_response, {
        "valid": len(warnings) == 0,
        "warnings": warnings,
        "tips": tips,
        "city": city,
        "days": days,
    })


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
            "version": "3.0.1",
            "build": "2026-06-14",
        })

    # ── Chat SSE ──
    if path == "/api/chat" and method == "POST":
        return _handle_chat(environ, start_response)

    # ── Cities API ──
    if path.startswith("/api/cities") and method == "GET":
        return _handle_cities(start_response, path)

    # ── Tools API ──
    if path.startswith("/api/tools") and method == "GET":
        return _handle_tools(start_response, path)

    # ── Estimate API ──
    if path == "/api/estimate" and method == "GET":
        return _handle_estimate(start_response)

    # ── Validate API ──
    if path == "/api/validate" and method == "POST":
        return _handle_validate(environ, start_response)

    # ── Static files (web/ + static/) ──
    result = _serve_static(start_response, path)
    if result is not None:
        return result

    # ── 404 fallback ──
    return _json_error(start_response, f"Not found: {path}", "404 Not Found")

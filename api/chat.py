"""VisePanda — SSE Chat API + FAQ Matching + System Prompt Builder."""

import json
import os
import re as _re
import urllib.request as _urllib_request

from api.common import (
    DATA_DIR, STATIC_DIR, _json, _json_error, _load_json, _sse_event,
)

# ── LLM config (check multiple env var names for compatibility) ──
DEEPSEEK_API_KEY = (os.environ.get("DEEPSEEK_API_KEY", "")
                    or os.environ.get("LLM_API_KEY", "")
                    or os.environ.get("AESCULAP_DEEPSEEK_KEY", ""))
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL",
                 os.environ.get("LLM_MODEL", "deepseek-v4-flash"))
DEEPSEEK_BASE = (os.environ.get("DEEPSEEK_BASE_URL", "")
                 or os.environ.get("LLM_BASE_URL", "")
                 or "https://api.deepseek.com/v1")


# ════════════════════════════════════════════════════════════
# FAQ MATCHING ENGINE
# ════════════════════════════════════════════════════════════

_FAQ_CACHE = None

def _load_faq() -> dict:
    global _FAQ_CACHE
    if _FAQ_CACHE is not None:
        return _FAQ_CACHE
    data = _load_json(DATA_DIR / "faq.json")
    _FAQ_CACHE = data or {"categories": []}
    return _FAQ_CACHE


def _tokenize(text: str) -> set:
    tokens = set()
    for word in _re.split(r"[\s,\-./?()\[\]{}!@#$%^&*;:\"'<>]+", text.lower()):
        word = word.strip()
        if len(word) > 1:
            tokens.add(word)
    return tokens


def _match_faq(user_text: str) -> dict | None:
    if not user_text:
        return None
    faq = _load_faq()
    categories = faq.get("categories", [])
    if not categories:
        return None
    tokens = _tokenize(user_text)
    if not tokens:
        return None
    best = None
    best_score = 0
    MIN_SCORE = 1
    for cat in categories:
        patterns = cat.get("patterns", [])
        if not patterns:
            continue
        text_lower = user_text.lower()
        score = 0
        matched_terms = []
        for p in patterns:
            p_lower = p.strip().lower()
            if len(p_lower) <= 2:
                continue
            if p_lower in text_lower:
                score += 1
                matched_terms.append(p_lower)
            if " " in p_lower:
                words_in_pattern = p_lower.split()
                matched_count = sum(1 for w in words_in_pattern if len(w) > 1 and w in tokens)
                if matched_count >= 2:
                    score += 0.3 * matched_count
                    if p_lower not in matched_terms:
                        matched_terms.extend(words_in_pattern[:2])
        if score >= 2:
            density = score / max(len(patterns), 1)
            score += density * 2
        if len(tokens) <= 3 and score >= len(patterns) * 0.3:
            score *= 0.5
        if score > best_score:
            best_score = score
            best = {
                "id": cat.get("id", ""),
                "title": cat.get("title", ""),
                "icon": cat.get("icon", "🐼"),
                "score": round(score, 1),
                "matched_terms": matched_terms[:6],
                "expanded_keywords": cat.get("expanded_keywords", []),
                "prompt_hint": cat.get("prompt_hint", ""),
            }
    if best and best_score >= MIN_SCORE:
        return best
    return None


# ════════════════════════════════════════════════════════════
# IMAGE MARKER HANDLER
# ════════════════════════════════════════════════════════════

def _yield_with_images(content):
    pattern = r'\[img:([a-z_]+)(?:\|([^\]]+))?\]'
    parts = _re.split(pattern, content)
    static_img_dir = str(STATIC_DIR / "img")
    i = 0
    while i < len(parts):
        if parts[i]:
            yield _sse_event(json.dumps({"type": "token", "content": parts[i], "token": parts[i]}))
        i += 1
        if i < len(parts):
            key = parts[i]
            label = parts[i + 1] if i + 1 < len(parts) else key.replace('_', ' ').title()
            i += 2
            candidates = [f"{key}.jpg", f"city-{key}.jpg", f"food-{key}.jpg"]
            found = None
            for name in candidates:
                p = os.path.join(static_img_dir, name)
                if os.path.exists(p):
                    found = f"/static/img/{name}"
                    break
            if found:
                yield _sse_event(json.dumps({"type": "image", "content": {
                    "key": key, "url": found, "label": label,
                }}))
            else:
                yield _sse_event(json.dumps({"type": "token", "content": f"[{label}]", "token": f"[{label}]"}))


# ════════════════════════════════════════════════════════════
# SYSTEM PROMPT BUILDER
# ════════════════════════════════════════════════════════════

def _build_system_prompt(params: dict, faq_match: dict | None = None) -> str:
    from api.cities import ESTIMATE_DATA

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
        "- Be concise and direct. Organize information into clear sections with ### headers.",
    ]
    if faq_match:
        prompt_parts.append("")
        prompt_parts.append(f"## QUESTION INTENT: {faq_match['title']}")
        prompt_parts.append(f"The user's question relates to '{faq_match['title']}'.")
        keywords = faq_match.get("expanded_keywords", [])
        if keywords:
            prompt_parts.append("Relevant topics to cover:")
            for i, kw in enumerate(keywords[:6], 1):
                prompt_parts.append(f"  {i}. {kw}")
        hint = faq_match.get("prompt_hint", "")
        if hint:
            prompt_parts.append("Answering guidance:")
            prompt_parts.append(hint)

    prompt_parts.extend([
        "",
        "## ITINERARY FORMAT",
        "**Day 1: [Title]**",
        "- 🕐 Morning: [activity] at [specific location]",
        "- 🕐 Afternoon: [activity] at [specific location]",
        "- 🕐 Evening: [activity] at [specific location]",
        "- 🍽️ Eat: [specific dish] at [restaurant name] (¥[price])",
        "- 🏨 Stay: [recommended area] - [budget/mid/luxury option]",
        "- 💡 Tip: [local insider advice]",
    ])

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

            foods = food_data.get(city, [])
            if foods:
                prompt_parts.append(f"\n### Must-eat Foods in {city.title()}")
                for f in foods[:6]:
                    prompt_parts.append(f"{'⭐ ' if f.get('must_try') else '   '}{f.get('name_en','')} ({f.get('description','')}) {f.get('price_range','')}")

            h = hotels_data.get(city, {})
            if h:
                prompt_parts.append(f"\n### Accommodation in {city.title()}")
                for tier, label in [("budget", "Budget"), ("mid", "Mid"), ("luxury", "Luxury")]:
                    t = h.get(tier, {})
                    if t:
                        prompt_parts.append(f"- {label}: {t.get('range','')} — {t.get('desc','')} ({t.get('areas','')})")
                if h.get('tip'):
                    prompt_parts.append(f"- Tip: {h['tip']}")

            tips = tips_data.get(city, [])
            if tips:
                prompt_parts.append(f"\n### Local Tips for {city.title()}")
                for t in tips[:4]:
                    if isinstance(t, dict):
                        prompt_parts.append(f"- {t.get('en','')}: {t.get('tip','')}")
                    else:
                        prompt_parts.append(f"- {t}")

            est = ESTIMATE_DATA.get(city)
            if est:
                prompt_parts.append(f"\n### Price Estimates for {city.title()}")
                prompt_parts.append(f"- Budget daily: {est.get('budget_daily', '')}")
                prompt_parts.append(f"- Mid daily: {est.get('mid_daily', '')}")
                prompt_parts.append(f"- Luxury daily: {est.get('luxury_daily', '')}")

    prompt_parts.append("\n## POPULAR CITY GUIDE (Quick Reference)")
    all_cities = _load_json(DATA_DIR / "cities.json") or {}
    for name, info in list(all_cities.items())[:8]:
        vibes = info.get('vibe', '').split('·')[0].strip() if info.get('vibe') else ''
        season = info.get('best_season', '')[:20]
        prompt_parts.append(f"- {name.title()}: {vibes} | Best: {season} | {info.get('days','')}")

    return "\n".join(prompt_parts)


# ════════════════════════════════════════════════════════════
# CHAT SSE HANDLER
# ════════════════════════════════════════════════════════════

def handle_chat(environ, start_response):
    """POST /api/chat — SSE streaming chat with DeepSeek V4 Flash."""
    if not DEEPSEEK_API_KEY:
        return _json_error(start_response, "DEEPSEEK_API_KEY not configured", "503 Service Unavailable")

    from api.common import _read_post
    params = _read_post(environ)
    messages = params.get("messages", [])
    if not messages:
        return _json_error(start_response, "messages required", "400 Bad Request")

    latest_user = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            latest_user = msg.get("content", "")
            break
    faq_match = _match_faq(latest_user)
    system_prompt = _build_system_prompt(params, faq_match=faq_match)

    def stream():
        if faq_match:
            yield _sse_event(json.dumps({"type": "faq", "content": json.dumps(faq_match), "faq": faq_match}))

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
        req = _urllib_request.Request(
            f"{DEEPSEEK_BASE}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with _urllib_request.urlopen(req, timeout=60) as resp:
                buffer = ""
                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break
                    buffer += chunk.decode("utf-8", errors="replace")
                    lines = buffer.split("\n")
                    buffer = lines.pop()
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
                                    if "---SPLIT---" in content:
                                        parts = content.split("---SPLIT---")
                                        for i, part in enumerate(parts):
                                            if part:
                                                yield from _yield_with_images(part)
                                            if i < len(parts) - 1:
                                                yield _sse_event(json.dumps({"type": "split", "content": "---SEPARATOR---", "split": True}))
                                    else:
                                        yield from _yield_with_images(content)
                            except (json.JSONDecodeError, KeyError, IndexError):
                                pass
        except Exception as ex:
            yield _sse_event(json.dumps({"type": "error", "content": str(ex)}), event="error")
        yield _sse_event(json.dumps({"done": True}), event="done")

    headers_out = [
        ("Content-Type", "text/event-stream"),
        ("Cache-Control", "no-cache"),
        ("Connection", "keep-alive"),
        ("Access-Control-Allow-Origin", "*"),
        ("X-Accel-Buffering", "no"),
    ]
    start_response("200 OK", headers_out)
    return stream()

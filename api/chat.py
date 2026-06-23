import json
import os
import urllib.error
import urllib.request
from http import HTTPStatus

from api.cities import all_cities
from api.common import cors_headers, error_response, json_response, read_json


SYSTEM_BRIEF = (
    "You are VisePanda, an English-language China travel assistant. "
    "Give practical, safety-aware planning help for international visitors."
)

CHAT_MODES = {
    "itinerary": {
        "label": "Itinerary strategist",
        "instruction": "Build a realistic day-by-day route with sequencing, rail or flight logic, daily pacing, meal ideas, and what to skip.",
    },
    "entry": {
        "label": "Entry and visa analyst",
        "instruction": "Focus on passport, visa, transit, customs, payment readiness, documents, and what the traveler must verify before booking.",
    },
    "budget": {
        "label": "Budget analyst",
        "instruction": "Break down costs by lodging, food, transport, attractions, payment setup, and cost-control tradeoffs.",
    },
    "transit": {
        "label": "Transit planner",
        "instruction": "Compare high-speed rail, flights, airport transfers, metro, taxi, DiDi, walking time, and booking friction for foreigners.",
    },
    "food": {
        "label": "Food and culture guide",
        "instruction": "Recommend local dishes, dining areas, etiquette, dietary issues, timing, and ordering tips.",
    },
    "safety": {
        "label": "Safety and readiness checker",
        "instruction": "Give calm risk checks, emergency numbers, health prep, scam avoidance, insurance, medicine, and offline backup steps.",
    },
    "city-fit": {
        "label": "City fit comparator",
        "instruction": "Compare cities by travel style, season, access, budget, food, culture, nature, English-friendliness, and required days.",
    },
    "custom": {
        "label": "General travel consultant",
        "instruction": "Answer as a practical China travel consultant and ask only the most useful follow-up questions.",
    },
}

DEPTH_INSTRUCTIONS = {
    "quick": "Keep the answer concise, but include the assumptions and the next action.",
    "standard": "Give a structured answer with assumptions, recommendations, tradeoffs, and next steps.",
    "expert": "Be detailed and professional. Include assumptions, decision criteria, scenario branches, and verification checkpoints.",
}


def _provider_routes():
    routes = [
        {
            "id": "auto",
            "label": "Auto route",
            "available": True,
            "model": "best configured route",
            "description": "Uses a configured remote model when available, otherwise the local guide.",
        },
        {
            "id": "local-guide",
            "label": "Local guide",
            "available": True,
            "model": "deterministic local fallback",
            "description": "No external API call; uses curated city and FAQ context.",
        },
        {
            "id": "deepseek",
            "label": "DeepSeek",
            "available": bool(os.environ.get("DEEPSEEK_API_KEY")),
            "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            "description": "Remote chat completions through DeepSeek when DEEPSEEK_API_KEY is configured.",
        },
        {
            "id": "openai-compatible",
            "label": "OpenAI-compatible",
            "available": bool(
                os.environ.get("OPENAI_COMPATIBLE_API_KEY")
                and os.environ.get("OPENAI_COMPATIBLE_BASE_URL")
                and os.environ.get("OPENAI_COMPATIBLE_MODEL")
            ),
            "model": os.environ.get("OPENAI_COMPATIBLE_MODEL", "configure OPENAI_COMPATIBLE_MODEL"),
            "description": "Generic OpenAI-compatible chat completions route for another model provider.",
        },
    ]
    return routes


def chat_options():
    return {
        "modes": [
            {"id": key, "label": value["label"], "description": value["instruction"]}
            for key, value in CHAT_MODES.items()
        ],
        "providers": _provider_routes(),
        "depths": [
            {"id": key, "label": key.capitalize(), "description": value}
            for key, value in DEPTH_INSTRUCTIONS.items()
        ],
    }


def _faq_categories():
    try:
        return read_json_file("faq.json").get("categories", [])
    except (OSError, ValueError, KeyError, AttributeError):
        return []


def read_json_file(filename):
    from api.common import load_json

    return load_json(filename)


def _matched_categories(message, mode):
    text = (message or "").lower()
    matches = []
    mode_map = {
        "entry": "visa",
        "transit": "transport",
        "city-fit": "comparison",
    }
    preferred = mode_map.get(mode, mode)
    for category in _faq_categories():
        patterns = category.get("patterns") or []
        score = 1 if category.get("id") == preferred else 0
        score += sum(1 for pattern in patterns if str(pattern).lower() in text)
        if score:
            matches.append((score, category))
    matches.sort(key=lambda item: item[0], reverse=True)
    return [category for _, category in matches[:3]]


def _matched_cities(message):
    text = (message or "").lower()
    cities = all_cities()
    matches = [city for city in cities if city["name"].lower() in text or city["id"] in text]
    return matches or cities[:4]


def _planning_context(message, mode):
    cities = _matched_cities(message)
    categories = _matched_categories(message, mode)
    city_context = "\n".join(
        "- {name}: {province}; {duration}; best season {season}; vibe {vibe}; highlights {highlights}".format(
            name=city["name"],
            province=city["province"],
            duration=city["duration"],
            season=city["bestSeason"],
            vibe=city["vibe"],
            highlights=", ".join(city["highlights"][:4]),
        )
        for city in cities[:5]
    )
    category_context = "\n".join(
        "- {title}: {hint}".format(title=category.get("title", "Travel topic"), hint=category.get("prompt_hint", ""))
        for category in categories
    )
    return city_context, category_context, cities, categories


def _advisor_prompt(message, mode, depth):
    selected_mode = CHAT_MODES.get(mode, CHAT_MODES["custom"])
    selected_depth = DEPTH_INSTRUCTIONS.get(depth, DEPTH_INSTRUCTIONS["standard"])
    city_context, category_context, _, _ = _planning_context(message, mode)
    return (
        f"{SYSTEM_BRIEF}\n\n"
        f"Consultation mode: {selected_mode['label']}.\n"
        f"Mode instruction: {selected_mode['instruction']}\n"
        f"Depth instruction: {selected_depth}\n\n"
        "Use this app context when relevant:\n"
        f"City context:\n{city_context}\n\n"
        f"Topic context:\n{category_context or '- No specific FAQ topic matched.'}\n\n"
        "Answer format:\n"
        "1. Start with the direct recommendation.\n"
        "2. State assumptions if the traveler did not provide nationality, dates, budget, mobility needs, or travel style.\n"
        "3. Give professional, specific details instead of generic advice.\n"
        "4. Add a short checklist or decision table when useful.\n"
        "5. End with 2 or 3 targeted follow-up questions only if they would materially improve the plan.\n\n"
        f"Traveler question: {message}"
    )


def _fallback_answer(message, mode="custom", depth="standard", route_note=""):
    matches = _matched_cities(message)
    categories = _matched_categories(message, mode)
    city_line = ", ".join(city["name"] for city in matches[:4])
    highlight_line = "; ".join(f"{city['name']}: {', '.join(city['highlights'][:3])}" for city in matches[:3])
    mode_label = CHAT_MODES.get(mode, CHAT_MODES["custom"])["label"]
    category_line = ", ".join(category.get("title", "Travel topic") for category in categories[:3]) or "General travel planning"
    detail_line = "Use a compact route first." if depth == "quick" else "Check timing, entry rules, payment setup, and daily pacing before locking hotels."
    if depth == "expert":
        detail_line = "Compare route logic, entry risk, budget range, transport friction, weather, and backup plans before booking."
    return (
        f"{route_note}"
        f"As your {mode_label.lower()}, I would anchor the answer around {city_line}. "
        f"Relevant planning lens: {category_line}. "
        f"Useful highlights: {highlight_line}. "
        f"{detail_line} "
        "Before departure, prepare passport copies, hotel confirmations, Alipay or WeChat Pay, offline maps, and a backup translation app. "
        "To make this more precise, tell me your nationality, travel month, total days, budget band, and whether food, history, nature, or comfort matters most."
    )


def _chat_completion(endpoint, api_key, model, prompt):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_BRIEF},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.35,
        "stream": False,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=22) as response:
        data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


def _remote_answer(message, provider, mode, depth):
    prompt = _advisor_prompt(message, mode, depth)
    if provider == "deepseek":
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            return None
        return _chat_completion(
            "https://api.deepseek.com/chat/completions",
            api_key,
            os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            prompt,
        )
    if provider == "openai-compatible":
        api_key = os.environ.get("OPENAI_COMPATIBLE_API_KEY")
        base_url = (os.environ.get("OPENAI_COMPATIBLE_BASE_URL") or "").rstrip("/")
        model = os.environ.get("OPENAI_COMPATIBLE_MODEL")
        if not (api_key and base_url and model):
            return None
        endpoint = base_url if base_url.endswith("/chat/completions") else f"{base_url}/chat/completions"
        return _chat_completion(endpoint, api_key, model, prompt)
    return None


def _answer_with_route(message, requested_provider, mode, depth):
    routes = {route["id"]: route for route in _provider_routes()}
    selected = requested_provider if requested_provider in routes else "auto"
    remote_order = ["deepseek", "openai-compatible"]
    if selected in {"deepseek", "openai-compatible"}:
        remote_order = [selected]
    if selected == "local-guide":
        return _fallback_answer(message, mode, depth), routes["local-guide"]

    for provider in remote_order:
        if not routes[provider]["available"]:
            continue
        try:
            answer = _remote_answer(message, provider, mode, depth)
            if answer:
                return answer, routes[provider]
        except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError, TimeoutError, ValueError):
            continue

    route_note = "" if selected == "auto" else f"{routes[selected]['label']} is not configured or did not respond, so I used the local guide. "
    return _fallback_answer(message, mode, depth, route_note), routes["local-guide"]


def _sse(answer, meta=None):
    chunks = []
    if meta:
        chunks.append(f"data: {json.dumps({'meta': meta})}\n\n")
    for word in answer.split(" "):
        chunks.append(f"data: {json.dumps({'token': word + ' '})}\n\n")
    chunks.append(f"data: {json.dumps({'done': True})}\n\n")
    return "".join(chunks)


def dispatch(method, environ, start_response):
    if method == "GET":
        return json_response(start_response, chat_options(), environ=environ)
    if method != "POST":
        return error_response(start_response, HTTPStatus.METHOD_NOT_ALLOWED, "method_not_allowed", "Method not allowed.", environ)
    try:
        body = read_json(environ)
    except ValueError as exc:
        return error_response(start_response, HTTPStatus.BAD_REQUEST, "bad_json", str(exc), environ)

    message = str(body.get("message") or body.get("prompt") or "").strip()
    mode = str(body.get("mode") or "custom").strip()
    provider = str(body.get("provider") or "auto").strip()
    depth = str(body.get("depth") or "standard").strip()
    if not message:
        return error_response(start_response, HTTPStatus.BAD_REQUEST, "message_required", "Message is required.", environ)
    if len(message) > 4000:
        return error_response(start_response, HTTPStatus.BAD_REQUEST, "message_too_long", "Message is too long.", environ)

    answer, route = _answer_with_route(message, provider, mode, depth)
    meta = {
        "provider": route["id"],
        "providerLabel": route["label"],
        "model": route["model"],
        "mode": mode if mode in CHAT_MODES else "custom",
        "modeLabel": CHAT_MODES.get(mode, CHAT_MODES["custom"])["label"],
        "depth": depth if depth in DEPTH_INSTRUCTIONS else "standard",
    }
    headers = [
        ("Content-Type", "text/event-stream; charset=utf-8"),
        ("Cache-Control", "no-cache"),
        ("X-Accel-Buffering", "no"),
    ]
    headers.extend(cors_headers(environ))
    start_response("200 OK", headers)
    return [_sse(answer, meta).encode("utf-8")]


def non_stream_preview(message):
    return {"answer": _fallback_answer(message)}

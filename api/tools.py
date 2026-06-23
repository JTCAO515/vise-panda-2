from http import HTTPStatus

from api.common import clean_text, error_response, json_response, load_json


ESSENTIAL_PACKING = [
    {"label": "Passport and printed copy", "required": True},
    {"label": "Visa or visa-free entry proof", "required": True},
    {"label": "Hotel booking confirmations", "required": True},
    {"label": "Flight and train tickets", "required": True},
    {"label": "Travel insurance", "required": False},
    {"label": "Payment apps set up with card", "required": True},
    {"label": "Offline maps and VPN prepared before arrival", "required": True},
]

PRICE_ESTIMATES = [
    {"label": "Subway ride", "amount": "RMB 3-8"},
    {"label": "High-speed rail, 100 km", "amount": "RMB 45+"},
    {"label": "Simple breakfast", "amount": "RMB 10-20"},
    {"label": "Casual dinner", "amount": "RMB 50-90"},
    {"label": "Boutique hotel", "amount": "RMB 300-700"},
]

PHRASES = [
    {"context": "Taxi", "english": "Please take me to this address.", "pinyin": "qing dai wo qu zhe ge di zhi"},
    {"context": "Dining", "english": "I am allergic to peanuts.", "pinyin": "wo dui hua sheng guo min"},
    {"context": "Transit", "english": "Which station should I get off at?", "pinyin": "wo zai na yi zhan xia che"},
    {"context": "Hotel", "english": "I have a reservation.", "pinyin": "wo yu ding le fang jian"},
    {"context": "Emergency", "english": "Please call an ambulance.", "pinyin": "qing bang wo jiao jiu hu che"},
]

EMERGENCY = {
    "police": "110",
    "fire": "119",
    "ambulance": "120",
    "traffic": "122",
}


def all_tools():
    raw = load_json("tools.json")
    tools = []
    for slug, item in raw.items():
        tools.append({
            "id": slug,
            "name": clean_text(item.get("name")) or slug.replace("_", " ").title(),
            "description": clean_text(item.get("desc")),
            "featured": slug in {"packing", "visa", "phrases", "emergency"},
        })
    return tools


def tool_detail(slug):
    slug = (slug or "").lower()
    if slug == "packing":
        return {"id": slug, "name": "Packing Checklist", "items": ESSENTIAL_PACKING}
    if slug == "pricing":
        return {"id": slug, "name": "Price Estimates", "items": PRICE_ESTIMATES}
    if slug == "phrases":
        return {"id": slug, "name": "Useful Chinese Phrases", "items": PHRASES}
    if slug == "emergency":
        return {"id": slug, "name": "Emergency Info", "numbers": EMERGENCY}
    if slug == "visa":
        return {"id": slug, "name": "China Visa Guide", "summary": "Check nationality rules, entry duration, required documents, and transit options before booking."}
    for tool in all_tools():
        if tool["id"] == slug:
            return tool
    return None


def dispatch(method, path_parts, environ, start_response):
    if method != "GET":
        return error_response(start_response, HTTPStatus.METHOD_NOT_ALLOWED, "method_not_allowed", "Method not allowed.", environ)
    if len(path_parts) == 2:
        tools = all_tools()
        return json_response(start_response, {"tools": tools, "count": len(tools)}, environ=environ)
    if len(path_parts) == 3:
        detail = tool_detail(path_parts[2])
        if not detail:
            return error_response(start_response, HTTPStatus.NOT_FOUND, "tool_not_found", "Tool not found.", environ)
        return json_response(start_response, {"tool": detail}, environ=environ)
    return error_response(start_response, HTTPStatus.NOT_FOUND, "not_found", "Endpoint not found.", environ)

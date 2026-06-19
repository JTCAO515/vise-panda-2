"""VisePanda — Tools API handler."""

from api.common import DATA_DIR, _json, _json_error, _load_json


def handle_tools(start_response, path: str):
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

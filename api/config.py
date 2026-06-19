"""VisePanda — Map & Client Config API handlers."""

import os

from api.common import DATA_DIR, _json, _load_json
from api.cities import _MAP_DATA
from api.index import APP_VERSION


def handle_map(start_response):
    """GET /api/map — return coordinates for all cities with map data."""
    cities = _load_json(DATA_DIR / "cities.json") or {}
    result = {}
    for name in cities:
        if name in _MAP_DATA:
            m = _MAP_DATA[name]
            result[name] = {"lat": m["lat"], "lng": m["lng"]}
    return _json(start_response, {"cities": result})


def handle_config(start_response):
    """GET /api/config — expose client-safe config (AMap key, etc.)."""
    amap_key = os.environ.get("AMAP_KEY", "")
    amap_security = os.environ.get("AMAP_SECURITY_CODE", "")
    google_client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    use_amap = bool(amap_key and amap_security)
    return _json(start_response, {
        "amap_key": amap_key if use_amap else "",
        "amap_security_code": amap_security if use_amap else "",
        "use_amap": use_amap,
        "version": APP_VERSION,
        "google_client_id": google_client_id,
    })

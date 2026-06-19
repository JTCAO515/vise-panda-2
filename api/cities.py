"""VisePanda — Cities, Estimate & Validate API handlers."""

from api.common import (
    DATA_DIR, STATIC_DIR, _json, _json_error, _load_json,
)

# ════════════════════════════════════════════════════════════
# ESTIMATE DATA
# ════════════════════════════════════════════════════════════

ESTIMATE_DATA = {
    "beijing": {"budget_daily": "¥300-500", "mid_daily": "¥600-1000", "luxury_daily": "¥1500-3000", "flight_avg": "¥500-1500", "food_avg": "¥30-80/meal"},
    "shanghai": {"budget_daily": "¥350-550", "mid_daily": "¥700-1200", "luxury_daily": "¥2000-4000", "flight_avg": "¥500-1500", "food_avg": "¥35-100/meal"},
    "chengdu": {"budget_daily": "¥200-400", "mid_daily": "¥500-800", "luxury_daily": "¥1200-2500", "flight_avg": "¥400-1200", "food_avg": "¥20-60/meal"},
    "guangzhou": {"budget_daily": "¥250-450", "mid_daily": "¥500-900", "luxury_daily": "¥1500-3000", "flight_avg": "¥400-1200", "food_avg": "¥25-70/meal"},
    "xian": {"budget_daily": "¥200-350", "mid_daily": "¥400-700", "luxury_daily": "¥1000-2000", "flight_avg": "¥400-1000", "food_avg": "¥20-50/meal"},
    "guilin": {"budget_daily": "¥180-300", "mid_daily": "¥350-600", "luxury_daily": "¥800-1800", "flight_avg": "¥400-1000", "food_avg": "¥20-45/meal"},
    "hangzhou": {"budget_daily": "¥250-400", "mid_daily": "¥500-900", "luxury_daily": "¥1500-3000", "flight_avg": "¥400-1200", "food_avg": "¥30-70/meal"},
}


# ════════════════════════════════════════════════════════════
# CITIES API
# ════════════════════════════════════════════════════════════

def handle_cities(start_response, path: str):
    """GET /api/cities — list all cities. GET /api/cities/:city — city detail."""
    cities = _load_json(DATA_DIR / "cities.json")
    food = _load_json(DATA_DIR / "food.json") or {}
    hotels = _load_json(DATA_DIR / "hotels.json") or {}
    tips = _load_json(DATA_DIR / "tips.json") or {}
    if cities is None:
        return _json_error(start_response, "City data not found")

    parts = path.strip("/").split("/")
    if len(parts) == 2:  # /api/cities
        summary = {}
        for name, info in cities.items():
            summary[name] = {
                "name_en": info.get("name_en", ""),
                "name_cn": info.get("name_cn", ""),
                "best_season": info.get("best_season", ""),
                "days": info.get("days", ""),
                "vibe": info.get("vibe", ""),
                "province": info.get("province", ""),
                "highlights": info.get("highlights", []),
                "image": f"/static/img/city-{name}.jpg" if (
                    STATIC_DIR / "img" / f"city-{name}.jpg"
                ).is_file() else "",
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
            detail["map"] = _MAP_DATA.get(city_name, {})
            detail["estimate"] = ESTIMATE_DATA.get(city_name, {})
            return _json(start_response, {"city": detail})
        return _json_error(start_response, f"City '{city_name}' not found", "404 Not Found")
    return _json_error(start_response, "Not found", "404 Not Found")


# ════════════════════════════════════════════════════════════
# MAP DATA
# ════════════════════════════════════════════════════════════

_MAP_DATA = {
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
    "shenzhen": {"lat": 22.5431, "lng": 114.0579, "zoom": 11},
    "nanjing": {"lat": 32.0603, "lng": 118.7969, "zoom": 11},
    "suzhou": {"lat": 31.2990, "lng": 120.5853, "zoom": 11},
    "wuhan": {"lat": 30.5928, "lng": 114.3055, "zoom": 11},
    "changsha": {"lat": 28.2282, "lng": 112.9388, "zoom": 11},
    "xiamen": {"lat": 24.4798, "lng": 118.0894, "zoom": 11},
    "qingdao": {"lat": 36.0671, "lng": 120.3826, "zoom": 11},
    "kunming": {"lat": 25.0389, "lng": 102.7183, "zoom": 11},
    "dali": {"lat": 25.5916, "lng": 100.2299, "zoom": 11},
    "lijiang": {"lat": 26.8721, "lng": 100.2299, "zoom": 11},
    "lasa": {"lat": 29.6500, "lng": 91.1000, "zoom": 11},
    "harbin": {"lat": 45.8038, "lng": 126.5350, "zoom": 11},
    "sanya": {"lat": 18.2528, "lng": 109.5120, "zoom": 11},
    "dunhuang": {"lat": 40.1421, "lng": 94.6620, "zoom": 10},
    "luoyang": {"lat": 34.6181, "lng": 112.4540, "zoom": 11},
    "huangshan": {"lat": 30.1330, "lng": 118.1750, "zoom": 11},
    "jiuzhaigou": {"lat": 33.2585, "lng": 104.2380, "zoom": 10},
    "lanzhou": {"lat": 36.0611, "lng": 103.8343, "zoom": 11},
    "guiyang": {"lat": 26.6470, "lng": 106.6300, "zoom": 11},
    "xining": {"lat": 36.6171, "lng": 101.7781, "zoom": 11},
    "hohhot": {"lat": 40.8422, "lng": 111.7498, "zoom": 11},
    "nanchang": {"lat": 28.6829, "lng": 115.8582, "zoom": 11},
    "fuzhou": {"lat": 26.0745, "lng": 119.2965, "zoom": 11},
    "macau": {"lat": 22.1987, "lng": 113.5439, "zoom": 12},
    "taipei": {"lat": 25.0330, "lng": 121.5654, "zoom": 11},
    "hainan": {"lat": 19.5664, "lng": 109.9497, "zoom": 9},
    "tibet": {"lat": 29.6500, "lng": 91.1000, "zoom": 7},
    "yunnan": {"lat": 25.0389, "lng": 102.7183, "zoom": 7},
    "zhangjiajie": {"lat": 29.3470, "lng": 110.4780, "zoom": 11},
}


# ════════════════════════════════════════════════════════════
# COMPARE API
# ════════════════════════════════════════════════════════════

def handle_cities_compare(environ, start_response):
    """GET /api/cities/compare?cities=beijing,chengdu — side-by-side comparison."""
    from urllib.parse import parse_qs
    from api.common import _json

    qs = environ.get("QUERY_STRING", "")
    params = parse_qs(qs)
    city_names = params.get("cities", [""])[0].split(",")
    city_names = [c.strip().lower() for c in city_names if c.strip()]

    if len(city_names) < 2:
        return _json(start_response, {"error": "Provide at least 2 cities via ?cities=a,b"}, "400 Bad Request")

    raw_data = _load_json(DATA_DIR / "cities.json") or {}
    cities_data = raw_data if isinstance(raw_data, dict) else {}

    # Build a lookup: name_en/cn → data
    lookup = {}
    for key, val in cities_data.items():
        if isinstance(val, dict):
            lookup[key.lower()] = val
            lookup[val.get("name_en", "").lower()] = val
            lookup[val.get("name_cn", "").lower()] = val

    comparisons = {"cities": [], "fields": {}}

    for name in city_names:
        # Try direct match
        raw = cities_data.get(name) or lookup.get(name)
        if raw is None:
            # Try partial match in name_en or name_cn
            for k, v in cities_data.items():
                if not isinstance(v, dict):
                    continue
                en = v.get("name_en", "").lower()
                cn = v.get("name_cn", "").lower()
                if name in en or name in cn or en in name or cn in name:
                    raw = v
                    break

        entry = {
            "name_en": "Unknown",
            "name_cn": "",
            "vibe": None,
            "best_season": None,
            "days": None,
            "budget_tip": None,
            "province": None,
            "highlights": [],
            "keywords": [],
            "found": raw is not None,
        }

        if raw and isinstance(raw, dict):
            for k in ("name_en", "name_cn", "vibe", "best_season", "days", "budget_tip", "province"):
                entry[k] = raw.get(k, entry[k])
            entry["highlights"] = raw.get("highlights", [])
            entry["keywords"] = raw.get("keywords", [])

        comparisons["cities"].append(entry)

    return _json(start_response, {"comparisons": comparisons})


# ════════════════════════════════════════════════════════════
# ESTIMATE API
# ════════════════════════════════════════════════════════════

def handle_estimate(start_response):
    """GET /api/estimate — return price estimates for cities."""
    return _json(start_response, {"estimates": ESTIMATE_DATA})


# ════════════════════════════════════════════════════════════
# VALIDATE API
# ════════════════════════════════════════════════════════════

def handle_validate(environ, start_response):
    """POST /api/validate — validate a trip plan."""
    from api.common import _read_post
    data = _read_post(environ)
    city = data.get("city", "").lower()
    days = data.get("days", 0)

    warnings = []
    tips = []

    if city and city not in ESTIMATE_DATA:
        warnings.append(f"We don't have detailed pricing data for {city.title()}")
    if days:
        if days < 1:
            warnings.append("Trip should be at least 1 day")
        elif days > 30:
            warnings.append("Trips over 30 days may need visa planning")

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

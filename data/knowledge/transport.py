"""Major China city-to-city transport data: high-speed rail + flight."""
import json

# High-speed rail (G-trains): key routes, duration, frequency
HSR_ROUTES = {
    "Beijing-Shanghai": {"type": "High-speed Rail (高铁)", "duration": "4.5h", "frequency": "Every 10–20 min (每10-20分钟一班)", "price": "2nd class ¥555, 1st class ¥940 (二等座¥555, 一等座¥940)"},
    "Beijing-Guangzhou": {"type": "High-speed Rail (高铁)", "duration": "8h", "frequency": "Every ~30 min (每30分钟一班)", "price": "2nd class ¥860, 1st class ¥1380 (二等座¥860, 一等座¥1380)"},
    "Beijing-Chengdu": {"type": "High-speed Rail (高铁)", "duration": "7.5h", "frequency": "~20 trains/day (每天约20班)", "price": "2nd class ¥780, 1st class ¥1250 (二等座¥780, 一等座¥1250)"},
    "Beijing-Xi'an": {"type": "High-speed Rail (高铁)", "duration": "4.5h", "frequency": "Every ~30 min (每30分钟一班)", "price": "2nd class ¥515, 1st class ¥825 (二等座¥515, 一等座¥825)"},
    "Beijing-Hangzhou": {"type": "High-speed Rail (高铁)", "duration": "4.5h", "frequency": "Every 20–30 min (每20-30分钟一班)", "price": "2nd class ¥625, 1st class ¥1055 (二等座¥625, 一等座¥1055)"},
    "Shanghai-Guangzhou": {"type": "High-speed Rail (高铁)", "duration": "7h", "frequency": "~15/day (每天约15班)", "price": "2nd class ¥790, 1st class ¥1270 (二等座¥790, 一等座¥1270)"},
    "Shanghai-Chengdu": {"type": "High-speed Rail (高铁)", "duration": "11h", "frequency": "~10/day (每天约10班)", "price": "2nd class ¥910, 1st class ¥1460 (二等座¥910, 一等座¥1460)"},
    "Shanghai-Xi'an": {"type": "High-speed Rail (高铁)", "duration": "6h", "frequency": "~15/day (每天约15班)", "price": "2nd class ¥670, 1st class ¥1070 (二等座¥670, 一等座¥1070)"},
    "Shanghai-Hangzhou": {"type": "High-speed Rail (高铁)", "duration": "1h", "frequency": "Every 5–10 min (每5-10分钟一班)", "price": "2nd class ¥73, 1st class ¥124 (二等座¥73, 一等座¥124)"},
    "Shanghai-Nanjing": {"type": "High-speed Rail (高铁)", "duration": "1h", "frequency": "Every 5–10 min (每5-10分钟一班)", "price": "2nd class ¥135, 1st class ¥230 (二等座¥135, 一等座¥230)"},
    "Guangzhou-Shenzhen": {"type": "High-speed Rail (高铁)", "duration": "0.5h", "frequency": "Every ~5 min (每5分钟一班)", "price": "2nd class ¥75, 1st class ¥130 (二等座¥75, 一等座¥130)"},
    "Guangzhou-Chengdu": {"type": "High-speed Rail (高铁)", "duration": "9h", "frequency": "~10/day (每天约10班)", "price": "2nd class ¥620, 1st class ¥990 (二等座¥620, 一等座¥990)"},
    "Guangzhou-Guilin": {"type": "High-speed Rail (高铁)", "duration": "2.5h", "frequency": "~20 trains/day (每天约20班)", "price": "2nd class ¥185, 1st class ¥295 (二等座¥185, 一等座¥295)"},
    "Chengdu-Chongqing": {"type": "High-speed Rail (高铁)", "duration": "1.5h", "frequency": "Every ~15 min (每15分钟一班)", "price": "2nd class ¥155, 1st class ¥245 (二等座¥155, 一等座¥245)"},
    "Chengdu-Xi'an": {"type": "High-speed Rail (高铁)", "duration": "3.5h", "frequency": "~15/day (每天约15班)", "price": "2nd class ¥285, 1st class ¥455 (二等座¥285, 一等座¥455)"},
    "Chengdu-Kunming": {"type": "High-speed Rail (高铁)", "duration": "6h", "frequency": "~10/day (每天约10班)", "price": "2nd class ¥525, 1st class ¥840 (二等座¥525, 一等座¥840)"},
    "Xi'an-Lanzhou": {"type": "High-speed Rail (高铁)", "duration": "3h", "frequency": "~10/day (每天约10班)", "price": "2nd class ¥230, 1st class ¥370 (二等座¥230, 一等座¥370)"},
    "Wuhan-Changsha": {"type": "High-speed Rail (高铁)", "duration": "1.5h", "frequency": "每10-15分钟一班", "price": "2nd class ¥110, 1st class ¥180 (二等座¥110, 一等座¥180)"},
    "Wuhan-Nanjing": {"type": "High-speed Rail (高铁)", "duration": "3h", "frequency": "~20 trains/day (每天约20班)", "price": "2nd class ¥255, 1st class ¥410 (二等座¥255, 一等座¥410)"},
    "Guilin-Guangzhou": {"type": "High-speed Rail (高铁)", "duration": "2.5h", "frequency": "~20 trains/day (每天约20班)", "price": "2nd class ¥185, 1st class ¥295 (二等座¥185, 一等座¥295)"},
    "Guilin-HK": {"type": "High-speed Rail (高铁)", "duration": "3h", "frequency": "~6/day (每天约6班)", "price": "2nd class ¥380, 1st class ¥610 (二等座¥380, 一等座¥610)"},
    "HK-Guangzhou": {"type": "High-speed Rail (高铁)", "duration": "1h", "frequency": "Every ~15 min (每15分钟一班)", "price": "2nd class ¥215, 1st class ¥345 (二等座¥215, 一等座¥345)"},
}

# Domestic flights: key routes
FLIGHT_ROUTES = {
    "Beijing-Shanghai": {"type": "Flight (飞机)", "duration": "2.5h", "frequency": "Every ~30 min (每30分钟一班)", "price": "Economy ¥600-1200 (经济舱¥600-1200)"},
    "Beijing-Guangzhou": {"type": "Flight (飞机)", "duration": "3h", "frequency": "Every ~1h (每小时一班)", "price": "Economy ¥800-1500 (经济舱¥800-1500)"},
    "Beijing-Chengdu": {"type": "Flight (飞机)", "duration": "3h", "frequency": "Every ~1h (每小时一班)", "price": "Economy ¥700-1300 (经济舱¥700-1300)"},
    "Beijing-Kunming": {"type": "Flight (飞机)", "duration": "4h", "frequency": "~15/day (每天约15班)", "price": "Economy ¥900-1600 (经济舱¥900-1600)"},
    "Beijing-Lhasa": {"type": "Flight (飞机)", "duration": "4.5h", "frequency": "~8/day (每天约8班)", "price": "Economy ¥1500-2500 (经济舱¥1500-2500)"},
    "Beijing-Urumqi": {"type": "Flight (飞机)", "duration": "4h", "frequency": "~10/day (每天约10班)", "price": "Economy ¥1000-1800 (经济舱¥1000-1800)"},
    "Shanghai-Guangzhou": {"type": "Flight (飞机)", "duration": "2.5h", "frequency": "Every ~1h (每小时一班)", "price": "Economy ¥600-1100 (经济舱¥600-1100)"},
    "Shanghai-Chengdu": {"type": "Flight (飞机)", "duration": "3.5h", "frequency": "~15/day (每天约15班)", "price": "Economy ¥700-1300 (经济舱¥700-1300)"},
    "Shanghai-Kunming": {"type": "Flight (飞机)", "duration": "3.5h", "frequency": "~12/day (每天约12班)", "price": "Economy ¥800-1400 (经济舱¥800-1400)"},
    "Shanghai-Xi'an": {"type": "Flight (飞机)", "duration": "2.5h", "frequency": "~15/day (每天约15班)", "price": "Economy ¥500-1000 (经济舱¥500-1000)"},
    "Guangzhou-Chengdu": {"type": "Flight (飞机)", "duration": "2.5h", "frequency": "~12/day (每天约12班)", "price": "Economy ¥500-1000 (经济舱¥500-1000)"},
    "Guangzhou-Kunming": {"type": "Flight (飞机)", "duration": "2.5h", "frequency": "~12/day (每天约12班)", "price": "Economy ¥500-900 (经济舱¥500-900)"},
    "Chengdu-Kunming": {"type": "Flight (飞机)", "duration": "1.5h", "frequency": "~10/day (每天约10班)", "price": "Economy ¥400-800 (经济舱¥400-800)"},
    "Chengdu-Lhasa": {"type": "Flight (飞机)", "duration": "2.5h", "frequency": "~8/day (每天约8班)", "price": "Economy ¥1200-2000 (经济舱¥1200-2000)"},
    "Guilin-Beijing": {"type": "Flight (飞机)", "duration": "3h", "frequency": "~10/day (每天约10班)", "price": "Economy ¥700-1300 (经济舱¥700-1300)"},
}


def get_transport_between(city_a: str, city_b: str) -> dict:
    """Get transport options between two cities. City names in English."""
    key1 = f"{city_a}-{city_b}"
    key2 = f"{city_b}-{city_a}"
    result = {}
    if key1 in HSR_ROUTES:
        result["hsr"] = HSR_ROUTES[key1]
    elif key2 in HSR_ROUTES:
        result["hsr"] = HSR_ROUTES[key2]
    if key1 in FLIGHT_ROUTES:
        result["flight"] = FLIGHT_ROUTES[key1]
    elif key2 in FLIGHT_ROUTES:
        result["flight"] = FLIGHT_ROUTES[key2]
    return result


def get_transport_summary() -> str:
    """Return a text summary of major routes for LLM prompt."""
    lines = []
    routes = list(HSR_ROUTES.items())[:8] + list(FLIGHT_ROUTES.items())[:8]
    for route, info in routes:
        lines.append(f"- {route}: {info['type']} {info['duration']}, {info['frequency']}, {info['price']}")
    return "\n".join(lines)

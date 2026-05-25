"""Weather data via wttr.in. Free, no API key needed."""
import httpx
import time

_weather_cache: dict[str, tuple] = {}
_CACHE_TTL = 1800  # 30 minutes

async def get_weather(city_en: str) -> dict | None:
    """Fetch 3-day forecast for a city. city_en='Beijing', 'Shanghai', etc."""
    key = city_en.lower().strip()
    cached = _weather_cache.get(key)
    if cached:
        if time.time() - cached[0] < _CACHE_TTL:
            return cached[1]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://wttr.in/{key}?format=j1")
            if resp.status_code != 200:
                return None
            data = resp.json()
            current = data.get("current_condition", [{}])[0]
            forecast = data.get("weather", [])[:3]
            result = {
                "city": city_en,
                "temp_c": current.get("temp_C", "?"),
                "feels_like": current.get("FeelsLikeC", "?"),
                "humidity": current.get("humidity", "?"),
                "wind_speed": current.get("windspeedKmph", "?"),
                "description": current.get("weatherDesc", [{}])[0].get("value", ""),
                "forecast": [
                    {
                        "date": day.get("date", ""),
                        "max": day.get("maxtempC", "?"),
                        "min": day.get("mintempC", "?"),
                        "desc": day.get("hourly", [{}])[0].get("weatherDesc", [{}])[0].get("value", "")
                    }
                    for day in forecast
                ]
            }
            _weather_cache[key] = (time.time(), result)
            return result
    except Exception:
        return None

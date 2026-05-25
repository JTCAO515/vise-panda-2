"""Simple currency converter. Uses frankfurter.app with static fallback."""
import httpx
import time

_FX_CACHE: dict = {}
_CACHE_TTL = 3600

_FALLBACK_RATES = {
    "USD": 1.0, "CNY": 7.24, "EUR": 0.92, "GBP": 0.79,
    "JPY": 151.5, "KRW": 1350, "THB": 36.5, "SGD": 1.35,
    "HKD": 7.82, "TWD": 32.5, "AUD": 1.53, "CAD": 1.38,
    "MYR": 4.72, "VND": 25450, "INR": 83.5, "RUB": 92.0
}


async def convert(amount: float, from_curr: str, to_curr: str = "CNY") -> dict:
    """Convert amount between currencies."""
    from_curr = from_curr.upper()
    to_curr = to_curr.upper()

    if from_curr == to_curr:
        return {"amount": amount, "from": from_curr, "to": to_curr, "result": amount, "rate": 1.0}

    cache_key = f"{from_curr}_{to_curr}"
    cached = _FX_CACHE.get(cache_key)
    if cached and time.time() - cached[0] < _CACHE_TTL:
        rate = cached[1]
        return {"amount": amount, "from": from_curr, "to": to_curr, "result": round(amount * rate, 2), "rate": rate}

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"https://api.frankfurter.app/latest?from={from_curr}&to={to_curr}")
            if resp.status_code == 200:
                data = resp.json()
                rate = data["rates"][to_curr]
                _FX_CACHE[cache_key] = (time.time(), rate)
                result = round(amount * rate, 2)
                return {"amount": amount, "from": from_curr, "to": to_curr, "result": result, "rate": rate}
    except Exception:
        pass

    if from_curr in _FALLBACK_RATES and to_curr in _FALLBACK_RATES:
        rate = _FALLBACK_RATES[to_curr] / _FALLBACK_RATES[from_curr]
        _FX_CACHE[cache_key] = (time.time(), rate)
        result = round(amount * rate, 2)
        return {"amount": amount, "from": from_curr, "to": to_curr, "result": result, "rate": rate, "source": "fallback"}

    return {"error": f"Unknown currency: {from_curr} or {to_curr}"}

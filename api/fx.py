"""Simple currency converter. Static fallback rates only (Vercel-compatible)."""
import time

_FX_CACHE: dict = {}
_CACHE_TTL = 3600

_RATES = {
    "USD": 1.0, "CNY": 7.24, "EUR": 0.92, "GBP": 0.79,
    "JPY": 151.5, "KRW": 1350, "THB": 36.5, "SGD": 1.35,
    "HKD": 7.82, "TWD": 32.5, "AUD": 1.53, "CAD": 1.38,
    "MYR": 4.72, "VND": 25450, "INR": 83.5, "RUB": 92.0
}


def convert(amount: float, from_curr: str, to_curr: str = "CNY") -> dict:
    """Convert amount between currencies using static rates."""
    from_curr = from_curr.upper()
    to_curr = to_curr.upper()

    if from_curr == to_curr:
        return {"amount": amount, "from": from_curr, "to": to_curr, "result": amount, "rate": 1.0}

    if from_curr in _RATES and to_curr in _RATES:
        rate = _RATES[to_curr] / _RATES[from_curr]
        return {"amount": amount, "from": from_curr, "to": to_curr, "result": round(amount * rate, 2), "rate": rate, "source": "static"}

    return {"error": f"Unknown currency: {from_curr} or {to_curr}"}

from http import HTTPStatus

from api.common import clean_list, clean_text, error_response, json_response, load_json, query_params


def _city_record(slug, raw):
    highlights = clean_list(raw.get("highlights") or raw.get("keywords"), 5)
    keywords = clean_list(raw.get("keywords"), 8)
    return {
        "id": slug,
        "name": clean_text(raw.get("name_en")) or slug.title(),
        "province": clean_text(raw.get("province")),
        "bestSeason": clean_text(raw.get("best_season")),
        "duration": clean_text(raw.get("days")),
        "budgetTip": clean_text(raw.get("budget_tip")),
        "vibe": clean_text(raw.get("vibe")),
        "highlights": highlights,
        "keywords": keywords,
        "image": raw.get("image") or "/static/img/og-image.jpg",
    }


def all_cities():
    data = load_json("cities.json")
    return [_city_record(slug, raw) for slug, raw in data.items()]


def city_by_id(city_id):
    city_id = (city_id or "").lower()
    for city in all_cities():
        if city["id"] == city_id:
            return city
    return None


def api_map_payload():
    cities = all_cities()
    return {
        "cities": cities,
        "regions": sorted({city["province"] for city in cities if city["province"]}),
    }


def dispatch(method, path_parts, environ, start_response):
    if method != "GET":
        return error_response(start_response, HTTPStatus.METHOD_NOT_ALLOWED, "method_not_allowed", "Method not allowed.", environ)

    if len(path_parts) == 2:
        params = query_params(environ)
        cities = all_cities()
        region = (params.get("region") or "").lower()
        q = (params.get("q") or "").lower()
        if region:
            cities = [city for city in cities if city["province"].lower() == region]
        if q:
            cities = [
                city for city in cities
                if q in city["name"].lower()
                or q in city["province"].lower()
                or any(q in keyword.lower() for keyword in city["keywords"])
            ]
        return json_response(start_response, {"cities": cities, "count": len(cities)}, environ=environ)

    if len(path_parts) == 3:
        city = city_by_id(path_parts[2])
        if not city:
            return error_response(start_response, HTTPStatus.NOT_FOUND, "city_not_found", "City not found.", environ)
        return json_response(start_response, {"city": city}, environ=environ)

    return error_response(start_response, HTTPStatus.NOT_FOUND, "not_found", "Endpoint not found.", environ)

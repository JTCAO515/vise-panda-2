from http import HTTPStatus

from api.common import clean_list, clean_text, error_response, json_response, load_json, query_params, read_json


def _policy(slug, raw):
    return {
        "id": slug,
        "country": clean_text(raw.get("country")),
        "nationality": clean_text(raw.get("nationality")),
        "visaRequired": bool(raw.get("visa_required")),
        "visaType": clean_text(raw.get("visa_type")),
        "processingTime": clean_text(raw.get("processing_time")),
        "validity": clean_text(raw.get("validity")),
        "maxStay": clean_text(raw.get("max_stay")),
        "fee": clean_text(raw.get("fee")),
        "documentsRequired": clean_list(raw.get("documents_required")),
        "specialNotes": clean_text(raw.get("special_notes")),
        "countryCode": clean_text(raw.get("country_code")),
    }


def policies():
    raw = load_json("visa_policies.json")
    return {slug: _policy(slug, item) for slug, item in raw.items()}


def find_policy(nationality):
    key = (nationality or "").strip().lower()
    aliases = {
        "usa": "us",
        "united states": "us",
        "american": "us",
        "gb": "uk",
        "united kingdom": "uk",
        "british": "uk",
        "australian": "australia",
        "canadian": "canada",
        "eu": "schengen",
        "europe": "schengen",
        "france": "schengen",
        "germany": "schengen",
        "italy": "schengen",
        "spain": "schengen",
    }
    key = aliases.get(key, key)
    return policies().get(key)


def recommendation(policy, duration_days):
    if not policy:
        return "Check with the nearest Chinese embassy or consulate before booking."
    if duration_days <= 6:
        return "Consider 144-hour visa-free transit if your route includes a confirmed onward flight to a third country or region."
    if not policy["visaRequired"] and duration_days <= 15:
        return "Your profile may fit the current short-stay visa-free program, but verify official rules close to departure."
    return f"Plan around the {policy['visaType']} and allow {policy['processingTime']} for processing."


def dispatch(method, path_parts, environ, start_response):
    if method == "GET" and len(path_parts) == 3 and path_parts[2] == "countries":
        items = sorted(policies().values(), key=lambda item: item["country"])
        return json_response(start_response, {"countries": items}, environ=environ)

    if method == "GET" and len(path_parts) == 3 and path_parts[2] == "info":
        nationality = query_params(environ).get("nationality")
        policy = find_policy(nationality)
        if not policy:
            return error_response(start_response, HTTPStatus.NOT_FOUND, "policy_not_found", "Visa policy not found.", environ)
        return json_response(start_response, {"policy": policy}, environ=environ)

    if method == "POST" and len(path_parts) == 3 and path_parts[2] == "generate":
        try:
            body = read_json(environ)
        except ValueError as exc:
            return error_response(start_response, HTTPStatus.BAD_REQUEST, "bad_json", str(exc), environ)
        duration = int(body.get("durationDays") or body.get("duration") or 7)
        policy = find_policy(body.get("nationality"))
        return json_response(
            start_response,
            {
                "policy": policy,
                "recommendation": recommendation(policy, duration),
                "checklist": [
                    "Verify the latest rule on an official consulate or immigration page.",
                    "Keep passport validity above six months.",
                    "Carry printed hotel and transport confirmations.",
                    "Choose hotels licensed to host foreign travelers.",
                ],
            },
            environ=environ,
        )

    return error_response(start_response, HTTPStatus.NOT_FOUND, "not_found", "Endpoint not found.", environ)

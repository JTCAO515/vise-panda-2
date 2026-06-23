from http import HTTPStatus

from api import auth, chat, cities, tools, visa
from api.common import error_response, json_response, static_response
from api.config import public_config


def application(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO") or "/"
    path_parts = [part for part in path.strip("/").split("/") if part]

    if method == "OPTIONS":
        return json_response(start_response, {"ok": True}, environ=environ)

    if path == "/api/health":
        return json_response(start_response, {"ok": True, "service": "VisePanda", "version": "6.1.1"}, environ=environ)

    if path == "/api/config":
        return json_response(start_response, public_config(), environ=environ)

    if path_parts[:2] == ["api", "cities"]:
        return cities.dispatch(method, path_parts, environ, start_response)

    if path == "/api/map":
        if method != "GET":
            return error_response(start_response, HTTPStatus.METHOD_NOT_ALLOWED, "method_not_allowed", "Method not allowed.", environ)
        return json_response(start_response, cities.api_map_payload(), environ=environ)

    if path_parts[:2] == ["api", "tools"]:
        return tools.dispatch(method, path_parts, environ, start_response)

    if path_parts[:2] == ["api", "visa"]:
        return visa.dispatch(method, path_parts, environ, start_response)

    if path == "/api/chat":
        return chat.dispatch(method, environ, start_response)

    if path_parts[:2] in (["api", "auth"], ["api", "trips"]) or path_parts[:2] == ["api", "admin"]:
        return auth.dispatch(method, path_parts, environ, start_response)

    if path.startswith("/api/"):
        return error_response(start_response, HTTPStatus.NOT_FOUND, "not_found", "Endpoint not found.", environ)

    return static_response(start_response, path, environ)


app = application

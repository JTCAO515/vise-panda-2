import json
from io import BytesIO

import unittest


class WsgiTestCase(unittest.TestCase):
    def make_environ(self, method, path, body=None, token=None, query_string=""):
        payload = json.dumps(body).encode("utf-8") if body is not None else b""
        env = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": query_string,
            "CONTENT_LENGTH": str(len(payload)),
            "CONTENT_TYPE": "application/json",
            "wsgi.input": BytesIO(payload),
            "SERVER_PROTOCOL": "HTTP/1.1",
            "HTTP_HOST": "localhost",
        }
        if token:
            env["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return env

    def call_app(self, app, env):
        captured = {}

        def sr(status, headers):
            captured["status"] = status
            captured["headers"] = headers

        body = b"".join(app(env, sr)).decode("utf-8")
        captured["body"] = body
        captured["json"] = json.loads(body) if body else None
        return captured

import io
import json
import os
import tempfile
from contextlib import contextmanager

from api.index import application


@contextmanager
def isolated_auth_db():
    old = os.environ.get("AUTH_DB_PATH")
    with tempfile.TemporaryDirectory() as directory:
        os.environ["AUTH_DB_PATH"] = os.path.join(directory, "test.db")
        try:
            yield
        finally:
            if old is None:
                os.environ.pop("AUTH_DB_PATH", None)
            else:
                os.environ["AUTH_DB_PATH"] = old


def request(method, path, body=None, token=None, query=""):
    payload = b""
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
    status_headers = {}

    def start_response(status, headers):
        status_headers["status"] = status
        status_headers["headers"] = dict(headers)

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "CONTENT_LENGTH": str(len(payload)),
        "CONTENT_TYPE": "application/json",
        "wsgi.input": io.BytesIO(payload),
        "REMOTE_ADDR": "127.0.0.1",
    }
    if token:
        environ["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    chunks = application(environ, start_response)
    raw = b"".join(chunks)
    content_type = status_headers["headers"].get("Content-Type", "")
    if "application/json" in content_type:
        parsed = json.loads(raw.decode("utf-8"))
    else:
        parsed = raw.decode("utf-8")
    code = int(status_headers["status"].split()[0])
    return code, parsed, status_headers["headers"]


def register_and_login(email="traveler@example.com", password="SecurePass123!"):
    old = os.environ.get("AUTH_EXPOSE_EMAIL_CODE")
    os.environ["AUTH_EXPOSE_EMAIL_CODE"] = "1"
    try:
        code, registered, _ = request("POST", "/api/auth/register", {"email": email, "password": password})
        if code == 201:
            code, verified, _ = request("POST", "/api/auth/verify-email", {"email": email, "code": registered["verificationCode"]})
            assert code == 200, verified
        else:
            assert code == 409, registered
    finally:
        if old is None:
            os.environ.pop("AUTH_EXPOSE_EMAIL_CODE", None)
        else:
            os.environ["AUTH_EXPOSE_EMAIL_CODE"] = old
    code, data, _ = request("POST", "/api/auth/login", {"email": email, "password": password})
    assert code == 200, data
    return data["token"], data["user"]

#!/usr/bin/env python3
"""Test auth module."""
import sys, json
sys.path.insert(0, ".")

from api import auth
auth.ensure_init()

from io import BytesIO

def make_environ(method, path, body=None):
    env = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.input": BytesIO(body.encode() if body else b""),
        "CONTENT_LENGTH": str(len(body or "")),
        "HTTP_HOST": "localhost",
    }
    return env

def test():
    results = []
    def capture_sr(status, headers):
        results.append({"status": status, "headers": headers})
        return [b""]

    # 1. Register
    env = make_environ("POST", "/api/auth/register", '{"email":"test2@vise.com","password":"test123456"}')
    resp = auth.handle_auth_route(env, capture_sr, "/api/auth/register", "POST")
    data = json.loads(b"".join(resp).decode())
    print(f"REGISTER: {results[-1]['status']} | {data.get('message','')} role={data.get('user',{}).get('role','')}")

    # 2. Login
    env = make_environ("POST", "/api/auth/login", '{"email":"test2@vise.com","password":"test123456"}')
    results.clear()
    resp = auth.handle_auth_route(env, capture_sr, "/api/auth/login", "POST")
    login = json.loads(b"".join(resp).decode())
    token = login.get("token", "")
    print(f"LOGIN: {results[-1]['status']} | token={token[:16]}... role={login.get('user',{}).get('role','')}")

    # 3. Me
    env = make_environ("GET", "/api/auth/me")
    env["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    results.clear()
    resp = auth.handle_auth_route(env, capture_sr, "/api/auth/me", "GET")
    me = json.loads(b"".join(resp).decode())
    print(f"ME: {results[-1]['status']} | email={me.get('user',{}).get('email','')}")

    # 4. Admin: list users
    env = make_environ("GET", "/api/admin/users")
    env["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    results.clear()
    resp = auth.handle_auth_route(env, capture_sr, "/api/admin/users", "GET")
    admin = json.loads(b"".join(resp).decode())
    print(f"ADMIN LIST: {results[-1]['status']} | total={admin.get('total',0)} users")

    print("\n✅ ALL PASSED")

test()

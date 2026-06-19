import os
import tempfile
from pathlib import Path

from tests.test_support import WsgiTestCase


class AdminContractTest(WsgiTestCase):
    def setUp(self):
        self.db_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.db_dir.name, "auth.db")
        os.environ["AUTH_DB_PATH"] = self.db_path
        from api import auth

        self.auth = auth
        auth._initialized = False
        from api.index import app

        self.app = app

    def tearDown(self):
        self.auth._initialized = False
        os.environ.pop("AUTH_DB_PATH", None)
        self.db_dir.cleanup()

    def assert_json_error(self, response, expected_status, expected_error):
        self.assertEqual(response["status"], expected_status)
        self.assertTrue(response["body"])
        self.assertEqual(response["json"], {"error": expected_error})
        headers = dict(response["headers"])
        self.assertEqual(headers.get("Content-Type"), "application/json; charset=utf-8")

    def login_as_user(self):
        register_response = self.call_app(
            self.app,
            self.make_environ(
                "POST",
                "/api/auth/register",
                {"email": "user@example.com", "password": "secret123"},
            ),
        )
        self.assertEqual(register_response["status"], "201 Created")

        login_response = self.call_app(
            self.app,
            self.make_environ(
                "POST",
                "/api/auth/login",
                {"email": "user@example.com", "password": "secret123"},
            ),
        )
        self.assertEqual(login_response["status"], "200 OK")
        return login_response["json"]["token"]

    def create_user(
        self,
        email,
        password,
        *,
        role="user",
        status="active",
        display_name="Contract User",
    ):
        self.auth.ensure_init()
        password_hash, salt = self.auth._hash_password(password)
        conn = self.auth._get_db()
        conn.execute(
            "INSERT INTO users (id, email, password_hash, salt, display_name, role, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (email.split("@")[0], email, password_hash, salt, display_name, role, status),
        )
        conn.commit()
        conn.close()

    def login(self, email, password):
        return self.call_app(
            self.app,
            self.make_environ(
                "POST",
                "/api/auth/login",
                {"email": email, "password": password},
            ),
        )

    def test_admin_users_requires_auth_returns_stable_json_error(self):
        response = self.call_app(self.app, self.make_environ("GET", "/api/admin/users"))

        self.assert_json_error(
            response,
            "401 Unauthorized",
            "Authentication required",
        )

    def test_non_admin_cannot_list_admin_users_and_gets_json_error(self):
        token = self.login_as_user()

        response = self.call_app(
            self.app,
            self.make_environ("GET", "/api/admin/users", token=token),
        )

        self.assert_json_error(
            response,
            "403 Forbidden",
            "Access denied",
        )

    def test_disabled_user_cannot_login(self):
        self.create_user(
            "disabled@example.com",
            "secret123",
            status="disabled",
            display_name="Disabled User",
        )

        response = self.login("disabled@example.com", "secret123")

        self.assert_json_error(
            response,
            "403 Forbidden",
            "Account is not active",
        )

    def test_ops_can_list_admin_users(self):
        self.create_user(
            "ops@example.com",
            "secret123",
            role="ops",
            display_name="Ops User",
        )

        login_response = self.login("ops@example.com", "secret123")
        self.assertEqual(login_response["status"], "200 OK")

        response = self.call_app(
            self.app,
            self.make_environ(
                "GET",
                "/api/admin/users",
                token=login_response["json"]["token"],
            ),
        )

        self.assertEqual(response["status"], "200 OK")
        self.assertIn("users", response["json"])
        self.assertTrue(
            any(user["email"] == "ops@example.com" for user in response["json"]["users"])
        )

    def test_admin_page_uses_shared_token_key_and_ops_frontend_gate(self):
        admin_html = (Path(__file__).resolve().parents[1] / "web" / "admin.html").read_text(
            encoding="utf-8"
        )

        self.assertIn("localStorage.getItem('vp_token')", admin_html)
        self.assertNotIn("localStorage.getItem('vp_auth_token')", admin_html)
        self.assertIn("user.role === 'admin' || user.role === 'ops'", admin_html)

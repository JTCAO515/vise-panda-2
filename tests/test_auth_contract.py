import os
import unittest

from api.auth import db
from tests.test_support import isolated_auth_db, register_and_login, request


class AuthContractTests(unittest.TestCase):
    def test_public_registration_never_creates_admin(self):
        with isolated_auth_db():
            old = os.environ.get("AUTH_EXPOSE_EMAIL_CODE")
            os.environ["AUTH_EXPOSE_EMAIL_CODE"] = "1"
            code, data, _ = request("POST", "/api/auth/register", {
                "email": "first@example.com",
                "password": "SecurePass123!",
            })
            if old is None:
                os.environ.pop("AUTH_EXPOSE_EMAIL_CODE", None)
            else:
                os.environ["AUTH_EXPOSE_EMAIL_CODE"] = old
            self.assertEqual(code, 201)
            self.assertEqual(data["user"]["role"], "user")
            self.assertFalse(data["user"]["emailVerified"])
            self.assertIn("verificationCode", data)

    def test_email_must_be_verified_before_password_login(self):
        with isolated_auth_db():
            old = os.environ.get("AUTH_EXPOSE_EMAIL_CODE")
            os.environ["AUTH_EXPOSE_EMAIL_CODE"] = "1"
            try:
                code, data, _ = request("POST", "/api/auth/register", {"email": "verify@example.com", "password": "SecurePass123!"})
                self.assertEqual(code, 201)
                code, login, _ = request("POST", "/api/auth/login", {"email": "verify@example.com", "password": "SecurePass123!"})
                self.assertEqual(code, 403)
                self.assertEqual(login["error"]["code"], "email_unverified")
                code, verified, _ = request("POST", "/api/auth/verify-email", {"email": "verify@example.com", "code": data["verificationCode"]})
                self.assertEqual(code, 200)
                self.assertTrue(verified["user"]["emailVerified"])
            finally:
                if old is None:
                    os.environ.pop("AUTH_EXPOSE_EMAIL_CODE", None)
                else:
                    os.environ["AUTH_EXPOSE_EMAIL_CODE"] = old

    def test_weak_default_admin_is_not_seeded(self):
        old_email = os.environ.get("ADMIN_EMAIL")
        old_password = os.environ.get("ADMIN_PASSWORD")
        os.environ["ADMIN_EMAIL"] = "admin@go2china.space"
        os.environ["ADMIN_PASSWORD"] = "admin123"
        try:
            with isolated_auth_db():
                with db() as conn:
                    row = conn.execute("SELECT * FROM users WHERE role = 'admin'").fetchone()
                self.assertIsNone(row)
        finally:
            if old_email is None:
                os.environ.pop("ADMIN_EMAIL", None)
            else:
                os.environ["ADMIN_EMAIL"] = old_email
            if old_password is None:
                os.environ.pop("ADMIN_PASSWORD", None)
            else:
                os.environ["ADMIN_PASSWORD"] = old_password

    def test_strong_explicit_admin_can_be_seeded(self):
        old_email = os.environ.get("ADMIN_EMAIL")
        old_password = os.environ.get("ADMIN_PASSWORD")
        os.environ["ADMIN_EMAIL"] = "owner@go2china.space"
        os.environ["ADMIN_PASSWORD"] = "VeryStrongAdminPassword123!"
        try:
            with isolated_auth_db():
                with db() as conn:
                    row = conn.execute("SELECT * FROM users WHERE email = ?", ("owner@go2china.space",)).fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row["role"], "admin")
        finally:
            if old_email is None:
                os.environ.pop("ADMIN_EMAIL", None)
            else:
                os.environ["ADMIN_EMAIL"] = old_email
            if old_password is None:
                os.environ.pop("ADMIN_PASSWORD", None)
            else:
                os.environ["ADMIN_PASSWORD"] = old_password

    def test_forgot_password_does_not_leak_token_by_default(self):
        old = os.environ.pop("AUTH_EXPOSE_RESET_TOKEN", None)
        try:
            with isolated_auth_db():
                register_and_login("reset@example.com", "SecurePass123!")
                code, data, _ = request("POST", "/api/auth/forgot-password", {"email": "reset@example.com"})
                self.assertEqual(code, 200)
                self.assertNotIn("resetToken", data)
        finally:
            if old is not None:
                os.environ["AUTH_EXPOSE_RESET_TOKEN"] = old

    def test_password_change_requires_current_password(self):
        with isolated_auth_db():
            token, _ = register_and_login()
            code, data, _ = request("POST", "/api/auth/update-profile", {"newPassword": "AnotherPass123!"}, token=token)
            self.assertEqual(code, 400)
            self.assertEqual(data["error"]["code"], "current_password_required")

    def test_auth_config_exposes_google_and_email_verification(self):
        with isolated_auth_db():
            code, data, _ = request("GET", "/api/auth/config")
            self.assertEqual(code, 200)
            self.assertIn("google", data)
            self.assertTrue(data["emailVerification"])

    def test_google_start_redirects_when_configured(self):
        old_client = os.environ.get("GOOGLE_CLIENT_ID")
        old_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        os.environ["GOOGLE_CLIENT_ID"] = "client-id.example"
        os.environ["GOOGLE_CLIENT_SECRET"] = "client-secret"
        try:
            with isolated_auth_db():
                code, _, headers = request("GET", "/api/auth/google/start")
                self.assertEqual(code, 302)
                self.assertIn("https://accounts.google.com/o/oauth2/v2/auth", headers["Location"])
                self.assertIn("client-id.example", headers["Location"])
        finally:
            if old_client is None:
                os.environ.pop("GOOGLE_CLIENT_ID", None)
            else:
                os.environ["GOOGLE_CLIENT_ID"] = old_client
            if old_secret is None:
                os.environ.pop("GOOGLE_CLIENT_SECRET", None)
            else:
                os.environ["GOOGLE_CLIENT_SECRET"] = old_secret


if __name__ == "__main__":
    unittest.main()

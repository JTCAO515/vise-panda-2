import os
import unittest

from tests.test_support import isolated_auth_db, register_and_login, request


class AdminContractTests(unittest.TestCase):
    def test_non_admin_cannot_list_users(self):
        with isolated_auth_db():
            token, _ = register_and_login()
            code, data, _ = request("GET", "/api/admin/users", token=token)
            self.assertEqual(code, 403)
            self.assertEqual(data["error"]["code"], "forbidden")

    def test_admin_can_list_users(self):
        old_email = os.environ.get("ADMIN_EMAIL")
        old_password = os.environ.get("ADMIN_PASSWORD")
        os.environ["ADMIN_EMAIL"] = "owner@go2china.space"
        os.environ["ADMIN_PASSWORD"] = "VeryStrongAdminPassword123!"
        try:
            with isolated_auth_db():
                token, user = register_and_login("owner@go2china.space", "VeryStrongAdminPassword123!")
                self.assertEqual(user["role"], "admin")
                code, data, _ = request("GET", "/api/admin/users", token=token)
                self.assertEqual(code, 200)
                self.assertGreaterEqual(len(data["users"]), 1)
        finally:
            if old_email is None:
                os.environ.pop("ADMIN_EMAIL", None)
            else:
                os.environ["ADMIN_EMAIL"] = old_email
            if old_password is None:
                os.environ.pop("ADMIN_PASSWORD", None)
            else:
                os.environ["ADMIN_PASSWORD"] = old_password


if __name__ == "__main__":
    unittest.main()

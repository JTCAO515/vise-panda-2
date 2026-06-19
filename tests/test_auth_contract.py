import os
import tempfile

from tests.test_support import WsgiTestCase


class AuthContractTest(WsgiTestCase):
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

    def test_unauthenticated_trips_returns_stable_json_error(self):
        response = self.call_app(self.app, self.make_environ("GET", "/api/trips"))

        self.assert_json_error(
            response,
            "401 Unauthorized",
            "Authentication required",
        )

    def test_db_path_tracks_environment_changes_before_reinit(self):
        self.assertFalse(os.path.exists(self.db_path))

        self.auth.ensure_init()
        self.assertTrue(os.path.exists(self.db_path))

        second_dir = tempfile.TemporaryDirectory()
        self.addCleanup(second_dir.cleanup)
        second_db_path = os.path.join(second_dir.name, "auth-second.db")
        os.environ["AUTH_DB_PATH"] = second_db_path

        self.auth._initialized = False
        self.auth.ensure_init()

        self.assertTrue(os.path.exists(second_db_path))

    def test_register_persists_display_name_through_login_and_me(self):
        register_response = self.call_app(
            self.app,
            self.make_environ(
                "POST",
                "/api/auth/register",
                {
                    "email": "user@example.com",
                    "password": "secret123",
                    "display_name": "Atlas User",
                },
            ),
        )
        self.assertEqual(register_response["status"], "201 Created")

        login_response = self.call_app(
            self.app,
            self.make_environ(
                "POST",
                "/api/auth/login",
                {
                    "email": "user@example.com",
                    "password": "secret123",
                },
            ),
        )
        self.assertEqual(login_response["status"], "200 OK")
        self.assertEqual(login_response["json"]["user"]["display_name"], "Atlas User")

        me_response = self.call_app(
            self.app,
            self.make_environ(
                "GET",
                "/api/auth/me",
                token=login_response["json"]["token"],
            ),
        )
        self.assertEqual(me_response["status"], "200 OK")
        self.assertEqual(me_response["json"]["user"]["display_name"], "Atlas User")

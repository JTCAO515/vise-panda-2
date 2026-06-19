import os
from unittest import mock

from tests.test_support import WsgiTestCase


class ConfigContractTest(WsgiTestCase):
    def setUp(self):
        from api.index import app

        self.app = app

    def test_health_and_config_share_version(self):
        health = self.call_app(self.app, self.make_environ("GET", "/api/health"))
        config = self.call_app(self.app, self.make_environ("GET", "/api/config"))

        self.assertEqual(health["json"]["version"], config["json"]["version"])

    def test_config_returns_empty_google_client_id_when_unset(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GOOGLE_CLIENT_ID", None)
            config = self.call_app(self.app, self.make_environ("GET", "/api/config"))

        self.assertIn("google_client_id", config["json"])
        self.assertEqual(config["json"]["google_client_id"], "")

    def test_config_returns_google_client_id_when_set(self):
        with mock.patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "test-google-client-id"}, clear=False):
            config = self.call_app(self.app, self.make_environ("GET", "/api/config"))

        self.assertEqual(config["json"]["google_client_id"], "test-google-client-id")

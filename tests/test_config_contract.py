import unittest

from tests.test_support import request


class ConfigContractTests(unittest.TestCase):
    def test_health_and_config_are_public(self):
        code, data, _ = request("GET", "/api/health")
        self.assertEqual(code, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["version"], "6.1.1")

        code, config, _ = request("GET", "/api/config")
        self.assertEqual(code, 200)
        self.assertEqual(config["app"]["domain"], "go2china.space")
        self.assertEqual(config["app"]["version"], "6.1.1")
        self.assertTrue(config["features"]["chat"])
        self.assertIn("local-guide", config["ai"]["routes"])
        self.assertTrue(config["auth"]["emailVerification"])

    def test_static_app_is_served(self):
        code, body, headers = request("GET", "/")
        self.assertEqual(code, 200)
        self.assertIn("VisePanda", body)
        self.assertIn("text/html", headers["Content-Type"])


if __name__ == "__main__":
    unittest.main()

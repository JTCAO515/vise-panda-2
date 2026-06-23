import unittest

from tests.test_support import request


class ApiContractTests(unittest.TestCase):
    def test_cities_are_clean_public_records(self):
        code, data, _ = request("GET", "/api/cities")
        self.assertEqual(code, 200)
        self.assertGreater(data["count"], 20)
        first = data["cities"][0]
        self.assertIn("name", first)
        self.assertNotIn("\u951b", " ".join(first["highlights"]))

        code, detail, _ = request("GET", "/api/cities/beijing")
        self.assertEqual(code, 200)
        self.assertEqual(detail["city"]["name"], "Beijing")

    def test_tools_and_visa_endpoints(self):
        code, tools, _ = request("GET", "/api/tools")
        self.assertEqual(code, 200)
        self.assertGreaterEqual(tools["count"], 4)

        code, detail, _ = request("GET", "/api/tools/packing")
        self.assertEqual(code, 200)
        self.assertTrue(detail["tool"]["items"][0]["required"])

        code, visa, _ = request("GET", "/api/visa/info", query="nationality=us")
        self.assertEqual(code, 200)
        self.assertEqual(visa["policy"]["country"], "United States")

    def test_chat_streams_server_sent_events(self):
        code, body, headers = request("POST", "/api/chat", {
            "message": "Plan Beijing and Chengdu for 7 days",
            "mode": "itinerary",
            "provider": "local-guide",
            "depth": "expert",
        })
        self.assertEqual(code, 200)
        self.assertIn("text/event-stream", headers["Content-Type"])
        self.assertIn("data:", body)
        self.assertIn("providerLabel", body)
        self.assertIn("Beijing", body)

    def test_chat_options_expose_modes_and_routes(self):
        code, data, _ = request("GET", "/api/chat")
        self.assertEqual(code, 200)
        self.assertIn("itinerary", {mode["id"] for mode in data["modes"]})
        self.assertIn("local-guide", {provider["id"] for provider in data["providers"]})
        self.assertIn("expert", {depth["id"] for depth in data["depths"]})


if __name__ == "__main__":
    unittest.main()

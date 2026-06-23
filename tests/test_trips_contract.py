import unittest

from tests.test_support import isolated_auth_db, register_and_login, request


class TripContractTests(unittest.TestCase):
    def test_trips_require_auth(self):
        with isolated_auth_db():
            code, data, _ = request("GET", "/api/trips")
            self.assertEqual(code, 401)
            self.assertEqual(data["error"]["code"], "unauthorized")

    def test_signed_in_user_can_create_and_list_trips(self):
        with isolated_auth_db():
            token, _ = register_and_login()
            code, created, _ = request("POST", "/api/trips", {
                "title": "First China Trip",
                "destination": "Beijing",
                "startDate": "2026-10-01",
                "endDate": "2026-10-07",
            }, token=token)
            self.assertEqual(code, 201)
            self.assertEqual(created["trip"]["destination"], "Beijing")

            code, listed, _ = request("GET", "/api/trips", token=token)
            self.assertEqual(code, 200)
            self.assertEqual(len(listed["trips"]), 1)
            self.assertEqual(listed["trips"][0]["title"], "First China Trip")


if __name__ == "__main__":
    unittest.main()

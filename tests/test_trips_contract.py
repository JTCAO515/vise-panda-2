import os
import sqlite3
import tempfile

from tests.test_support import WsgiTestCase


class TripsContractTest(WsgiTestCase):
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

    def _register_and_login(self, email="trip@example.com"):
        register_response = self.call_app(
            self.app,
            self.make_environ(
                "POST",
                "/api/auth/register",
                {
                    "email": email,
                    "password": "secret123",
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
                    "email": email,
                    "password": "secret123",
                },
            ),
        )
        self.assertEqual(login_response["status"], "200 OK")
        return login_response["json"]["token"]

    def test_create_trip_persists_full_content_and_preview_summary(self):
        token = self._register_and_login()

        response = self.call_app(
            self.app,
            self.make_environ(
                "POST",
                "/api/trips",
                {
                    "title": "Beijing 3 Days",
                    "city": "beijing",
                    "days": "3",
                    "preview": "short summary",
                    "content": "full itinerary body",
                },
                token=token,
            ),
        )

        self.assertEqual(response["status"], "201 Created")
        self.assertEqual(response["json"]["trip"]["preview"], "short summary")
        self.assertEqual(response["json"]["trip"]["content"], "full itinerary body")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        trip = conn.execute(
            "SELECT preview, content FROM trips WHERE id = ?",
            (response["json"]["trip"]["id"],),
        ).fetchone()
        conn.close()

        self.assertIsNotNone(trip)
        self.assertEqual(trip["preview"], "short summary")
        self.assertEqual(trip["content"], "full itinerary body")

    def test_get_trips_returns_content_and_falls_back_to_preview_for_legacy_rows(self):
        token = self._register_and_login()
        user_id = self.auth._get_user_from_token(token)["id"]
        self.auth.ensure_init()

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT INTO trips (id, user_id, title, city, days, preview, content, is_saved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-trip",
                user_id,
                "Legacy Trip",
                "shanghai",
                "2",
                "legacy summary",
                "",
                0,
            ),
        )
        conn.commit()
        conn.close()

        response = self.call_app(
            self.app,
            self.make_environ("GET", "/api/trips", token=token),
        )

        self.assertEqual(response["status"], "200 OK")
        recent = response["json"]["trips"]["recent"]
        legacy_trip = next(t for t in recent if t["id"] == "legacy-trip")
        self.assertEqual(legacy_trip["preview"], "legacy summary")
        self.assertEqual(legacy_trip["content"], "legacy summary")

    def test_init_db_adds_content_column_for_legacy_trips_table(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript(
            """
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL DEFAULT '',
                salt TEXT NOT NULL DEFAULT '',
                display_name TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT 'user',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE trips (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                city TEXT NOT NULL,
                days TEXT NOT NULL DEFAULT '',
                preview TEXT NOT NULL DEFAULT '',
                is_saved INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.commit()
        conn.close()

        self.auth.ensure_init()

        conn = sqlite3.connect(self.db_path)
        columns = {
            row[1]: row[2]
            for row in conn.execute("PRAGMA table_info(trips)").fetchall()
        }
        conn.close()

        self.assertIn("content", columns)

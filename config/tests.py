from django.conf import settings
from django.test import SimpleTestCase, TestCase

from config.deploy import database_config


class DatabaseConfigTests(SimpleTestCase):
    def test_sqlite_takes_the_write_lock_at_transaction_start(self):
        db = database_config("sqlite:///x.sqlite3", conn_max_age=0)
        self.assertEqual(db["OPTIONS"]["transaction_mode"], "IMMEDIATE")

    def test_postgres_disables_server_side_cursors(self):
        db = database_config("postgres://u:p@localhost:5432/d", conn_max_age=0)
        self.assertEqual(db["ENGINE"], "django.db.backends.postgresql")
        self.assertTrue(db["DISABLE_SERVER_SIDE_CURSORS"])


class SmokeTests(TestCase):
    def test_healthz_needs_no_login(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    def test_time_zone_is_manila(self):
        self.assertEqual(settings.TIME_ZONE, "Asia/Manila")
        self.assertTrue(settings.USE_TZ)

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


class DeploymentSettingsTests(SimpleTestCase):
    def manage(self, *args, **environ):
        import os
        import subprocess
        import sys

        base = {k: v for k, v in os.environ.items() if k not in ("HTTPS_ONLY", "DATABASE_URL")}
        return subprocess.run(
            [sys.executable, "manage.py", *args], cwd=settings.BASE_DIR,
            env={**base, "DEBUG": "False", "SECRET_KEY": "test-" + "k7Qz9xW2pL" * 6, **environ},
            capture_output=True, text=True,
        )

    def test_vercel_hosts_come_from_system_variables(self):
        from config.deploy import vercel_hosts

        environ = {
            "VERCEL_URL": "pokernights-abc123.vercel.app",
            "VERCEL_BRANCH_URL": "",
            "VERCEL_PROJECT_PRODUCTION_URL": "pokernights.vercel.app",
        }
        self.assertEqual(vercel_hosts(environ), ["pokernights-abc123.vercel.app", "pokernights.vercel.app"])
        self.assertEqual(vercel_hosts({}), [])

    def test_deploy_check_passes_on_vercel(self):
        """`check --deploy` is clean with the settings a Vercel deployment gets."""
        result = self.manage(
            "check", "--deploy", "--fail-level", "WARNING",
            VERCEL="1", VERCEL_URL="pokernights-abc123.vercel.app",
            DATABASE_URL="postgres://u:p@db.example.com:5432/app",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_vercel_refuses_to_start_without_a_database_url(self):
        from pathlib import Path

        local = Path(settings.BASE_DIR) / ".env"
        if local.exists() and any(line.startswith("DATABASE_URL=") for line in local.read_text().splitlines()):
            self.skipTest("the local .env sets DATABASE_URL")
        result = self.manage("check", VERCEL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Set DATABASE_URL", result.stderr)

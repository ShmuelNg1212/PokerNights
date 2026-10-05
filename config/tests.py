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


class StaticVersionTests(SimpleTestCase):
    def test_no_version_away_from_vercel(self):
        from config.deploy import static_version
        self.assertEqual(static_version({}), "")
        self.assertEqual(static_version({"VERCEL_URL": "x.vercel.app"}), "")

    def test_version_follows_the_deployment(self):
        from config.deploy import static_version
        one = static_version({"VERCEL": "1", "VERCEL_DEPLOYMENT_ID": "dpl_one", "VERCEL_GIT_COMMIT_SHA": "aaa"})
        two = static_version({"VERCEL": "1", "VERCEL_DEPLOYMENT_ID": "dpl_two", "VERCEL_GIT_COMMIT_SHA": "aaa"})
        self.assertEqual(len(one), 10)
        self.assertNotEqual(one, two)
        self.assertEqual(one, static_version({"VERCEL": "1", "VERCEL_DEPLOYMENT_ID": "dpl_one"}))
        self.assertTrue(static_version({"VERCEL": "1", "VERCEL_GIT_COMMIT_SHA": "aaa"}))
        self.assertTrue(static_version({"VERCEL": "1", "VERCEL_URL": "x.vercel.app"}))

    def test_vercel_without_any_identifier_refuses_to_start(self):
        from config.deploy import static_version
        with self.assertRaises(RuntimeError):
            static_version({"VERCEL": "1"})

    def test_only_stylesheets_and_scripts_are_versioned(self):
        from django.templatetags.static import static
        from django.test import override_settings
        with override_settings(STATIC_VERSION="abc1234567"):
            self.assertEqual(static("css/app.css"), "/static/css/app.css?v=abc1234567")
            self.assertEqual(static("js/live.js"), "/static/js/live.js?v=abc1234567")
            self.assertEqual(static("fonts/archivo.woff2"), "/static/fonts/archivo.woff2")
            self.assertEqual(static("branding/logo-mark.svg"), "/static/branding/logo-mark.svg")
        with override_settings(STATIC_VERSION=""):
            self.assertEqual(static("css/app.css"), "/static/css/app.css")

    def test_cache_headers_cover_only_static_files(self):
        import json
        from pathlib import Path
        rules = json.loads((Path(__file__).resolve().parent.parent / "vercel.json").read_text())["headers"]
        self.assertTrue(all(rule["source"].startswith("/static/") for rule in rules))
        year = next(r for r in rules if "(css|js)" in r["source"])["headers"][0]["value"]
        self.assertIn("immutable", year)
        self.assertNotIn("immutable", next(r for r in rules if "fonts" in r["source"])["headers"][0]["value"])


class VersionedPageTests(TestCase):
    def test_pages_render_versioned_addresses_and_the_font_matches_the_stylesheet(self):
        from django.test import override_settings
        with override_settings(STATIC_VERSION="abc1234567"):
            html = self.client.get("/accounts/login/").content.decode()
        self.assertIn('href="/static/css/app.css?v=abc1234567"', html)
        self.assertIn('src="/static/js/forms.js?v=abc1234567"', html)
        # The preload and the stylesheet's own reference must be the same address, or the font downloads twice.
        self.assertIn('href="/static/fonts/archivo.woff2"', html)

"""Settings helpers that depend on where the app runs (local or Vercel).

Kept free of Django imports so settings.py can call them and tests can
exercise them directly.
"""

import dj_database_url


def database_config(url: str, *, conn_max_age: int) -> dict:
    """DATABASES["default"] for a DATABASE_URL (SQLite or PostgreSQL)."""
    db = dj_database_url.parse(url, conn_max_age=conn_max_age, conn_health_checks=True)
    if db["ENGINE"] == "django.db.backends.sqlite3":
        # select_for_update() is a no-op on SQLite. Taking the write lock at
        # transaction start makes concurrent writers wait instead of interleave.
        db["OPTIONS"] = {
            "transaction_mode": "IMMEDIATE",
            "timeout": 20,
            "init_command": "PRAGMA journal_mode=WAL;",
        }
    elif db["ENGINE"] == "django.db.backends.postgresql":
        # Safe behind PgBouncer in transaction mode (e.g. a pooled Neon URL).
        db["DISABLE_SERVER_SIDE_CURSORS"] = True
    return db


def vercel_hosts(environ) -> list[str]:
    """Host names Vercel assigns to this deployment (empty when not on Vercel)."""
    names = ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL")
    return [environ[n] for n in names if environ.get(n)]


def static_version(environ) -> str:
    """A short tag that changes with every Vercel deployment; empty when not on Vercel.

    It is added to stylesheet and script addresses so they can be cached for a year
    and still change on the next release. On Vercel a missing tag would leave old
    files cached for good, so that case refuses to start.
    """
    import hashlib

    if not environ.get("VERCEL"):
        return ""
    names = ("VERCEL_DEPLOYMENT_ID", "VERCEL_GIT_COMMIT_SHA", "VERCEL_URL")
    source = next((environ[n] for n in names if environ.get(n)), "")
    if not source:
        raise RuntimeError("Vercel gave no deployment id, commit or URL to version the static files with.")
    return hashlib.sha256(source.encode()).hexdigest()[:10]

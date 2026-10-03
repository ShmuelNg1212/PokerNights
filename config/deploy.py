"""Settings helpers that depend on where the app runs.

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

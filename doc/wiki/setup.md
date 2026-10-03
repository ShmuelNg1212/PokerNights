# Setup

How to install, configure, run and test PokerNights on one machine. The app is not deployed.

## Requirements

- Python **3.14** (pinned in `.python-version`).
- No database server for simple local use: SQLite is the default.
- PostgreSQL 17 to run the tests as the shared deployment will run (Homebrew `postgresql@17` on this machine).

## Install

```sh
cd /Users/shm/PokerNights
/opt/homebrew/bin/python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/python manage.py migrate
```

## Configure (`.env`)

`.env` is gitignored. `.env.example` lists each variable.

| Variable | Required | Purpose |
|---|---|---|
| `DEBUG` | locally | `True` enables debug pages and a fixed development `SECRET_KEY` |
| `SECRET_KEY` | when `DEBUG` is off | Django secret key. The app refuses to start without one |
| `ALLOWED_HOSTS` | when served to others | Comma-separated host names. Default `localhost,127.0.0.1` |
| `DATABASE_URL` | no | For example `postgres://user@127.0.0.1:5432/pokernights`. Default: `db.sqlite3` |
| `DB_CONN_MAX_AGE` | no | Seconds to keep a database connection. Default 60 |
| `HTTPS_ONLY` | no | Secure cookies, HSTS and HTTPS redirect |
| `LOG_LEVEL` | no | Level for `pokernights.*` loggers. Default `INFO` |

## Run

```sh
.venv/bin/python manage.py runserver          # http://127.0.0.1:8000
.venv/bin/python manage.py createsuperuser    # optional, for /admin/
```

To let phones on the same Wi-Fi reach it: add the machine's address to `ALLOWED_HOSTS` and run `manage.py runserver 0.0.0.0:8000`. This is for a test at home only. `runserver` is not a production server.

## Test

```sh
.venv/bin/python manage.py test
```

368 tests. SQLite tests use a file-backed database (`test_db.sqlite3`, gitignored) so that threads see real locking.

To run the same suite on PostgreSQL:

```sh
/opt/homebrew/opt/postgresql@17/bin/pg_ctl -D /opt/homebrew/var/postgresql@17 -l /tmp/pn_postgres.log -w start
/opt/homebrew/opt/postgresql@17/bin/createdb pokernights        # once
DATABASE_URL=postgres://$USER@127.0.0.1:5432/pokernights .venv/bin/python manage.py test --noinput
/opt/homebrew/opt/postgresql@17/bin/pg_ctl -D /opt/homebrew/var/postgresql@17 stop
```

The concurrency tests are in `web/tests/test_concurrency.py`. They must pass on PostgreSQL before a release. See [footguns/sqlite_hides_missing_locks.md](footguns/sqlite_hides_missing_locks.md).

Both engines passed on 2026-10-03.

## Back up the dev database

SQLite runs in write-ahead-log mode, so recent data can sit in `db.sqlite3-wal`. A plain copy of `db.sqlite3` can miss it. Use the backup API:

```sh
python3 -c "import sqlite3; s=sqlite3.connect('db.sqlite3'); d=sqlite3.connect('db.backup.sqlite3'); s.backup(d)"
```

See [footguns/sqlite_copy_misses_the_wal.md](footguns/sqlite_copy_misses_the_wal.md).

## Admin

`/admin/` is for support by a superuser. Money, result, transfer, payment and audit rows are read-only there. All changes to them go through the app.

# Setup

How to install, configure, run and test PokerNights on one machine. For the Vercel deployment see [deployment.md](deployment.md).

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

`.env` is gitignored. `.env.example` lists common variables.

| Variable | Required | Purpose |
|---|---|---|
| `DEBUG` | locally | `True` enables debug pages and a fixed development `SECRET_KEY` |
| `SECRET_KEY` | when `DEBUG` is off | Django secret key. The app refuses to start without one |
| `ALLOWED_HOSTS` | when served to others | Comma-separated host names. Default `localhost,127.0.0.1` |
| `DATABASE_URL` | no | For example `postgres://user@127.0.0.1:5432/pokernights`. Default: `db.sqlite3` |
| `DB_CONN_MAX_AGE` | no | Seconds to keep a database connection. Default 60 |
| `HTTPS_ONLY` | no | Secure cookies, HSTS and HTTPS redirect |
| `SIGNUP_REQUIRES_INVITE` | no | Sign-up only from a usable invite link. Default: on at Vercel, off locally |
| `DEBTS_VIEW` | no | Enables debts across sessions and receiver payment confirmation. Default `False` |
| `LOG_LEVEL` | no | Level for `pokernights.*` loggers. Default `INFO` |

Debts across sessions is unreleased. It is not enabled on Vercel. Keep `DEBTS_VIEW=False` for release unless the human opts in at ship time.

Migration `settlement.0011` adds clearance records. Run the normal migration command. No manual backfill is needed.

With the flag off, stored clearances still count in settlement totals. New clearances and clearance undo are disabled. Only hosts can mark a transfer paid or undo a payment.

## Run

```sh
.venv/bin/python manage.py runserver          # http://127.0.0.1:8000
.venv/bin/python manage.py createsuperuser    # optional, for /admin/
```

To let phones on the same Wi-Fi reach it: add the machine's address to `ALLOWED_HOSTS` and run `manage.py runserver 0.0.0.0:8000`. This is for a test at home only. `runserver` is not a production server.

To test debts across sessions locally:

```sh
DEBUG=True DEBTS_VIEW=True .venv/bin/python manage.py runserver
```

## Test

```sh
DEBUG=True .venv/bin/python manage.py test
```

The test runner reports the current test count. SQLite tests use a file-backed database (`test_db.sqlite3`, gitignored). This lets test threads share a database. SQLite skips PostgreSQL-only row-lock tests.

To run the same suite on PostgreSQL:

```sh
/opt/homebrew/opt/postgresql@17/bin/pg_ctl -D /opt/homebrew/var/postgresql@17 -l /tmp/pn_postgres.log -w start
/opt/homebrew/opt/postgresql@17/bin/createdb pokernights        # once
DEBUG=True DATABASE_URL=postgres://$USER@127.0.0.1:5432/pokernights .venv/bin/python manage.py test --noinput
/opt/homebrew/opt/postgresql@17/bin/pg_ctl -D /opt/homebrew/var/postgresql@17 stop
```

Run the full PostgreSQL suite before a release. Its row-lock tests must pass. See [footguns/sqlite_hides_missing_locks.md](footguns/sqlite_hides_missing_locks.md).

Browser fixtures, test tools and commands are in [the browser README](../../web/tests/browser/README.md). Use a fresh temporary database for each flow run. Install the separate browser test tool outside the repository. It is not an application dependency. See [mobile overflow checks](footguns/mobile_browser_overflow_checks.md) when checking narrow layouts.

## Back up the dev database

SQLite runs in write-ahead-log mode, so recent data can sit in `db.sqlite3-wal`. A plain copy of `db.sqlite3` can miss it. Use the backup API:

```sh
python3 -c "import sqlite3; s=sqlite3.connect('db.sqlite3'); d=sqlite3.connect('db.backup.sqlite3'); s.backup(d)"
```

See [footguns/sqlite_copy_misses_the_wal.md](footguns/sqlite_copy_misses_the_wal.md).

## Admin

`/admin/` is for support by a superuser. Money, result, transfer, payment and audit rows are read-only there. All changes to them go through the app.

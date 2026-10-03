# External dependencies

## Python packages

Pinned in `requirements.txt`. Verified against PyPI and against the LightChat reference repository on 2026-10-03.

| Package | Version | Purpose |
|---|---|---|
| `Django` | 6.1.1 | Framework |
| `django-environ` | 0.14.0 | Settings from the environment and `.env` |
| `dj-database-url` | 3.1.2 | `DATABASE_URL` to `DATABASES` |
| `psycopg[binary]` | 3.3.6 | PostgreSQL driver |

There is no other runtime dependency, no JavaScript package and no build tool.

## Services

| Service | Use | Status |
|---|---|---|
| PostgreSQL 17 | Test target, and the database for shared use | Local Homebrew install. Started by hand for test runs (see [setup.md](setup.md)) |

The app calls no external API. It needs no key or secret for local use.

## Not decided

A deployment target is a Stage 5 decision. LightChat's Vercel with Neon PostgreSQL is a known working pattern for this stack. `config/deploy.py` already disables server-side cursors on PostgreSQL, which a pooled Neon URL needs.

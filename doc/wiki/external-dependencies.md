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
| PostgreSQL 17 | Local test target | Local Homebrew install. Started by hand for test runs (see [setup.md](setup.md)) |
| Vercel (Hobby) | Hosting: one Python function in `sin1` and the static CDN | Project `pokernights`. See [deployment.md](deployment.md) |
| Neon Postgres (Free) | Production database, `aws-ap-southeast-1` | Resource `pokernights-db`, added through the Vercel integration |

The app calls no external API. It needs no key or secret for local use. No Python package was added for deployment.

## Local visual assets

- Archivo variable font, from the Google Fonts Archivo source. SIL Open Font License 1.1. A WOFF2 subset includes Latin text, peso and minus symbols. It is hosted locally; no Google Fonts request runs in the app.
- Nine Lucide inline SVG icons. ISC license. Paths are embedded in the presentation template tag; no icon package is installed.
- Licenses: `static/fonts/OFL.txt`, `static/icons/LICENSE`.

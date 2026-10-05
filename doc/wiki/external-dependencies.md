# External dependencies

## Python packages

Pinned in `requirements.txt`. Verified against PyPI and against the LightChat reference repository on 2026-10-03.

| Package | Version | Purpose |
|---|---|---|
| `Django` | 6.1.1 | Framework |
| `django-environ` | 0.14.0 | Settings from the environment and `.env` |
| `dj-database-url` | 3.1.2 | `DATABASE_URL` to `DATABASES` |
| `psycopg[binary]` | 3.3.6 | PostgreSQL driver |

There is no other Python runtime dependency and no build tool.

## JavaScript library

| Library | Version | Purpose |
|---|---|---|
| Turbo (Hotwire, 37signals) | 8.0.23 | Sends marked forms in the background and updates the page in place (stage 3 of the app-like experience) |

- One vendored file, `static/js/vendor/turbo-8.0.23.js` (217 KB, 46 KB compressed), the `turbo.es2017-umd.js` build from the npm package `@hotwired/turbo@8.0.23`. SHA-256 begins `f9e09e3a3093874f`. MIT licence in `static/js/vendor/turbo-LICENSE.txt`.
- No package manager and no build step. To update: download the new build under a new file name with its version, change the one `<script>` in `base.html`, and run every browser check.
- It is the recorded exception to the "no front-end framework" rule in AGENTS.md, approved in the [stage 3 plan](../plan/1791178826_actions_in_place.md).
- Navigation is switched off (`Turbo.session.drive = false`). Only elements marked `data-turbo="true"` use it.

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

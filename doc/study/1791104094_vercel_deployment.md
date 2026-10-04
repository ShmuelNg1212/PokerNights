# Deploying PokerNights on Vercel

Date: 2026-10-04, Asia/Manila. Status: complete. Repository baseline: main `06986a8`, clean working tree, pushed to `origin/main` (public repository `ShmuelNg1212/PokerNights`).

## Outcome

Make PokerNights reachable on the internet through Vercel so a group can use it from their phones. This is the deployment part of roadmap Stage 5. Password reset and claim links are separate Stage 5 items and are not part of this request.

## Sources

- Vercel documentation read on 2026-10-04: [Deploy a Django app](https://vercel.com/docs/frameworks/full-stack/django) (updated 2026-07-24), [Python runtime](https://vercel.com/docs/functions/runtimes/python) (updated 2026-08-12), [Hobby plan](https://vercel.com/docs/plans/hobby) (updated 2026-09-14).
- The human's other project, LightChat (`~/LightChat`, same stack and pins), deployed on Vercel with Neon on 2026-09-29. Its `vercel.json`, `.vercelignore`, `config/deploy.py`, settings and `doc/wiki/deployment.md` are a tested pattern on this account.
- This repository: `config/settings.py`, `config/deploy.py`, `requirements.txt`, the wiki and AGENTS.md.

## What Vercel does for a Django project

- **Detection.** Vercel finds `manage.py`, reads `DJANGO_SETTINGS_MODULE` and loads `WSGI_APPLICATION`. PokerNights already has `config.wsgi.application`. The app becomes one Vercel Function.
- **Python.** 3.12, 3.13 and 3.14 are available; the version comes from `.python-version`, which already says 3.14. Dependencies come from `requirements.txt`.
- **Static files.** With `STATIC_ROOT` set, Vercel runs `collectstatic` in the build and serves `/static/` from its CDN. `STATIC_ROOT` is already set. No WhiteNoise or other package is needed.
- **Build command.** `vercel.json` can run tests and migrations before the new version goes live. A failing command fails the build and the live site keeps its current version.
- **Git.** A connected GitHub repository deploys on every push: `main` to production, other branches to previews.

## What the app is missing

| Gap | Evidence | Remedy (as in LightChat) |
|---|---|---|
| Vercel's host names are not allowed | `ALLOWED_HOSTS` defaults to localhost only | A `vercel_hosts()` helper adds `VERCEL_URL`, `VERCEL_BRANCH_URL` and `VERCEL_PROJECT_PRODUCTION_URL` |
| HTTPS settings are off unless `HTTPS_ONLY` is set | `HTTPS_ONLY` defaults to False | Default it to on when `VERCEL` is set |
| The app would run on a throwaway SQLite file if `DATABASE_URL` were missing | SQLite is the fallback; Vercel's filesystem is not persistent | Refuse to start on Vercel without `DATABASE_URL` |
| No `vercel.json` | none in the repository | Framework, region, build command |
| No `.vercelignore` | none | Keep secrets, local databases, the journal and tool folders out of the upload |
| No deployment page in the wiki | `setup.md` says the app is not deployed | A deployment page with runbooks |

Already in place: PostgreSQL support with `psycopg`, `DISABLE_SERVER_SIDE_CURSORS` for a pooled Neon URL, `SECURE_PROXY_SSL_HEADER` and secure cookies under `HTTPS_ONLY`, a `/healthz` address without login, database-backed sessions, and a refusal to start without `SECRET_KEY` when `DEBUG` is off.

## Database

Vercel's filesystem does not persist, so SQLite cannot be used. The app's rules need PostgreSQL anyway: every session write locks the session row with `select_for_update()`, which SQLite ignores. Neon Postgres through the Vercel integration is the pattern already running for LightChat:

- The app uses the pooled `DATABASE_URL` (PgBouncer in transaction mode) with `DB_CONN_MAX_AGE=0`. Row locks inside `transaction.atomic()` work in that mode.
- Migrations use `DATABASE_URL_UNPOOLED`.
- Git previews get their own Neon branch, so a preview never touches production data. CLI previews share the production database.
- Migrations run before the new version goes live and a rollback does not undo them, so each release must keep the database usable by the previous version (additive changes only).

The players are in the Philippines. Singapore is the nearest region on both services: Vercel `sin1` and Neon `aws-ap-southeast-1`. Function and database should be in the same region.

## Fit with the free plans

- **Vercel Hobby** includes 1,000,000 function invocations, 4 hours of active CPU and 100 GB of transfer a month, a 300-second function limit and 100 deployments a day.
- **Polling.** The set page asks for changes every 4 seconds while it is open. Eight phones open for a five-hour game make about 36,000 requests, most of them answered with "no change". Four game nights a month are about 15% of the invocation allowance. If a limit is exceeded on Hobby the feature pauses until 30 days have passed; nothing is billed.
- **Neon Free** (figures from LightChat's notes of 2026-09-29): 0.5 GB of storage and 100 compute-hours a month; the database sleeps after five idle minutes and takes about half a second to wake. Polling keeps it awake during a game, which costs a few compute-hours per night.
- **Terms.** Hobby is for non-commercial, personal use only. A private tool for friends fits that wording. Whether a game that collects rake counts as commercial under Vercel's fair-use rules is the human's judgement; the app itself records amounts and moves no money.

## Risks

1. **Open sign-up on a public address.** Anyone who finds the address can create an account and a group. They cannot see another group without an invite, but accounts and groups use database space, and there is no rate limit or email check.
2. **No password reset.** The app sends no email. A person who forgets a password needs a superuser to set a new one in `/admin/`.
3. **Concurrency tests do not run in the Vercel build.** The build has no PostgreSQL for tests, so the ten PostgreSQL-only tests are skipped there. They must keep passing locally on PostgreSQL before each release, as the wiki already requires.
4. **Every push to `main` becomes a production release** once Git is connected. AGENTS.md says not to push or deploy without an instruction; that rule then covers every push to `main`.
5. **The repository is public.** No secret is in it. Secrets live only in Vercel's environment variables.
6. **Money data on a free database.** Neon Free has a short point-in-time restore window and no off-site copy. A scheduled export would need a separate plan.
7. **Admin on the internet.** `/admin/` is reachable. Money rows are read-only there, but a superuser password must be strong.

## Options

1. **Vercel + Neon, following LightChat (recommended).** Small, known change: two settings lines, one helper, two configuration files, tests and a wiki page. Free. Auto-deploy from GitHub with tests and migrations as a build gate.
2. **Vercel with CLI-only deploys.** Same code change, but no Git connection; each release is a manual `vercel deploy --prod`. Keeps "no deploy without an instruction" literal, loses automatic previews with their own database branch.
3. **A long-running host** (a small VM or a container platform). Suits polling and persistent connections better, but the human asked for Vercel and the measured load fits the free plan.

## Open questions for the human

1. Sign-up: leave it open, or allow sign-up only through an invite link?
2. Start production with an empty database, or copy the local development data?
3. Connect GitHub so that every push to `main` releases, or deploy only by command?
4. Which Vercel project name (it decides the address `NAME.vercel.app`), and is a custom domain wanted?

## What only the human can do

A Vercel CLI login already exists on this machine, and LightChat's project is under the same account, so the project, the Neon database and the environment variables can be created from here. The human must approve the Neon integration's terms in the browser if Vercel asks, choose the superuser password, and confirm the plan's use terms.

Baseline: 510 SQLite tests pass with ten PostgreSQL-only skips; all 510 pass on PostgreSQL 17.

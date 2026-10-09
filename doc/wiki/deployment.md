# Deployment (Vercel)

PokerNights runs on Vercel's free Hobby plan with a free Neon Postgres database, both in Singapore. Production address: **https://pokernights-five.vercel.app** (released 2026-10-04; [plan](../plan/1791104210_vercel_deployment.md)).

## What runs where

| Piece | Where | Notes |
|---|---|---|
| Django app | One Vercel Function (Python 3.14, WSGI, `config/wsgi.py`), region **`sin1`** (Singapore) | Vercel finds `manage.py` and `WSGI_APPLICATION` by itself |
| Static files | Vercel CDN at `/static/` | Vercel runs `collectstatic` because `STATIC_ROOT` is set. No extra package |
| Database | Neon Postgres (Free), `aws-ap-southeast-1`, resource `pokernights-db` | The app uses the pooled `DATABASE_URL` (PgBouncer). Migrations use `DATABASE_URL_UNPOOLED` |
| Build gate | Every build (`vercel.json` → `buildCommand`) | 1. The full test suite runs on a throwaway SQLite file. 2. Only if it passes, migrations run. A failing test or migration fails the build and the live site keeps its version |

- **Vercel project:** `pokernights` in `shmuelng8310-5097s-projects`. The local link is in `.vercel/` (gitignored).
- **Configuration files:** [`vercel.json`](../../vercel.json) and [`.vercelignore`](../../.vercelignore).
- **Git:** the project is connected to GitHub `ShmuelNg1212/PokerNights`, so every push deploys: `main` to production, any other branch to a private preview.

## Environment variables (Vercel → Settings → Environment Variables)

None are in Git. Names are also in [`.env.example`](../../.env.example).

| Variable | Set by | Purpose |
|---|---|---|
| `SECRET_KEY` | us, sensitive | Random, different for Production and Preview |
| `DB_CONN_MAX_AGE` | us | `0`: hold no database connection between requests; PgBouncer pools. Opening one costs 16 to 33 ms per request (measured 2026-10-06). `60` is being tried; the `?perf=1` readout's `open` figure shows whether it helps. Set back to `0` if anything errors |
| `DATABASE_URL`, `DATABASE_URL_UNPOOLED` (+ `PG*`, `POSTGRES_*`, `NEON_*`) | Neon integration | Connection strings. Only the first two are used |
| `VERCEL`, `VERCEL_URL`, `VERCEL_BRANCH_URL`, `VERCEL_PROJECT_PRODUCTION_URL` | Vercel | Turn on the HTTPS settings, invite-only sign-up, and add the deployment's host names to `ALLOWED_HOSTS` |
| `SIGNUP_REQUIRES_INVITE` | optional | Defaults to on at Vercel. Set `False` to open sign-up to everyone |
| `ANSWER_IN_PLACE` | optional | Defaults to on. Set `False` to answer every in-place action with a redirect again (two trips instead of one), without a release (`config/inplace.py`). Redeploy for it to take effect |
| `PLAYER_ENTRIES` | optional | Defaults to on. Set `False` to make rebuys and final counts host-only again and to ignore counts players already sent, without a release (`ledger/services.py`). Redeploy for it to take effect |
| `RESET_LINKS` | optional | Defaults to on. Set `False` to hide password reset links and refuse every one already sent, without a release (`accounts/services.py`). Redeploy for it to take effect |
| `ROSTER_TOOLS` | optional | Defaults to on. Set `False` to return Group settings → Players to one-name add, rename and remove, without a release (`groups/services.py`). The removal confirmation page stays on. Redeploy after changing it. |
| `CLAIM_LINKS` | optional | Defaults to on. Set `False` to hide claim links and refuse every one already sent, without a release (`groups/services.py`). Redeploy after changing it. |
| `NUMPAD` | optional | Defaults to on. Set `False` to return every number field to the phone's own keyboard without a release (the in-app numpad, `static/js/numpad.js`). Redeploy for it to take effect |
| `DEBUG` | never set | Off |

To replace a sensitive value, remove it and add it again. A change takes effect on the next deployment.

```sh
npx vercel@latest env rm SECRET_KEY production
python3 -c "import secrets;print(secrets.token_urlsafe(64),end='')" | npx vercel@latest env add SECRET_KEY production --sensitive
```

## Production settings (automatic on Vercel)

When `VERCEL` is set, `config/settings.py` trusts `X-Forwarded-Proto`, redirects to HTTPS, marks session and CSRF cookies `Secure`, and sends HSTS for one year (this host only). `manage.py check --deploy` is clean with these settings and `config/tests.py` enforces it. The app refuses to start on Vercel without `DATABASE_URL`.

## Static files and caching

- Stylesheet and script addresses carry `?v=<release>` on Vercel (`config.storage.VersionedStaticStorage`, tag from `config.deploy.static_version`). `vercel.json` caches `/static/css/` and `/static/js/` for a year as immutable.
- Fonts, branding and icons are cached for a week with background revalidation and are not versioned. **To change a font or a logo, give the file a new name.**
- On Vercel with no deployment id, commit or URL to derive the tag from, the app refuses to start, so the build fails and production keeps its version.
- The web app manifest is cached for a day with background revalidation.
- HTML is never cached.
- Locally and in tests there is no tag and addresses are plain.

## Service worker and its kill switch

`/sw.js` is served by the Django function with `Cache-Control: no-cache`. If the worker ever misbehaves on phones: set the environment variable `SERVICE_WORKER=False` in Vercel and redeploy. The next visit from each phone then removes the worker and its cache. Remove the variable to turn it back on.

App icons live under `/static/icons/` and are cached for a week without a version tag. To change the icon art, render new files under new names and update `base.html` and the manifest.

## Who can get in

Sign-up works only from a usable invite link (not revoked, expired or used up). Anything else answers 403 with an explanation. The first host of a group is added by a superuser: `/admin/` → Users → Add user. That person logs in, creates a group and sends invite links from Group settings. There is no password reset by email. A host creates a one-use reset link for a member in Group settings and sends it; Sign up and a refused login say so. A superuser still sets the password in `/admin/` for a site administrator, for a person who hosts more than one group, and for a group's only host.

A signed-out visitor who opens a usable invite link lands on Sign up, and the new account joins that group at once. A person who already has an account logs in and confirms on the Join page. Where sign-up needs an invite, Log in offers the Sign up link only when the visit carries a usable one.

## Releasing a change

**Run the suite the way the build does before every push.** On Vercel the tests run with `VERCEL` set, which adds `?v=<release>` to stylesheet and script addresses. A test that passes locally can fail there:

```sh
VERCEL=1 VERCEL_URL=example.vercel.app HTTPS_ONLY=False DATABASE_URL=sqlite:////private/tmp/pn-buildlike.sqlite3 .venv/bin/python manage.py test --noinput
```

On 2026-10-05 a test that asserted the plain stylesheet address failed the build of `6a3f24b`. Production kept the previous version, as designed, and the fix followed. A failed build is silent: after a push, check that the live site actually changed.

1. Work on a branch. Run `.venv/bin/python manage.py test`, and the PostgreSQL suite when the change touches writes or locking (see [setup.md](setup.md)). **The Vercel build skips the ten PostgreSQL-only tests**, so the local PostgreSQL run is the only gate for concurrency.
2. Push the branch. Vercel builds a private preview. Preview addresses need a Vercel login.
3. Merge into `main` and push. Vercel runs the tests, then the migrations, then switches production to the new version.

**A push to `main` is a release.** The agent asks before every push.

One-off deploys from a folder: `npx vercel@latest deploy --target preview`, or `--prod`. Always name the target: a new project's first plain `vercel deploy` goes to production.

### Database changes: additive only

Migrations run on the production database before the new version goes live, and a rollback does not undo them. Each release must keep the database usable by the previous version: add tables, nullable columns, columns with defaults and indexes freely; remove or rename a column in a later release than the code that stops using it.

### Preview databases

CLI previews **share the production database** (verified 2026-10-04: both environments pointed at the same Neon host), and their build migrates it. Do not create test data on a CLI preview once production holds real games. Git previews use a Neon branch only if preview branching is turned on for the resource in the Neon integration; check before relying on it.

## Rollback (a bug in production)

1. Vercel → project **pokernights** → Production tile → **Instant Rollback**, or `npx vercel@latest rollback`. The previous version serves again in seconds. On Hobby this goes back one release; for older, `git revert` the bad commit and push.
2. While rolled back, pushes to `main` build but do not go live.
3. Push the fix, then **Undo Rollback** and pick the fixed deployment, or `npx vercel@latest promote <deployment-url>`.
4. Rollback restores code only. For a bad migration, deploy a forward fix or restore the database in the Neon console.

## A leaked secret or abuse

Rollback does not help: an old deployment keeps the variables it was built with.

1. **Close the site:** Vercel → Settings → Deployment Protection → **All Deployments**. Every address then needs a Vercel login.
2. **Rotate:** replace `SECRET_KEY` as shown above (this signs everyone out). For the database password: Neon console → Roles → reset; the integration updates `DATABASE_URL*`.
3. **Redeploy**, check, then set protection back to **Standard Protection**.
4. **Review:** `/admin/` → Users and Audit events, and Vercel → Logs.

## Commands against production

Run them locally with the direct connection string from Vercel → Storage → `pokernights-db` → `.env.local` tab (`DATABASE_URL_UNPOOLED`). Do not save it in the repository.

```sh
DATABASE_URL='postgresql://…' DEBUG=False SECRET_KEY=any-long-local-value-for-this-command-only \
  .venv/bin/python manage.py createsuperuser
```

## Limits to know

| Limit | Value | Effect |
|---|---|---|
| Vercel Hobby | 1,000,000 function invocations, 4 h active CPU, 100 GB transfer a month; non-commercial use | A set page polls every 4 s. Eight phones for five hours are about 36,000 requests. Past a limit the feature pauses until 30 days pass; nothing is billed |
| Neon Free | 0.5 GB storage, 100 compute-hours a month; sleeps after 5 idle minutes | The first request after idle waits about half a second. Short restore window; no off-site copy |
| Runtime logs (Hobby) | 1 hour | Look soon after a problem |

## Verified on 2026-10-04 (private preview)

- Build: 518 tests passed in the Vercel build (ten PostgreSQL-only skips), then all migrations applied to Neon.
- HTTP: `/healthz` 200; login 200; sign-up without an invite 403; CSS, logo and admin CSS served from `/static/`; `/.env`, `/db.sqlite3`, `/doc/…` and `/manage.py` 404; `Strict-Transport-Security`, `Secure` CSRF cookie, `X-Frame-Options: DENY`, `nosniff`; served from `sin1`.
- A full game in two phone-sized browsers, 26 of 26 checks: host login, group, table, roster player, invite link on https, sign-up from the invite, join, session, opening buy-ins, the second browser seeing the start through polling, rebuy, count-up, batch cash-out, balanced books, finalize, close, transfers marked paid to Settled, Your groups record, Stats, and `/admin/` refusing a non-staff account.
- Polling on one set page for three minutes: 44 requests, median 109 ms, 95th percentile 179 ms.
- The test data was removed afterwards; the database is empty with all migrations applied.


## 2026-10-05 release — numpad and count-up

Released `4a80de9` through the GitHub push to `main`. Deployment `dpl_C6m2u66yzgQSSXqjCUPog5EtETXu` reached Ready and was assigned https://pokernights-five.vercel.app. The Vercel build passed 677 tests with ten PostgreSQL-only skips, then reported no migrations to apply. All 677 had passed on local PostgreSQL 17 before release; the exact Vercel-style run also passed locally.

The release adds the in-app numpad, even host-control gaps, player-first count-up, explicit review verdicts and a Finalize confirmation. `NUMPAD=False` remains the fallback after redeployment. Real iPhone acceptance remains open. See the [plan](../plan/1791202390_host_gaps_numpad_count_up.md).


Live read-only checks: `/healthz` and Log in return 200, sign-up without an invite returns 403, HSTS is present, and the versioned app CSS and numpad script return 200. Their tag `ce4bbb73ee` matches the SHA-256-derived tag of the Ready deployment ID; the Log in document has `data-numpad="on"`. No production game data was created or changed.

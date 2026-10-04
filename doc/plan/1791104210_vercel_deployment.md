# Deploying PokerNights on Vercel: plan

Status: awaiting approval. Date: 2026-10-04, Asia/Manila. Study: [Deploying PokerNights on Vercel](../study/1791104094_vercel_deployment.md).

## Outcome

PokerNights runs at a public HTTPS address on Vercel with a Neon PostgreSQL database in Singapore. A release happens only when its tests pass and its migrations apply. The human can sign in, create a group and run a game from a phone. Runbooks exist for release, rollback and a leaked secret.

## Decisions I need from you

1. **Sign-up.** I recommend **invite-only sign-up plus one way in for a new host**: the sign-up page works when it is reached from a valid invite link, and a superuser creates the first host accounts in `/admin/`. This keeps strangers from filling the database. The alternative is to leave sign-up open as today, which needs no code change.
2. **Starting data.** I recommend an **empty production database**. The local data is test data (`hana`, `ben`, "Browser Check").
3. **Releases.** I recommend **connecting GitHub**: a push to `main` releases after the tests pass; a branch push makes a private preview with its own database branch. From then on "push to main" means "release", and I will keep asking before every push.
4. **Name and domain.** I propose the project name `pokernights`. Vercel gives the address `pokernights.vercel.app` if it is free, otherwise a variant. No custom domain in this cycle unless you want one.
5. **Plan terms.** Vercel Hobby is for non-commercial, personal use. Please confirm that this use fits, given the group may collect rake.

## What changes in the repository

Each step is one Conventional Commit, with the full SQLite suite and `manage.py check` before it. No model, migration, URL or money-rule change, and no new dependency.

1. `feat(config): prepare settings for Vercel`
   - `config/deploy.py`: `vercel_hosts(environ)` returns the host names Vercel assigns.
   - `config/settings.py`: add those hosts to `ALLOWED_HOSTS`; default `HTTPS_ONLY` to on when `VERCEL` is set; refuse to start on Vercel without `DATABASE_URL`.
   - `config/tests.py`: the helper; `check --deploy` is clean with the settings a Vercel deployment gets; the refusal without a database.
   - `.env.example` and `.gitignore`: document `DATABASE_URL_UNPOOLED`; ignore `.vercel/` and `.env.local`.
2. `build: add Vercel project configuration`
   - `vercel.json`: `framework: django`, region `sin1`, and a build command that runs the full test suite on a throwaway SQLite file, then `migrate` over `DATABASE_URL_UNPOOLED`.
   - `.vercelignore`: secrets, local databases, `.venv`, `doc/`, `.impeccable/`, `.claude/`, editor folders and `staticfiles/` stay out of the upload. Tests stay in, because the build runs them.
3. Only if you choose invite-only sign-up: `feat(accounts): limit sign-up to invite links`
   - This is a behavior change with its own tests: sign-up without a valid invite shows a short explanation instead of the form; the invite flow is unchanged. I will add a short dated addendum to this plan with the exact rule before building it.
4. `docs: add deployment page and runbooks`
   - `doc/wiki/deployment.md`: what runs where, environment variables, releasing, additive-only migrations, preview databases, rollback, a leaked secret, admin commands against production, limits.
   - Update `setup.md`, `external-dependencies.md`, the wiki index, the roadmap (Stage 5 deployment done; password reset and claim links remain), TODO and AGENTS.md's command and deploy notes.

## What happens on Vercel and Neon

In this order, each step checked before the next:

1. Create the Vercel project `pokernights` under your existing account with the CLI and link this folder (`.vercel/` is ignored by Git).
2. Add the Neon integration with a database in `aws-ap-southeast-1`. It sets `DATABASE_URL` and `DATABASE_URL_UNPOOLED`.
3. Set environment variables for Production and Preview: a fresh random `SECRET_KEY` for each (marked sensitive) and `DB_CONN_MAX_AGE=0`. `DEBUG` stays unset, so it is off.
4. Make a first **preview** deployment from a branch. Check it before anything is public.
5. With your go-ahead, connect the GitHub repository and release `main` to production.
6. Create your superuser against the production database. You type the password yourself; I never see or store it.

## Verification

- Local: SQLite suite, PostgreSQL suite, `check --deploy` with the Vercel settings, migration-drift check.
- Preview, then production, with a script and by hand on a phone-sized browser: `/healthz`; HTTPS redirect, secure cookies and HSTS; static files and the favicon served from `/static/`; sign-up or invite flow as decided; create a group, a table and a session; buy-in, rebuy, cash-out; a second browser sees the change through polling; end play, count, finalize, close, mark a transfer paid; Stats and Your groups; `/admin/` login; a wrong host name is refused; no `.env`, database file or journal is served.
- A 30-minute polling run on one set page to measure function invocations and active CPU against the Hobby allowance, recorded in the progress notes.
- Rollback rehearsal on the preview project: release a harmless change, roll back, undo.

## Acceptance criteria

- AC1. The production address serves the app over HTTPS and `check --deploy` is clean.
- AC2. A build with a failing test or migration does not replace the live version.
- AC3. Data survives a redeploy; production uses PostgreSQL in Singapore, and the app refuses to start on Vercel without a database.
- AC4. A full game (buy-ins through settle-up) works on production from a phone-sized browser, and a second browser sees changes within about five seconds.
- AC5. Sign-up behaves as you decided.
- AC6. No secret is in the repository or served by the site; secrets exist only in Vercel's environment variables.
- AC7. The wiki has the deployment page with release, rollback and leaked-secret runbooks, and each was tried once.
- AC8. All existing tests pass on SQLite and PostgreSQL.

## Exclusions and rollback

Not in this cycle: password reset by email, claim links for roster players, a custom domain, scheduled database exports, rate limiting, and any change to polling. They stay on the roadmap.

Roll back code by reverting the commits; the settings changes do nothing off Vercel. Roll back a release with Vercel's Instant Rollback. To take the site offline, turn on Deployment Protection for all deployments. Deleting the Vercel project and the Neon database removes everything that was created; I will not delete either without your instruction.

## Progress and blockers

2026-10-04: Study and plan complete. Implementation and all actions on Vercel and Neon await approval of this plan and the five decisions above.

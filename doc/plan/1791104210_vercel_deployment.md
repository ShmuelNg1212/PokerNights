# Deploying PokerNights on Vercel: plan

Status: approved 2026-10-04. Date: 2026-10-04, Asia/Manila. Study: [Deploying PokerNights on Vercel](../study/1791104094_vercel_deployment.md).

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

2026-10-04: Human approved this plan with “approved. I agree with the defaults.” Decisions: invite-only sign-up with first hosts created in `/admin/`; empty production database; GitHub connected so a push to `main` releases; project name `pokernights`, no custom domain; the Hobby plan's personal-use terms accepted by the human. Execution uses branch `feat/vercel-deploy`, worktree `/private/tmp/pn-vercel`. The production release and the superuser password still need the human at the time.

## 2026-10-04 addendum — the invite-only sign-up rule (step 3)

- A setting, `SIGNUP_REQUIRES_INVITE`, read from the environment. It is on by default on Vercel and off elsewhere, so local development and the existing tests keep open sign-up.
- When it is on, the sign-up page shows its form only if `next` points at an invite address (`/join/<token>/`) whose invite can still be used: not revoked, not expired, not used up. The same check runs again when the form is posted.
- Otherwise the page answers 403 with one sentence and a link to log in. No account is created.
- The invite itself is not used up by signing up. It is used when the new person accepts it on the next page, as today.
- First hosts: a superuser adds the account in `/admin/` → Users. That person logs in, creates a group and sends invite links.
- `accounts` must not import `groups` (design rule 11). `accounts` keeps a small list of checks; `groups` registers its invite check when the app loads, the same way `games.clock.SKIP_ON_RESUME` works.
- No model, migration or URL change.

2026-10-04 execution, branch `feat/vercel-deploy`:

1. `303901a` settings for Vercel with three tests. 2. `4ab8001` `vercel.json` and `.vercelignore`. 3. `3e8bd87` invite-only sign-up with five tests. 4. `15b42f5` tests no longer depend on the build environment.

On Vercel and Neon:

- Project `pokernights` created and linked. Neon `pokernights-db` (Free, `sin1`, auth off) connected to Production and Preview. `SECRET_KEY` (random, sensitive, different per environment) and `DB_CONN_MAX_AGE=0` set for both.
- **First deploy mistake.** A plain `vercel deploy` on the new project targeted production. Its build failed at the test gate (seven tests saw `VERCEL=1` and got invite-only sign-up), so nothing went live and no migration ran. The tests were fixed (`15b42f5`) and every later deploy names its target.
- The Neon integration wrote `.agents/`, `.claude/skills/` and `skills-lock.json` into the worktree. They were not asked for and were deleted, uncommitted.
- Preview `pokernights-lkixhct6c-…vercel.app`: build ran 518 tests, then all migrations.

2026-10-04 verification: local SQLite 518 pass (ten PostgreSQL-only skips), also under the build's variables. Preview HTTP checks, a 26-check full game in two browsers and a three-minute polling measurement are recorded in `doc/wiki/deployment.md`. The CLI preview shares the production database; its two test users and one test group were removed with `flush`, leaving an empty migrated database. Local copies of the database credentials and the test password were deleted.

Deviations from the plan: the polling measurement ran three minutes, not thirty, and read client-side timings only; function invocations and active CPU on Vercel's side were not read. The rollback rehearsal needs a production release first and is still to do. The local PostgreSQL suite is run before the merge (next entry).

2026-10-04: PostgreSQL 17 (temporary local instance, now stopped): all 518 tests pass. Documentation synced: new `doc/wiki/deployment.md`; setup, external dependencies, wiki index, features, roadmap, TODO and AGENTS.md updated.

2026-10-04 rendezvous: merged into local main as `ef35d53 feat: merge Vercel deployment preparation`. Main SQLite: 518 pass, ten PostgreSQL-only skips. Not pushed. Waiting for the human's go-ahead to connect GitHub and release `main` to production, then for the human to create the superuser. AC2, AC5, AC6 and AC8 are met; AC1, AC3 and AC4 are met on the preview and still to confirm on production; AC7's runbooks are written, the rollback rehearsal is still to do.

2026-10-04 release: the human said “release”. GitHub `ShmuelNg1212/PokerNights` connected to the project; `main` pushed at `170d371`. The production build ran 518 tests (ten skips), found no migrations to apply and went live at **https://pokernights-five.vercel.app** (`pokernights.vercel.app` was taken). Production checks without any bypass: `/healthz` 200; `/` redirects to login; sign-up 403; CSS and logo 200; `/.env`, `/db.sqlite3`, `/manage.py` and `/doc/…` 404; http redirects to https; HSTS, `nosniff`, `X-Frame-Options: DENY`, Secure cookies; a wrong Host header is refused; served from `sin1`. No game was played on production, to keep its database free of test data; the full game was verified on the preview, which runs the same code against the same database.

2026-10-04 rollback rehearsal on production: a docs-only release (`8e75aaf`, deployment `ehx7bmcmo`) went live through the build gate. `vercel rollback` returned production to the first release (`f3p3bfy04`) in about two seconds; `/healthz` answered 200 throughout. `vercel promote` put `ehx7bmcmo` back. The address serves the newest release again. The leaked-secret runbook was written but not rehearsed, because closing the site and rotating the key would sign everyone out for no benefit on an empty site. AC1, AC2, AC3, AC5, AC6 and AC8 are met on production. AC4 was met on the preview only. AC7: release and rollback were tried; the leaked-secret steps were not. Open for the human: create the superuser and play a first game on the live site.

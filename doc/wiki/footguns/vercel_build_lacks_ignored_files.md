# The Vercel build runs the tests without the ignored files

Date: 2026-10-14, Asia/Manila.

**Trigger.** A Django test opens a file under a path that `.vercelignore` leaves out: `web/tests/browser/`, `doc/`, `.impeccable/`, `.claude/`.

**Observed behavior.** The test passes locally on SQLite and PostgreSQL. On Vercel the build command runs the tests before the migrations, the file is not there, and the build fails. The release of `ba7e297` (the launch screen) failed this way: `test_the_renderer_draws_the_same_sizes` reads `web/tests/browser/make_splash.mjs`. Production kept the previous build, so the live site served a 404 for the new images four minutes after the push.

**Impact.** Nothing breaks for anyone, but the release silently does not happen. The only sign from this machine is the live check after the push.

**Remedy.** A test that reads a file from an ignored path is skipped when the file is absent (`@skipUnless(os.path.exists(...))`), with a comment naming `.vercelignore`. To run a suite as Vercel does, move `web/tests/browser/` aside for the run. Fixed in `c222173`.

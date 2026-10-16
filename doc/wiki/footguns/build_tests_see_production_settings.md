# The Vercel build's tests see production's settings

**What happened (2026-10-16).** Table alerts in the header passed 1,216 tests locally on SQLite and PostgreSQL, then failed the Vercel build. The build runs `manage.py test` with the project's environment variables, and production sets `VAPID_PUBLIC_KEY` and `VAPID_PRIVATE_KEY`. With both keys set, the bell renders on every signed-in page. Its empty error line carried `role="alert"`, and `test_end_set` asserts that a balanced page has no alert. Locally the keys are unset, so the bell was absent and the test passed. Production stayed on the previous release, because a failed build deploys nothing.

**Remedy.** A part of the page that a setting turns on, and that is on in production, needs tests run with that setting on. For table alerts, run the suite with the keys exported:

```sh
.venv/bin/python -c "..."   # any valid pair, as in web/tests/browser/README.md (table alerts)
VAPID_PUBLIC_KEY=... VAPID_PRIVATE_KEY=... .venv/bin/python manage.py test
```

For markup shared by every page (the header, `base.html`), give it no `role="alert"`, `autofocus` or other page-wide marker until it is used. `web/tests/test_table_alerts.py` checks the bell for this.

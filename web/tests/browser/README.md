# Browser checks

Use a **fresh temporary database**, never the development database. The fixture creates synthetic host `hana`, player `ben`, and five sets. These dependency-free Node scripts drive installed Chrome through CDP. The scripts close only their own browser process.

From the repository root, with the existing Python environment:

```sh
DEBUG=True DATABASE_URL=sqlite:////private/tmp/pn-rack-check.sqlite3 .venv/bin/python manage.py migrate --noinput
DEBUG=True DATABASE_URL=sqlite:////private/tmp/pn-rack-check.sqlite3 .venv/bin/python manage.py shell < web/tests/browser/seed.py
DEBUG=True DATABASE_URL=sqlite:////private/tmp/pn-rack-check.sqlite3 .venv/bin/python manage.py runserver 127.0.0.1:8765 --noreload
```

After the edit batch, restart the server to clear compiled templates. In another terminal:

```sh
node web/tests/browser/rack.mjs
node web/tests/browser/rack_accessibility.mjs
```

Run sequentially: both use port 9341. Override `PN_CHROME_PATH`, `PN_BROWSER_URL` or `PN_REVIEW_DIR` when needed. The first script captures the phone, desktop, sheet and representative regression screens. The second measures contrast, keyboard wrapping, reduced motion, layout stability, live count typing, stale polling and JavaScript-free actions. Both use the seeded set IDs and synthetic fixture credentials.

The fixture is intended for one verification run. The service requests are real writes to that temporary database. Start with another fresh temporary database for a repeatable run.

For visual redesign slice 2, seed the additional end-of-set states after `seed.py`:

```sh
DEBUG=True DATABASE_URL=sqlite:////private/tmp/pn-rack-check.sqlite3 .venv/bin/python manage.py shell < web/tests/browser/seed_end_set.py
node web/tests/browser/end_set.mjs
```

`seed_end_set.py` adds sets 6–11: chips counting with an earlier partial cash-out, no money, balanced books, a discrepancy, an override, and long names with large amounts. `end_set.mjs` captures the count-up, review and finalized layouts at 390 and 1280 px, plus the 320 px large-content case and player views. It checks deferred live updates, draft retention after refusal, multi-count submission with zero and empty fields, stale review rejection, keyboard focus, dock guidance/clearance, reduced motion and the once-only balance rule. It also performs counts, batch review, finalization and a final cash-out reversal without JavaScript.

The script expects those exact fixture IDs and consumes its counting fixtures. Use another fresh temporary database for the confirmation run. Its overflow checks compare against the requested device width, because mobile Chrome can expand `innerWidth` when content overflows. Full-page capture uses CDP's content dimensions; the fixed dock appears at its viewport position within the tall image.

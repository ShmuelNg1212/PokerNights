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


For slices 3 and 4, seed the session and remaining-screen states after both seeds above:

```sh
DEBUG=True DATABASE_URL=sqlite:////private/tmp/pn-rack-check.sqlite3 .venv/bin/python manage.py shell < web/tests/browser/seed_night.py
DEBUG=True DATABASE_URL=sqlite:////private/tmp/pn-rack-check.sqlite3 .venv/bin/python manage.py shell < web/tests/browser/seed_remaining.py
```

Start the temporary server after seeding. Run these scripts sequentially:

```sh
node web/tests/browser/night.mjs
node web/tests/browser/remaining.mjs
node web/tests/browser/remaining_supplement.mjs
node web/tests/browser/remaining_actions.mjs
```

`night.mjs` checks the session overview, settlement, paid/Undo, frozen results, recap and native fallback. `remaining.mjs` captures home, group, accounts, invitation recovery, supporting forms, picker, canceled set and log. It checks 48 px action links, first-viewport session access, bound errors and native roster actions. `remaining_supplement.mjs` captures the one-time invite URL, invitation acceptance, reversed large-money final log and override log. `remaining_actions.mjs` exercises account/group/table creation, pesos and chips presets, new session, settings refusal and save, rename refusal and save, and native picker refusal and success.

The default run reports 20 Rack, 13 accessibility, 47 end-set, 53 night, 95 remaining, 10 supplement and 12 action checks (250 total). For the complete run, seed all four files before starting, then run all seven browser scripts in the order above and in the first examples. Fixtures are consumed: reset to a fresh database for a repeat. The remaining scripts read synthetic IDs from `/private/tmp/pn-slice4-manifest.json`; night checks use `/private/tmp/pn-slice3-manifest.json`. `PN_EMPTY_ACCOUNT` can select a fresh synthetic account for an empty-home recapture when an earlier invitation run has consumed `unattached`.


For default opening buy-ins, seed after `seed.py`, `seed_end_set.py` and `seed_night.py` on a fresh temporary database:

```sh
DEBUG=True DATABASE_URL=sqlite:////private/tmp/pn-rack-check.sqlite3 .venv/bin/python manage.py shell < web/tests/browser/seed_opening.py
node web/tests/browser/opening.mjs
node web/tests/browser/opening_drafts.mjs
```

`opening.mjs` checks the default and exact amount, phone/desktop fit, native start, mixed existing buy-ins, exact retry, log, a new set, opt-out and chips (16 checks). `opening_drafts.mjs` checks that another host’s write and live redraw preserve the unchecked option and that native submission then records no extra opening buy-ins (3 checks). Run sequentially; each consumes separate synthetic fixtures named in `/private/tmp/pn-opening-manifest.json`. Reset the temporary database for a repeat.

For the live counted total, seed `seed_counts.py` after the normal fixtures and run `counts.mjs` sequentially with the other Chrome scripts. The fixture writes `/private/tmp/pn-counts-manifest.json` and isolates its own pesos/chips sets. Checks cover immediate input, saved fallback, zero, invalid syntax, exact large amounts, partial cash-outs, confirmation and batch recording, two-host polling, refused-default draft retention, no-JS baseline and phone/desktop placement. Captures cover 390 px pesos/chips and 1280 px pesos. Use a fresh temporary database for each fixture run.

For late-player addition, seed `seed_late_player.py` after `seed.py` on a fresh temporary database, then run `late_player.mjs`. The manifest is `/private/tmp/pn-late-manifest.json`. Separate running/full/stale/chips fixtures verify visible entry with an exhausted roster, native new-name creation, separate buy-in, group persistence, duplicate/local error, full table, another host ending play, polling arrival, existing roster selection and player permissions. Captures cover the picker at 390/1280px and duplicate-name recovery at 390px. Run sequentially with other Chrome checks; the fixture is consumed.


For rake, use a fresh temporary database and run `seed_rake.py` independently (without the older seeds). Run `rake.mjs`, then `rake_extra.mjs` sequentially against that server. The fixture writes `/private/tmp/pn-rake-manifest.json`. The main story has 36 checks and 17 phone/desktop captures: native percentage settings/error/locking, automatic/manual/rebuy/late deductions, draft-preserving two-host count preview, batch review, finalization, equal-loss settlement, flat chips, Off and separate group lifetime totals. The supplemental 12 checks cover inherited rules, mixed Off/rake sessions, and native percentage/flat finalization and closure in both units. Use `PN_BROWSER_URL` to select the server and `PN_REVIEW_DIR` for captures. All fixture accounts/data are synthetic. Reset the database for a repeat.

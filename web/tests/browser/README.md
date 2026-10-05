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

For the rake control fix, migrate a fresh temporary database and seed `seed_rake.py`, then serve it and run `rake_controls.mjs` with `PN_BROWSER_URL` pointing to that server. Do not reuse the fixtures for another run. This verifies native New session and settings choices, inactive stale values, initial opening fees, next-set inheritance/editing, locked controls and keyboard radio use. It captures creation, errors, settings, pre-start and locked states at 390/1280px. `PN_REVIEW_DIR` selects the capture directory.

For the collapsible host dock, seed a fresh temporary database with `seed.py`, `seed_end_set.py`, `seed_night.py`, `seed_remaining.py`, `seed_opening.py` and `seed_counts.py`, then run `dock.mjs` (175 checks since 2026-10-05, including the slide, reduced motion, the button-styled options and the iPhone keyboard, which is a stand-in `visualViewport` reporting a 336px keyboard; `__pan` slides its visible frame as a scroll with the keyboard open does, and the checks cover the bar staying a bar, the page keeping its length, the bar following without an event, a single frame watcher, focus-only scrolling and the `?kb=1` readout). It reads both manifests in `/private/tmp` and uses its own Chrome profile (`/private/tmp/pn-dock-chrome`); delete that profile before a run so cached scripts are not reused. The checks at 320, 390 and 1280 px cover both dock states in draft, open, in-play and count-up sets, clearance of the last link, overflow against the requested width, reload, a live update from a second session with focus kept, the choice carried from open to count-up, the typed verdict in the collapsed bar, desktop, refused storage, no JavaScript and a player. The run starts and ends the `default` opening set and records one buy-in on set 3, so use a fresh database for a repeat.

On 2026-10-04 the older scripts were found stale on unmodified `main`: `rack.mjs` (8-player height limit, then a crash), `end_set.mjs` (the removed slate contrast pair), `opening.mjs`, `opening_drafts.mjs` and `counts.mjs` (each stops on a selector that no longer exists). They report the same results with the dock change, apart from two dock-clearance checks that now pass.

For archive and delete, seed a fresh temporary database with `seed.py`, `seed_end_set.py`, `seed_night.py` and `seed_archive.py`, delete `/private/tmp/pn-archive-chrome`, then run `archive.mjs` (85 checks). The fixture writes `/private/tmp/pn-archive-manifest.json`: a closed session with unpaid transfers, two canceled sessions without money, a session in play, an empty group and a group with a long unbroken name. The script archives and restores the session and compares the Stats tab before, during and after; deletes one empty session with JavaScript and one without; and archives, restores and deletes the empty group. It consumes its fixtures.

For the entry pages, seed a fresh temporary database with `seed.py` and `seed_entry.py`, delete `/private/tmp/pn-entry-chrome`, then run `entry.mjs` (81 checks). The fixture writes `/private/tmp/pn-entry-manifest.json` with a usable invite, an invite to a group with a 60-character unbroken name and an expired invite. The script covers Log in and Sign up with and without an invite at 320, 390 and 1280 px, contrast, the Show button, keyboard order, refused login and sign-up, the invite flow from link to group as a new account, the join page and its error, and login without JavaScript. It creates the account `newcomer`.

Since 2026-10-04 the shared login line in every script submits with `form.form-section [type=submit]`, because the Show button is now the first button in the login form.

For the settle status, seed a fresh temporary database with `seed.py`, `seed_end_set.py` and `seed_night.py`, delete `/private/tmp/pn-settled-chrome`, then run `settled.mjs` (24 checks): the Past sessions rows at 320, 390 and 1280 px, all three statuses, agreement between each row and its session page, and a row changing after the last paid mark and after undo.

For the stakes forms, seed a fresh temporary database with `seed.py`, delete `/private/tmp/pn-form-chrome2`, then run `session_form.mjs` (69 checks): New session, Set settings and the preset form at 320, 390 and 1280 px, field edges and heights, pairs, a refused pair, locked settings, keyboard order and submission without JavaScript. It creates one session. Chrome does not reproduce the iPhone date control; that needs a real phone.

Since 2026-10-05 `entry.mjs` has 91 checks and follows the new flow: a newcomer goes link → Sign up → group; the seeded account `visitor` goes link → Sign up → “Log in” → Join → group. `seed_entry.py` creates `visitor`.

For the installable app, seed a fresh temporary database with `seed.py`, `seed_end_set.py` and `seed_night.py`, then run `install.mjs` (33 checks). It uses Chrome's default profile context, because Chrome never calls an incognito page installable, and it stops and restarts the Django server on port 8765 itself to produce failed navigations and to turn the kill switch on (`PN_DB` names the SQLite file; default `/private/tmp/pn-dock-check.sqlite3`). It checks Chrome's own installability report, the worker's scope and cache contents, a way back on 17 screens, the refresh on return and its exceptions, the offline notice, the offline page with Try again, and the kill switch. `make_icons.mjs` renders the PNG icons from the SVG.

For actions in place, seed a fresh temporary database with `seed.py`, `seed_end_set.py`, `seed_night.py` and `seed_opening.py`, then run `inplace.mjs` (37 checks). It restarts the Django server on port 8765 itself to produce a failed send. It covers a rebuy from a sheet (no reload, position, typed text, open sections, requests), a fresh request id on the next rebuy, a refused amount, a double tap, a slow answer, the poll after an update, two hosts, a failed send and its retry, a floating error, set transitions, count confirmation, a success message, mark paid and undo, links still loading pages, and the native form with JavaScript off. `probe_rebuy.mjs` prints the before-and-after measurement used in the stage 3 study.

For screen changes, seed a fresh temporary database with `seed.py`, `seed_end_set.py`, `seed_night.py` and `seed_opening.py`, then run `navigate.mjs` (37 checks; it restarts the server on port 8765 itself). It walks the app by tapping links and requires no document load, makes 22 screen changes and counts poll loops, dialogs and script errors, checks pages reached by a tap behave as after a fresh load, Back and Forward with a figure changed by a second host, scroll restoration, the announcement and focus, the loading line, an anchor link, a page outside the app, forms that lead elsewhere, an expired login, the offline page, and plain links without JavaScript. `lifetime.mjs` (22 checks, after `seed.py`, `seed_end_set.py`, `seed_night.py`) restarts every page script repeatedly on one page. `probe_leak.mjs` and `probe_navtime.mjs` print the measurements used in the stage 4 study.

Since link navigation, a click on a link no longer loads a document. A script that needs to know a page arrived should check the address and the content, not a marker on `window`.

For the motion system, seed a fresh temporary database with `seed.py`, `seed_end_set.py`, `seed_night.py` and `seed_opening.py`, then run `motion.mjs` (34 checks). It logs every `Motion.animate` call, so it can say which element moved and with which properties. It covers the button press and release, the busy line, the sheet's rise, rest, leave and a close mid-rise, an action sent during the rise, toasts arriving, stacking and leaving, the nudge on a refused amount, the dock's spring, ten screen changes, 1280px, reduced motion and a blocked Motion file. It records several buy-ins on set 3, so use a fresh database for a repeat. It cannot judge how the motion feels.

For motion on the live set page, seed a fresh temporary database with `seed.py` and `seed_flow.py`, serve it, then run `flow.mjs` (52 checks). `PN_DB` names the SQLite file (default `/private/tmp/pn-flow-check.sqlite3`): the "other host" is a second process that writes through the real services, and the page under test learns of each change by polling, which the script asks for at once instead of waiting 4 seconds. The fixture writes `/private/tmp/pn-flow-manifest.json` with six sets. The script reads every redraw on its first frame (in `requestAnimationFrame`, because Motion starts an animation on the frame after it is asked): what each row shows, how far it is from its place and how opaque it is. It covers arrivals and their 40ms stagger, rows sliding after a cash-out, a tap on a moving row, a rebuy by the other host and by you, the mark fading, a player joining, a state change, typing, a confirmed count, the books balancing once, twenty redraws, a hidden tab, 1280px, reduced motion and a blocked Motion file. It consumes its fixtures. It cannot judge how the motion feels.

Since 2026-10-05 `motion.mjs` accepts `transform` among the animated properties, because sheets now move by `transform`.

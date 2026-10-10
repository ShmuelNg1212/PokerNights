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

`night.mjs` checks the session overview, settlement, paid/Undo, frozen results, recap and native fallback. `seed_night.py` also makes `two-sets`, a closed session of two sets with a rebuy, for the recap's sections, highlights, bars and sticky head. `remaining.mjs` captures home, group, accounts, invitation recovery, supporting forms, picker, canceled set and log. It checks 48 px action links, first-viewport session access, bound errors and native roster actions. `remaining_supplement.mjs` captures the one-time invite URL, invitation acceptance, reversed large-money final log and override log. `remaining_actions.mjs` exercises account/group/table creation, pesos and chips presets, new session, settings refusal and save, rename refusal and save, and native picker refusal and success.

The default run reports 20 Rack, 13 accessibility, 47 end-set, 68 night, 95 remaining, 10 supplement and 12 action checks (265 total). For the complete run, seed all four files before starting, then run all seven browser scripts in the order above and in the first examples. Fixtures are consumed: reset to a fresh database for a repeat. The remaining scripts read synthetic IDs from `/private/tmp/pn-slice4-manifest.json`; night checks use `/private/tmp/pn-slice3-manifest.json`. `PN_EMPTY_ACCOUNT` can select a fresh synthetic account for an empty-home recapture when an earlier invitation run has consumed `unattached`.


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

For the collapsible host dock, seed a fresh temporary database with `seed.py`, `seed_end_set.py`, `seed_night.py`, `seed_remaining.py`, `seed_opening.py` and `seed_counts.py`, then run `dock.mjs` (178 checks since 2026-10-05, the last three for a keyboard that shortens the page itself, as Chrome on an iPhone does; including the slide, reduced motion, the button-styled options and the iPhone keyboard, which is a stand-in `visualViewport` reporting a 336px keyboard; `__pan` slides its visible frame as a scroll with the keyboard open does, and the checks cover the bar staying a bar, the page keeping its length, the bar following without an event, a single frame watcher, focus-only scrolling and the `?kb=1` readout). It reads both manifests in `/private/tmp` and uses its own Chrome profile (`/private/tmp/pn-dock-chrome`); delete that profile before a run so cached scripts are not reused. The checks at 320, 390 and 1280 px cover both dock states in draft, open, in-play and count-up sets, clearance of the last link, overflow against the requested width, reload, a live update from a second session with focus kept, the choice carried from open to count-up, the typed verdict in the collapsed bar, desktop, refused storage, no JavaScript and a player. The run starts and ends the `default` opening set and records one buy-in on set 3, so use a fresh database for a repeat.

On 2026-10-04 the older scripts were found stale on unmodified `main`: `rack.mjs` (8-player height limit, then a crash), `end_set.mjs` (the removed slate contrast pair), `opening.mjs`, `opening_drafts.mjs` and `counts.mjs` (each stops on a selector that no longer exists). They report the same results with the dock change, apart from two dock-clearance checks that now pass.

For archive and delete, seed a fresh temporary database with `seed.py`, `seed_end_set.py`, `seed_night.py` and `seed_archive.py`, delete `/private/tmp/pn-archive-chrome`, then run `archive.mjs` (85 checks). The fixture writes `/private/tmp/pn-archive-manifest.json`: a closed session with unpaid transfers, two canceled sessions without money, a session in play, an empty group and a group with a long unbroken name. The script archives and restores the session and compares the Stats tab before, during and after; deletes one empty session with JavaScript and one without; and archives, restores and deletes the empty group. It consumes its fixtures.

For the entry pages, seed a fresh temporary database with `seed.py` and `seed_entry.py`, delete `/private/tmp/pn-entry-chrome`, then run `entry.mjs` (81 checks). The fixture writes `/private/tmp/pn-entry-manifest.json` with a usable invite, an invite to a group with a 60-character unbroken name and an expired invite. The script covers Log in and Sign up with and without an invite at 320, 390 and 1280 px, contrast, the Show button, keyboard order, refused login and sign-up, the invite flow from link to group as a new account, the join page and its error, and login without JavaScript. It creates the account `newcomer`.

Since 2026-10-04 the shared login line in every script submits with `form.form-section [type=submit]`, because the Show button is now the first button in the login form.

For the settle status, seed a fresh temporary database with `seed.py`, `seed_end_set.py` and `seed_night.py`, delete `/private/tmp/pn-settled-chrome`, then run `settled.mjs` (24 checks): the Past sessions rows at 320, 390 and 1280 px, all three statuses, agreement between each row and its session page, and a row changing after the last paid mark and after undo.

For the stakes forms, seed a fresh temporary database with `seed.py`, delete `/private/tmp/pn-form-chrome2`, then run `session_form.mjs` (69 checks): New session, Set settings and the preset form at 320, 390 and 1280 px, field edges and heights, pairs, a refused pair, locked settings, keyboard order and submission without JavaScript. It creates one session. Chrome does not reproduce the iPhone date control; that needs a real phone.

Since 2026-10-05 `entry.mjs` has 91 checks and follows the new flow: a newcomer goes link → Sign up → group; the seeded account `visitor` goes link → Sign up → “Log in” → Join → group. `seed_entry.py` creates `visitor`.

For the installable app, seed a fresh temporary database with `seed.py`, `seed_end_set.py` and `seed_night.py`, then run `install.mjs` (33 checks). It uses Chrome's default profile context, because Chrome never calls an incognito page installable, and it stops and restarts the Django server on port 8765 itself to produce failed navigations and to turn the kill switch on (`PN_DB` names the SQLite file; default `/private/tmp/pn-dock-check.sqlite3`). It checks Chrome's own installability report, the worker's scope and cache contents, a way back on 17 screens, the refresh on return and its exceptions, the offline notice, the offline page with Try again, and the kill switch. `make_icons.mjs` renders the PNG icons from the SVG.

For actions in place, seed a fresh temporary database with `seed.py`, `seed_end_set.py`, `seed_night.py` and `seed_opening.py`, then run `inplace.mjs` (38 checks). It restarts the Django server on port 8765 itself to produce a failed send. It covers a rebuy from a sheet (no reload, position, typed text, open sections, requests), a fresh request id on the next rebuy, a refused amount, a double tap, a slow answer, the poll after an update, two hosts, a failed send and its retry, a floating error, set transitions, count confirmation, a success message, mark paid and undo, links still loading pages, and the native form with JavaScript off. `probe_rebuy.mjs` prints the before-and-after measurement used in the stage 3 study.

For screen changes, seed a fresh temporary database with `seed.py`, `seed_end_set.py`, `seed_night.py` and `seed_opening.py`, then run `navigate.mjs` (37 checks; it restarts the server on port 8765 itself). It walks the app by tapping links and requires no document load, makes 22 screen changes and counts poll loops, dialogs and script errors, checks pages reached by a tap behave as after a fresh load, Back and Forward with a figure changed by a second host, scroll restoration, the announcement and focus, the loading line, an anchor link, a page outside the app, forms that lead elsewhere, an expired login, the offline page, and plain links without JavaScript. `lifetime.mjs` (22 checks, after `seed.py`, `seed_end_set.py`, `seed_night.py`) restarts every page script repeatedly on one page. `probe_leak.mjs` and `probe_navtime.mjs` print the measurements used in the stage 4 study.

Since link navigation, a click on a link no longer loads a document. A script that needs to know a page arrived should check the address and the content, not a marker on `window`.

For the motion system, seed a fresh temporary database with `seed.py`, `seed_end_set.py`, `seed_night.py` and `seed_opening.py`, then run `motion.mjs` (34 checks). It logs every `Motion.animate` call, so it can say which element moved and with which properties. It covers the button press and release, the busy line, the sheet's rise, rest, leave and a close mid-rise, an action sent during the rise, toasts arriving, stacking and leaving, the nudge on a refused amount, the dock's spring, ten screen changes, 1280px, reduced motion and a blocked Motion file. It records several buy-ins on set 3, so use a fresh database for a repeat. It cannot judge how the motion feels.

For motion on the live set page, seed a fresh temporary database with `seed.py` and `seed_flow.py`, serve it, then run `flow.mjs` (52 checks). `PN_DB` names the SQLite file (default `/private/tmp/pn-flow-check.sqlite3`): the "other host" is a second process that writes through the real services, and the page under test learns of each change by polling, which the script asks for at once instead of waiting 4 seconds. The fixture writes `/private/tmp/pn-flow-manifest.json` with six sets. The script reads every redraw on its first frame (in `requestAnimationFrame`, because Motion starts an animation on the frame after it is asked): what each row shows, how far it is from its place and how opaque it is. It covers arrivals and their 40ms stagger, rows sliding after a cash-out, a tap on a moving row, a rebuy by the other host and by you, the mark fading, a player joining, a state change, typing, a confirmed count, the books balancing once, twenty redraws, a hidden tab, 1280px, reduced motion and a blocked Motion file. It consumes its fixtures. It cannot judge how the motion feels.

Since 2026-10-05 `motion.mjs` accepts `transform` among the animated properties, because sheets now move by `transform`.

For motion between screens, seed a fresh temporary database with `seed.py`, serve it, then run `screens.mjs` (46 checks since the fix of 2026-10-05: the direction must stay until the browser reports each change finished, and a tab's marker and words are separate layers). It wraps `document.startViewTransition` and records, for every screen change the browser animates, the direction on `<html>` when it began, the animations that ran on each layer and how long they last. It walks Your groups → group → session → set → set log and back at 390 and 1280px, the three tabs, the phone's Back and Forward, the carried name on every hop, the chips between a closed session and its set, a real pointer tap during a movement, an action on a set page, twenty changes, and reduced motion. It records one buy-in on set 3. It cannot judge how the movement feels, and headless Chrome is not Safari.

Since 2026-10-05 `motion.mjs` waits 150ms after closing a sheet under reduced motion before reopening it: the dialog's `close` event arrives a moment after `close()`, and one run in five reopened the sheet before it.

On 2026-10-05 `remaining.mjs` was found stale as well: it stops on "missing route preset" after 60 checks, on the current code and on the release before stage 3 of the motion overhaul.

For the Your groups page, seed a fresh temporary database with `seed_home.py` alone, serve it, then run `home.mjs` (60 checks at 320, 390 and 1280px). The fixture writes `/private/tmp/pn-home-manifest.json`: the viewer `mara` belongs to five groups (a set in play with fourteen players, dues and records in pesos and chips; an open session; a 60-character name with nothing played; a session she sat out; an even result), and `pia` belongs to one. Checks: each group is a card, no overflow, one 48px settings button per card that leads to Group settings, no foot links, 48px targets, contrast of all text including the felt band, the states, the chip counter, large unbroken figures, the count of small text, keyboard order, the New group form and a refused name, two packed columns at 1280px, a single group, and no JavaScript. Restart the server after editing a template: templates are cached per process, and a stale server once made this check measure the wrong page.

For the in-app numpad, seed a fresh temporary database with `seed.py` alone, serve it, then run `numpad.mjs` (87 checks). It emulates a phone with touch, because the keys appear only where a finger is the main pointer, and taps through `Input.dispatchTouchEvent`. It covers the buy-in and cash-out sheets at 390, 375 and 320px, every key rule in pesos, chips and percentage fields, the setup forms and seats, a live update under an open sheet, leaving the page, reduced motion, a forced script error, the script blocked, and a computer. It makes real writes.

For count-up, review and finalize, seed `seed.py` and `seed_count_flow.py` on a fresh temporary database, serve it, then run `count_flow.mjs` (89 checks). The fixture writes `/private/tmp/pn-count-flow-manifest.json`: an eight-player set in pesos and in chips, sets whose books balance, are off and are off with an override, a two-player set that the script walks to a finalized set, and a set with no buy-in. It makes real writes and takes about three minutes, because it waits for live updates and for messages to leave before some captures.

Since 2026-10-05 `dock.mjs` has 223 checks: it also measures the gap between neighbouring host controls (8px in every state at 320, 390 and 1280px), expects the count-up bar to carry the running total when expanded, and clears the tab's saved counts before its keyboard section, because typed counts are now kept for the tab.



On 2026-10-05 `inplace.mjs` was updated to confirm typed counts through `[data-confirm-typed]`, the shared main action. Count rows no longer contain individual Confirm buttons. The check still verifies draft/reason preservation and count-field position after confirmation. It exposed a 34px shift when the accepted status wrapped; counts.js now preserves the visible field's position after the Turbo update. The confirming run passed all 38 checks.

For transfer alignment, seed a fresh temporary database in this order: `seed.py`, `seed_end_set.py`, `seed_night.py`, `seed_transfer_layout.py`. Serve it and run `transfer_layout.mjs` (155 checks). It reads `/private/tmp/pn-transfer-layout-manifest.json` plus the earlier night manifest. Checks cover mixed paid/unpaid cards, long names and large pesos/chips at 320, 390, 768, 900 and 1280px; actual text bounds and complete units; first-line identity alignment; assigned financial rows; 48px actions, keyboard focus and DOM order; host/player/archived views; container-query fallback; reduced motion; in-place payment/Undo and native forms without JavaScript. Desktop 200% zoom reflow is emulated with a 640px CSS viewport and DPR 2, corresponding to a 1280px physical window. This is not a Safari appearance check. Fixtures are consumed by real service writes. Use a fresh database for each repeat and each other browser suite.

On 2026-10-05 the night regression’s native-close assertion was corrected: it checks two transfer cards and removal of the close action, rather than the stale wording “Session closed.” The server’s accepted message is “The session is closed. Transfers are listed below.”

Since 2026-10-06:

- `perf.mjs` (12 checks) covers the `Server-Timing` header and the `?perf=1` readout. Seed `seed.py` and `seed_flow.py`, serve, run.
- `marks.mjs` (18 checks) marks three neighbouring player rows the way `changes.js` does and measures that no mark or badge covers a row, a name, an amount or a button, at 320, 390 and 1280px, as host and as player, also with a long name and a large amount. Same seeds. It only reads, so it can be rerun on the same database.
- `dock.mjs` has 228 checks: the slide is a transform, a fold and an unfold each lay the page out at most 4 times, the dock's top edge never jumps back, and the last row glides when the dock folds at the end of the page.
- `navigate.mjs` has 52 checks (a real touch held 60 and 130 ms sends one request for the screen, as the finger lands, and leaves the page's timers alone): a held link looks pressed, a tapped link stays pressed while its screen is on the way, a button link shows the busy line, and nothing stays marked after arrival or Back. A tapped tab must not light.
- `navigate.mjs` and `inplace.mjs` restart the server themselves. `PN_PORT` names its port (default 8765); they stop only the server on that port.- `inplace.mjs` has 39 checks: a rebuy is one request to the server, the POST, and the page is not fetched again. Run it with `ANSWER_IN_PLACE=False` in the environment to see the two-trip fallback (that one check then fails, the rest pass).
- `perf.mjs` prints any script error it catches.
- `reset.mjs` has 43 checks: a host creates a password reset link, it is shown once, the player sets a new password with it (a refused password, a mismatch, then success), the used and the cancelled link are refused, and the page works without JavaScript; layouts at 320, 390 and 1280px. Seed `seed.py` on a fresh database; it changes `ben`'s password, so do not run other scripts after it on the same database.
- `copy.mjs` has 33 checks for the Copy button on a new invite link and a new reset link: the clipboard's content, Copied only after confirmation, a refused and a missing clipboard, script restart, no JavaScript, and layout at 320, 390 and 1280px. Seed `seed.py` on a fresh database. It grants the clipboard permission to its own browser only.
- `player_entries.mjs` has 48 checks with three browsers (the host, two players) and one without JavaScript: a player's own rebuy reaching the others without a reload, the doubled rebuy refused and then recorded on a second try, a player's count reaching the host's row and running total, typing on either side surviving the other's update, the host typing over one number and accepting another, the app's number keys on the player's field, and layout at 320, 390 and 1280px. Seed `seed.py` and `seed_player_entries.py` on a fresh database; the fixture is consumed.

Since 2026-10-09:

- `roster.mjs` has 44 checks for Group settings → Players. Seed a fresh temporary database with `seed_roster.py` alone (host `rosa`, a player with a login, players without one, a closed session with an unpaid transfer, a running set and a removed player), serve it on port 8771 (or set `PN_BROWSER_URL`), run. It covers the activity line, your own name with a refusal, the contact note, a refused and an accepted batch of names with the mark on the new rows, the removal page (refused for a seated player, with an unpaid transfer, removing nobody when opened), bringing a player back, what a player sees, reduced motion and no JavaScript, at 320, 390 and 1280px. It writes to the database: use a fresh one for each run.
- `claim.mjs` has 30 checks for claim links. Seed a fresh temporary database with `seed_claim.py` alone, serve it on port 8771 (or set `PN_BROWSER_URL`), run. A host creates and copies a link; a signed-out browser signs up from it and arrives as the player with the old session; an account with an empty entry confirms and replaces it; an account with games of its own is refused; a used link is refused; and a claim without JavaScript. Layout at 320, 390 and 1280px. It writes to the database: use a fresh one for each run.
- `stats.mjs` has 75 checks for the Stats tab and a player's page. Seed a fresh temporary database with `seed_stats.py` alone (nine regulars and a newcomer, fourteen pesos sessions and four chips sessions with synthetic figures, a removed player, sessions without recorded time), serve it on port 8771 (or set `PN_BROWSER_URL`), run. It only reads, so it can be run again on the same database. It covers the summary, the ranked and unranked lists, each order, the Month list, a chips board, a player's page, the chart's geometry, the readout by pointer and keyboard, reduced motion and no JavaScript, at 320, 390 and 1280px.
- `numpad.mjs` has 105 checks since the keys gained movement: see the list in DESIGN.md, "Numpad motion". It still runs after `seed.py` alone on a fresh temporary database.
- `numpad.mjs` has 120 checks since each digit moves by itself (DESIGN.md, "Numpad digit motion"). It decodes two captures of a field, one with the drawn copy up and one with the field's own text, and compares every pixel.
- `door.mjs` has 134 checks for the front door (DESIGN.md, "Front door"). Seed a fresh temporary database with `seed.py` and `seed_entry.py` and serve it on port 8765. For the switch and the "needs an invite" page, serve the same database a second time with `DOOR_MOTION=False SIGNUP_REQUIRES_INVITE=True` on another port and name it in `PN_OFF_URL`; without it those eight checks are skipped. It records the first frame on which the sheet exists, so it can say an arrival started there and not a frame late. It changes no data.
- `entry.mjs` (91 checks) follows the front door since 2026-10-09: the frame is `.door-hero` and `.door-sheet`, an invited Sign up says "Join {group}", the button of the desktop card is 374px wide, and a control measured while it arrives is rounded to a hundredth of a pixel.
- `welcome.mjs` has 36 checks for the arrival after login (DESIGN.md, "Arrival into the app"). Seed a fresh temporary database with `seed_home.py` alone and serve it on port 8765; for the switch, serve the same database a second time with `DOOR_MOTION=False` and name it in `PN_OFF_URL`. It logs in through the form each time, because only the page after a login is the arrival, and it creates one account named `newcomer` followed by digits.
- `table.mjs` has 63 checks for the set page while a set is prepared and in play (DESIGN.md, "Set page"). Seed a fresh temporary database with `seed.py`, `seed_end_set.py`, `seed_night.py` and `seed_opening.py` and serve it on port 8765; for the switch, serve the same database a second time with `TABLE_REVAMP=False` and name it in `PN_OFF_URL`. It measures the panel and the rows at 320, 390 and 1280px, walks draft → add players → open → start, and covers the sheet swap, a player's view, a live update, reduced motion, no JavaScript and Motion blocked. It writes to the database.
- Since the set page revamp: `motion.mjs` unfolds the host menu first (it starts folded in play); `dock.mjs` expects the stored choice `open` and a folded start in play; `numpad.mjs` reaches the cash-out form through the player's sheet; `flow.mjs` expects a player's own row first, in the place of the join line; `rake_controls.mjs` reads the rake rule from the checklist's stakes step and presses Open by its value.
- On 2026-10-09 `opening.mjs`, `opening_drafts.mjs`, `rake.mjs` and `late_player.mjs` gave the same failures with `TABLE_REVAMP=False` as with the new page (each names a selector or a page that changed in an earlier release), so they say nothing about this change. `table.mjs` covers opening buy-ins and the start.

Since the count-up and settle-up revamp (2026-10-10, [plan](../../../doc/plan/1791630963_count_up_and_settle_up_revamp.md)):

- `count_flow.mjs` has 91 checks: it expects the order overview, players, host action, the books; reads the contrast of the help line and of the line under a name; and checks that each accepted count gets its tick and its mark in the overview with nothing written inline.
- `night.mjs` has 83 checks: the host's first screen (overview and four whole transfers), row heights, each viewer's headline, the order of the page, folded payment records, a transfer settling after the server accepts, "Settled" arriving once per session per browser, and both under reduced motion. "large amount remains one line" now reads the overview's figure.
- `dock.mjs` (228 checks): during count-up the folded bar keeps the main action or the hint beside the running total, so its "collapsed" checks allow that one extra element there. Its last scroll check passes when the list is too short to scroll.
- `player_entries.mjs` (48 checks) finds a player's own count in the "Your count" block above the list, and an entered count as "entered ₱1,450" on the row.
- `end_set.mjs` runs to its end again (47 checks, 46 pass). Its no-JavaScript chips walk had stopped on `.next-action`, which is the hidden confirm button; it now follows the link and the finalize form. The one failure, the slate contrast pair, was already stale on `main` (the slate surface was removed).
- `transfer_layout.mjs` describes the earlier stacked transfer card. 55 of its 155 checks no longer apply; the row is covered by `night.mjs`. It is kept for reference and is not part of a release run.
- A count-up run with `COUNT_REVAMP=False` needs the earlier expectations: four of `count_flow.mjs`'s checks name the new layout.

For the pot's figure (2026-10-11), seed a fresh temporary database with `seed.py` and `seed_pot.py`, serve it, then run `pot.mjs` (53 checks). `PN_DB` names the SQLite file (default `/private/tmp/pn-pot-check.sqlite3`); the fixture writes `/private/tmp/pn-pot-manifest.json`. The "grow" set allows buy-ins up to ₱1,000,000 so the figure can reach its long size. Waits after a redraw are measured from the redraw, not from the previous check.

Seen on `main` on 2026-10-11, before this change: `flow.mjs` passes 50 of 52 ("1280px cash-out: rows end at rest" and "count confirmed: the status badge springs"), and `table.mjs` stops at "a player on an open set" with seeds `seed_end_set.py`, `seed_night.py`, `seed_opening.py`. Neither was looked into.

# Words, formats and the home card

Status: approved 2026-11-20 with the recommended answers. Verified on branch `feat/words-formats-home` 2026-11-20; frozen. Reconstituted 2026-11-20 from the queued plan ui_6_words_formats_home (removed from the queue with this plan), critique issues 7 and 8 (P3) and the minor observations in the [UI critique](../study/1795101392_ui_critique.md). Mode: design, with two small technical parts (time format, token order). Skills: `/impeccable clarify` in execute; `tdd` for task 5; at rendezvous `code-review`, `break-ui`, `/impeccable critique`.

## Goal

The app uses the same words and the same formats on every screen. The home card shows a player only what a player can use.

## What the code does now

- The buy-in sheet has the quick amount "Default" (`templates/web/_buy_in_form.html:11`). Every other screen says "Usual buy-in", "usual" or "usually".
- Times use 24 hours ("23:07") in 31 places: `session_log.html` (12), `_player_records_body.html`, `_player_actions.html`, `_player_manage.html` (4 each), `night.html` (4), `_invite_row.html` (2), `_group_players.html` (1). The session log head, the home card and the attendance line use "11:07 PM".
- Set settings always says "Configure rake before the first buy-in. Buy-ins already recorded keep their amounts." (`templates/games/settings_form.html:9`), also when the set has buy-ins.
- New session uses a native date field (`games/forms.py:171`). The phone shows "11/19/2026".
- Amount fields show "1000". Blinds and buy-in fields in Set settings, New session and presets show no unit. The server already accepts "1,000" and "₱1,000" (`ledger/money.py:25`, `:70`).
- The home card shows the gear to every member (`templates/web/_group_card.html:6`). A player's Settings tab is read-only (tables, presets, rake).
- The home card tokens are the first six members by name (`web/home.py:69`).
- "And 3 more unpaid transfers in past sessions." is text, not a link (`_group_card.html:42`). The filter exists: `?past=unsettled#past-sessions`.
- A player who left shows the buy-in total large and "Cashed out ₱2,650" small (`templates/web/_player_row.html:20`).
- Stats: the sort pills scroll sideways with no cue. A host who has not played reads "You have no closed session yet." (`templates/web/_group_stats.html:25`).
- Text under 14 px: `.75rem` (12 px) and `.6875rem` (11 px) appear in 15 rules, mostly chip letters, labels and ledger meta. The ramp label size is `--h-label` (13 px).
- Dropped from the queue: `templates/offline.html:14` uses 1.75rem. That is `--h-page`. The offline page cannot load `app.css`, so it repeats the value. No change.

## OPEN QUESTIONS

1. **Who the home tokens show.** My recommendation: the members who played in the group's most recent sessions, latest first, then the others by name. The viewer is not shown (they know they are in it). A new group with no sessions keeps the order by name. **Answer (2026-11-20): as recommended.**
2. **A player who left: the colour of the net.** My recommendation: the net is large and signed ("+₱1,650", "−₱350") in the existing plus and minus amount colours, with "In ₱1,000 · out ₱2,650" small under it. Only the player's own row and rows of players who left change. Players still at the table keep the buy-in total. **Answer (2026-11-20): as recommended.**
3. **Grouping while typing.** My recommendation: group digits in the field as the person types ("1,000"), and show "₱" before or "chips" after the field as a fixed part of the field. The keypad and the server already handle commas. The risk is the caret position on an iPhone; if a browser probe shows a jump, fall back to grouping on blur. **Answer (2026-11-20): as recommended.**

## Tasks

### 1. One word for the usual buy-in — `tests: alongside`

- [x] Change the quick amount "Default" to "Usual" in `_buy_in_form.html`.

Acceptance: no screen says "Default" for the buy-in. Completion: `grep -rn '>Default<' templates` is empty; the buy-in tests pass.

### 2. 12-hour times everywhere — `tests: alongside`

- [x] Replace each `H:i` display format with `g:i A` (and `H:i:s` with `g:i:s A`) in the seven templates above.
- [x] Do not change `datetime-local` values (`_host_controls.html:101`). They need the 24-hour form.
- [x] Add a test that renders the session log and the player sheet with a record at 23:07 Manila time and finds "11:07 PM".

Acceptance: no screen shows a 24-hour time. Completion: `grep -rnE 'date:"[^"]*H:i' templates` is empty; the new test fails on old code and passes.

### 3. Set settings says what is true — `tests: alongside`

- [x] Before the first buy-in: "Set the rake before the first buy-in. After it, the rake stays as it is."
- [x] After a buy-in or cash-out: "This set has money recorded, so the rake stays as it is. New blinds and buy-in limits apply from the next buy-in." (Changed in execute: `games/services.py:280` refuses a rake change once money is recorded; stakes can still change.)
- [x] Use a fact the view already has: `services.has_money(session)`.

Acceptance: each state shows its own line. Completion: a view test for each state (`games/tests/test_form_layout.py`, set settings test).

### 4. Dates and amounts that read like the rest — `tests: alongside`

- [x] New session: show "Thu, Nov 19" next to the date field. A small script updates it on `change`. Without the script, the native field stays.
- [x] Amount fields (buy-in and cash-out sheets, Set settings, New session, presets): group digits as the person types, per OPEN QUESTION 3.
- [x] Each blinds and buy-in field shows its unit: "₱" before the field in a pesos game, "chips" after it in a chips game. On New session the unit follows the unit choice.
- [x] Keep the 48 px targets. Use DESIGN.md tokens only.

Acceptance: "1,000" reads the same in the field and on the row. A saved amount is the same as before. Completion: a browser probe types 1000 and 1650.50 in a pesos sheet and 2500 in a chips sheet, then submits; the recorded amounts are 100000 centavos, 165050 centavos and 2500 chips. (In execute: set 5 allows at most 2,000 chips, so the probe types 1,500 chips. Probe: `web/tests/browser/amounts.mjs`. A count of one chip colour stays ungrouped, because `denominations.js` reads plain digits.)

### 5. The home card for players — `tests: first` for the token order

- [x] The gear shows to hosts only.
- [x] The tokens follow OPEN QUESTION 1. Write the order tests in `web/tests/` first. Keep the query count of Your groups the same or lower (`assertNumQueries`).
- [x] "And 3 more unpaid transfers in past sessions." links to `?past=unsettled#past-sessions`.

Acceptance: a player sees no gear; the tokens show who played last; the line opens the Not settled list. Completion: the order tests fail first, then pass; `home.mjs` passes.

### 6. A player who left shows the net — `tests: alongside`

- [x] In `_player_row.html`, a player who cashed out shows the net per OPEN QUESTION 2.
- [x] Count-up rows and the results table do not change.

Acceptance: on a set in play, a player who left reads "+₱1,650" large. Completion: a view test for a left player's row; `table.mjs` stays at its current count.

### 7. Stats cues — `tests: alongside`

- [x] The sort pills fade at the right edge while more pills are off screen. The fade goes when the row is scrolled to the end.
- [x] A member with no closed session reads: "You have not played in a closed session yet. Your figures show here after you do." (Changed in execute: the line is true for every member, so it is not for hosts only. `profile.html` keeps its own line.)

Acceptance: the cue shows only when the row overflows. Completion: a browser probe at 320 px and 900 px.

### 8. Small text at the table — `tests: alongside`

- [x] Raise to `--h-label` (13 px) the 12 px text that a player reads during play: `.facts dt`, `.facts dd small`, `.ledger-meta`, `.count-pill`.
- [x] Keep chip letters, `.badge-host` and uppercase table heads as they are. They are marks, not reading text.
- [x] Check no row wraps worse at 320 px. (In execute: at 13 px a past session line left "pay" alone at 320 px; the amount and "still to pay" now stay together.)

Acceptance: no reading text during play is under 13 px. Completion: a browser probe counts elements under 13 px on a set in play, before and after; `break-ui` worst-case names at 320 px show no new overlap.

## Checks at rendezvous

- [x] SQLite suite; PostgreSQL suite before release. (SQLite 1846 OK after the last fix. PostgreSQL 1844 OK before the review fixes; run again before release.)
- [x] `code-review`, `/impeccable critique`, `break-ui` on the home card and the player row. (See Rendezvous record.)
- [x] Browser probe: sign in as a player, open Your groups (no gear, tokens, the link), then a set in play (12-hour times in the sheet, a left player's net). (`home.mjs` covers the player's cards; the times are a view test; the net is a view test and a 320 px screenshot.)

## Rendezvous record (2026-11-20)

- **code-review (medium), 7 findings.** Fixed 6 in round 1:
  1. The chip sheet dropped the breakdown at totals of 1,000 or more (`denominations.js` compared grouped text). `chip_batch.mjs` now uses ₱1,320; it fails without the fix (6 pass, then it stops) and passes with it (21/21).
  2. A partial cash-out showed a net. Now only `status == left` shows the net. View tests updated.
  3. A grouped server value looked typed. The default is grouped too. `amounts.mjs` checks it.
  4. Quick amounts, presets and redrawn fields were grouped late. They are grouped at once. `amounts.mjs` checks the quick amount.
  5. Backspace after a comma did nothing. It removes the digit. `amounts.mjs` checks "12,345" → "1,345".
  6. Home tokens counted draft sets and future sessions. They do not; a view test checks it.
  7. Gear hidden from players: kept. It is the approved plan; players reach Settings by the tab.
- **/impeccable critique (dual-agent).** Detector: clean (8 `design-system-color` false positives from the unresolved stylesheet). Design review 24/32 (Good). Fixed: the "more unpaid transfers" link is a 48 px quiet button; a zero net reads "Even"; a hidden "Net" label before the figure; plainer rake words; `.date-words` uses `--s-1`; DESIGN.md `.count-pill` is 13 px. Not done (P3): a unit mark in the buy-in sheet field (it says "Amount (pesos)"); a left fade on the Stats pills.
- **break-ui (targeted).** A player who left after a ₱5,000,000 buy-in at 320 px: "−₱4,999,999.99" and "In ₱5,000,000 · out ₱0.01" fit, no overflow. The past sessions line at 320 px: "₱199,999,999.98 still to pay" fits on one line. Text under 13 px on the group page: 14 → 0.
- **Probes.** `home.mjs` 63/63; `stats.mjs` 90/90; `amounts.mjs` 12/12 (new); `chip_batch.mjs` 21/21; `chip_numpad.mjs` 24/24; `multi_host.mjs` 29/29. Same as main (failures that already exist): `numpad.mjs` 103/105, `flow.mjs` 50/52, `table.mjs` 38 then a crash at the draft dock (`dock-next` is gone before Start since the host dock release).

## Completion criterion

All eight tasks are ticked, the checks are recorded here, and the branch is verified. The TODO.md phone check is written.

# Final polish after the critique items

Status: approved 2026-11-20 with the recommended answers. Reconstituted from the queued plan `ui_7_final_polish` (removed from the queue with this approval) and the [UI critique](../study/1795101392_ui_critique.md). Critique items 1 to 8 are released (plans 1795101620, 1795103143, 1795105635, 1795134971, 1795144795, 1795146808). Mode: design. Skills: `/impeccable polish` in execute; at rendezvous `/impeccable critique` (same method as the study), `break-ui`, `code-review`.

## Goal

The screens that items 1 to 8 changed look like one app again: same spacing, same type steps, same states, same motion. The rerun critique shows whether the score moved from 29/40.

## What the code does now

- Six releases on 2026-11-19 and 2026-11-20 changed these screens: the set in play (chips, felt, rows), the draft and joining dock, count-up (dock, books, mismatch panel), the closed session page (money first, recap card), the player sheet (Cash out, Records and corrections, Reverse), the buy-in sheet, Your groups (home card, Your record), New session, Set settings and Stats.
- Each release had its own critique. No pass has looked at all of them side by side.
- Minor critique items that no plan took: "8 · 2 seats free" on the set and "7 at the table" on home count different things; the count-up progress bar tells segment types apart by colour only. Heuristic 7 (no fast "same rebuy again") and heuristic 10 (no explanation for a first-time player of stripes, hatching or "Counting up") are product changes, not polish.

## OPEN QUESTIONS

1. **The two minor items.** My recommendation: take both into this plan as small tasks (task 2). They are polish-sized: one word change and one pattern or label in the bar. **Answer (2026-11-20): as recommended.**
2. **"Same rebuy again" and first-time help.** My recommendation: keep them out of this plan. Add them to TODO.md "Next" as items that need their own study. **Answer (2026-11-20): as recommended.**
3. **Bar for done.** My recommendation: the rerun scores at least 30/40, with no heuristic lower than before. If it scores lower, I stop and report, and I do not fix more in this plan. **Answer (2026-11-20): as recommended.**

## Tasks

### 1. Polish pass on the changed screens — `tests: alongside`

- [x] Seed a fresh SQLite database with the study's seeds (`seed.py`, `seed_end_set.py`, `seed_night.py`, `seed_opening.py`, `seed_home.py`).
- [x] Run `/impeccable polish` on each screen in the list above at 390 px, and at 1280 px for the set in play and the session page.
- [x] Fix only alignment, spacing, type steps, state styles, focus rings and motion presets. Stay inside DESIGN.md tokens. No new words, no new layout.
- [x] Record each fix in this plan as one line with `file:line`.

Fixes (commits `a624925`, `814b223`):

- A player who left: "In ₱X" and "out ₱Y" each stay whole (`templates/web/_player_row.html:20`). At 390 px "out" was alone at the end of a line.
- A player with no buy-in: the empty edge stack took a slot before "No buy-in yet" (`static/css/app.css`, `.buy-stack:empty`).
- The player sheet: the records were 36 px under "Records and corrections"; now 16 px (`.records > .section-label + .list`).
- The session page: a set's badge sits on its name's line, and the first set row starts under the label (`.night-sets li.row`).
- The session page from 900 px: the left column had a 133 px gap under the lead, because the detail column spans two grid rows. The second row now takes the extra height (`.night-layout { grid-template-rows: auto 1fr }`). Gap now 28 px.
- Your groups, as a player: "And 3 more unpaid transfers in past sessions" touched its card's edges. The dues row rule took its padding (`.home-dues a.btn`).
- Looked at and kept: count-up from 900 px has about 54 px above "The books" (row gap, the heading's 24 px margin and some grid slack). Set settings says twice that the rake is locked; a word change is outside polish.

Checks: SQLite 1847 OK. `home.mjs` 63/63, `reverse_apart.mjs` 24/24, `dock_before_start.mjs` 28/28, `night.mjs` 88/88.

Acceptance: each listed screen was looked at, and each fix is in the list. Completion: SQLite suite passes; the browser probes for the changed screens pass at the same counts as main or better.

### 2. The two minor items (if question 1 is yes) — `tests: alongside`

- [x] Make the home card and the set count the same thing, or name what each counts. The pill now counts the people at the table, as Your groups does: "7 · 2 seats free" (`web/views.py`, `templates/web/_players.html:8`). "7 at the table · 2 seats free" ran into Add players at 320 px, so the short form stays. Test: `games/tests/test_participants.py` `test_count_leaves_out_a_player_who_left` fails on the old code.
- [x] Give the count-up bar segments a second cue besides colour (a pattern or a label). Already met: since the calm count-up release (plan 1795105635) a ready mark is half filled and a cashed-out mark is full, and a hidden line gives the counts in words (`templates/web/_count_v2.html:12`). No change.

Acceptance: a colour-blind simulation of the bar still tells each segment apart; the two counts read as the same people. Completion: a browser probe checks the new word and the second cue.

### 3. Rerun the whole-app critique — `tests: alongside`

- [ ] Run `/impeccable critique` with the study's method: host `hana`, player `ben`, viewer `mara`; 390 px every screen, 1280 px main screens, 320 px one set in play; two assessments that do not see each other.
- [ ] Write the new score and the per-heuristic table as a dated addendum in the [study](../study/1795101392_ui_critique.md).
- [ ] Put new P1 and P2 issues in TODO.md "Next". Do not fix them in this plan.

Acceptance: the addendum has the score, the table and the change against 29/40. Completion: the addendum is committed as `docs:`.

## Completion criterion

All tasks ticked, the rendezvous checks recorded here, and a verified branch `feat/final-polish` from main.

# Plan: count-up, clear figure, calm mismatch

Study: [1795101392_ui_critique.md](../study/1795101392_ui_critique.md), issues 4 and 5 (P2). Reconstituted 2026-11-20 from `doc/roadmap/plan_queue/ui_3_count_up_calm.md` against main `cd53a37`. Mode: mixed. Tasks 1, 2 and 5 change what the page says and where a money form is. Tasks 3, 4 and 6 are a design pass. Skills: `tdd` and `/impeccable clarify` (tasks 1, 2, 5); `/impeccable quieter` (tasks 3, 4, 6); `code-review`, `/impeccable critique`, `break-ui` (rendezvous).

Branch: `feat/count-up-calm`, from main `cd53a37`.

Human answer 2026-11-19: a mismatch is a **calm search**, not an alarm.

## OPEN QUESTIONS

Answered 2026-11-20: approved, both recommendations (counts first; "Find the ₱100 difference").

1. **Mismatch order (task 4).** Today, when every player is cashed out and the books are off, the books move up above Player counts (`app.css:429`, `app.css:1230`, `app.css:1749`). This was on purpose: the gap in words comes first. The queued plan says: put Player counts first. The dock still says "₱100 missing" and its button leads to the wrong record (`gap.js`). Recommendation: **counts first**, as queued. If no: drop task 4.
2. **The main button's words on a mismatch (task 3).** Today: "See the ₱100 difference", in the danger style. Recommendation: **"Find the ₱100 difference"**, in the normal bone style. The press does the same thing as today.

## Evidence (main `cd53a37`)

- The folded dock bar says "₱3,550 of ₱8,500 bought in" with no label (`templates/web/_host_controls.html:5`). The text is in the template, not in the books query. The open dock has the label in its equation: "₱X counted + ₱Y cashed out" (`_count_total.html:5`).
- Before every player is cashed out, the host reads "₱4,950 still to account for. 3 still to count." three times: the folded dock bar, the dock's count total (`_count_total.html:7`), and the books verdict (`_books.html:35`). The books also have the notice with the names (`_books.html:47`, `queries.py:307`).
- On a mismatch, four things are coral: the books panel (`.discrepancy`, `app.css:401`: Down border, Down background, Down amount), the dock line (`.dock-gap`, `app.css:2270`), the count total's verdict (`data-tone="down"`, `_count_total.html:7`, `counts.js:78`), and the main button (`btn-danger`, `_host_controls.html:55`).
- "Finalize with an override" sits in the books, under the gap (`_books.html:64-81`). The dock hint says "Find the wrong record, or record an override." Where to look says "record an override below" (`_books.html:20`).
- The count pips: awaiting is an outline, ready is a bone fill, cashed out is a Good fill (`app.css:1726-1728`). Ready and cashed out differ only by colour.

## Outcome

- The host reads the folded dock without remembering what the figure is.
- The remaining sentence shows once, in the dock.
- A mismatch reads as a search: one coral amount, neutral surfaces, the counts first.
- The override is one tap further away, in More host controls. Its form, its reason, its rules and its permission do not change.
- A colour-blind host can tell ready from cashed out in the pips.

## Non-goals

- No change to services, to `ledger/queries.py` figures, or to what an override records.
- No change to the player's (not host's) books and count total.
- No change to the balanced moment or to the covered (override) state.

## Tasks

- [x] **1. Label the folded dock figure.** `tests: first`.
  - The folded bar reads "Counted + cashed out ₱3,550 of ₱8,500". With rake: "Counted, cashed out + rake ₱3,550 of ₱8,500".
  - Changed in execute: "Accounted for ₱3,550 of ₱8,500". "Counted + cashed out" took two lines at 320 px, and `dock.mjs` "counting 320 collapsed bar is small" failed. "Accounted for" is the verdict's own words ("still to account for") and covers rake. The open dock keeps the full sum.
  - `counts.js` keeps the "Preview · " prefix in front of the label while counts are typed.
  - Done when: a view test finds the label in the counting dock, with and without rake, and the browser probe sees the label and the prefix at 390 px.
- [x] **2. The remaining sentence once, in the dock.** `tests: first`.
  - Remove the host's books verdict (`_books.html:35`). The dock keeps it (folded bar and count total).
  - The books keep the table, "Counted, not cashed out", and the notice with the names.
  - Done when: a view test finds "still to account for" once in the host's counting page outside the folded bar, and the player's page is unchanged. Update the TODO.md phone check "the verdict under it move".
- [x] **3. Calm mismatch.** `tests: alongside`.
  - `.discrepancy`: the neutral panel surface and the `--line` border. Only the amount stays in Down. Keep the "₱100 missing" words and the minus sign.
  - `.dock-gap`: the amount in Down, the rest in the default ink.
  - The count total's verdict on a gap: the `warn` tone, not `down` (template and `counts.js:78`).
  - The main button: `btn-primary`, words from open question 2. Keep `data-books-gap` and `gap.js`.
  - Update DESIGN.md lines 377 and 714.
  - Done when: at 390 px and 1280 px, on a mismatch, a browser probe finds one element in the Down colour (the amount) in the books and one in the dock, and the button opens Where to look as before.
- [x] **4. Counts first on a mismatch.** `tests: alongside`. Depends on open question 1.
  - Remove the `.books-known` order rules. Player counts come before The books at every width.
  - Changed at rendezvous (code review): for the host only. A player has no dock, so `books-known` stays for a player and their verdict stays under the overview.
  - Done when: a browser probe on a mismatch finds Player counts above The books at 390 px and at 1280 px, and the dock button still scrolls to the wrong record.
- [x] **5. The override in More host controls.** `tests: first`.
  - Move the "Finalize with an override" disclosure from `_books.html` into `.host-more` in `_host_controls.html`. Show it in the same state as today: host, every player cashed out, books off.
  - Keep the form unchanged: `override_add`, `request_id`, `absorber`, `note` (required), "Record override", the `data-keep` keys.
  - "Remove the override" stays in the books, beside the override line.
  - New words: the dock hint says "Find the wrong record, or record an override in More host controls." Where to look says "or record an override in More host controls if the error cannot be found."
  - Done when: tests show the form posts the same fields to the same address, a player never gets it, the service still refuses a non-host, and it is gone from the books. The existing `test_books_off_panel.py` tests pass after their location changes.
- [x] **6. Pips by more than colour.** `tests: alongside`.
  - Ready: a bone outline with a bone fill on the left half. Cashed out: a full Good fill. Awaiting: an outline, as today.
  - Keep the `pip-fill` motion; reduced motion stays still.
  - Done when: a 390 px capture in greyscale tells the three states apart.

## Rendezvous checks (2026-11-20, branch `feat/count-up-calm`)

- SQLite suite: 1827 OK (23 skipped).
- `count_flow.mjs`: 96/98. The two failures are the 48 px numpad panel checks, which fail on main too. New checks: the bar label with Preview, counts before books, only the amount in Down in the panel and the bar, a neutral panel border, the override in More host controls, the pip shapes, and the 1280 px mismatch.
- `books_gap.mjs`: 36/36. First run on the branch: 32/36. Two failures were the old all-Down bar rule (check updated). Two were real: with the books after the counts, the tap measured "Where to look" while it was still opening, so the panel was left under the bar. Fix in `gap.js`: open it at once (`.open-at-once`), then measure. Rerun: 36/36.
- `dock.mjs`: 194/196, the same as main (both fail "toggle keeps focus across live update" and "bar verdict follows typing"). Before the label change the branch had a third failure (320 px folded bar), fixed by "Accounted for".
- `end_set.mjs` 47/47, `counts.mjs` 35/35.
- The write: at 390 px a host opened More host controls, then "Finalize with an override", chose equal shares, typed a note and recorded it. The books then said "Off by ₱100,000, covered by an override from …", the note showed, and "Finalize results" was the main button.
- `code-review` (medium): 8 nits. Fixed 6: a browser check that compared two missing elements, the dead `books-known` class (now player only), the duplicated gap words (`Balance.headline_word`), the player's verdict placement, a stale DESIGN.md order sentence, a redundant tone branch. Not changed: the warn mark on the 1280 px verdict follows the Verdict Rule (DESIGN.md corrected), and a 7-figure total can still wrap the bar at 320 px, as on main.
- `break-ui`: a 52-character name and ₱2,222,221 at 320 px. No overflow; the name ends with "…"; the bar wrapped "of" away from its total, so "of ₱X" now stays together.
- Not run: `/impeccable critique` as a separate pass; the captures at 320 and 390 px were read instead.

## Completion

Every task is ticked, every check is recorded, and `feat/count-up-calm` is verified and not pushed.

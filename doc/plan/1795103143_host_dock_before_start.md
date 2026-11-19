# Plan: host dock before Start

Study: [1795101392_ui_critique.md](../study/1795101392_ui_critique.md), priority issue 2 (P1). Reconstituted 2026-11-19 from `doc/roadmap/plan_queue/ui_2_host_dock_before_start.md` against main `a444720`. Mode: design (mixed in effect: task 1 changes `dock.js`). Skills: `/impeccable distill` (execute); `/impeccable critique`, `break-ui`, `code-review` (rendezvous).

Branch: `feat/host-dock-before-start`, from main `a444720`.

## OPEN QUESTIONS

Answered 2026-11-19: approved, both recommendations (option A; drop the toggle before the start).

1. **Where does the host's "Join this set" go?** The queued plan says: move it out of the dock. But release `4455be2` (2026-11-19) put it in the dock on purpose. Before that, it was an underlined line at the end of the list, and the open dock covered it. Options:
   - **A. In the Players head (recommended).** A small neutral "+ Join" button on the right of "PLAYERS 2 · 2 seats free". It is near the top of the page, so the dock never covers it. It sits beside the seat count that it changes. The dock keeps Start and its checkbox only.
   - B. A "+ You" row card at the end of the Players list. It matches the rows. With 8 players it is under the dock until the host scrolls. This is the place that failed before `4455be2`.
   - C. Keep it in the dock, above Start (no change). The dock then has two buttons before the start.
2. **Drop the "Host controls" toggle before the start?** Recommendation: **yes**, on draft and joining sets only. Before the start, the toggle's folded text says "Next: Start the set". This only repeats the button under it. The toggle stays in play and in the count-up, where its folded bar carries the next step or the count. If no: task 1 is dropped, and the dock keeps two disclosures.

## Evidence (main `a444720`, 390 × 844, host not seated, 2 of 4 seats taken)

- The dock is 283 px high: one third of the screen. It shows a "Host controls" toggle row, Join this set, the usual buy-in checkbox, Start the set, and "More host controls". That is two disclosures and two buttons.
- With the set full, Join goes and the dock is 227 px.
- The "Host controls" heading (`templates/web/_host_controls.html:5`) is already hidden on phones (`static/css/app.css:331`). The queued plan's first task is partly done. The toggle (`_host_controls.html:4`) is the remaining extra disclosure.
- The critique counted about ten controls. The new draft page (`prep`) already folded the stakes into one row. The page now shows Draw, the summary row, one Buy-in per row, and Full set log above the dock.

## Outcome

- On a phone, before the start, the dock shows the usual buy-in checkbox, **Start the set**, and "More host controls". Nothing else.
- A host who is not seated finds Join without a scroll and without opening a menu (option A).
- In play and in the count-up, the dock is unchanged.

## Non-goals

- No change to services, permissions or what Join or Start records.
- No change from 900 px up.
- No change to the player's own Join (`_players.html:14`) or to the host's in-play Join under the list ("Playing too?", `_players.html:23`).

## Tasks

- [x] **1. No toggle on draft and joining sets.** `tests: alongside`.
  - Render `.dock-toggle` only when the set is running or counting up.
  - Footgun: `:root.dock-collapsed` stays from an earlier set, and `app.css:891` then hides every child of the dock except the toggle. Scope that rule (and the `.kb-bar` rules) to a dock that has a toggle: `.host-controls:has(> .dock-toggle)`. Else a host who folded the dock in play sees an empty dock on the next set.
  - `dock.js` `sync()` returns early without a toggle. Make sure `measure()` still sets `--dock-h`, so the last row clears the dock.
  - Completion: before the start, one disclosure in the dock. A host who folded the dock in play, then opens a new set, sees Start.
- [x] **2. Join in the Players head (option A).** `tests: alongside`.
  - Move the host's open-set Join form from `_host_controls.html:16-18` to the Players head in `_players.html`. Same condition: open set, `can_join`, host not seated, `seats_free > 0`. Neutral style, 48 px target, `{% icon 'plus' %} Join`, with an accessible name "Join this set".
  - Update `web/tests/test_table.py` `test_on_an_open_set_the_host_joins_from_the_host_controls` to the new place.
  - Completion: the dock has the checkbox, Start and More host controls only. The Join button is in the first screen at 390 × 844 with 8 players.
- [x] **3. Browser check.** `tests: alongside`.
  - Add `web/tests/browser/dock_before_start.mjs` on `seed_overture.py`. At 390 × 844 and 320 × 568: the dock has no toggle and exactly one primary button; the dock fits without its own scroll (`scrollHeight <= clientHeight`); Join is in the viewport and a tap seats the host; after `dock-collapsed` is set on `<html>`, Start is still visible. At 1280 px: the page is as on main.
  - Each check must fail on main.
  - Completion: the probe passes on the branch, and its new checks fail on main.

## Rendezvous

Commits: `88f673f` (feat), `786e140` (fix after review).

- [x] SQLite suite: 1816 OK.
- [x] `dock_before_start.mjs`: 28/28 on the branch; 12 of them fail on main (no toggle, dock height, Join place and name, top padding, draft, fold carried from play, Join tap, 320 checks, 1280 Join). The other checks are regression guards. "The page reserves the measured dock height" fails with main's `dock.js` on the branch: it guards the `sync()` change.
- [x] `dock.mjs`: updated for no toggle before the start; 194/196, the same two failures as main (226/228): "toggle keeps focus across live update", "bar verdict follows typing".
- [x] `count_flow.mjs`: 90/92 on both; the same two failures ("panel keys and buttons are at least 48px", "320 by 568").
- [x] `code-review` (medium, run on the plan diff). Findings and outcome: Join on an open set with no players (already handled; the test now says so); the keyboard bar on a dock with no toggle (fixed in `786e140`: the dock is out of sight above the keyboard; CSS check only, headless Chrome has no keyboard); `measure()` without a toggle (fixed in `88f673f`, guarded); top padding (fixed, checked); the Players head at 320px (checked: one line, 48px); stale comments (updated); footgun (written); mode (noted above).
- [x] Visual review of the captures at 320, 390 and 1280px instead of a full `/impeccable critique`. Long name and 11 players at 320px: head on one line, no sideways scroll. The table name is in the set panel, which this change does not touch, so no `break-ui` run.
- [x] TODO.md phone check added.

Deviations:
- At 320 × 568 the set panel alone reaches the dock, so Join is one short scroll away, as the first control after the panel. At 390 × 844 it is on the first screen.
- Join moves at every width, also from 900px, where it is beside Players in the right column. Splitting it by width would render it twice.

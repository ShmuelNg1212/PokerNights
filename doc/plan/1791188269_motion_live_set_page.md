# Motion on the live set page: plan

Status: approved, built and released on 2026-10-05. Date: 2026-10-05, Asia/Manila. Study: [Motion on the live set page](../study/1791188203_motion_live_set_page.md). Stage 2 of the [motion overhaul](1791186717_motion_overhaul.md).

## Outcome

On the set page, a change made by you or by someone else is visible as movement: a new player's row slides in and the rows below make room, a buy-in lands on its stack, changed figures are marked and the mark fades, a state change cross-fades, and the books balancing is a moment. Nothing delays a tap.

Mode: Operate. Visual authority: the built Rack in DESIGN.md and its Motion system.

## Decisions for the human

Approving the plan accepts the recommendations unless you say otherwise.

1. **No reordering.** The programme promised rows that "arrive, leave and reorder". On this page rows only arrive: players stay in joining order and no action removes a row. I recommend not inventing a reorder. Say so if you want the list sorted differently (for example by amount bought in); that is a product change, not a motion one.
2. **Rows that carry money move without bounce.** This is the kit's guidance for serious figures. Bounce stays on buttons, badges and the buy-in edge.
3. **The Motion server.** Connected since the session of 2026-10-05 (see Progress). Its docs search is used during the build. No decision is needed.
4. **Stage 1 is adjusted to the kit's rules** as part of this stage (sheets move by `transform`; a compositor hint on toasts and buttons while they move). No visible change is intended.

## What you will see

| Event | Motion |
|---|---|
| A player is added | The new row fades in and rises 12px; rows below slide down to make room (no bounce, about 260ms). Several players added at once arrive 40ms apart. |
| A buy-in or rebuy | The new edge drops onto the stack with a small bounce. The "Rebuy added" badge springs in. The row's brass mark fades out over its last 400ms instead of vanishing. |
| "Still in play" and other watched figures | The brass underline draws from left to right, holds, and fades. The figure itself appears at once. |
| A cash-out; a player marked Left | The row's mark as above; the "Left" badge springs in; the row dims over 200ms instead of at once. |
| The set changes state | The region cross-fades in 180ms. |
| Count-up: a count is confirmed | The row's status badge springs when it changes; the progress line ("1 of 2") is marked as a watched figure. |
| The books balance (once per set) | The green rule draws left to right with the sheet spring, then the message rises 8px and fades in. Within 900ms. |
| Your first sight of a set | Nothing moves. |
| While you type | Nothing moves; redraws already wait. |
| Reduced motion, no JavaScript, Motion not loaded | As today. |

## Implementation

1. **A before-event.** `live.js` dispatches `live:updating` on the region before it replaces the HTML. `turbo-setup.js` dispatches the same event before a morph render. `live:updated` stays as the after-event.
2. **`static/js/flow.js`** (new). On `live:updating` it records the top of every `[data-watch]` row by key and the set's state. On `live:updated`:
   - a row whose key was not recorded and is not in `changes.js`'s seen list is an arrival: fade and rise, staggered with `Motion.stagger`;
   - a row whose top moved by more than 1px animates `transform` from the old offset to none, with a spring without bounce;
   - a changed state cross-fades the region (opacity only).
   It registers with `window.pokerPage`, cancels what it started on stop, and does nothing when `pokerMotion.on()` is false or the redraw came while the tab was hidden.
3. **`changes.js`.** The fixed 3-second removal becomes: at 2.6s add a fading class, at 3s remove. The edge, the badges and the underline call `pokerMotion.run` with new presets; the CSS animations remain for the plain path. A new arrival is exposed to `flow.js` through one shared helper so the two agree on what "new" means.
4. **Books balanced.** `changes.js` keeps the once-per-set marker. With Motion on, the rule and the message animate through `pokerMotion.run`; otherwise the existing CSS reveal plays.
5. **Presets added** to `motion.js` and DESIGN.md: `shift` (spring, 260ms, bounce 0), `drop` (spring, 220ms, bounce 0.35), `mark` (ease-out underline), `fade` (180ms).
6. **Kit alignment of stage 1.** Sheets animate `transform` (a string) instead of `y`. Toasts and a pressed button get `will-change: transform` while moving, removed at rest.
7. **Tests first.**
   - Django: both redraw paths still render the keys (`data-watch`) the module relies on; the script list gains `flow`.
   - New browser check `flow.mjs` at 390 and 1280px, with a second signed-in session making the changes:
     - a player added by the other session: the new row starts transparent and ends opaque; a row below starts displaced by the new row's height and ends at rest; a tap on a Rebuy button during the movement opens its sheet;
     - the same for your own action through the morph path;
     - a rebuy: the edge and badge animate; the amount text equals the accepted value on the first frame after the redraw; the mark is gone after 3s;
     - a state change cross-fades and leaves opacity at 1;
     - books balanced plays once and not on reload;
     - first load, typing, a hidden tab, reduced motion and a blocked Motion file: no animation, correct final state;
     - Motion animates only `transform` and `opacity`;
     - twenty redraws leave no running animation and no inline style on rows.
   - Existing checks: `motion.mjs`, `dock.mjs`, `inplace.mjs`, `navigate.mjs`, `lifetime.mjs`.
8. **Verify.** SQLite suite, the build-style run, PostgreSQL before release. Mid-animation captures inspected.
9. **Sync docs.** DESIGN.md Motion system (presets, the events table), wiki features and architecture, browser README, TODO phone checklist. Correct the stage 1 notes that say the AI kit is not installed.

## Acceptance criteria

- AC1. Each row of "What you will see" passes its browser check.
- AC2. A tap during any of these animations is accepted, and no figure is ever shown at a value other than its accepted one.
- AC3. First load, typing, reduced motion, no JavaScript and a blocked Motion file behave as today.
- AC4. All existing tests and the listed browser checks pass.
- AC5. **On your phone, with a second person or a second device changing the set:** the movement helps you see what changed and does not get in the way. Only you can judge this.

## Out of scope

- Sorting or reordering players; removing rows.
- Screen-to-screen transitions (stage 3); results, recap and settle-up (stage 4).
- The session page.
- Changing how polling works.

## Rollback

Revert the stage's commits. No migration and no data change.

## Progress and blockers

2026-10-05: Stage 1 released. The human said “push”; all 639 tests passed on local PostgreSQL 17 first. Pushed `main` at `680c3b1` (previous production commit `62e869c`). About two and a half minutes later the live site served the Motion file and `motion.js`. Not checked on production: any signed-in page, a touch screen.

2026-10-05: Study and plan for stage 2 complete. Waiting for approval.

2026-10-05, later session: the "motion" server (`https://mcp.motion.dev`) is connected. Its docs search answered and the `stagger` and `spring` pages were read. Checked against the plan:

- Motion's own layout animation for plain JavaScript (`animateLayout`) is part of Motion+, which is paid and was declined. The plan's hand-written measure-and-`transform` move in `flow.js` stays; it needs only the free `animate`.
- `delay: stagger(0.04)` is the documented form for the 40ms arrivals.
- `visualDuration` is in seconds and `bounce: 0` is a spring with no overshoot, so `shift` is `{ type: "spring", visualDuration: 0.26, bounce: 0 }`.

Not available: the server's spring generator did not appear among this session's tools (only the docs search did), and the "motion-plus" server is not signed in. Neither is needed: the presets use Motion's real springs, not generated CSS curves. No change to the plan's scope. Still waiting for approval.

2026-10-05: approved by the human ("approved"). Built and verified. Not pushed.

Changes from the plan:

1. **A new state fades in; it does not cross-fade.** The old state's HTML is gone when the new one arrives, so there is nothing to fade out without keeping a copy. The new state fades from clear to solid in 180ms.
2. **"The rows below slide down to make room" seldom happens for a new player**, because a new player joins at the end of the list. Rows do slide whenever a row above changes height: a cash-out with Left removes that row's buttons, a player joining removes the "Join this set" line, and on a phone the overview growing pushes the list.
3. **The row "dims" by its name.** A Left row differs from the others only in its name colour, so that colour eases over 200ms. The row's opacity does not change.
4. **`mark` is a CSS animation, not a Motion preset.** The underline is drawn by a pseudo-element, which Motion cannot address. It runs only while Motion is on. The books-balance rule is likewise CSS, timed with the `sheet` spring that `pokerMotion.timing` provides.
5. **The stagger is a 40ms delay per row** set by `flow.js`, not `Motion.stagger`, so each row keeps its own controls for cleanup.
6. **No shared "new row" helper.** `flow.js` alone decides what arrived: a keyed row that was not on the page before the redraw.
7. **The set's state is published** as `data-state` on `#live` and as `state` in the poll's JSON. The balanced message is wrapped in `<span class="books-message">`. No other template change.
8. **Found while building:** Motion writes its final style again one frame after it reports the end, which undid the cleanup. `pokerMotion.settle` waits two frames. Stage 1's sheet had the same leftover once it moved by `transform`; it uses `settle` now.
9. **The "other session" in `flow.mjs` is a second process calling the services**, not a second browser. The page under test sees the same thing: a poll that returns a new snapshot.

Verification:

- 642 tests pass on SQLite (ten PostgreSQL-only skips), in the build-style run, and on local PostgreSQL 17 (none skipped).
- `flow.mjs`: 52 of 52, three runs in a row on fresh databases. The books balance completed in under 900ms from its first frame.
- `motion.mjs` 34, `lifetime.mjs` 22, `dock.mjs` 163, `inplace.mjs` 38 and `navigate.mjs` 37 pass on fresh databases.
- Mid-animation captures were inspected at 390 and 1280px (rebuy mark, rows mid-slide with a sheet rising, count-up rows).

AC1 to AC4 are met, AC1 with changes 1 to 3. **AC5 is open: only the human can judge it on a phone with a second device.** Not verified: a real phone, Safari (it draws the `linear()` spring easing only from 17.2), frame rate with a long player list, and the books-balance moment when its panel is off-screen as it arrives (it plays unseen and does not replay).

2026-10-05: Stage 2 released. The human pushed `main` at `1106548` (previous production commit `680c3b1`); the agent's own push was refused by the session's permission check. The suite had passed on local PostgreSQL 17 for this code. Checked on the live site: the login page lists `flow.js` in the script order, and `flow.js`, `motion.js`, `changes.js`, `live.js`, `turbo-setup.js`, `sheets.js` and `app.css` are byte-for-byte the local files. Not checked on production: any signed-in page (so not the set page's `data-state` or the movement itself), a touch screen.

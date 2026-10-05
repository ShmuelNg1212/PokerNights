# Motion on the live set page: plan

Status: awaiting approval. Date: 2026-10-05, Asia/Manila. Study: [Motion on the live set page](../study/1791188203_motion_live_set_page.md). Stage 2 of the [motion overhaul](1791186717_motion_overhaul.md).

## Outcome

On the set page, a change made by you or by someone else is visible as movement: a new player's row slides in and the rows below make room, a buy-in lands on its stack, changed figures are marked and the mark fades, a state change cross-fades, and the books balancing is a moment. Nothing delays a tap.

Mode: Operate. Visual authority: the built Rack in DESIGN.md and its Motion system.

## Decisions for the human

Approving the plan accepts the recommendations unless you say otherwise.

1. **No reordering.** The programme promised rows that "arrive, leave and reorder". On this page rows only arrive: players stay in joining order and no action removes a row. I recommend not inventing a reorder. Say so if you want the list sorted differently (for example by amount bought in); that is a product change, not a motion one.
2. **Rows that carry money move without bounce.** This is the kit's guidance for serious figures. Bounce stays on buttons, badges and the buy-in edge.
3. **The Motion server.** Its docs search and spring generator are not connected in this session. To use them, start a new Claude session in this project and approve the "motion" server when asked. I recommend going ahead now with the kit's best-practice files, which are what shaped this plan.
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

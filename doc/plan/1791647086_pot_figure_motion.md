# Pot figure motion: plan

Status: approved 2026-10-10 ("approved"); all four decisions as recommended. Built on `feat/pot-figure-motion`, kept local. Date: 2026-10-10, Asia/Manila. Study: [Pot figure motion](../study/1791647037_pot_figure_motion.md).

## Outcome

When a buy-in lands, the "Still in play" figure shows it: the digits that changed roll to the new amount and "+₱500" rises beside the figure. A player watching their own phone sees the pot grow and by how much, without looking for the row that changed.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new colour, font or asset. No migration, no server change, no template change.

## Behaviour

| Moment | Today | After |
|---|---|---|
| A buy-in or rebuy is accepted | The figure is replaced in one frame; a brass line draws under it | Each digit that changed rolls: the old one leaves upward as the new one comes up from below, 260ms, no bounce. Digits that did not change, the peso sign and the commas stay still. The brass line draws as today |
| The amount added | Not shown | "+₱500" in brass beside "Still in play" rises 8px and fades in, stays while the brass line stays, and fades out with it (3 seconds in all) |
| Several changed digits | — | They start 30ms apart from the left, four steps at most, so the whole roll ends within 350ms |
| The figure gets wider (₱9,500 to ₱10,000) | It jumps | The new leading digit fades in and the others glide to their places |
| Two buy-ins arrive in one update | One jump | One roll to the new amount; the amount added is their sum |
| A second change during a roll | — | The roll in progress is dropped and the new one starts from the figure as accepted |
| A cash-out or a reversal lowers the figure | It jumps; the brass line draws | The same roll, downward, with "−₱500" (decision 2) |
| First sight of a set, a hidden tab, reduced motion, Motion not loaded | Nothing moves | Nothing moves; no "+₱500" either under the first two, and a still "+₱500" under reduced motion |

Rules that hold throughout:

- The page's text is the accepted amount from the first frame. A screen reader, a copy and a reload never get anything else.
- No value in between is ever shown. Nothing counts.
- Only transform and opacity change. The figure's size and place, and everything around it, stay put.
- Nothing waits for it. Rebuy and every other control work during the roll.
- Half a second after the last change the figure is the plain text it is today, with nothing added to the page. The "+₱500" is removed when its 3 seconds end.

Built with the design and motion skills.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **The money rule changes for this one figure.** DESIGN.md's "digits do not count" stays. "Digits do not move" becomes: "A changed digit of the pot may roll to its accepted value. No figure counts through other values." For a quarter of a second a changed cell shows the old digit leaving and the new one arriving.
2. **Every change of the figure moves the same way,** not only buy-ins: a cash-out or a reversal rolls downward and shows "−₱500". Recommended, because one figure that rolls for a buy-in and jumps for a cash-out looks broken. Say "buy-ins only" to leave falls as they are today.
3. **No new switch.** The roll checks itself and falls back to the plain figure (see Implementation). Say if you want a `POT_MOTION` switch in Vercel as the revamps have.
4. **Only the large figure of a set in play.** The "₱X bought in" line of a set that has not started keeps its brass mark only.

## Implementation

1. **`static/js/pot.js`, new, about 90 lines.** Loaded on the set page after `changes.js`.
   - On `live:updating` it reads the figure's text and `data-value`. On `live:updated` it compares. The first sight of a set uses the value `changes.js` already remembers per browser session, so a reload does not roll.
   - If the value changed and motion is on and the tab is visible: the figure's text node is replaced, for the length of the movement, by one inline-block cell per character, each clipped to its own height. The whole drawn copy is `aria-hidden`; the amount stays in the page as visually hidden text. Characters are matched from the right, which lines up digit columns (the figure uses tabular numerals).
   - A changed cell holds two glyphs: the old leaves by `translateY(∓60%)` and opacity to 0 in 120ms with the ease-in curve; the new comes from `translateY(±60%)` to rest with the `shift` spring. First keyframes are written inline before the animation starts (the frame-late footgun). Kept cells glide from where they were drawn when the width changed.
   - The movement uses the browser's own animation calls, as the numpad digits do; `pokerMotion.on()` decides whether anything moves.
   - **Fail-safe.** Before anything moves, the drawn copy's width must equal the plain figure's within 0.5px, and the figure must be on one line. If not, or on any error, the figure is left as the server drew it. The plain text is restored on the end of the roll, on the next redraw, and on leaving the page.
   - **The amount added.** `now − was` as integers. A small formatter writes it from the unit on the panel (`data-unit`): centavos to `₱1,600` or `₱1,600.50` by integer division, chips to `1,600 chips`. Before each use it formats the new total and compares with the figure's own text; a mismatch means no amount is shown. The element is added beside the "Still in play" label, `aria-hidden` (the row's "Rebuy added" already tells a screen reader), and removed with the existing 3-second mark.
2. **CSS (`app.css`, set page motion section).** `.pot-roll` cells and `.pot-delta`: brass, the label's size, weight 700, tabular numerals, placed on the label's line so the figure's layout does not change. Under reduced motion `.pot-delta` shows without movement.
3. **Template.** Only the script tag. `data-unit` and `data-value` are already on the panel.
4. **Tests.**
   - `web/tests/browser/pot.mjs`, new, on the `seed_flow.py` sets, at 390 and 1280px, pesos and chips:
     - first frame after a buy-in by another person: the page's text is the new amount, changed cells are mid-roll, unchanged cells have no transform;
     - the figure's box is the same size and place before, during and after;
     - "+₱1,000" is shown, matches the server's format, and is gone after its hold;
     - a change of width (₱9,500 to ₱10,000) and a switch to the "long" size end at the right place;
     - two buy-ins in one poll show one roll and their sum;
     - a cash-out rolls downward with "−";
     - the host's own Rebuy tap (in place) moves the same way, and Rebuy can be tapped again mid-roll;
     - 600ms after: plain text, no cell, no inline style, no running animation; twenty redraws leave nothing behind;
     - first sight, reload, hidden tab: nothing moves; reduced motion: nothing moves and the amount added is still; Motion blocked: the page is as today;
     - a forced width mismatch and a forced formatter mismatch leave the plain figure and no amount.
   - `flow.mjs`, `table.mjs`, `motion.mjs` and `inplace.mjs` run again; `flow.mjs`'s check "the figure appears at once" is rewritten to "the page's text is the accepted amount on the first frame".
   - The SQLite suite. PostgreSQL is not needed for the change, and is run before a release as always.
5. **Sync docs.** DESIGN.md (motion rule 3, the set page rules and events table, a dated addendum), wiki features, browser README, TODO with a phone check. SPEC.md is the human's.

Work is done on branch `feat/pot-figure-motion` from `main`, kept local. Nothing is merged or pushed without an instruction.

## Acceptance criteria

- AC1. After a buy-in by anyone, the changed digits of "Still in play" roll to the new amount within 350ms; unchanged characters do not move.
- AC2. The amount added is shown beside the label in the app's format, with its sign, and leaves after 3 seconds.
- AC3. The page's text is the accepted amount on the first frame; no other amount is ever shown.
- AC4. The figure's box and everything around it do not move or change size.
- AC5. Controls work during the roll; a second change mid-roll ends at the right amount.
- AC6. At rest the figure is plain text with nothing added.
- AC7. If the drawn copy or the formatter cannot match the server's figure, the figure is as today.
- AC8. First sight, reload, a hidden tab, reduced motion and a missing Motion file: nothing moves.
- AC9. Existing tests and the browser checks named above pass.

## Out of scope

- The player's row, the stack edge, "Rebuy added" and the brass underline.
- Count-up totals, results, settle-up, stats and every other figure.
- Sound and vibration.

## Rollback

Revert the feature commit. No data, migration or setting is involved.

## Progress and blockers

2026-10-10: Study and plan complete. Waiting for the human's approval. No code written.

2026-10-11: The human approved with "approved". Built on `feat/pot-figure-motion` from `main`; kept local.

Changes from the plan:

- **A change seen on opening the page does not roll.** The plan compared with the value remembered per browser session. The script compares only with what this page showed before a redraw, so opening or reloading a set never moves the figure.
- **The drawn figure stays about 420ms, not half a second,** and up to 540ms when five or more digits change. The spring reports its end near 500ms but is at rest to the eye by 380ms.
- **Cells are cut at 0.12em from the top.** Not in the plan; without it a leaving digit reached the "Still in play" label.
- **`flow.mjs` needed no rewrite.** Its figure checks read the player rows, which this change does not touch.
- **One Django test changed:** the expected order of scripts in `web/tests/test_inplace.py` names `pot`.
- **Skills.** Built with the motion skill. The design skill was not run; the one new element, the amount added, was set from DESIGN.md's tokens and looked at in two captures at 390px.

Verification:

- 964 tests pass on SQLite (15 skipped, the PostgreSQL-only ones). PostgreSQL was not run: nothing on the server changed.
- `pot.mjs`: 53 of 53 on a fresh temporary database. `motion.mjs`: 34 of 34. `inplace.mjs` ran to its end with no failure.
- `flow.mjs`: 50 of 52. The same two checks fail on `main` without this change ("1280px cash-out: rows end at rest" and "count confirmed: the status badge springs"). Not looked into.
- `table.mjs` stops at "a player on an open set", the same on `main` without this change. Its 45 earlier checks pass. Not looked into.
- Captures at 390px of the first frame of a roll and of the amount added at rest were looked at once.

Acceptance: AC1 to AC8 are met in headless Chrome. AC9 is met for the Django suite, `pot.mjs`, `motion.mjs` and `inplace.mjs`; `flow.mjs` and `table.mjs` are as they are on `main`.

Not verified: an iPhone and Safari, where the width of a digit set alone can differ from the same digit in running text (the roll would then not show, by the guard); how the roll feels at a phone's frame rate; a screen reader.

A fresh reviewer did not read the branch; the author's own read of the diff is the only review.

Documentation synced: DESIGN.md, wiki features, browser README, TODO.

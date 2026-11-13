# Chip to the pot

Status: waits for approval. Date: 2026-11-13, Asia/Manila. Study: [More flair](../study/1794301535_more_flair.md), idea 1. This is plan 2 of 3 from that study, after [the session finale](1794301755_thats_the_night_finale.md). Plan 3 is [Streaks and records](1794561295_streaks_and_records.md). Reconstituted from the queue against the code at `8acb556`.

Mode: design. Visual authority: the built Rack in DESIGN.md. No new colour, font, file or dependency. Execute skills: `animate`, `mobile-native`. Rendezvous skills: `review-animations`, `break-ui`, `code-review`.

Branch: `feat/chip-to-the-pot`, from main.

## Decided

- 2026-11-10, the human: idea 1 goes to a plan.
- 2026-11-10, the human: no haptics.
- 2026-11-13, the human: "finish the flair queue".

## Decided by the agent (say so if one is wrong)

1. Length: 360 ms, so that the chip ends with the pot's digit roll. The study said about 400 ms.
2. A reversal moves no chip. It is a correction. The pot's roll and the "Updated" mark already show it.
3. The start of a set moves no chip. The overture owns that moment.
4. The chip never stops a tap. It has no skip. It covers nothing and takes no pointer events.
5. A row that this page view sees for the first time moves no chip. A late player's row has its own arrival (`arrivals.js`).
6. `chipfly.js` keeps its own values in memory. `changes.js` reads `sessionStorage`, which also holds values from earlier page views. The chip must count only a change that this page view saw.

## Outcome

A rebuy or a later buy-in is accepted during play. One chip in the player's colour goes from the player's row to the pot. A cash-out is accepted. One chip goes from the pot to the row. Each phone on the set page sees it at its next redraw. The chip shows that money moved. It does not count money.

## Behaviour

| Moment | What happens |
|---|---|
| A rebuy or a later buy-in is accepted, on any phone | A copy of the row's token flies from the row to the pot figure. It gets smaller and fades at the pot |
| A cash-out is accepted | A chip in the player's colour leaves the pot figure and lands on the row's token |
| The pot figure | It shows the accepted amount from the first frame and rolls as today (`pot.js`). It does not wait for the chip |
| The sender's phone, with the sheet still closing | The chip starts when the sheet closes (the dialog's `close` event). If the sheet is still open after 400 ms, no chip |
| Several rows change in one redraw | One chip each, 60 ms apart, 4 at most. More rows: no chip |
| The set's state changes in the same redraw (`#live` `data-state`) | No chip |
| The first view of the page, a reload, a full page replacement | No chip |
| A reversal (the buy-in count or the cashed-out amount goes down) | No chip |
| A new row | No chip. See decision 5 |
| The row is under the host dock or off the screen | The chip goes to, or comes from, that edge and fades (the overture's edge rule, `overture.js` `edge()`) |
| The pot is off the screen | The chip goes to, or comes from, the top edge. If both ends are off the screen, no chip |
| A stage has the screen (`pokerStage.taken()`), or the seat draw dialog is open | No chip |
| A hidden tab, reduced motion, no Motion file, no JavaScript | No chip |
| The page is left during a flight | The layer is removed. Nothing keeps running |

## Motion

- One transform and one opacity for each chip. Both run in the compositor.
- Row to pot: 360 ms, ease `[0.55, 0, 0.2, 1]` (the overture's fly). Scale goes from the token's size to 0.5. Opacity goes to 0 in the last 120 ms.
- Pot to row: the same path in reverse. Scale goes from 0.5 to the token's size. Opacity goes from 0 to 1 in the first 120 ms. The chip is removed on arrival; the row's token is under it.
- The first keyframe is written before Motion starts ([motion_starts_a_frame_late.md](../wiki/footguns/motion_starts_a_frame_late.md)).

## Tasks

- [ ] **1. Record the decision (tests: alongside).** DESIGN.md addendum "Chip to the pot (2026-11-13)" after "The pot's figure rolls". It states the 360 ms length against the 300 ms interaction rule, with the pot's roll as the precedent. Completion: committed with the build.
- [ ] **2. Browser check first (tests: alongside).** New `web/tests/browser/chip_pot.mjs` on the `seed_pot.py` seed. Checks:
  - A rebuy on the host's phone and on a second phone gives one chip. It starts on the token (within 1 px) and ends on the pot figure.
  - A cash-out goes the other way.
  - The pot's text is the accepted amount on the chip's first frame.
  - A reversal, the start of a set, a reload and a full replacement give no chip.
  - Five rebuys in one redraw give no chip. Two give two chips, 60 ms apart.
  - A tap on Rebuy during the flight opens the sheet.
  - Nothing is left 1 s later: no element in the layer, no animation, no inline style in `#live`.
  - Reduced motion and a blocked Motion file give no chip.
  - Widths 320, 390 and 1280 px.
  - No frame over 50 ms with the processor slowed four times.
  
  Completion: the checks fail before the build and pass after it.
- [ ] **3. Build (tests: alongside).** New `static/js/chipfly.js`, loaded in `templates/base.html` after `overture.js`. Update the script-order test in the Django suite.
  - It registers with `pokerPage` and reads each `.player-row[data-watch]` `data-value` (`bought in : buy-ins : cashed out : status`) into memory.
  - On `live:updated` it compares. Buy-ins up: row to pot. Cashed out up: pot to row. It then stores the new values.
  - The ends: the row's `.chip` token and `.pot-main[data-watch="in-play"] .display-amount`.
  - The layer is one fixed `div` in `#table-sheets`, `aria-hidden`, `pointer-events: none`, outside `#live` ([poll_morph_strips_inline_styles.md](../wiki/footguns/poll_morph_strips_inline_styles.md)). Styles go in `static/css/app.css`.
  - It uses `pokerMotion.run` and `pokerStage.at` / `centre`. It does not open a stage.
  - A thrown error turns the script off for the page view and is still reported, as in `pot.js`.
  
  Completion: `chip_pot.mjs`, `pot.mjs`, `overture.mjs` and the Django suite pass.
- [ ] **4. Phone checks and docs (tests: alongside).** TODO.md: rebuy and cash out with a second phone on the page. Reword the existing check "Nothing moves at the first cash-out": it means the layout, and a chip now moves. Sync `doc/wiki/features.md`. Run `graphify update .`.

## Rendezvous

Run the SQLite suite, `chip_pot.mjs`, `pot.mjs`, `overture.mjs`, `mobile_motion.mjs` and `table.mjs`. Run `review-animations`, `break-ui` and `code-review`. The first thing the user does: a rebuy on a running set with a second phone on the page. Record the checks here.

## Not in scope

- Sound and vibration.
- A chip for each buy-in at the start of a set.
- A chip on the session page or in count-up.

## Risks

- The move runs many times a night. If it tires in review, shorten it. Do not add to it.
- Fail-safe: the script only adds. Without it, or after an error, the page is the page of today.

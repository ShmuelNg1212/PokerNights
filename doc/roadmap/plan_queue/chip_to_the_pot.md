# Chip to the pot (queued)

Status: queued 2026-11-10. Study: [More flair](../../study/1794301535_more_flair.md), idea 1. The human sent it to a plan on 2026-11-10. It is plan 2 of 3, after [the session finale](../../plan/1794301755_thats_the_night_finale.md). Reconstitute against the current code before approval.

Mode: design. Execute skills: `animate`, `mobile-native`. Rendezvous skills: `review-animations`, `break-ui`, `code-review`.

## Goal

When a rebuy or a buy-in is accepted during play, one chip in the player's colour goes from the player's row to the pot. When a cash-out is accepted, one chip goes from the pot to the row. Each phone on the set page sees it at its next redraw. It shows that money moved. It does not count money.

## Decided by the agent (confirm at approval)

1. Length: about 360 ms, so that the chip ends with the pot's digit roll. The study said about 400 ms.
2. A reversal moves no chip. It is a correction, and the pot's roll and the "Updated" mark already show it.
3. The start of a set moves no chip. The overture owns that moment.
4. The chip never stops a tap. It has no skip, because it covers nothing and takes no pointer events.

## Behaviour

| Moment | What happens |
|---|---|
| A rebuy or a later buy-in is accepted, on any phone | A copy of the row's token flies from the row to the pot figure, gets smaller and fades at the pot |
| A cash-out is accepted | A chip in the player's colour leaves the pot figure and lands on the row's token |
| The pot figure | It shows the accepted amount from the first frame and rolls as today (`pot.js`). It does not wait for the chip |
| The sender's phone, with the sheet still closing | The chip starts when the sheet is closed. If the sheet is still open after 400 ms, no chip |
| Several rows change in one redraw | One chip each, 60 ms apart, 4 at most. More rows: no chip |
| The set's state changes in the same redraw (start, count-up, finish) | No chip |
| The first view of the page, a reload, a full page replacement | No chip. Only a change seen by this page view counts |
| The row is under the host dock or off the screen | The chip goes to, or comes from, that edge and fades (the overture's edge rule) |
| The pot is off the screen | The chip goes to, or comes from, the top edge. If both ends are off the screen, no chip |
| The overture or the seat draw stage is open | No chip |
| A hidden tab, reduced motion, no Motion file, no JavaScript | No chip |

## Draft tasks

- [ ] **Record the decision (tests: alongside).** DESIGN.md addendum "Chip to the pot" under "Motion on the live set page". It states the length against the 300 ms interaction rule, with the pot's roll as the precedent. Completion: committed with the build.
- [ ] **Browser check first (tests: alongside).** New `web/tests/browser/chip_pot.mjs` on the `pot.mjs` seed. Checks: a rebuy on the host's phone and on a second phone gives one chip that starts on the token (1 px) and ends on the pot figure; a cash-out goes the other way; the pot's text is the accepted amount on the chip's first frame; a reversal, the start of a set, a reload and a full replacement give no chip; five rebuys in one redraw give no chip; a tap on Rebuy during the flight opens the sheet; nothing is left in the page 1 s later (no element, no animation, no inline style in `#live`); reduced motion and a blocked Motion file give no chip; 320, 390 and 1280 px; no frame over 50 ms with the processor slowed four times. Completion: the checks fail before the build and pass after it.
- [ ] **Build (tests: alongside).** New `static/js/chipfly.js`. It listens to `live:updating` and `live:updated`, as `pot.js` does. It compares each `.player-row[data-watch]` `data-value` (`bought in : buy-ins : cashed out : status`) with the value this page view saw before. Buy-ins up: row to pot. Cashed out up: pot to row. The layer is a fixed `div` in `#table-sheets`, `aria-hidden`, `pointer-events: none`, outside `#live` ([poll_morph_strips_inline_styles.md](../../wiki/footguns/poll_morph_strips_inline_styles.md)). Completion: the probe and the Django suite pass.
- [ ] **Phone checks and docs (tests: alongside).** TODO.md: rebuy and cash out with a second phone on the page. Reword the existing check "Nothing moves at the first cash-out": it means the layout, and a chip now moves. Sync `doc/wiki/features.md`.

## Not in scope

- Sound and vibration.
- A chip for each buy-in at the start of a set.
- A chip on the session page or in count-up.

## Risks

- The move runs many times a night. If it tires in `critique`, shorten it; do not add to it.
- `changes.js` already compares the same values for the "Updated" mark. Reconstitution decides whether `chipfly.js` reads that result or keeps its own copy.

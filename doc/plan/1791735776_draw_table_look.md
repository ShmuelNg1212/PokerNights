# The look of the table in the seat draw: plan

Status: approved 2026-10-12 with one change ("approved, can the animation be around 30% shorter for the draw. keep the same length for the seating animation. make sure to use motion and design skills for this."). Built; kept local. Date: 2026-10-12, Asia/Manila. Study: [The look of the table in the seat draw](../study/1791735775_draw_table_look.md).

## Outcome

The seat draw plays on a table that looks like a poker table: a racetrack with a padded rail, lit felt with a betting line and the app's mark, a chair at every place and a proper dealer button. A light follows the button around the table and the winner is named with a brighter moment. The still table on the set page has the same look.

Mode: Operate, with the one Experience moment the seat draw already has. No new colour, font or downloaded file. No migration. Built with the impeccable and motion skills.

## What changes

| Part | Today | After |
|---|---|---|
| Shape | An ellipse | A racetrack: straight sides, round ends. Upright on a phone's stage, lying down on the set page and wide screens |
| Rail | A flat 9 to 11px border | A padded rail about twice as wide: dark outer edge, lit top, shadow onto the felt |
| Felt | One gradient | Lit from above and darker toward the rail, a thin betting line a little inside it, and the app's mark, faint, in the middle |
| Seats | 48px dashed rings on an ellipse | A small chair behind each place, facing the table, evenly spaced along the edge. An empty chair shows its number; the tap target stays 48px. Players' chips sit at their chairs with the name under them, as now |
| Dealer button | A flat Brass circle with "D" | Bone with an Ink rim and a Brass inner ring, "D" in Ink |
| Still table on the set page | The flat ellipse | The same table, still, at the size it has now |

## Motion

All movement stays `transform` and `opacity`. A tap still skips the part that is playing, and the total length does not change (about four seconds for the draw, about two for the seating).

1. **The table arrives.** The rail and felt fade up, then the chairs set down around it, then the chips, in the order they do now.
2. **The draw.** The table dims and a soft light travels with the button, so the chip it is passing is the brightest thing on the screen. The button is a quarter larger while it runs.
3. **The winner.** When the button springs back, the dimming lifts, a Brass ring opens once from the winner's chip, and the rail's highlight brightens once.
4. **Choosing.** The empty chairs lift slightly in turn to show they can be tapped; a pressed chair sinks.
5. **The seating.** Unchanged in path and timing; each chip lands on its chair and the chair settles 2px under it.

Reduced motion and a missing Motion file show each result still, as now.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **The felt stays the app's blue.** Recommended: it is the felt of the set page, and green would be a new colour. Say "green" if you want a classic table.
2. **The mark in the middle is the app's own mark, faint.** Say if the table should have none, or the group's name.
3. **No cards and no chip stacks on the felt.** Recommended, to keep the "no casino imagery" rule where the seat draw put it: drawn furniture yes, gambling props no.
4. **The lengths stay as accepted** (four seconds and two). The light and the winner's moment add intensity, not time.

## Implementation

Branch `feat/draw-table-look` from `main`.

1. **Geometry.** One rule for a seat's place and facing on a racetrack of given proportions, spaced by distance along the edge, seat 1 at the top: `games/seats.py` (percent, for the page) and `static/js/seats.js` (pixels, for the stage). Tests first: the two agree for 2 to 12 seats, neighbours are equally far apart along the edge, and seat 1 is top centre.
2. **Markup.** The table becomes rail, felt, line and mark; each seat gets its chair. Template `_seat_table.html` and the stage built by `seats.js`.
3. **CSS.** The rail's bands, the felt's light, the line, the mark, chairs (empty, taken, the viewer's, away), the button, at 320, 390 and 1280px; reduced motion.
4. **Motion** in `seats.js`: the light and the dimming layer, the button's size in flight, the winner's ring and rail highlight, the chairs' lift and settle.
5. **Design passes.** Captures at 320, 390 and 1280px with 2, 6 and 12 players, looked at and corrected in at most two rounds; the motion skill's rules for springs and compositor-only movement.
6. **Tests.** Django: geometry, and the page's markup. Browser: `seat_draw.mjs` reruns whole, with new checks for the racetrack (seats on the edge, chairs face the middle), the light moving by transform only, the winner's moment playing once, and the unchanged checks for twelve seats at 320px and for late frames with the processor slowed four times. `table.mjs` reruns.
7. **Documents.** DESIGN.md (the seat draw addendum, and where "no casino imagery" stands), wiki features and architecture, browser README, TODO.md with a phone checklist.

## Out of scope

- The length or order of the draw.
- Sound and vibration.
- Cards, pot chips, or any photo.
- The felt panel of the set page in play.

## Acceptance

1. The stage and the set page's table are a racetrack with a rail, a betting line, the mark, chairs and the new button, at 320, 390 and 1280px.
2. Seats sit evenly along the edge and in the same order and places on the page and on the stage.
3. A light follows the button; the winner gets one brighter moment.
4. Twelve players still fit a 320px phone, and no frame runs late with the processor slowed four times.
5. Reduced motion and no JavaScript show the same table, still.
6. Both test suites pass.

## Release

Kept local on its branch until you say to push. No migration. `SEAT_DRAW=False` still turns the whole seat draw off.

## Changes at approval

Decision 4 changes: the draw is about 30% shorter; the seating keeps its length.

## Progress

2026-10-12: Built on `feat/draw-table-look` from `main`; kept local.

- **The draw** runs about 2.7 seconds from the stage opening to the dealer's name, measured; it was about 3.9. Every part of it was shortened by about the same share. The seating is untouched in path and timing.
- **On a wide screen the stage's table lies down.** The first build left it nearly round there.
- **Found in the browser:** the ring that opens from the winner kept its large size after fading and made the stage 28px wider than a 320px phone. It now returns to its small size.
- The impeccable and motion skills' rules were applied from their earlier loading in this session (compositor-only movement, springs for what lands, one authored moment). No separate critique run and no MotionScore audit was made.

Verification:

- 1103 tests pass on SQLite (15 skipped); 3 more geometry tests, and the page test extended.
- `seat_draw.mjs`: 50 of 50 on a fresh temporary database, 5 of them new. Twelve seats at 320px and the late-frame check with the processor slowed four times pass unchanged.
- Captures of the ring, the light mid-run, the winner, the choice, the seating and the page's table at 320, 390 and 1280px were looked at, in two rounds.

Acceptance: 1 to 5 are met in headless Chrome; 6 on SQLite, PostgreSQL before release.

Not verified: real phones; whether the table reads as a poker table to the human; the light on a slow phone (the check slows the processor, not the graphics). A fresh reviewer did not read the branch.

Documentation synced: DESIGN.md, wiki (features, architecture), browser README, TODO.

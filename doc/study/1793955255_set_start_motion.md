# Study: a grander set start

Date: 2026-11-06. Mode: design. Base: `aa0ff82` on `main`.

## Request

The human wants the start of a set to be more flashy and grand. This study explores directions. It does not change application code, DESIGN.md or the wiki.

Skills used: impeccable `shape` (study stage), with the motion rules in DESIGN.md as the reference. The shape interview was replaced by a prototype, so the human chooses from moving examples, not from words. The questions are in OPEN QUESTIONS below.

## OPEN QUESTIONS

1. **Length.** DESIGN.md limits a signature moment to 900 ms. The seat draw has a recorded exception. Each new direction needs about 1.1 to 2.0 s. Which length do you accept?
2. **Cover the page.** Direction C covers the whole set page for about 2 s, and any tap skips it. Direction B covers the rows for about 0.4 s. Is a short takeover acceptable at the start of a set?
3. **First set only.** Should the grandest version play only on the first set of a session, with a shorter one on later sets?
4. **Words.** Direction C shows "Shuffle up and deal" in large type. PRODUCT.md asks for plain, short words. Keep this phrase, use "Set 1 is in play", or show no phrase?
5. **Haptics and sound.** A vibration on Android is possible. iPhone Safari has no vibration API for web pages. Sound is possible but plays on every phone at the table, at different moments. Include either, or neither?

## Prototype

- Page: <https://claude.ai/artifact/9uzb4dHHQucR93mL5P2TWP> (private to the owner). Open it on the phone.
- Source: [prototype.html](1793955255_set_start_motion_assets/prototype.html).
- It is a copy of the set page for a host with eight players. It uses the app's tokens, Archivo and the spring curves from `static/css/app.css`. It moves only `transform` and `opacity`. It has Replay, a ×4 slow-down and a player's view.
- It uses the Web Animations API directly. A build must use `pokerMotion.run` and the rules in "Motion system".

## Current state

- `static/js/table.js:71-83` plays the start once per set and browser. A localStorage key `rack-start:{url}` records it. Resume play does not replay it.
- The movement: the felt is revealed left to right by `clip-path` in 500 ms. Then the timer side rises 8 px and the rows rise 8 px, 30 ms apart. The total is 780 ms (DESIGN.md, line 874; "Start" at line 1315).
- `static/js/flow.js:36` gives the start to `table.js` alone, so no other movement plays at the same time.
- The start plays on each phone that sees the set change from open to running. A player's phone sees it at the next poll: 1.5 to 4 s after the host taps (`static/js/live.js:18-25`). Around a real table the phones light up one after another.

Evidence: a slowed capture of the real start on a local server (set 21 from `seed_opening.py`, 390 × 844). The panel changes from the neutral Rail surface to felt behind a hard vertical edge. The rows move 8 px. At full speed this reads as a state change, not as the start of the night.

Inference: the clip edge reads more like a loading wipe than an occasion. `clip-path` is also not a composite-only property in every engine. A grander version must use only `transform` and `opacity`.

## Rules that any direction keeps

1. Money shows its accepted value from the first frame. No figure counts up. (DESIGN.md "Motion system", rule 3.)
2. Without Motion, under reduced motion or in a hidden tab, the page changes at once and is complete.
3. It plays once per set and browser. Resume play never replays it.
4. Any tap ends it. No control waits for it.
5. No casino props: no cards, no chip stacks in the pot, no photographs. Drawn furniture is allowed: felt, rail, chairs and the dealer button (DESIGN.md "Seat draw: the table").
6. Only `transform` and `opacity` move. Each light, dimming or glow is its own element, as in the seat draw. The felt is never repainted.
7. It must not cause the first-frame defect recorded in [motion_starts_a_frame_late.md](../wiki/footguns/motion_starts_a_frame_late.md).

## Directions

| | Name | Length | Takeover | What moves |
|---|---|---|---|---|
| 0 | Today's sweep | 0.78 s | No | Clip reveal, rows rise 8 px |
| A | Lights up | 1.2 s | No | Dimming lifts off the felt, a light falls from above, a glint crosses the figure, the rail flashes Brass once, In play stamps, each chip turns over |
| B | Felt from the tap | 1.1 s | Rows, 0.4 s | A felt disc grows from the finger to fill the screen, then lifts into the panel's shape; the rows rise out from under it |
| C | Shuffle up and deal | 2.0 s | Whole page | Dim stage, felt pool, the dealer button drops and spins, the chips sweep in and circle it, the set number stamps, then each item flies to its place on the page |
| D | Deal them in | 1.6 s (8 players) | No | Quick felt rise, then the dealer button hops down the rows; each chip turns over and its amount gets a Brass underline as the button reaches it |

### A. Lights up

- It reuses the seat draw's light and dimming. It reads as the same world, louder.
- It stays in place, so it is the safest for a host who taps again at once.
- Risk: the glint uses `mix-blend-mode`. Check its cost on an iPhone. The plain overlay is the fallback.

### B. Felt from the tap

- It connects cause and effect: this tap started the night.
- A player's phone has no tap. There the disc grows from the In play badge.
- Risk: the felt and the panel must line up when the cloth stops. The diamond pattern can show a seam. Anchor the pattern to the panel, or end with a short cross-fade.

### C. Shuffle up and deal

- It is the grand option. It is a short overture, like the seat draw stage.
- Each chip lands on its own row. This shows who is in the set. Chips for rows under the dock slide behind its edge and fade.
- The set number flies to the "Set N" label of the panel title.
- Risks:
  - It repeats the seat draw's imagery when a draw ran just before the start. Shorten it in that case, or start from the drawn seats.
  - With 12 players the ring is crowded at 320 px. Measure it.
  - A takeover hides the page for 2 s on each phone. Any tap skips it, and the stage must leave no layer that takes taps (the prototype's first build had this defect).

### D. Deal them in

- The players are the event, not the panel.
- It ties to the seat draw's dealer button.
- Risk: its length grows with the number of players. Cap the hops at eight, as the rows' stagger is capped.

## Recommendation

Use a tier:

- **First set of a session:** C, about 2 s, skippable.
- **Later sets:** A, about 1.2 s, in place.

Reason: grandeur works when it is rare. The first set starts the night, once. Later sets start after a break, and a 2 s takeover each time will become noise. A alone is the fallback if you do not accept a takeover.

The build is more than one commit. It needs a plan, an exception recorded in DESIGN.md, and a browser check of the start's frames on 320, 390 and 1280 px, with the processor slowed four times. The plan must also update the 900 ms check in `web/tests/browser/table.mjs:131`.

## Limits

- The prototype ran in headless Chrome only. No iPhone or WebKit check ran, so frame rate on a phone is not known.
- The prototype fixes eight players and a pesos game. Chips games, 2 players and 12 players are not shown.
- The player's view in the prototype changes only the origin of B and removes the dock. It does not show the poll delay.

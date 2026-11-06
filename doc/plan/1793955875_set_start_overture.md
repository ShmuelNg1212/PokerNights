# Shuffle up and deal: the set start overture

Status: approved 2026-11-06 ("plan is approved"); answers: every set, no haptics. Date: 2026-11-06, Asia/Manila. Study: [A grander set start](../study/1793955255_set_start_motion.md), direction C. Prototype: <https://claude.ai/artifact/9uzb4dHHQucR93mL5P2TWP>.

Mode: design (Operate, with one Experience moment). Visual authority: the built Rack in DESIGN.md. No new colour, font, raster file or dependency. Execute skills: `animate`, `mobile-native`. Rendezvous skills: `review-animations`, `break-ui`, impeccable `critique` and `audit`.

## Decided

- 2026-11-06, the human: "i like shuffle up and deal". This selects direction C and keeps the phrase "Shuffle up and deal".
- Selecting C accepts its length (about 2 s) and its takeover of the page. These need a recorded exception to the 900 ms rule, as the seat draw has.

## Answered questions

1. **Every set, or the first set only?** Every set, once per set and browser (the human, 2026-11-06: "Every set").
2. **Vibration?** None (the human, 2026-11-06: "no need for haptics").

## Outcome

When a set starts, each phone on the set page plays a short overture once. The screen dims to a pool of felt. The dealer button drops and spins. The players' chips sweep in and circle it. "Shuffle up and deal" and the set number appear. Then each chip flies to its player's row, the set number flies to the title, and the page is ready to use. Any tap ends it at once.

## Behaviour

| Moment | What happens |
|---|---|
| The host taps Start the set | The button shows its busy line. The overture starts when the page shows the running set, after the server accepts the start. It never plays before that |
| A player's phone on the set page | The same overture, at its next poll (1.5 to 4 s later) |
| Words on the stage | "Shuffle up and deal" (Brass, small capitals), "Set {N}" (large), then "{count} players · Blinds {blinds}". All values come from the page. A line with no blinds leaves out "· Blinds …" |
| Order of the chips | With a seated seat draw: the seat order, clockwise from the dealer. Without one: the order of the rows |
| Where the dealer button goes | With a seated seat draw: to the first dealer's row token. Without one: it shrinks into the In play badge. It never marks a player as dealer who was not drawn |
| A row under the host dock or below the screen | Its chip goes down behind the dock's edge, or off the screen edge, and fades. Nothing piles up on an edge |
| A tap, a key press or Escape during the overture | Every part goes to its end at once. The page is complete in that frame |
| A poll during the overture | No effect. The stage is outside the live region. Targets are measured again when the chips start to fly |
| The tab is hidden during the overture | The overture ends at once |
| A sheet or the seat draw stage is open | No overture. It is marked as seen |
| The page is left during the overture | The stage is removed and nothing keeps running |
| Resume play, a reload, a new tab | No replay. The existing `rack-start:{url}` key in localStorage records the start |
| Storage refused | No overture, as today |
| Reduced motion, no Motion file, no JavaScript | No overture. The page shows the running set at once |

## Motion

The prototype's timeline, about 1.95 s with eight players. Each layer is its own element and moves by `transform` or `opacity` through `pokerMotion.run`.

| Time | Part |
|---|---|
| 0 to 240 ms | The stage's dark ground fades in (Ground at 97%). A felt pool grows from the middle (`sheet` spring) |
| 0 to 640 ms | The dealer button (64 px, as drawn in the seat draw) drops from 20% size and turns 620° to rest |
| 140 to 1,300 ms | The chips sweep in from outside, 45 ms apart (`arrive` curve), then circle the button by 40° together |
| 500 to 820 ms | "Set {N}" stamps from 150% (`arrive` spring); the words above and below fade in |
| 620 to 1,260 ms | One Brass ring opens from the button and fades (the seat draw's winner ring) |
| 1,300 to 1,760 ms | Exit. The dark ground fades. The chips fly to their row tokens, 28 ms apart. "Set {N}" flies to the title's "Set {N}". The dealer button flies to its place (see Behaviour) |
| 1,700 to 1,950 ms | The real tokens, title label and badge show. The stage is removed |

- Under the stage the page is already in its running state. Money is at its accepted value in every frame.
- The real row tokens are hidden by an attribute on `<html>` while the stage runs, not by inline styles. A poll's morph removes inline styles from elements in `#live`.
- Each first keyframe is written before Motion starts ([motion_starts_a_frame_late.md](../wiki/footguns/motion_starts_a_frame_late.md)).

## Tasks

### 1. Record the decision (tests: alongside)

- [x] DESIGN.md: add "Set start overture (2026-11-06)". It supersedes the start row of the set page motion table (line 874) and the "Start" item of the 2026-10-31 revamp (line 1315).
- [x] Record it as a second exception to "a signature moment within 900ms", with the human's words.
- [x] State: drawn furniture only (felt, the dealer button, the chips that already are player identity). No cards.

Acceptance: DESIGN.md describes every row of Behaviour and Motion. Completion: the section is committed with the build.

### 2. Browser check first (tests: alongside)

- [x] New `web/tests/browser/overture.mjs` with a seed for an open set of 2, 8 and 12 players, one with a seated draw and one without.
- [x] Checks: the first visible frame of the stage is dark and has no chip at rest; each chip ends within 1 px of its row token; the dealer button ends on the dealer's token with a draw and on the badge without one; the stage leaves no element and no running animation; a tap at 600 ms completes the page in one frame; a poll during the overture changes nothing; a player's phone plays it once after its poll; a reload and Resume play do not replay it; reduced motion, a blocked Motion file and no JavaScript show the running set at once; 320, 390 and 1280 px; 12 chips at 320 px stay inside the screen; no frame over 50 ms with the processor slowed four times.
- [x] `web/tests/browser/table.mjs:127-134`: replace the felt-sweep and 900 ms checks with "the overture starts" and "the page is complete at the end".

Acceptance: the checks fail before task 3 and pass after it. Completion: the probe and its seed are committed and listed in `web/tests/browser/README.md`.

### 3. Build the overture (tests: alongside)

- [x] New `static/js/overture.js`, loaded after `table.js` in `templates/base.html`. It exposes one function, `window.pokerOverture.play(region)`, which returns at once when it cannot play.
- [x] `static/js/table.js:71-83`: keep the once-per-set key. Replace the sweep with a call to `pokerOverture.play`.
- [x] The stage is a `div` in `#table-sheets`, with `aria-hidden="true"`. It is not a dialog and it does not take focus. The page's own state change stays the announcement.
- [x] Skip on `pointerdown`, `keydown` and `visibilitychange`. Clean up in the `pokerPage.register` return.
- [x] CSS for the stage under one block in `static/css/app.css`, with the existing tokens.

Acceptance: every row of Behaviour holds on 390 and 1280 px. Completion: task 2's checks pass and the Django suite passes.

### 4. Phone checks (tests: alongside)

- [x] Add to TODO.md: start a set on the host's phone with two other phones on the page. Check that the overture plays on all three, that a tap skips it, and that a Rebuy right after it works.
- [ ] Run `mobile_motion.mjs`'s WebKit setup against the overture, as a WebKit frame check.

Completion: the TODO lines exist; the WebKit result is recorded in Checks.

## Not in scope

- Sound.
- A different overture for later sets.
- Vibration.
- The seat draw stage. It does not change.

## Risks

- iPhone frame rate is not known. The fail-safe: a frame over 50 ms in the slowed check fails the build in rendezvous, and the fallback is the plain page.
- With a draw just before the start, the dealer button and chips appear twice in a short time. The overture keeps the seat order so the two read as one story.

## Checks

Empty until rendezvous.

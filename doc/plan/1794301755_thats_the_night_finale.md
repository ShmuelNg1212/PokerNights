# That's the night: the session finale

Status: approved 2026-11-10 ("approved"). Date: 2026-11-10, Asia/Manila. Study: [More flair](../study/1794301535_more_flair.md), idea 5. This is plan 1 of 3 from that study. Plans 2 and 3 wait in the queue: [Chip to the pot](../roadmap/plan_queue/chip_to_the_pot.md), [Streaks and records](../roadmap/plan_queue/streaks_and_records.md).

Mode: design (one Experience moment). Visual authority: the built Rack in DESIGN.md. No new colour, font, raster file or dependency. Execute skills: `animate`, `mobile-native`. Rendezvous skills: `review-animations`, `break-ui`, impeccable `critique` and `audit`, `code-review`.

## Decided

- 2026-11-10, the human: picks 1, 2 and 3 of the study go to a plan.
- 2026-11-10, the human: "let it stay at around 900ms". The finale is a signature moment inside the 900 ms rule. It needs no recorded exception.
- 2026-11-10, the human: no haptics.

## Decided by the agent (say so if one is wrong)

1. The finale plays when the recap opens by itself: once for each session and viewer. A viewer who opens the session the next day sees it then. The existing `rack-recap:{session}:{viewer}` key records it. No second key is added.
2. Only the top positive result is marked. The other chips land in the page's order, not in result order. A stack does not rank a loss.
3. The stage shows one phrase, "That's the night". It shows no figure. The recap that follows has the figures.
4. The stage's shared parts move out of `overture.js` into one small module. The finale and the overture both use it.

## Outcome

A host closes a session. Each phone on the session page shows a short finale, once. The screen dims. The players' chips slide into one stack. The chip of the top result lands last, and a Brass ring opens around it. "That's the night" stamps in. Then the stage fades and the recap rises. All of it is at rest within 900 ms. A tap ends it at once.

## Behaviour

| Moment | What happens |
|---|---|
| The host taps Close the session | The server accepts the close. The session page loads with Who pays whom in view, as today. The finale plays over it, then the recap rises |
| A player's phone on the session page | The same finale, after its next redraw (`nightlive.js`, 5 s or less) |
| A viewer opens the closed session for the first time, later | The same finale, then the recap. See decision 1 |
| The chips | One chip for each player in the recap, copied from the recap's tokens. They land in the order of their members. The top result lands last |
| A tie for the top result | The tied chips land last, one after the other. One ring opens around the stack |
| No positive result (everyone even, or none after rake) | No ring. No chip is last on purpose |
| A full table of 12 players | The stagger and the lift get smaller. The end time does not change |
| A tap, a key press or Escape during the finale | Every part ends in that frame. The recap opens when the tap or the key is over. Enter or Space does not also press a control |
| The tab is hidden during the finale | The finale ends. The recap is open when the person comes back |
| The recap opens a second time (the button, a reload) | No finale. The sheet rises as today |
| The page is left during the finale | The stage is removed and nothing keeps running |
| Storage refused | No finale and no automatic recap, as today |
| Reduced motion, no Motion file | No finale. The recap opens by itself, as today |
| No JavaScript | No finale. The recap facts are in the page, as today |
| The install sheet wants the same moment | The recap keeps the turn, as today (`install.js:114`) |

## Motion

One stage, 900 ms at most from its first frame to the recap at rest. Each layer moves by `transform` or `opacity` through `pokerMotion.run`. The times below are the built ones. The first draft opened the recap at 600 ms; its spring then came to rest at 933 to 950 ms, so execute moved each part earlier.

| Time | Part |
|---|---|
| 0 to 160 ms | The dark ground fades in (Ground at 97%) |
| 0 to 420 ms | The chips rise into one stack, 30 ms apart at most, each 6 px above the one before (`shift` spring, no bounce) |
| 200 to 440 ms | "That's the night" stamps from 150% (`arrive` spring). Brass, as "Shuffle up and deal" |
| 340 to 640 ms | With a top result: one Brass ring opens from the top chip and fades |
| 490 to 650 ms | The ground, the stack and the words fade |
| 490 to about 850 ms | The recap sheet rises (`sheet` spring) |

- Under the stage the page is the closed session. Each money figure is at its accepted value in each frame.
- The stage is a `div` in `#table-sheets` with `aria-hidden="true"`. It does not take focus. The recap's dialog is the announcement.
- The first keyframe of each part is written before Motion starts ([motion_starts_a_frame_late.md](../wiki/footguns/motion_starts_a_frame_late.md)).

## Changed in execute

- **Twelve players, not fourteen.** A table has 12 seats at most (`games/services.py` `create_table`). The seed's largest session has twelve.
- **The order of the other chips** is the order of their members. The recap's list is in result order, so "the page's order" would have ranked the losses.
- **A skip opens the recap when the tap or the key is over**, not in the same frame. The same tap would otherwise land on the sheet's backdrop and close it.
- **Script order.** `stage.js` and `finale.js` load before `sheets.js`, not after `overture.js` ([module_start_runs_at_registration.md](../wiki/footguns/module_start_runs_at_registration.md)).
- **The screen is taken.** The stage carries `data-stage`. `nightlive.js`, `install.js`, `carry.js` and `alerts.js` treat it as an open sheet. Without this the install sheet could open over the stage at 500 ms, and a redraw during the stage could lose the recap.
- **The top result** is marked in the template (`data-top` in `_night_recap.html`), with two Django tests.
- **Other probes.** `night.mjs`, `carried_debts.mjs` and `debts.mjs` now wait for the finale's end. `night_live.mjs`, `install_prompt.mjs` and `journey.mjs` needed no change.

## Tasks

### 1. Record the decision (tests: alongside)

- [x] DESIGN.md: add "Session finale (2026-11-10)" after "Set start overture". Describe each row of Behaviour and Motion.
- [x] State that it is inside the 900 ms rule, with the human's words.
- [x] State: drawn furniture only (the players' chips, the Brass ring). No cards, no confetti, no figure.
- [x] "Closing recap" (DESIGN.md:325): say that the first automatic opening follows the finale.

Acceptance: DESIGN.md describes each row of Behaviour and Motion. Completion: the section is committed with the build.

### 2. Move the stage shell out of the overture (tests: alongside)

- [x] New `static/js/stage.js`, loaded before `overture.js` in `templates/base.html`. It holds what a stage needs: build the `div` in `#table-sheets`, `run` with the first keyframe written, timers, the skip on `pointerdown`, `keydown` and `visibilitychange`, the swallowed click after a skipping tap, and the 4 s guard.
- [x] `static/js/overture.js` uses it. Its timeline, its words and the felt light do not change.

Acceptance: the overture behaves as before. Completion: `overture.mjs` passes all of its checks with no change to the probe.

### 3. Browser check first (tests: alongside)

- [x] New `web/tests/browser/finale.mjs` with a seed: a session ready to close with 2, 8 and 14 players; one with a tie at the top; one where everyone is even.
- [x] Checks: the host's close plays the finale and then the recap is open; the recap is at rest within 900 ms of the stage's first frame; the top result's chip is the last to land and has the ring; a tie gives one ring; an even session gives no ring; a tap at 300 ms opens the recap in that frame and presses nothing under it; Enter does not press the focused control; a second phone plays it once after its redraw; a reload and "View session recap" do not replay it; a hidden tab ends it; the stage leaves no element, no running animation and no inline style; reduced motion, a blocked Motion file and no JavaScript give today's page; 320, 390 and 1280 px; no frame over 50 ms with the processor slowed four times.
- [x] Find the checks in `night.mjs`, `night_live.mjs` and `journey.mjs` that wait for the automatic recap. Make them wait for the finale's end.

Acceptance: the new checks fail before task 4 and pass after it. Completion: the probe and its seed are committed and listed in `web/tests/browser/README.md`.

### 4. Build the finale (tests: alongside)

- [x] New `static/js/finale.js`, loaded after `stage.js`. It exposes `window.pokerFinale.play(region, done)`. It calls `done` exactly once: at the end, on a skip, or at once when it cannot play.
- [x] `static/js/sheets.js:181-191`: keep the key and the scroll to Who pays whom. Replace the direct `open("recap", …)` with `pokerFinale.play(region, open the recap)`. Without `pokerFinale` it opens the recap as today.
- [x] The chips are copies of `.recap-ranking .chip` in the recap's source. The top result is read from the page (the recap's winners), not worked out in the script.
- [x] CSS for the stage in one block in `static/css/app.css`, next to the overture's, with the existing tokens.
- [x] Clean up in the `pokerPage.register` return.

Acceptance: each row of Behaviour holds at 390 and 1280 px. Completion: task 3's checks pass and the Django suite passes.

### 5. Phone checks and docs (tests: alongside)

- [x] TODO.md: close a session with two other phones on the session page. Check that the finale plays once on each, that the top chip gets the ring, that a tap skips to the recap, and that Reduce Motion gives the recap alone.
- [x] Run the WebKit setup of `mobile_motion.mjs` against the finale as a frame check.
- [x] Sync `doc/wiki/features.md` (closing a session).

Completion: the TODO lines exist; the WebKit result is recorded in Checks.

## Not in scope

- Sound and vibration.
- A change to the recap's content or to the share picture.
- Night titles (idea 6 of the study).
- A finale for the end of one set.

## Risks

- 900 ms is short for chips, words and a sheet. Fail-safe: if the frame check fails or the moment reads as noise in `critique`, drop the ring first, then the stagger. The limit does not move.
- Moving the stage shell touches a released feature. Fail-safe: task 2 is its own commit and `overture.mjs` guards it.
- The session page redraws by a Turbo morph, then `pokerPage.start()` runs again ([in_place_answer_skips_page_start.md](../wiki/footguns/in_place_answer_skips_page_start.md)). A second start must not play a second finale: the key is written before the stage is built.

## Checks

To be recorded at rendezvous.

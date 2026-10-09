# Arrival after login: plan

Status: approved 2026-10-09 ("approved"); all four decisions as recommended. Date: 2026-10-09, Asia/Manila. Study: [Arrival after login](../study/1791546703_arrival_after_login.md).

## Outcome

Logging in ends with the app answering: the chip lands in the top bar and the screen you arrive on settles into place around it, leading your eye to what needs you. It happens once per login, takes under a second and never holds up a tap.

Mode: Operate. Visual authority: the built Rack in DESIGN.md and its "Front door" section. No new colour, font, asset or words. No migration. Built with the design and motion skills.

## What you will see

On the one page that follows a successful log in, sign up, reset link or claim:

| Moment | What happens |
|---|---|
| The chip lands in the top bar | The top bar's mark settles: it sinks 2px and springs back, once, as a button does |
| Your groups: the cards | Each group's card rises 16px and fades in, 70ms apart. The fourth card and any after it arrive together |
| The players on a card | The tokens slide into their overlap from the right, 30ms apart, like chips set down in a row |
| A set in play | After its card lands, the "In play" badge springs in |
| Money to settle | The brass "To settle" heading takes the underline that marks a change elsewhere in the app, once |
| "New group" and the heading | The heading is there from the start; the New group button fades in last |
| A newcomer's first screen | The mark, the heading, the sentence and the form rise in turn, 60ms apart |
| Any other landing page (a group after an invite, an address you were sent from) | The chip's landing, and the page's content rises 12px once as a whole |
| Every later visit, Back, a reload | Nothing. The screen is simply there, as today |
| Reduced motion | Nothing moves |

Rules that hold throughout:

- Every money figure shows its true value from the first frame. A card moves with its figures inside it; no digit counts or rolls.
- Nothing waits. A tap during the movement goes to the control under the finger, and the first tap or key ends the movement.
- All of it is over within 900ms of the page appearing. No exception to DESIGN.md is needed.
- Only position and opacity move.
- The page is complete without it: JavaScript off, Motion blocked or an old browser shows the screen as it is today.

## Decisions for you

Approving accepts the recommendations unless you say otherwise.

1. **No greeting sentence.** "Welcome back, shm" would be new words, and wrong for someone who signed up a second ago. Recommended: the movement is the welcome. Say if you want a line of words; I would then propose its wording first.
2. **Every way of logging in gets it,** not only the Log in form: sign up, a reset link and a claim link too. Recommended: yes, they are all "you are in now".
3. **The same switch.** `DOOR_MOTION=False` turns this off together with the front door's movement. Recommended: no second switch.
4. **Nothing celebratory.** No confetti, no glow, no count-up of your record. Recommended: keep it to arriving, since this screen can also carry what you owe.

## Implementation

Branch `feat/arrival-after-login` from `main`. Not merged and not pushed without your word.

1. **Tests first** (`accounts/tests/test_door.py`, `web/tests/test_home.py`):
   - the page after a login by form, by sign-up, by reset link and by claim link carries `data-welcome`; the next page does not; a reload does not;
   - a signed-out page never carries it; a refused login sets nothing;
   - the cookie lasts 30 seconds, is `SameSite=Lax`, `Secure` in production, and is removed by the page that reads it;
   - `DOOR_MOTION=False`: no cookie and no `data-welcome`;
   - no database write and no extra query on Your groups (the existing query-count test stays as it is).
2. **Server** (`config/door.py`): a receiver for `user_logged_in` marks the request; `DoorCookie` sets the cookie `arrived` on that response and removes it once a signed-in page has read it; the `door` context gains `welcome`. `base.html` writes `data-welcome` on `<main>`. No view, model or service changes.
3. **CSS** (`app.css`, after the front door's arrival): keyframes that run from a start state to the ordinary state, with the app's `shift` and `arrive` springs, keyed on `[data-welcome]`; the steps for cards, tokens, the badge, the heading's underline, the newcomer's screen and the plain rise for other pages.
4. **JavaScript** (`door.js`): end the movement on the first key or tap; give the top bar's mark its settle through `pokerMotion.run` when the browser reports that it carried the chip. Nothing in it is needed for the page to work.
5. **Browser check**, new `web/tests/browser/welcome.mjs`, at 320 × 568, 390 × 844 and 1280 × 800:
   - the first frame after a login is the start state, with no frame of the finished page before it;
   - every figure's text on the first frame equals its text at rest;
   - the movement is over within 900ms; a tap or key ends it within 50ms; a tap on a card's button during it follows the link;
   - one card, four cards and seven cards; a card in play; a card with dues; the newcomer's screen; a landing on a group page;
   - a reload, Back and a second visit play nothing;
   - reduced motion, JavaScript off, Motion blocked, the switch off: the screen is complete and still;
   - late frames with the processor slowed four times, with and without it;
   - no inline style and nothing running at rest.
6. **Regression.** Both test suites (SQLite and PostgreSQL 17). `door.mjs`, `home.mjs`, `screens.mjs`, `navigate.mjs` and `motion.mjs`.
7. **Sync docs.** DESIGN.md (a paragraph and table under "Front door"), wiki features, browser README, TODO with the phone checklist.

No critique is planned for this cycle: it adds movement to a screen whose layout and words do not change.

## Acceptance criteria

- AC1. The page after each way of logging in plays the arrival once; a reload, Back and later visits play nothing.
- AC2. Every money figure is at its final text on the first frame.
- AC3. The movement is over within 900ms, and a tap or key ends it at once.
- AC4. On Your groups the order is cards, then tokens, then the "In play" badge and the "To settle" underline.
- AC5. With reduced motion, no JavaScript, Motion blocked or `DOOR_MOTION=False`, the screen is complete and still.
- AC6. No query is added to Your groups and nothing is stored.
- AC7. Both suites pass; the listed browser checks pass.

## Out of scope

- A greeting sentence, a first-step guide for a new player, or any change to what Your groups shows.
- Redrawing the top bar's mark so it can turn.
- Celebrating a win or a settled session.

## Rollback

`DOOR_MOTION=False` in Vercel stops it at once. To remove it, revert the feature commits. No migration; the cookie holds nothing and lasts 30 seconds.

## Cannot be verified from here

A physical iPhone, and how the movement reads together with the chip's flight on one. These go on your phone checklist.

## Progress and blockers

2026-10-09: Study and plan written. Waiting for approval.

2026-10-09: approved ("approved"), all four decisions as recommended. Built on `feat/arrival-after-login`.

Changes from the plan:

- **Other landing pages do not rise.** Moving `<main>` would re-anchor the floating messages and the host dock inside it for the length of the movement. There only the top bar's mark lands.
- **The top bar's mark lands by CSS,** on every arrival, not by a script that waits for the browser's report of the carry. It is 2px and reads the same without the carry.
- **Checked with one card and five,** not one, four and seven: the seed has five. The fourth and fifth share a step, which is the rule the seven were meant to show.
- **A fix outside the plan:** `turbo-setup.js` left a promise unhandled when a link was tapped while the browser was still carrying the chip in. The screen changed correctly, but the console showed an error. It is now ignored on purpose.
- **A front-door screen seen signed in** (Join, Claim) passes the arrival on to the page behind it.

Verification:

- 915 tests on SQLite (15 skips) and 915 on PostgreSQL 17. Ten new tests.
- `welcome.mjs` 35 of 35. `door.mjs` 134, `home.mjs` 60, `screens.mjs` 46, `motion.mjs` 34, `navigate.mjs` 52, each on a fresh seed.
- The movement ends at 880ms.
- With the processor slowed four times, the arrival had one late frame (50ms); a plain visit to the same page had none.

Acceptance: AC1 to AC7 are met. AC6 by the unchanged query-count tests.

Not verified: a physical phone, and how the movement reads together with the chip's flight on one. A claim link was not walked in the browser; it logs in through the same Django call the tests cover.

2026-10-09, after the human tried it locally: "there's a moment where the login block stays in view while the animations play". Cause: the login sheet had a carried name on every change of screen. Going into the app it had nothing to become, so the browser kept its layer, with the opaque backing that stops it stretching, over the new screen for the 420ms of the chip's flight. This was already in the front door release (`394b4f3`); the new arrival made it visible. Fix: the sheet and the name are carried only between two front-door screens (`data-door-swap`). `welcome.mjs` has a 36th check: after a login the browser carries the chip and the page, and no layer for the sheet. `door.mjs` 134 of 134, with Log in ⇄ Sign up still moving the sheet. Seen once and not again in two reruns: the browser check reported the browser aborting the carry on a just-started server.

2026-10-09 rendezvous: merged into `main` as `f2bd882 feat: merge the arrival after login` and pushed on the human's word ("ok push this to the live version"). 915 tests passed on PostgreSQL 17 on the branch and on SQLite on `main` before the push. About three and a half minutes later the live stylesheet had the arrival keyframes and the `data-door-swap` fix, and the live `door.js` had its half. Previous production commit `394b4f3`. Not checked on the live site: a login. The phone checks are open.

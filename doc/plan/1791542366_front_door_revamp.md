# Front door revamp: plan

Status: approved 2026-10-09 ("approved"); all six decisions as recommended. Date: 2026-10-09, Asia/Manila. Study: [Front door revamp](../study/1791542264_front_door_revamp.md).

## Outcome

Opening PokerNights feels like arriving somewhere made with care. The chip lands, the form rises to meet you, the page answers each thing you do, and logging in carries the chip into the app. Logging in takes no longer than it does today.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new colour, font or raster asset. No migration. Built with the design and motion skills.

## What you will see

### The frame, on all seven front-door screens

- **Two surfaces.** The top of the screen is the night: the ground colour with the chip and the name. Below it a raised sheet holds the task: the rail surface, a fine edge, 26px corners. On a phone the sheet runs to the bottom of the screen; from 900px it is a centred 440px card.
- **The chip is drawn in the page**, not loaded as a picture, so its ring and its crescent can move. It gets the short solid underside the app's buttons have.
- **Log in:** the chip at 96px, "PokerNights" under it, the description, then the sheet with the heading and form.
- **Sign up and Set a new password:** a compact row, the chip at 56px beside the name, so the long form fits. The description moves to the foot of the sheet.
- **Invite needed, broken links, Join group, Claim:** the same frame. The claim page keeps the player's own token as its hero.
- Fields, buttons, labels, help, errors, the Show button and every word of a rule stay as they are.

### The movement

| Moment | What happens |
|---|---|
| You arrive (first time in a browser session) | The chip drops 28px and settles with a small bounce while its ring turns a third of a turn into place. The crescent rises into the chip. The name widens into place. The sheet rises 24px; its heading, fields and button follow 40ms apart. The description fades in last. About 1 second in all |
| You arrive again in the same session | Everything fades in and rises 8px together, in 240ms. The chip does not drop |
| During any arrival | The username field has focus from the first frame. A key or a tap ends the arrival at once |
| You type | The chip's ring turns a little with each key, and back with each delete. The crescent stays still |
| You tap Show | The crescent tips, like an eye opening; it tips back on Hide |
| You send the form | The ring spins steadily until the answer comes. The button keeps its busy line and words |
| You are refused | No arrival. The chip shakes once with the notice, and the refused field is nudged as today |
| You get in | The chip travels from the middle of the screen into the top bar of the next screen, shrinking to the small mark. On Log out it travels back. Where the browser cannot do this, screens change as today |
| Log in ⇄ Sign up | One place changing: the chip glides between its two sizes, the sheet changes height, the fields fade through. No full-screen fade |
| Quieter screens | The short arrival only. The claim token still springs in |
| Reduced motion | Nothing moves. Every state still changes |

Rules that hold throughout:

- Nothing waits for a movement. A tap during one goes to the control under the finger.
- Nothing loops while the page is idle. The chip is still unless you did something.
- The page is complete without any of it: JavaScript off, Motion blocked, or an old browser shows the new frame, still.
- Only position, size-by-scale, rotation and opacity move. One measured exception: the name's width as it arrives (decision 4).
- Username, password, their names for the phone's password manager, and the way the form is sent are untouched.

## Decisions for you

Approving accepts the recommendations unless you say otherwise.

1. **The 1-second arrival is an exception to DESIGN.md's 900ms rule,** for the front door only, once per browser session. You chose this; it will be written into DESIGN.md.
2. **Make the invitation the subject.** On an invited Sign up the heading becomes "Join {group}" with "Create your account to get in." under it, in place of "Create your account" and "You're invited to {group}". This is the open item from the last critique. Recommended: yes.
3. **Move the description to the foot of the sheet on Sign up and Set a new password** ("It records the game. It never moves money." stays word for word). It frees the height the sheet costs. Recommended: yes.
4. **The name widens as it arrives** (Archivo's width axis, from compressed to its normal 88%). It is the one movement that is not position or opacity. It stays only if the check finds no late frame on a slowed phone; otherwise the name fades and rises. Recommended: try it under that gate.
5. **One switch, `DOOR_MOTION=False` in Vercel,** removes every new movement and leaves the new frame still. No switch returns the old frame; keeping two frames would double the upkeep. Recommended: accept.
6. **The chip turns as you type, in every field.** It shows nothing the dots in the password field do not already show. Say if you want it off for passwords.

## Implementation

Branch `feat/front-door` from `main`. Not merged and not pushed without your word.

1. **Probe the hand-over first** (throwaway, not kept): one name shared by the hero chip and the top bar's mark, across a native login POST and its redirect, in Chrome and in iPhone-sized Safari via the simulator if available. If it cannot work after a POST, the hand-over is dropped from this cycle and the rest goes on; you are told.
2. **Tests first** (`accounts/tests/test_entry.py`, `web/tests/test_branding.py`):
   - each of the seven screens renders the frame, the inline mark and the right hero size;
   - `data-arrival` is `full` on a first GET, `short` once the cookie is set, absent on a refused POST and when `DOOR_MOTION` is off;
   - the cookie is session-lifetime, `SameSite=Lax`, `Secure` in production, and no database row is written for a signed-out visitor;
   - field names, `autocomplete` values, `next`, the single alert and autofocus placement are unchanged;
   - the invited heading (decision 2).
3. **Server.** `config/settings.py`: `DOOR_MOTION`. `accounts/views.py` and the invite, claim and reset views: a small shared helper that reads and sets the cookie and passes `arrival` to the template. No model, no service, no write.
4. **Templates.** A new `partials/mark.html` (inline SVG with named parts). `partials/entry_head.html` gains the `row` variant. Each screen wraps its task in the sheet. `base.html`: the top bar's mark gets the shared name; one new script tag.
5. **CSS** (the entry section of `app.css`): the frame, the two hero sizes, the sheet, the arrival keyframes with the app's springs as `linear()` curves made with the motion skill's spring generator, the names for the two view transitions, reduced motion.
6. **JavaScript.** One new module, `static/js/door.js`, registered with `page.js` and stopped on leaving: end the arrival on the first key or tap; the ring's turn per key; the crescent on Show; the spin while `aria-busy`; the shake on a refused page. All through `pokerMotion.run`, cleaned with `settle`. Nothing in it is needed for the page to work.
7. **Browser check,** new `web/tests/browser/door.mjs`, at 320 × 568, 390 × 844 and 1280 × 800:
   - first frame of each arrival is the start state, with no frame of the finished page before it;
   - the username field accepts a key on the first frame; a key ends the arrival within 50ms;
   - the full arrival is over within 1,100ms, the short one within 300ms;
   - no horizontal overflow, every control at least 48px, text at 4.5:1 or more, the 3px focus ring visible on the sheet;
   - the empty Sign up, invited and not, shows its whole button at 390 × 844; the refused heights are recorded;
   - typing, deleting, Show, sending, a refusal: each movement runs, and no inline style is left at rest;
   - ten changes between Log in and Sign up leave one set of listeners and nothing running;
   - reduced motion, JavaScript off, Motion blocked, `DOOR_MOTION` off: the frame is complete and still, and login works;
   - late frames at 4× CPU slowdown during the full arrival (the gate for decision 4);
   - the hand-over, or its plain fallback.
8. **Regression.** Both test suites (SQLite and PostgreSQL 17). `entry.mjs`, `reset.mjs`, `claim.mjs`, updated for the frame, then `motion.mjs`, `screens.mjs` and `navigate.mjs`, and the scripts that log in through these pages.
9. **Review.** One `/impeccable critique` of Log in and Sign up, scored beside the earlier 25 of 40, and one fix batch from it.
10. **Sync docs.** DESIGN.md addendum (frame, movement table, the arrival exception), wiki features and deployment (the switch), browser README, TODO with the phone checklist.

## Acceptance criteria

- AC1. All seven screens use the new frame, with no overflow and 48px controls at the three sizes.
- AC2. The first visit plays the full arrival within 1.1 seconds; later visits in the session play the short one; a refused page plays neither.
- AC3. The username field takes a key on the first frame, and a key or tap ends any arrival.
- AC4. The chip answers typing, Show, sending and a refusal as the table says, and is still when idle.
- AC5. Log in ⇄ Sign up changes as one place in a browser with view transitions; getting in carries the chip to the top bar, or step 1 recorded why not.
- AC6. With reduced motion, no JavaScript, Motion blocked or `DOOR_MOTION=False`, every screen is complete and every form works.
- AC7. The empty Sign up shows its button without a scroll at 390 × 844.
- AC8. A password manager sees the same form: names, `autocomplete` and submission unchanged.
- AC9. Both suites pass; the listed browser checks pass.
- AC10. The repeat critique scores above 25 of 40.

## Out of scope

- A password-strength meter or live rule ticks. Two of the four rules can only be judged by the server.
- A "change my password" screen (still in TODO).
- New copy beyond decisions 2 and 3.
- Sound, haptics, a marketing page, any picture.
- The first step for a new player on the group page (still in TODO).

## Rollback

`DOOR_MOTION=False` in Vercel stops the movement at once. To return the old frame, revert the feature commits. No migration; the cookie holds nothing and expires with the browser session.

## Cannot be verified from here

A physical iPhone (Safari and the installed app), a real password manager's fill and save, and a screen reader. These go on your phone checklist.

## Progress and blockers

2026-10-09: Study and plan written after three direction questions to the human. Waiting for approval.

2026-10-09: approved ("approved"), all six decisions as recommended. Built on `feat/front-door`.

Changes from the plan:

- **Step 1, the probe.** Not run as a separate throwaway. The carry was built and then measured: in Chrome 155 the browser carries the chip across the login POST and its redirect, and back on log out. iPhone Safari was not available here; it is on the phone checklist.
- **The cookie's helper** is a context processor and a middleware in `config/door.py`, so no view changed.
- **The top bar gives the carried name up inside the app** (`data-door-done`). Without it every screen change in the app would have gained a layer for the mark.
- **Decision 4.** The name's widening stays: with the processor slowed four times, no frame was late with it or without it (worst frame 33ms both ways).
- **`entry.mjs`** changed in three places: the frame's selectors, the invited heading, and rounding a height measured mid-arrival (47.99994px).
- **From the critique:** the phone keyboard's return key now says Next, then Go. The other findings need a decision or a new cycle and are in TODO.

Verification:

- 905 tests on SQLite (15 skips) and 905 on PostgreSQL 17.
- `door.mjs` 134 of 134. `entry.mjs` 91, `reset.mjs` 43, `claim.mjs` 30, `motion.mjs` 34, `screens.mjs` 46, `navigate.mjs` 52, each on a fresh seed.
- Critique: 29 of 40, two isolated assessments. Snapshot `.impeccable/critique/2026-10-09T11-18-45Z__templates-registration-login-html.md`.

Acceptance:

- AC1 to AC4 and AC6 to AC10 are met. The full arrival runs 780ms.
- AC5 is met in Chrome. Safari on an iPhone is not verified.

Not verified: a physical phone, the installed app, a real password manager, a screen reader, and whether the phone's keyboard hides the chip while typing (the critique computed that it may on Sign up).

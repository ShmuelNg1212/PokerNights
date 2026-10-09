# Arrival after login: study

Date: 2026-10-09, Asia/Manila. Request: "can you add some animations once a user has successfully logged in." It follows the front door, released the same day as `394b4f3`.

Skills used: the design skill (impeccable, `shape`) and the motion skill. No question round was held; the choices are in the plan as decisions, as in earlier cycles.

## What happens today

A person logs in and a new page loads. In a browser that can, the chip travels from the front door into the top bar (420ms) while the rest cross-fades (180ms). Then the screen is simply there. The front door makes an entrance; the room behind it does not answer.

Where a login lands:

| Way in | Lands on | Extra |
|---|---|---|
| Log in | Your groups, or the address the person was sent from (`next`) | none |
| Sign up from an invite | The group's page | The toast "Welcome to {group}. You're in." |
| Sign up without an invite | Your groups, usually the "Start your first group" screen | none |
| Reset link | Your groups | The toast "Password changed. You're logged in." |
| Claim link, signed out | The group's page | A welcome toast |

Every one of them calls Django's `login()`, in `accounts/views.py` and inside Django's own `LoginView`. Django sends the signal `user_logged_in` with the request each time.

Your groups is one card per group: the name and the overlapping player tokens, then a band for what is going on now (felt when a set is in play), then "To settle" and the viewer's own figures. A newcomer sees the mark, a heading and the create form.

## What the arrival should do

The same job the front door's arrival does, once more: say that the tap worked and show where to look. On Your groups there is an order of importance already built into each card: a set in play, then money to settle, then your record. The movement can follow that order.

It must stay inside the rules that already hold:

- Money is at its accepted value on the first frame. A card may fade and rise with its figures inside it; a digit never counts or rolls.
- Nothing waits. A tap during the movement goes to the control under the finger.
- A signature moment ends within 900ms, once. This one needs no exception.
- Reduced motion removes it. Without JavaScript or Motion the screen is complete.
- No casino imagery. Cards "rise", they are not dealt from a deck.

## Findings

1. **The server has to say "this page is the arrival".** The page that follows a login is an ordinary GET. A mark in the address would stay in the history and replay on Back. The front door already has the right tool: `config/door.py` sets a cookie from a middleware. A listener on `user_logged_in` can mark the request; the middleware then sets a cookie that lasts 30 seconds; the next page reads it, writes `data-welcome` on `<main>`, and the middleware removes the cookie. One page gets it, whatever view served it. Nothing is stored, and no view changes.

2. **It must be CSS, for the same reason as the front door.** Scripts are deferred, so a script-driven entrance would show the finished page for a frame first (`motion_starts_a_frame_late.md`). Keyframes that run from a start state to the ordinary state begin on the first paint and leave a complete page if they never run.

3. **It plays under the chip's flight.** The browser's own change between the two pages lasts up to 420ms. The new page is live underneath it, so its own keyframes show through. Starting the cards about 100ms in lets the cross-fade clear first; the chip lands as the first card settles.

4. **What can move, cheaply.** All of it is `transform` and `opacity` on a handful of elements:
   - each group card rising into place, one after another;
   - the player tokens of a card sliding into their overlap, like chips being set down in a row;
   - the "In play" badge springing in after its card, because that is the one thing a host came for;
   - the brass "To settle" heading taking the existing `mark-draw` underline;
   - the top bar's mark settling as the chip lands.

5. **The top bar's mark is an `<img>`.** It can be nudged as a whole (a small settle) without being redrawn in parts. Making it turn like the front door's chip would mean drawing it inline on every page; not worth it for a 28px mark.

6. **Other landing pages.** A `next` address or a group page after an invited sign-up has no cards. There the chip's landing and the page's first block rising are enough; the welcome toast already arrives with the `arrive` spring.

7. **Many groups.** Stagger steps are capped (as roster rows are capped at eight), so a person in ten groups does not wait: the fourth card and every later one arrive together.

8. **Words.** A greeting ("Welcome back, shm") would be new copy, and wrong for a person who signed up a second ago. The top bar already shows the username. The movement can carry the welcome without a sentence.

9. **One switch is enough.** `DOOR_MOTION=False` already means "no movement on the way in". This is the last step of the same way in.

## Risks

| Risk | Answer |
|---|---|
| Your groups is the most used screen; a fault there is seen by everyone | Keyframes only run from a visible, complete page; nothing is hidden until a script shows it. `DOOR_MOTION=False` removes it |
| It replays on Back, reload or a later visit | The cookie is removed as the page is served. A page restored by Back does not restart finished CSS animations |
| The cookie outlives a failed redirect | It lasts 30 seconds and is only read by a signed-in page |
| Money seems to animate | Checked on the first frame: every figure's text equals its final text |
| It fights the chip's flight on a slow phone | Measured with the processor slowed four times, as the front door was |

## Not studied

Sound, haptics, confetti or any celebration of a win; a greeting sentence; changes to what Your groups shows.

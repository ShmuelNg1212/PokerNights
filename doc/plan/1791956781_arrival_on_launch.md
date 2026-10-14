# The arrival on every app open: plan

Status: approved 2026-10-14 ("approved", with the recommended answers: each time the app is started; the installed app and a new browser tab alike). Built on `feat/arrival-on-launch`, not released. Date: 2026-10-14, Asia/Manila. Study: [The arrival on every app open](../study/1791956780_arrival_on_launch.md).

## Outcome

Each time a signed-in person starts PokerNights, after the splash screen, Your groups arrives as it does after a log-in: the cards rise in turn, the player tokens slide in, In play springs, the brass line draws under "To settle", and the header's chip lands. Nothing plays for the rest of that visit, and nothing plays when the app comes back from the background.

No new movement, colour or words. No migration, no server state.

## Decisions for the human

1. **When it plays.** Recommended: each time the app is started (study, option A). Alternative: also when it comes back after 15 minutes or more away (option B), with the cards vanishing and rising again.
2. **Where.** Recommended: the installed app and a new browser tab alike. Alternative: the installed app only.

## Implementation

Branch `feat/arrival-on-launch` from `main`.

1. **The mark.** In `templates/base.html`, the first thing inside `<main>` is a one-line inline script, rendered only when the switch is on and the person is signed in. If the window's `sessionStorage` has no `pn-launched` entry and the navigation is a `navigate`, it writes the entry and adds `data-welcome` to `<main>`; it writes the entry in every other case too, so only the first page of a window can play. A refused `sessionStorage` plays nothing.
2. **The rest is today's arrival.** The `welcome-*` CSS, `door.js`'s ending on a tap or key and after 1.2 seconds, reduced motion and `DOOR_MOTION=False` all apply unchanged. A page that the server already marked after a log-in plays once, not twice.
3. **The switch.** `LAUNCH_ARRIVAL` (default on) in `config/settings.py`, read by the `door` context processor. `False` returns to today: the arrival only after a log-in.
4. **Tests** (Django, `web/tests/`): the script is in a signed-in page with the switch on; absent signed out, with `LAUNCH_ARRIVAL=False` and with `DOOR_MOTION=False`.
5. **Browser check:** `welcome.mjs` gains a launch section at 390 × 844 and 1280 × 800: a new window on `/` plays the arrival and ends within 900 ms; a second page, Back, a reload and a Turbo visit to Your groups in the same window play nothing; a new window plays it again; reduced motion stills it; the switch off plays nothing; the log-in arrival still plays once.
6. **Docs.** DESIGN.md "Arrival into the app" gains the launch row (and "A later visit, a reload, Back: Nothing" keeps holding within a window); `doc/wiki/features.md` "Arrival after login"; TODO.md.

## Acceptance

1. The Django suite passes on SQLite and PostgreSQL, and as the Vercel build runs it (browser scripts left out).
2. `welcome.mjs` passes, with its new checks failing first on `main`.
3. On the human's iPhone: close the app fully, open it: the splash, then Your groups arrives. Open a group and come back: nothing plays. Switch to another app and back: nothing plays.

## Fail-safe

The script only adds the mark the log-in arrival already uses; if it fails, the page is today's. `LAUNCH_ARRIVAL=False` in Vercel turns it off at the next deployment without a code change.

## Not covered

- A movement for a resume from the background (decision 1, option B, is the cards replaying; anything quieter is its own design).
- The front door's chip blinking out after the splash when signed out.

## Release

Built and checked locally, then held for the human's word. After a release, one request about four minutes after the push to see the script on the live page.

## Progress

- [x] Approve the plan and answer the two decisions. Approved 2026-10-14.
- [x] Build, test, and run the browser check.
- [ ] Say when to merge and release it.
- [ ] On your iPhone: close the app fully and open it, then move around and switch away and back. Say whether the arrival feels right each time you open it.

## Verification record (2026-10-14)

- **Django.** 5 new tests in `accounts/tests/test_door.py` (`LaunchArrivalTests`). 1,123 pass on SQLite, on PostgreSQL 17, and with `web/tests/browser/` moved aside as the Vercel build has it.
- **`welcome.mjs`:** 54 of 54, twice, with both switches served (18 new checks). Against `main`'s code the new launch checks fail (7 failures; the rest pass). Screenshot of Your groups at rest after an open, 390 px: whole.
- **`door.mjs`:** 134 of 134, because `door.js` changed.
- **Not checked:** the iPhone. Whether iOS empties `sessionStorage` when it closes the installed app decides whether the arrival plays on each start; the phone check shows it.

### Rulings made while building

1. **The script is in the head, not in `<main>`.** The plan put it first inside `<main>`. `ScriptsLoadOnceTests` holds the project's rule that no script is in the body ([footgun](../wiki/footguns/scripts_run_once_per_tab.md)). So the script writes `data-launch` on `<html>` from the head, before the stylesheet so it waits for nothing; the arrival's CSS answers `data-launch` as well as `data-welcome`, and `door.js` takes it off when the arrival ends and when the page is left, because `<html>` outlives a screen change.
2. **A comment that broke the head.** A four-line `{# #}` comment printed as text in the head and cost the screen-change opt-in. Found by `welcome.mjs`, fixed with `{% comment %}`, and guarded by a test ([footgun](../wiki/footguns/django_comment_is_one_line.md)).
3. **Front-door screens seen signed in** (Join, Claim) empty the `launch` block as they empty `welcome`, so the page behind them is the one that arrives.
4. **If `door.js` failed to load,** the `data-launch` mark would stay on `<html>` and Your groups would arrive again on each visit in that window. Every page script loads together from the head, so this is not expected; `LAUNCH_ARRIVAL=False` is the way out.

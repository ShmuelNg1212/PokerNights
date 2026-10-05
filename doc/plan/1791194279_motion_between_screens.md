# Motion between screens: plan

Status: approved, built and released on 2026-10-05. Date: 2026-10-05, Asia/Manila. Study: [Motion between screens](../study/1791194279_motion_between_screens.md). Stage 3 of the [motion overhaul](1791186717_motion_overhaul.md).

## Outcome

Tapping deeper into the app and tapping back feel different, so you can tell where you went. The name of the group or session you tapped travels to become the next screen's heading. Nothing waits for the movement.

Mode: Operate. Visual authority: the built Rack in DESIGN.md and its Motion system.

## Decisions for the human

Approving the plan accepts the recommendations unless you say otherwise.

1. **A short shift, not a full slide.** Recommended: going deeper, the old screen moves 24px to the left and fades while the new one arrives from 24px to the right; going back is the mirror image. About 220ms. A full edge-to-edge slide is the alternative; it is heavier and clashes with the iPhone's own Back gesture.
2. **The phone's Back gesture and Back button keep today's plain cross-fade.** The iPhone already slides the screen during the gesture; a second directional movement would play twice. On-screen links such as "← Your groups" do get the back direction.
3. **No player chip is carried.** The programme promised "a session title and a player chip". No tap leads from a chip to another screen: a player's details open as a sheet on the same screen. I recommend carrying the **group's name** (Your groups → the group) and the **session's table name** (Sessions list → session → set) instead. If you want a chip to travel, say from where to where.
4. **Tabs do not shift sideways.** Sessions, Stats and Group settings are the same depth; they keep the cross-fade.
5. **Your iPhone needs iOS 18 or later** to show any of this. On an older version screens change at once, as now. Tell me if yours is older; then this stage would show you nothing.

## What you will see

| Tap | Motion |
|---|---|
| A group card on Your groups | The screen shifts deeper. The group's name moves from the card to the heading. |
| A session row in a group | Deeper. The table name moves from the row to the heading. |
| A set on a session | Deeper. The table name stays in the heading and settles into the set's overview. |
| The set log, New session, Set settings, Add players, Manage | Deeper. |
| "← Your groups", "← Session: …", a form's Cancel or its save | Back. A carried name returns to its card or row. |
| A tab of a group; a screen at the same depth | Cross-fade, as today. |
| The phone's Back or Forward | Cross-fade, as today. |
| Log in, Sign up, invites, offline | Cross-fade, as today. |
| An action on the set page (rebuy, count) | As stage 2: no screen movement. |
| The top bar | Stays still on every change. |
| Reduced motion; a browser without the feature; no JavaScript | As today. |

## Implementation

1. **Depth.** `base.html` puts `data-depth` on `<main>` from a template block; each template sets its depth (the study's table). Screens without one get no direction.
2. **`turbo-setup.js`.** On `turbo:before-render` for a screen change (not a morph): read the depth of the screen leaving and of the one arriving, and set `data-go="deeper"`, `"back"` or nothing on `<html>`. A history visit (Turbo's direction is not a tapped link) sets nothing. The attribute is removed when the transition ends.
3. **Carried names.** One name, `title`. The headings of the group, session and set screens carry it. On `turbo:click`, the tapped card's or row's title element gets it for that visit. Going back, the card or row on the arriving screen whose link is the address being left gets it. `turbo-setup.js` guarantees one holder per screen and removes the temporary ones afterwards.
4. **`static/css/app.css`.**
   - `html[data-go=deeper]` and `[data-go=back]`: keyframes for `::view-transition-old(root)` and `::view-transition-new(root)` (24px shift with fade, 220ms, the existing ease curves). Without the attribute: today's 180ms cross-fade.
   - `.site-header { view-transition-name: site-header }` with no animation, so the bar stays still.
   - `::view-transition-group(title)`: 260ms, the ease-out curve; the two photographs of the name fade through each other without stretching.
   - `::view-transition { pointer-events: none }`: a tap during the movement reaches the new screen.
   - All of it inside `prefers-reduced-motion: no-preference`.
5. **Motion tokens.** DESIGN.md gains `screen` (220ms) and `carry` (260ms). No Motion library call runs during a screen change; the study explains why.
6. **Tests first.**
   - Django: each screen renders its depth; the three headings carry the name once; the cards and rows have the hook the script needs.
   - New browser check `screens.mjs` at 390 and 1280px:
     - each row of "What you will see": the direction set during the change, the animation that ran on the old and new screen, and nothing left on `<html>` afterwards;
     - the top bar does not animate;
     - the carried name: exactly one holder before and after, a moving group for it during the change, the same for the way back, and no holder left on a card or row afterwards;
     - a list of several sessions never has two holders (a transition that the browser cancels fails the check);
     - a tap on a link during the movement is followed;
     - every movement ends within 300ms;
     - the phone's Back and Forward: cross-fade only;
     - an action on the set page does not set a direction;
     - reduced motion: no animation, screens still change;
     - 20 screen changes leave no attribute, no temporary name and no script error.
   - Existing checks: `navigate.mjs`, `lifetime.mjs`, `inplace.mjs`, `motion.mjs`, `flow.mjs`, `dock.mjs`.
7. **Verify.** SQLite suite, the build-style run, PostgreSQL before release. Mid-movement captures inspected at both widths.
8. **Sync docs.** DESIGN.md Motion system, wiki features and architecture, browser README, TODO phone checklist.

## Acceptance criteria

- AC1. Each row of "What you will see" passes its browser check.
- AC2. No tap waits: a link tapped during a movement is followed, and every movement ends within 300ms.
- AC3. All existing tests and the listed browser checks pass.
- AC4. **On your phone:** tap Your groups → a group → a session → a set and back with the on-screen links, then with the Back gesture. The direction should tell you where you went, the carried name should read as one thing moving, and nothing should play twice. Only you can judge this.

## Out of scope

- Results, recap, settle-up and closing a session (stage 4).
- A new screen for a player, or any change to where links lead.
- Sheets, toasts and the dock.
- Edge-to-edge slides and swipe gestures of our own.

## Rollback

Revert the stage's commits. No migration and no data change.

## Progress and blockers

2026-10-05: Study and plan complete. The Motion server's docs were read for `animateView`; the plan uses the browser feature it wraps, through Turbo, for the reason in the study. Waiting for approval.

2026-10-05: approved by the human, with four answers: the agent decides how the player chip is carried; the Sessions, Stats and Group settings tabs are to have movement too; the iPhone runs iOS 18 or later; the implementation note is acknowledged. Built on `motion-stage-3`. Tests were written first and seen to fail.

Changes from the plan:

1. **Tabs move** (the human's instruction, replacing decision 4). The content shifts towards the side the chosen tab is on, the marker slides to it, and the back link, heading and tab bar stay still.
2. **Chips are carried** (the agent's decision, replacing decision 3): between a session's results and one of its sets' rows, for a player who has one chip in each list with the same colour and letters, when the chip was on screen. Chips are coloured by joining order within a set and by standing within a session, so in a session of several sets some chips differ and stay put. From the top of a session page the results are usually below the screen, so the chips are seen mostly on the way back from a set, or after scrolling to the results.
3. **The transition no longer goes through Turbo's own.** The implementation note the human acknowledged said it would. Turbo starts its transition before it tells the page what the new screen is, and the browser photographs the old screen at that moment, so nothing could be marked as carried in time. `turbo-setup.js` now pauses Turbo's render, sets the markers, starts the browser's transition itself and resumes the render inside it. This is Turbo's documented way to pause a render. Turbo's `view-transition` meta tag is removed from `base.html`. Motion's `animateView` is still not used.
4. **A tap during a movement is passed on by script.** `pointer-events: none` on the transition layer did not work in Chrome: the tap went to the page and the browser reported nothing under the finger. The script finds the control by its position and clicks it when exactly one control is there. Where two overlap (the host bar over a row), the tap is dropped and has to be repeated.
5. **The name is also carried from a card's "in play" band** on Your groups to the set it opens.
6. **A name is carried only when the words match.** A link that jumps levels (a "To settle" line on Your groups to a session) has no matching name and only shifts.
7. **The depth of forms:** a form opened from a group is 2, the Manage page of a session is 3, forms opened from a set are 4.
8. **`motion.mjs` was hardened.** One run in five stopped under reduced motion when the check reopened a sheet in the same instant it closed it. The check now waits 150ms there. The cause is inferred from the code (the dialog's `close` event is delivered late), not proven; it ran clean three times after the change. A person cannot tap that fast.

Verification:

- `screens.mjs`: 42 of 42 on a fresh temporary database. Every movement lasts 260ms or less; a whole change, from the tap's response to the end of the movement, took up to about 480ms in headless Chrome.
- `lifetime.mjs` 22, `flow.mjs` 52, `dock.mjs` 175, `inplace.mjs` 38, `navigate.mjs` 37 pass. `motion.mjs` 34 in four of five fresh runs before the hardening (change 8).
- Mid-movement captures were inspected at 390px (a tab change with the marker sliding; chips travelling from a session's results to a set).

**AC4 is open: only the human can judge it on a phone.** Not verified: Safari and the installed app on an iPhone (whether a tap during a movement reaches its control there, how the carried name looks when its two sizes differ a lot, and whether the phone's Back gesture plays cleanly with the cross-fade); frame rate on a long page.

2026-10-05 release: the human merged and pushed `main` at `648cca8` (previous production commit `8190e23`). The suite had passed on local PostgreSQL 17 for this code. About two and a half minutes after the merge commit the live site served the new `turbo-setup.js` (byte-for-byte the local file) and the stylesheet with the screen movements, and the login page no longer carried Turbo's `view-transition` meta tag. Not checked on production: any signed-in page, and anything on a real iPhone (AC4).

2026-10-05, the human on the released stage: "the animations have some flickering going on where it shows the previous page for a split second after the animation", and the three tabs "have an awkward animation because the word moves with the outline". AC4 is therefore not met; both are fixed on `fix/screen-flash-and-tabs` under this plan. Not pushed.

1. **The flash of the previous screen.** Cause: the script removed the direction marker when the layers' animations ended, a moment before the browser removed the layers. Without the marker, the old screen's layer fell back to the default fade and played it again. Reproduced in Chrome by a new check (the marker was gone before the browser reported the change finished), though Chrome does not show the flash. Fix: the marker and the temporary names are removed only on the transition's own `finished`. That this was the flash seen on the iPhone is inferred, not confirmed.
2. **The word moving with the marker.** The whole current tab was one layer, word included. Now the marker is its own element under the word: in a tab change the marker slides, the words stay in place and change colour, and the tab bar stays still. A mid-movement capture was inspected.

Verification: `screens.mjs` 46 of 46 (four new checks, which failed first). `lifetime.mjs` 22, `motion.mjs` 34, `flow.mjs` 52, `inplace.mjs` 38, `navigate.mjs` 37. 649 tests on SQLite and in the build-style run; PostgreSQL not rerun (a template, a script and CSS). `remaining.mjs` stops on "missing route preset" after 60 checks, and does the same on the release before stage 3, so it is an older stale script; it is added to the list in the browser README.

2026-10-05 release of the two fixes: the human merged and pushed `main` at `fc321da` (previous production commit `648cca8`). About two and a half minutes later the live site served the new `turbo-setup.js` (byte-for-byte the local file) and the stylesheet with the tab marker. Not checked on production: any signed-in page, and whether the flash is gone on a real iPhone (AC4).

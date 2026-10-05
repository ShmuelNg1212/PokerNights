# Motion between screens: plan

Status: awaiting approval. Date: 2026-10-05, Asia/Manila. Study: [Motion between screens](../study/1791194279_motion_between_screens.md). Stage 3 of the [motion overhaul](1791186717_motion_overhaul.md).

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

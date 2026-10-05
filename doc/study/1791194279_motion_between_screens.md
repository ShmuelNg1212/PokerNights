# Motion between screens: study

Date: 2026-10-05, Asia/Manila. Stage 3 of the [motion overhaul](../plan/1791186717_motion_overhaul.md). The programme's line for this stage: "Deeper and back have directions; a session title and a player chip carry across screens."

## What happens today

- A tapped link changes the screen without loading a page (Turbo 8.0.23, [screen changes without a reload](../plan/1791181102_screen_changes_without_reload.md)).
- Every page carries `<meta name="view-transition" content="same-origin">`. Where the browser has the View Transition API, Turbo wraps each screen change in it, and the stylesheet gives the whole page a 180ms cross-fade. That is the only motion between screens. It is the same in every direction.
- Turbo marks the kind of visit on `<html>` (`data-turbo-visit-direction`: `forward` for a tapped link, `back` or `forward` for the phone's Back and Forward). It does not know that "← Your groups" goes up and a session row goes down; both are tapped links.
- Under reduced motion the cross-fade is off.

## The screens and their depth

| Depth | Screen |
|---|---|
| 0 | Your groups |
| 1 | A group (Sessions, Stats and Group settings are tabs at the same depth) |
| 2 | A session |
| 3 | A set |
| 4 | The set log; forms opened from a screen (New session, Set settings, Add players, Manage) are one deeper than the screen they open from |
| none | Log in, Sign up, invites, the offline page |

## What repeats from one screen to the next

- **The group's name:** the card on Your groups, then the heading of the group.
- **The session's table name:** the row in a group's Sessions list, then the heading of the session, then the heading of each of its sets.
- **A player's chip** appears on a set's rows, the count-up rows, the results and the Stats tab. No tap leads from one chip to a screen about that player: a player's details open as a sheet on the same screen. A chip therefore has no journey between screens today.

## What the tools can do

- **The View Transition API** photographs the old screen, lets the page change, and animates from the photograph to the new screen. Each named element is photographed separately and moves from its old place and size to its new one. The page beneath is already the new page.
- **Motion's `animateView`** (read through the Motion server's docs) is a wrapper around the same browser API. It adds automatic naming, springs and queuing. It expects to run the page change itself; here Turbo runs it. Using `animateView` would mean taking the screen change away from Turbo's own handling, which stage 4 of the app-like work proved with 37 checks.
- **Plain CSS on Turbo's existing transition** can do the directions and the carried elements: the page's two photographs get different animations according to an attribute on `<html>`, and an element with a `view-transition-name` on both screens is carried.

## Constraints found

1. **Two elements with the same name on one screen cancel the whole transition.** A list of sessions cannot all carry the title's name. Only the tapped row may have it, and on the way back only the row for the session just left.
2. **The phone's Back gesture already animates.** On an iPhone, a swipe from the edge slides the old screen away by itself. A second animation after it would play twice.
3. **While a transition runs, the photographs sit above the page and take the taps** unless told otherwise. The rule is that nothing waits for an animation.
4. **Browser support.** Safari has the API from version 18 (iOS 18). An older iPhone changes screens at once, as it does now.
5. **An in-place update** of a set page (a rebuy, a count) is not a screen change and must stay as stage 2 left it.
6. **The top bar** is the same on every screen and should not slide with the page.
7. **Text that changes size** between screens (a row title becoming a heading) is carried as two photographs that fade into each other while moving. It reads as a move when the two are similar in size, and as a smear when they are very different.

## Options

**A. Directions and carried names in CSS, on Turbo's own transition.** A depth on each screen; `turbo-setup.js` compares the two depths before the change and sets `deeper`, `back` or `same` on `<html>`; the stylesheet does the rest. Durations and curves come from the motion tokens. No new library code runs during a screen change.

**B. Hand the screen change to Motion's `animateView`.** Springs on carried elements and its queuing. Replaces Turbo's transition handling; more to break.

**C. Slide whole screens edge to edge,** as native apps do. Costly for long pages, and it looks wrong after the iPhone's own Back gesture.

## Recommendation

A. Directions are a short shift with a fade (the old screen moves 24px away and fades, the new one arrives from 24px on the other side), not an edge-to-edge slide. The group's name and the session's table name are carried. The player chip is left out, because no tap carries a chip to another screen (a decision for the human). The phone's Back and Forward keep the plain cross-fade.

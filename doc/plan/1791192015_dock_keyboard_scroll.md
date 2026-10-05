# Host dock while scrolling with the iPhone keyboard open: plan

Status: awaiting approval. Date: 2026-10-05, Asia/Manila. Study: [Host dock while scrolling with the iPhone keyboard open](../study/1791191973_dock_keyboard_scroll.md).

## Outcome

On an iPhone, in the home screen app and in Safari, while the keyboard is open on a set page: the host bar stays the one-line bar, stays attached to the top of the keyboard while you scroll, and the page scrolls freely under your finger. Count-up is the case checked most closely.

## Decisions for the human

Approving the plan accepts the recommendations unless you say otherwise.

1. **What you see.** I could not reproduce this without an iPhone. The study found three faults in the script that match "buggy while scrolling": the menu opening in full or flickering between bar and full, the page jumping back to the field you are typing in, and the bar lagging behind and then snapping. If what you see is something else, say so before I build.
2. **A readout for your phone.** Recommended: a set page opened with `?kb=1` at the end of its address shows a small label with the numbers the script reads. Hosts only; nobody sees it otherwise. This is the second fix made without an iPhone; if it is still wrong, a screenshot of that label tells me why.
3. **If the bar still trembles while the page moves** after this fix, the fallback is to fade the bar out during the movement and back in when it rests. Not built now.

## Behaviour

- **Keyboard open, scrolling.** The dock is the bar for as long as the keyboard is open, wherever the page is scrolled. The page's length does not change during the scroll. Nothing scrolls the page except your finger.
- **A field gains focus under the bar,** or the keyboard opens over it: the page moves once so the field is clear of the bar.
- **Typing in a field inside the dock.** As today: the dock stays expanded above the keyboard.
- **Keyboard closed, desktop, Android, pinch-zoomed page, no `visualViewport`, no JavaScript.** As today.

## Implementation

1. **`static/js/dock.js`, `keyboard()`.**
   - Keyboard height = the dock's unraised bottom edge (the layout frame's height) − the visible frame's height. Under 80px, or zoomed, or the dock not fixed: 0. This drives `kb-open`, `kb-bar` and a new `--kb-h` used for the page's bottom padding and the fields' scroll margin.
   - Dock offset = layout frame height − `offsetTop` − visible frame height, never below 0. This drives `--kb`, which only positions the dock.
   - The "scroll the field clear" step runs only after `focusin` and when the keyboard height goes from 0 to above 0.
   - While the keyboard is open, a per-frame loop reads the visible frame and updates `--kb` when it changed. It stops when the keyboard closes and when the page is left.
   - State changes (`sync()`, cancelling the slide) happen only when the keyboard height or the bar state changes, not when the offset does.
2. **`static/css/app.css`.** The two padding rules and the scroll margin use `--kb-h`. The dock's `bottom` keeps `--kb`.
3. **Readout.** With `?kb=1`, `dock.js` adds a fixed label at the top of the screen: layout height, visible height, `offsetTop`, keyboard height, dock offset, the dock's reported bottom edge, and whether it runs as the installed app. No server change.
4. **Tests first,** in `web/tests/browser/dock.mjs`: the stand-in keyboard gains a movable `offsetTop`.
   - At `offsetTop` 0, 150 and 336 with a 336px keyboard, dock left expanded, count field focused: the dock is the bar each time; `kb-open` stays; the page's height is the same each time; the bar's bottom edge is at the bottom of the visible frame each time.
   - Keyboard opening with `offsetTop` already at 336 (a low field): the dock is the bar, not the full menu.
   - A visible-frame scroll event with the focused field under the bar leaves the page's scroll position alone; a new focus on a covered field moves it clear once.
   - The frame loop: moving `offsetTop` without any event moves the dock within two frames; after the keyboard closes and after a screen change no loop is running.
   - `?kb=1` shows the label; without it there is none.
   - The 163 existing checks pass unchanged.
5. **Verify.** SQLite suite and the build-style run. `dock.mjs` on a fresh temporary database; `inplace.mjs`, `navigate.mjs`, `lifetime.mjs`, `motion.mjs` and `flow.mjs`, which share the page. PostgreSQL is not rerun: a script and CSS change.
6. **Sync docs.** The footgun note (state and position are different numbers; the stand-in must move), DESIGN.md, wiki features, browser README, TODO phone check.

## Acceptance criteria

- AC1. Every check in step 4 passes.
- AC2. With no keyboard detected the dock is as today (the existing checks pass unchanged).
- AC3. **On your iPhone, in the home screen app, after release:** open a set that is counting up with the host menu left open. Tap the last count field. The menu is the one-line bar above the keyboard. Scroll up and down with the keyboard open: the bar stays a bar on the keyboard, the page follows your finger and does not jump back. Only you can check this.
- AC4. If AC3 fails, a screenshot of the page with `?kb=1` is enough for the next step.

## Out of scope

- Bottom sheets and toasts above the keyboard.
- What the dock contains; the saved collapse choice.
- Changing how the set page scrolls (option C in the study).

## Rollback

Revert the commit. No migration and no data change.

## Progress and blockers

2026-10-05: Study and plan complete. Not reproduced: the agent has no iPhone. One assumption is unproven (the study, "One assumption that is not proven"); the readout exists to settle it. Waiting for approval.

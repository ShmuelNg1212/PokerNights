# Host dock behind the iPhone keyboard: plan

Status: approved 2026-10-05, executed 2026-10-05. Date: 2026-10-05, Asia/Manila. Study: [Host dock behind the iPhone keyboard](../study/1791184941_dock_behind_keyboard.md).

## Outcome

On an iPhone, while the host types a count, the dock sits directly above the keyboard as its one-line bar and shows the live count verdict. When the keyboard closes, the dock returns to the bottom of the screen in the state the host left it.

## Decisions for the human

Approving the plan accepts the recommendations unless you say otherwise.

1. **What the dock shows while the keyboard is up.** Recommended: the collapsed bar, even if you had the dock expanded; it expands again when the keyboard closes. Your saved choice is not changed. The alternative, lifting the expanded dock whole, would cover the field you are typing in.
2. **Scope.** Recommended: every set state that has the dock (draft, open, in play, counting up), since the same fault applies wherever you type on the set page. Count-up is the case that is checked most closely.

## Behaviour

- **Keyboard up, typing in the page.** The dock is the collapsed bar, attached to the top of the keyboard, without the home-indicator padding. Tapping the bar does nothing harmful: it expands the dock within the visible area, as below.
- **Keyboard up, typing in a field inside the dock** (for example "Or add one player"). The dock stays expanded, sits above the keyboard, and is no taller than the visible area; it scrolls inside if needed.
- **Keyboard closed.** As today.
- **Page zoomed by pinch, desktop widths, Android, no JavaScript, browsers without `visualViewport`.** As today.
- **Motion.** The dock moves with the keyboard without an animation of its own.

## Implementation

1. **`static/js/dock.js`.** On start, if `window.visualViewport` exists, listen to its `resize` and `scroll` events and to `focusin`/`focusout`. Compute `covered = layout viewport height − (visualViewport.offsetTop + visualViewport.height)`, rounded, never below 0, and treated as 0 when `visualViewport.scale` is not 1 or the result is under 80px (a toolbar, not a keyboard). Write it to `--kb` on `<html>` and set the class `kb-open` when it is above 0. Add `kb-in-dock` when the focused element is inside the dock. Remove the listeners, the variable and the classes on stop. Re-measure `--dock-h` after each change.
2. **`static/css/app.css`**, in the dock block, below 900px only:
   - `.kb-open .table-layout .host-controls { bottom: var(--kb); padding-bottom: 6px; max-height: calc(100dvh − var(--kb) − 16px); }`
   - `.kb-open:not(.kb-in-dock)` hides the dock's content except the toggle and shows the status line, reusing the collapsed rules.
   - `.kb-open .host-controls .next-action` gets the same `bottom` offset.
3. **Tests first.** New section in `web/tests/browser/dock.mjs`, at 390px, replacing `visualViewport` with a stand-in that reports a 336px keyboard:
   - in count-up with the dock expanded and a count field focused: the dock's bottom edge is at the top of the keyboard, it is the one-line bar, the verdict is visible and changes as a count is typed, and the focused field is not covered;
   - the same with the dock already collapsed;
   - focus inside the dock: expanded, above the keyboard, within the visible area;
   - keyboard closed: position, state and the saved choice are as before;
   - a zoomed viewport and a 50px change do not move the dock;
   - after moving to another screen and back, one set of listeners is active;
   - no `visualViewport`: no error, dock as today.
4. **Verify.** SQLite suite and the build-style run. `dock.mjs` on a fresh temporary database, plus `inplace.mjs`, `navigate.mjs` and `lifetime.mjs`, which exercise the same scripts. PostgreSQL is not rerun: only a script and CSS change.
5. **Sync docs.** DESIGN.md addendum, wiki features, a footgun note "fixed elements sit under the iOS keyboard", TODO with the phone check below.

## Acceptance criteria

- AC1. With the stand-in keyboard, every check in step 3 passes.
- AC2. With no keyboard detected, the dock is pixel-for-pixel as today in all four states (the existing 145 `dock.mjs` checks pass unchanged).
- AC3. **On your iPhone, after release:** in count-up, tap a count field. The bar with the verdict is visible directly above the keyboard and updates as you type; closing the keyboard puts the dock back. This is the only check that proves the fix, and only you can run it.

## Out of scope

- The bottom sheets (buy-in, cash-out) and the toasts. If one of them also hides behind the keyboard, say so and it gets the same treatment.
- Any change to what the dock contains or to the saved collapse choice.

## Rollback

Revert the commit. No migration and no data change.

## Progress and blockers

2026-10-05: Study and plan complete. The cause is inferred from the code and documented iOS behaviour; it was not reproduced, because the agent has no iPhone. Waiting for approval.

2026-10-05: The human approved with “approved”, and added a requirement: the one-line bar must show the live chip count as it is typed, to check for discrepancies.

2026-10-05 execution on `fix/dock-behind-keyboard`. Tests were written first and seen to fail.

Changes from the plan:

1. **The bar shows the running total** (the added requirement). In count-up the collapsed bar reads “₱1,900 of ₱2,000 bought in” above the verdict, in place of the “Host controls” label, and `counts.js` updates it on each keystroke. This applies to the collapsed bar with or without the keyboard. The bar may be up to 76px at 320px (was 72px).
2. **A tap on the bar while the keyboard is up puts the keyboard away.** The plan had it expand the dock in the visible area; that would have needed a second, unsaved expanded state.
3. **The covered height is measured from the dock's own bottom edge**, not from the layout viewport height, so it does not depend on which height an iPhone reports.
4. **The page reserves the keyboard height too**, and a focused field under the bar is scrolled clear. Found in the first browser run: the last field could not scroll above the raised bar.
5. **`.next-action` needed no change**; it is not fixed below 900px on the set page.

2026-10-05 verification:

- 639 tests pass on SQLite (ten PostgreSQL-only skips), and the same in the build-style run. PostgreSQL was not rerun: a template, a script and CSS changed.
- `dock.mjs`: 163 of 163 on a fresh temporary database (145 earlier checks plus 18 for the keyboard and the running total). One earlier limit changed: the count-up bar at 320px, see change 1.
- `inplace.mjs` 38, `navigate.mjs` 37 and `lifetime.mjs` 22 pass on fresh databases.

AC1 and AC2 are met, AC2 with the one changed limit. **AC3 is not met yet: it needs the human's iPhone after release.** The keyboard in the checks is a stand-in; nothing here proves that an iPhone reports the values assumed. If the dock still hides, the change does nothing harmful: with no keyboard detected the dock is as before.

2026-10-05 release: the human said “push”. All 639 tests passed on local PostgreSQL 17 first (started for the run, stopped after). Pushed `main` at `62e869c` (previous production commit `8d3184f`). About two minutes later https://pokernights-five.vercel.app served the new stylesheet (with the `kb-open` rules) and the new `dock.js`. Not checked on production: any signed-in page, and the keyboard on a real iPhone (AC3).

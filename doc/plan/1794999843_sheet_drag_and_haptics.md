# Plan: drag a sheet down to close it, and haptics

Study: [1794999762_sheet_drag_and_haptics.md](../study/1794999762_sheet_drag_and_haptics.md). Mode: design. Skills: `animate`, `mobile-native` (execute); `review-animations`, `break-ui`, `code-review` (rendezvous).

Branch: `feat/sheet-drag-haptics`, from `main`. No code-writing subagents: tasks 4 and 5 both edit `sheets.js`, and tasks 2 and 3 both edit `haptics.js`.

## OPEN QUESTIONS

Answered 2026-11-18: yes to all three. The Vibration switch is on by default. Plan approved.

1. **A Vibration switch for each phone.** Recommendation: yes. Put a "Vibration" switch in the account menu. It is on by default and is kept in this browser only. Reason: some players will not want a buzz at the table. The iPhone already obeys its System Haptics setting; Android does not always. If no, delete task 3.
2. **A tick on each number key.** Recommendation: yes. The iPhone keyboard ticks on each key, and the app's own keys replace it. It is the moment most likely to work on the iPhone, because it is a direct tap. If no, delete that line from task 2.
3. **A grab handle on the sheet.** Recommendation: yes. A 36 × 4 px Bone Dim bar, centred, 8 px above the title, shown only below 900 px. It tells a person that the sheet can be dragged. It adds 12 px to the height of the head. If no, the drag still works without a visible handle.

## Outcome

- Below 900 px, a person can drag any sheet down with a finger to close it, as in an iOS app.
- The phone gives a short vibration at five moments. Where the phone cannot, nothing changes.

## Non-goals

- No haptic for other people's changes (their buy-ins, joins, cash-outs). That would buzz all night.
- No haptic on every button.
- No drag for the host dock. That is a separate change.
- No drag with a mouse, and no drag from 900 px, where the sheet is centred.
- No sound.

## Design decisions (from the study)

**Drag.**

| Item | Decision |
|---|---|
| Where a drag starts | The sheet head (handle, title row) at any scroll position. The body only when the sheet is scrolled to its top and the first 8 px of movement is down and more vertical than horizontal. (Changed at rendezvous: 6 px, and nothing is cancelled before then.) |
| Where a drag never starts | A number key, an input, a select, a textarea, a range, a sideways-scrolling row (`.pills`), a text selection. |
| Input | Touch events only, below 900 px. |
| While dragging | The sheet follows the finger 1:1 down. Up, it resists: 0.2 of the movement, 12 px at most. The backdrop fades with the distance, where the browser supports it. The field that has focus loses it, so a native keyboard goes down. |
| Release: close | When the distance is at least 30 % of the sheet's height, or 160 px, whichever is less. Or when the finger moves down at 0.6 px/ms or more, with at least 16 px of distance. |
| Release: close motion | New preset `fling`: 180 ms, ease `[0.2, 0, 0, 1]`, from where the sheet is to its height. The sheet keeps its speed and does not start slowly again. Then the usual close: content back, focus back to the opener. |
| Release: stay | The `sheet` spring from where the sheet is back to 0. |
| A touch during a movement | A touch during the rise, a snap-back or a fling takes the sheet from where it is. |
| During a send | No drag while a form in the sheet is sent (`data-sent`, or a button with `aria-busy`). |
| Reduced motion, no Motion file | The sheet still follows the finger. On release it is at once closed or back, with no movement. |
| Page left during a drag | The page's stop function ends the drag and removes its listeners. |

**Haptics.** `static/js/haptics.js`, loaded after `motion.js`. `window.pokerHaptics.play(kind)`.

| Kind | Android (`navigator.vibrate`) | iPhone (switch tick) |
|---|---|---|
| `tick` | 8 ms | one tick |
| `done` | `[10, 50, 14]` | one tick |
| `refused` | `[24, 40, 24]` | two ticks, 70 ms apart |

- Not more than one play in 60 ms. Nothing in a hidden tab. Nothing when the Vibration switch is off.
- The iPhone helper is a label and a switch input. It goes in the open dialog when there is one, else at the end of `<body>`. It is never inside a form. It is hidden from assistive technology and cannot take focus. Focus stays where it was.
- Reduced motion does not turn haptics off. Haptics are not movement.

**Moments.**

| Moment | Kind | Where | Likely on iPhone |
|---|---|---|---|
| A number key pressed (open question 2) | `tick` | `numpad.js`, `pointerdown` | Yes: direct tap |
| A sheet drag passes the close distance (once per drag, going down) | `tick` | `sheets.js` | Unknown: touch movement |
| Your own write is accepted | `done` | `motion.js`, `answered(false)` | Unknown: after a server answer |
| Your own write is refused | `refused` | `motion.js`, `answered(true)` and `nudge()` | Unknown: after a server answer |
| The books balance (once per set per browser) | `done` | `changes.js`, beside the `balanced:` key | Unknown: after a poll |
| The seat draw shows the dealer | `done` | `seats.js`, at the dealer's crown | Unknown: animation |

## Tasks

- [x] **1. Haptics helper.** `tests: alongside`
  - Add `static/js/haptics.js` with `play(kind)`, the patterns, the rate limit, the hidden-tab rule and the iPhone switch helper. Add it to the base template after `motion.js`. Add `"haptics"` after `"motion"` in `ScriptsLoadOnceTests.NAMES`.
  - Acceptance: with `navigator.vibrate` stubbed, `play("done")` calls it once with `[10, 50, 14]`. Two plays 30 ms apart give one call. In a hidden tab, no call. Without `navigator.vibrate` and with switch support, a play clicks the helper's label once, and focus and every form's values do not change. With neither, `play` does nothing and throws nothing.
  - Done when: the Django suite passes on SQLite and the probe checks in task 6 for the helper pass.
  - Commit: `feat: add a haptics helper and a Vibration switch` (tasks 1 and 3 together: the switch's code is in `haptics.js`).

- [x] **2. Haptic moments.** `tests: alongside`
  - Call `pokerHaptics.play` at the moments in the table: the number keys (if open question 2 is yes), accepted and refused writes, the books balance, the dealer.
  - Acceptance: each moment calls `play` once with its kind. A poll that changes nothing calls nothing. Another person's buy-in calls nothing. A reload of a balanced set calls nothing.
  - Done when: the probe checks in task 6 for the moments pass.
  - Commit: `feat: vibrate at a write, a number key, the books balancing and the dealer`.

- [x] **3. Vibration switch** (only if open question 1 is yes). `tests: alongside`
  - Add a "Vibration" switch to the account menu, shown only where the phone has a mechanism. Keep the choice in `localStorage` (`rack-haptics`). Storage that fails means on.
  - Acceptance: off stops every play on this browser. On again restores them. The switch has a 48 px target and a visible label. Another browser is not changed.
  - Done when: the probe checks pass, and the account menu passes its existing browser check.
  - Commit: with task 1.

- [x] **4. Drag a sheet down to close it.** `tests: alongside`
  - CSS: the grab handle (open question 3), `overscroll-behavior: contain` on `.sheet`, `touch-action: none` on the head below 900 px, and backdrop opacity from a `--sheet-drag` property.
  - `sheets.js`: the drag as in the decisions table. Add the `fling` preset to `motion.js`. Route the close through the existing `close()` path, so content, draft and focus behave as today.
  - Acceptance: every row of the drag table, checked in task 6. Close, Escape, the backdrop and an accepted write still close the sheet as before. The first frame of an opening still has no flash.
  - Done when: `motion.mjs` and `mobile_motion.mjs` give the same results as their recorded baselines, and the new drag checks pass in Chromium and WebKit.
  - Commit: `feat: drag a sheet down to close it`.

- [x] **5. Tick at the close distance.** `tests: alongside`
  - In the drag, call `play("tick")` once when the distance first passes the close distance going down. No tick when it comes back up and goes down again in the same drag.
  - Done when: the probe check passes.
  - Commit: in task 4's commit (it is three lines).

- [x] **6. Browser checks.** `tests: alongside`
  - Built: `sheet_drag.mjs` (Chromium, 35 checks), `sheet_drag_webkit.mjs` (WebKit, 15 checks), `haptics.mjs` (Chromium, 31 checks) and `seed_sheet_drag.py`. WebKit has no `Touch` constructor and Playwright no touch move, so the WebKit drags are synthetic events that scroll nothing; the scroll case is covered in Chromium with real touch input.
  - Add `web/tests/browser/sheet_drag.mjs` and `web/tests/browser/haptics.mjs`, with a seed if the existing seeds do not supply a sheet with long content, a sheet with number keys and the recap. Add their run steps to `web/tests/browser/README.md`.
  - The drag probe uses Chromium touch input through CDP and WebKit touch emulation, at 320, 390 and 1280 px. It samples each frame from the first touch to rest.
  - Required checks: a drag from the head closes; a short drag goes back; a flick closes; a drag from a scrolled body scrolls and does not drag; a drag on a number key types and does not drag; no drag at 1280 px or with a mouse; no drag during a send; a touch during the rise; reduced motion; a blocked Motion file; the recap sheet; focus back to the opener; only `transform` and `opacity` animate; nothing inline left at rest; a page change during a drag leaves no listener.
  - The haptics probe stubs `navigator.vibrate`, removes it for the iPhone path, and records plays. It checks each moment, the non-moments, the rate limit, focus, form values and the switch (task 3).
  - Done when: both probes pass in full. Record the count.
  - Commit: `test: browser checks for sheet drag and haptics`.

- [x] **7. Docs.**
  - DESIGN.md: a "Sheet drag and haptics" addendum, the `fling` preset in the presets table, and the grab handle. `doc/wiki/features.md`: both features. A footgun file for each surprise found during the work. TODO.md: the phone checks below.
  - Done when: the wiki matches the code.
  - Commit: `docs: record sheet drag and haptics`.

## Completion criterion

All tasks are ticked. The Django suite passes on SQLite and PostgreSQL. Both new probes pass. `motion.mjs` and `mobile_motion.mjs` match their baselines. The branch is verified and not merged.

## Rendezvous checks (2026-11-18)

Two fix rounds were allowed; one was used for code, and one small layout fix followed the `break-ui` pass.

- [x] Django suite, SQLite with `--parallel`: 1784 tests, OK (23 skipped). Run after the last code change.
- [x] Django suite, PostgreSQL: 1784 tests, OK. Run after the review fixes; the later change was CSS only and the SQLite suite ran after it.
- [x] `sheet_drag.mjs`, Chromium with real touch input: 39/39 on fresh data.
- [x] `sheet_drag_webkit.mjs`, WebKit: 15/15. Its drags are synthetic events that scroll nothing.
- [x] `haptics.mjs`: 38/38 on fresh data (Android, iPhone, neither, laptop).
- [x] `motion.mjs`: 40/40 on a clean copy of its seed, after the review fixes.
- [x] `mobile_motion.mjs`: 58/60 on this branch, 56/60 on `main` with the same seed and the same Playwright build. Both fail the two WebKit disclosure-fallback checks; `main` also failed the two Chromium view-transition error checks. No new failure. The recorded baseline (2026-11-01) was 58/60 with different failures, before a WebKit update.
- [x] `code-review` (medium) on `54f03a6..HEAD`: 9 findings, 7 fixed, 2 kept:
  - Fixed: "done" vibrated on every Turbo render, so on a screen change and on the session page's redraw for another player's change. This broke the plan's first non-goal. Now only a form this phone sent vibrates ([footgun](../wiki/footguns/inplace_updated_fires_on_every_render.md)).
  - Fixed: the books vibrated on the first view of a set balanced long ago. Now only in a live update.
  - Fixed: the Vibration switch showed on a laptop. Now haptics need a coarse pointer.
  - Fixed: a blocking `touchmove` listener for the sheet's whole life, and a cancelled first move at the top ([footgun](../wiki/footguns/blocking_touch_listener_waits_scroll.md)).
  - Fixed: an upward flick after a long drag still closed. Fixed: the click suppression could drop the iPhone's haptic click and a real tap after a snap-back, and did not stop the backdrop listener. Fixed: the stylesheet's own entry (without Motion) held the sheet against the finger. Fixed: a layout read on each move.
  - Kept: the `window.pokerHaptics` guards in four files. They keep each file safe when `haptics.js` is blocked.
  - Kept (by design): the dealer haptic plays on every phone that watches the draw, as the draw itself does.
- [x] Each new check could fail for its reason. Run against the code before the fixes, "a screen change: no vibration" and "the session page's own redraw: no vibration" failed with `[[10,50,14]]`. "A flick back up after a long drag keeps the sheet" and "a blocking touchmove listener only at the top" failed. "A tap on Close just after a drag" failed in one of two runs. "A jitter then a swipe up scrolls" passed against both: Chromium scrolls after a cancelled first move, so only the phone check can show that case.
- [x] `break-ui` pass, by hand (`review-animations` is not installed; the frames and screenshots were read instead): at 320 × 568 the grab handle made the buy-in sheet scroll by 7 px (552 against 545). The handle moved into the top padding; the sheet is 540 px again, as on `main`. The account menu with the Vibration row was read at 390 px.
- [ ] Not checked here: a physical iPhone. Whether the switch tick plays after a server answer or a poll, and the iPhone's own scroll after a cancelled first move, wait for the phone check.

## Phone checks for TODO.md (after release)

- In the installed app: drag the buy-in sheet down from its title. It closes and follows your finger. A short drag goes back.
- Scroll the recap sheet down, then drag down from the middle. It scrolls up first, then drags only at the top.
- Press number keys. Each press ticks (iPhone with System Haptics on).
- Drag a sheet past half: does it tick once?
- Record a buy-in. Does the phone vibrate when it is accepted? (Unknown on the iPhone.)
- Type an amount the app refuses. Does the phone vibrate twice?
- Let the books balance at count-up. Does it vibrate once, and not on a reload?
- Run a seat draw. Does it vibrate when the dealer is shown?
- Switch Vibration off in the account menu (if built). Nothing vibrates.

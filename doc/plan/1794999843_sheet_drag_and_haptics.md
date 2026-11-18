# Plan: drag a sheet down to close it, and haptics

Study: [1794999762_sheet_drag_and_haptics.md](../study/1794999762_sheet_drag_and_haptics.md). Mode: design. Skills: `animate`, `mobile-native` (execute); `review-animations`, `break-ui`, `code-review` (rendezvous).

Branch: `feat/sheet-drag-haptics`, from `main`. No code-writing subagents: tasks 4 and 5 both edit `sheets.js`, and tasks 2 and 3 both edit `haptics.js`.

## OPEN QUESTIONS

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
| Where a drag starts | The sheet head (handle, title row) at any scroll position. The body only when the sheet is scrolled to its top and the first 8 px of movement is down and more vertical than horizontal. |
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

- [ ] **1. Haptics helper.** `tests: alongside`
  - Add `static/js/haptics.js` with `play(kind)`, the patterns, the rate limit, the hidden-tab rule and the iPhone switch helper. Add it to the base template after `motion.js`. Add `"haptics"` after `"motion"` in `ScriptsLoadOnceTests.NAMES`.
  - Acceptance: with `navigator.vibrate` stubbed, `play("done")` calls it once with `[10, 50, 14]`. Two plays 30 ms apart give one call. In a hidden tab, no call. Without `navigator.vibrate` and with switch support, a play clicks the helper's label once, and focus and every form's values do not change. With neither, `play` does nothing and throws nothing.
  - Done when: the Django suite passes on SQLite and the probe checks in task 6 for the helper pass.
  - Commit: `feat: add a haptics helper for short vibrations`.

- [ ] **2. Haptic moments.** `tests: alongside`
  - Call `pokerHaptics.play` at the moments in the table: the number keys (if open question 2 is yes), accepted and refused writes, the books balance, the dealer.
  - Acceptance: each moment calls `play` once with its kind. A poll that changes nothing calls nothing. Another person's buy-in calls nothing. A reload of a balanced set calls nothing.
  - Done when: the probe checks in task 6 for the moments pass.
  - Commit: `feat: vibrate at a write, the books balancing and the dealer`.

- [ ] **3. Vibration switch** (only if open question 1 is yes). `tests: alongside`
  - Add a "Vibration" switch to the account menu, shown only where the phone has a mechanism. Keep the choice in `localStorage` (`rack-haptics`). Storage that fails means on.
  - Acceptance: off stops every play on this browser. On again restores them. The switch has a 48 px target and a visible label. Another browser is not changed.
  - Done when: the probe checks pass, and the account menu passes its existing browser check.
  - Commit: `feat: let each phone switch vibration off`.

- [ ] **4. Drag a sheet down to close it.** `tests: alongside`
  - CSS: the grab handle (open question 3), `overscroll-behavior: contain` on `.sheet`, `touch-action: none` on the head below 900 px, and backdrop opacity from a `--sheet-drag` property.
  - `sheets.js`: the drag as in the decisions table. Add the `fling` preset to `motion.js`. Route the close through the existing `close()` path, so content, draft and focus behave as today.
  - Acceptance: every row of the drag table, checked in task 6. Close, Escape, the backdrop and an accepted write still close the sheet as before. The first frame of an opening still has no flash.
  - Done when: `motion.mjs` and `mobile_motion.mjs` give the same results as their recorded baselines, and the new drag checks pass in Chromium and WebKit.
  - Commit: `feat: drag a sheet down to close it`.

- [ ] **5. Tick at the close distance.** `tests: alongside`
  - In the drag, call `play("tick")` once when the distance first passes the close distance going down. No tick when it comes back up and goes down again in the same drag.
  - Done when: the probe check passes.
  - Commit: in task 4's commit if it is small, else `feat: tick when a sheet drag will close it`.

- [ ] **6. Browser checks.** `tests: alongside`
  - Add `web/tests/browser/sheet_drag.mjs` and `web/tests/browser/haptics.mjs`, with a seed if the existing seeds do not supply a sheet with long content, a sheet with number keys and the recap. Add their run steps to `web/tests/browser/README.md`.
  - The drag probe uses Chromium touch input through CDP and WebKit touch emulation, at 320, 390 and 1280 px. It samples each frame from the first touch to rest.
  - Required checks: a drag from the head closes; a short drag goes back; a flick closes; a drag from a scrolled body scrolls and does not drag; a drag on a number key types and does not drag; no drag at 1280 px or with a mouse; no drag during a send; a touch during the rise; reduced motion; a blocked Motion file; the recap sheet; focus back to the opener; only `transform` and `opacity` animate; nothing inline left at rest; a page change during a drag leaves no listener.
  - The haptics probe stubs `navigator.vibrate`, removes it for the iPhone path, and records plays. It checks each moment, the non-moments, the rate limit, focus, form values and the switch (task 3).
  - Done when: both probes pass in full. Record the count.
  - Commit: `test: browser checks for sheet drag and haptics`.

- [ ] **7. Docs.**
  - DESIGN.md: a "Sheet drag and haptics" addendum, the `fling` preset in the presets table, and the grab handle. `doc/wiki/features.md`: both features. A footgun file for each surprise found during the work. TODO.md: the phone checks below.
  - Done when: the wiki matches the code.
  - Commit: `docs: record sheet drag and haptics`.

## Completion criterion

All tasks are ticked. The Django suite passes on SQLite and PostgreSQL. Both new probes pass. `motion.mjs` and `mobile_motion.mjs` match their baselines. The branch is verified and not merged.

## Rendezvous checks (to fill in)

- [ ] Django suite, SQLite with `--parallel`.
- [ ] Django suite, PostgreSQL.
- [ ] `sheet_drag.mjs`, Chromium and WebKit.
- [ ] `haptics.mjs`.
- [ ] `motion.mjs` and `mobile_motion.mjs` against their baselines.
- [ ] `review-animations` on the drag.
- [ ] `break-ui`: the recap sheet with twelve players, a sheet at 320 × 568 with the keyboard up, a drag that starts during the opening rise.
- [ ] `code-review` on the branch.

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

# Plan: table moments

Study: [1795006697_table_moments.md](../study/1795006697_table_moments.md). Mode: design. Skills: `animate`, `mobile-native`, `tdd` (execute); `review-animations`, `break-ui`, `code-review` (rendezvous).

Branch: `feat/table-moments`, from `build/parallel-tests` (unreleased). No code-writing subagents: both tasks edit `static/css/app.css`.

## OPEN QUESTIONS

1. **Blind levels become a stakes change.** spec.md excludes a blind timer ("Cash games only"). The list item "blind levels going up" therefore becomes: when a host changes the stakes during a set, every other phone marks it. Recommendation: yes. If no, delete task 1. A real blind timer would change scope; it needs its own study, a spec.md change and an ADR.
2. **A vibration on the other phones when the stakes change.** Recommendation: yes, one `done` pattern. It comes after a poll, so the iPhone may stay silent; Android vibrates. The Vibration switch turns it off. If no, delete that line from task 1.
3. **The money meter for count-up.** The figure "4 of 7" and the pips that fill already exist. Recommendation: leave the meter out (the study gives the reasons). If yes, a task 3 is added and this plan comes back for approval.

## Outcome

- When the host raises or lowers the blinds during play, each other phone at the table sees "Blinds up" or "Blinds down" beside the figure, with the Brass mark, for 3 s.
- A finger on a row or card makes it give slightly, as a button does.

## Non-goals

- No blind timer, no levels, no schedule.
- No mark on the host's own phone after Set settings: it is a full page load, and the host knows.
- No change to the count-up page.
- No movement of money digits. The blinds figure is at its new value on the first frame.
- No press scale with a mouse.

## Tasks

### 1. Mark a stakes change in play

`tests: first` for the server value; `tests: alongside` for the browser.

- [ ] In `templates/web/_session_live.html:10`, give `<strong data-fact="blinds">` the attributes `data-watch="stakes"` and `data-value="{small}:{big}:{min}:{max}"` (integers, no formatting). Add a hidden `<span class="change-label stakes-label" aria-hidden="true">` after the "Blinds" label.
- [ ] Django test first: a running set renders `data-value` with the four integers of the current `SettingsVersion`. After `update_settings` with a higher big blind, the value changes. A draft set has the same attribute (harmless; no mark before play, because no earlier value differs).
- [ ] In `static/js/changes.js`, in the `data-watch` loop: when `el.dataset.watch === "stakes"` and the value changed, set the label from the integers. Compare the big blind first, then the small blind. Higher: "Blinds up". Lower: "Blinds down". Both the same, and only the buy-in limits changed: "Stakes changed". Show it with `pop()`, hide it at the end of the hold, as player badges do. Play `pokerHaptics.play("done")` once, only on a live update, not on first page view.
- [ ] CSS: `[data-watch="stakes"].just-changed` uses the pot's underline (`box-shadow: 0 2px 0 var(--brass)`), not the box outline. The label uses the existing `.change-label` style. At 320 px the felt's side column must not wrap the label over the figure: the label goes on the label line, which may wrap.
- [ ] Screen readers: the label is `aria-hidden`, as the other change labels are. The server cannot know which value a viewer saw last, so it cannot render an announcement. Record this as a known limit in the plan's checks.
- [ ] Browser check `web/tests/browser/stakes_mark.mjs`: two contexts on one running set. The host's context posts Set settings with a higher big blind. The player's context, after its next poll: the figure shows the new blinds on the first frame (no other value in between), "Blinds up" is visible, `just-changed` is present, and both are gone after 3.5 s. With `navigator.vibrate` stubbed: one call. A second change within 3 s restarts the hold. A change of only the maximum buy-in says "Stakes changed". Reduced motion: the label shows, nothing moves. 320 px: no overlap (bounding boxes).

Done when: the Django test and `stakes_mark.mjs` pass, and `changes`-related scripts (`motion.mjs`, `haptics.mjs`, `screens.mjs`) still pass.

### 2. Rows give under a finger

`tests: alongside`.

- [ ] In `static/js/motion.js`, extend the `pointerdown` listener: for `event.pointerType !== "mouse"`, find the closest of `.session-link, .set-link, .home-row, .table-card, .roster-link, .player-opener, .stat-row a`. Run `scale: 0.98` with `press` on that element. On `pointerup` and `pointercancel`, run `scale: 1` with `shift` (no bounce), then `settle`.
- [ ] Scale the opener, not `.player-row`, so `flow.js`'s row movement keeps its own transform (footgun `press_interrupts_a_combined_animation.md`).
- [ ] Before a view transition starts (`turbo:before-render` or the existing `is-going` class), cancel the press and clear the inline transform, so the shared-element snapshot is at scale 1.
- [ ] Inside an open sheet, do nothing while a drag can start (`sheets.js` marks the dragging state; skip when the sheet is dragging).
- [ ] Browser check, added to `fluid.mjs` or a new `row_press.mjs`: with touch emulation, a press on a session card gives a computed scale below 1 within 100 ms; release returns to exactly no inline transform; a press then a scroll (pointercancel) returns it; a mouse press does nothing; the card's view transition to the session page still carries the name (existing check passes); reduced motion: nothing moves.

Done when: the new check and `fluid.mjs`, `motion.mjs`, `sheet_drag.mjs`, `screens.mjs` pass.

## Rendezvous

- [ ] Django suite on SQLite (`--parallel 4`) and on PostgreSQL.
- [ ] Browser scripts named above.
- [ ] `review-animations` on the diff; `break-ui` on the felt with long stakes (₱1,000,000 / ₱2,000,000) at 320 px; `code-review`.
- [ ] First thing a user does: a signed-in host changes the blinds during a real set while a player's page is open. Check the player's page.
- [ ] Phone checks into TODO.md: the mark on a second phone; the vibration on Android and, unknown, on the iPhone; the row give on an iPhone, and that scroll still starts at once.

## Checks

(Filled at rendezvous.)

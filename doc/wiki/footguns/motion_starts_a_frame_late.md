# Motion starts a frame late, and a pill row forgets where it was scrolled

- **Trigger:** A script moves something into place right after a screen is swapped in (`pokerPage` start, which runs inside `turbo:render`): a row gliding from its old position, a marker sliding between pills, a block fading in.
- **Observed behavior:** `Motion.animate` does not apply the first keyframe at once. The browser draws one frame with the element already at its final place, and the animation then starts from the far end. On a phone this reads as a jitter on every change. Separately, a swapped screen draws every sideways-scrolling row (`.pills`) from its start, so a row the person had scrolled jumps back, and anything measured from it is measured in the wrong place.
- **Impact:** Reported by the human on 2026-10-09 for the order pills on the Stats tab: "a weird jittering" when switching, and "weird jumps" after scrolling the pills sideways. Nothing stored was affected.
- **Evidence:** A frame-by-frame probe in Chrome showed the marker at its final position (93px) on the first frame of the new screen with no animation attached, then at its start (−70px) on the next. `stats.mjs` now checks the first frame: the marker is where the chosen pill was, every row is where it was, and the pill row and the page have not moved.
- **Remedy:**
  - Before calling Motion, write the first keyframe to the element's inline style (`el.style[name] = keyframes[name][0]`). `pokerMotion.settle` removes it when the animation ends. `stats.js` and `roster.js` do this in their `move` helpers.
  - When a screen is swapped for another state of the same screen, put the page and each sideways row back (`scrollLeft`) **before** measuring or animating, inside the start function, not only on `turbo:load`.
  - Check the first frame, not only that an animation ran and cleaned up.
- **Scope:** Set the first keyframe in the caller when it differs from the element's current state. `pokerMotion.run` also serves movements that start from the current state, such as a pressed button or a nudge.

## 2026-10-09 addendum: a later movement on the same element

`pokerMotion.settle` clears inline styles only when its animation is still the element's latest. A numpad key pressed while it was rising had the press as its latest movement, so the rise's own `opacity` and `transform` stayed on the key. Where an element can be touched while it arrives, the script clears what it wrote itself when its animation ends (`go` in `numpad.js`), instead of relying on `settle`.

## 2026-11-01 addendum: a sheet flashes before it rises

`sheets.js` called `showModal()`, then `pokerMotion.run`, without first setting the entry transform. The [iPhone motion study](../../study/1793517118_iphone_motion.md) found the same defect in all three desktop Chrome runs. The first open frame was fully opaque at Y = 0. A later frame moved the sheet down by more than 500 px. The sheet then rose to rest.

The open handler now sets `translateY(dialog.offsetHeight + "px")` before it calls Motion. It uses `pokerMotion.settle` to clear that transform after entry. The guard in `settle` checks the latest animation after two frames. Thus, an old entry or exit completion cannot clear a newer movement during close and reopen.

`web/tests/browser/motion.mjs` samples the first open frame on three openings. It also checks that the entry transform is cleared. A sample taken only after 60 ms could miss the flash. `mobile_motion.mjs` adds Chromium and WebKit checks for the first frame, a close during entry, and focus after a player-to-cash-out swap. These desktop browser checks do not establish installed-iPhone performance.

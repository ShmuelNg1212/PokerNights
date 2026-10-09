# Motion starts a frame late, and a pill row forgets where it was scrolled

- **Trigger:** A script moves something into place right after a screen is swapped in (`pokerPage` start, which runs inside `turbo:render`): a row gliding from its old position, a marker sliding between pills, a block fading in.
- **Observed behavior:** `Motion.animate` does not apply the first keyframe at once. The browser draws one frame with the element already at its final place, and the animation then starts from the far end. On a phone this reads as a jitter on every change. Separately, a swapped screen draws every sideways-scrolling row (`.pills`) from its start, so a row the person had scrolled jumps back, and anything measured from it is measured in the wrong place.
- **Impact:** Reported by the human on 2026-10-09 for the order pills on the Stats tab: "a weird jittering" when switching, and "weird jumps" after scrolling the pills sideways. Nothing stored was affected.
- **Evidence:** A frame-by-frame probe in Chrome showed the marker at its final position (93px) on the first frame of the new screen with no animation attached, then at its start (−70px) on the next. `stats.mjs` now checks the first frame: the marker is where the chosen pill was, every row is where it was, and the pill row and the page have not moved.
- **Remedy:**
  - Before calling Motion, write the first keyframe to the element's inline style (`el.style[name] = keyframes[name][0]`). `pokerMotion.settle` removes it when the animation ends. `stats.js` and `roster.js` do this in their `move` helpers.
  - When a screen is swapped for another state of the same screen, put the page and each sideways row back (`scrollLeft`) **before** measuring or animating, inside the start function, not only on `turbo:load`.
  - Check the first frame, not only that an animation ran and cleaned up.
- **Not changed:** `pokerMotion.run` itself. Its other callers start from where the element already is (a pressed button, a nudge), where the first keyframe equals the current state.

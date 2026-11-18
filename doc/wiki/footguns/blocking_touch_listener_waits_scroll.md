# A blocking touch listener makes scrolling wait, and a cancelled first move can stop the gesture

- **Trigger:** A drag on a surface that also scrolls, such as a sheet whose content scrolls. The drag needs `preventDefault()` on `touchmove`, so the listener is registered with `passive: false`.
- **Observed behavior:** While a non-passive `touchmove` listener is on an element, the browser waits for the main thread on each move before it scrolls. A busy page (Motion, a live redraw) then makes scrolling jitter. Separately, on an iPhone, `preventDefault()` on the first `touchmove` stops scrolling for the whole touch, even when the finger then goes the other way.
- **Impact:** Found on 2026-11-18 in review, before release. The first sheet drag kept a blocking listener for the sheet's whole life, and cancelled the first move when the content was at its top and the finger moved down by 1px.
- **Evidence:** `sheet_drag.mjs` reads the sheet's listeners through DevTools: one blocking `touchmove` listener at the top of the content, none when it is scrolled. The first build had one in both cases. Chromium keeps scrolling after a cancelled first move, so no probe here shows the iPhone's case; the phone check does.
- **Remedy:**
  - Track the drag in a passive listener. Add the blocking listener, which only calls `preventDefault()`, while a drag can start that needs it: for a sheet, while its content is at its top (`sync()` on `scroll` in `sheets.js`).
  - Give the drag handle `touch-action: none`, so it needs no blocking listener.
  - Decide nothing, and cancel nothing, in the first 6px. The browser starts its own scroll only after about 10px.
- **Scope:** Each surface that both drags and scrolls.

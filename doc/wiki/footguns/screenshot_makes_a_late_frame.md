# A screenshot during a frame probe makes a late frame

- **Trigger:** A browser check measures frame times with `requestAnimationFrame` and takes a screenshot while it measures.
- **Observed behavior:** The capture holds up rendering. The probe records one frame of 64 to 78 ms at the moment of the screenshot, as if the animation had dropped frames.
- **Impact:** Found on 2026-11-06 in the WebKit check of the set start overture. Each run had one late frame, always at about 785 ms, when the script took its mid-overture screenshot. Without the screenshot, four runs had no frame over 34 ms (worst 25 ms).
- **Evidence:** Same set, same code, with and without `page.screenshot()` in the middle of the measured window.
- **Remedy:** Do not capture during a measured window. Take screenshots in a separate run, or before or after the window. `overture.mjs` measures its frame times in a run with no screenshot.
- **Scope:** Seen in Playwright WebKit. Treat Chrome's `Page.captureScreenshot` the same way.

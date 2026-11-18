# Headless Chrome can run frames faster than the probe's waits

- **Trigger:** A browser probe that starts a timed animation, waits with `setTimeout` or `sleep` in Node, then reads the element in the middle of the animation.
- **Observed behavior:** In headless Chrome driven over the DevTools protocol with `--disable-gpu`, frames and animation time can run without a display's limit. On 2026-11-18 a `requestAnimationFrame` sampler logged about 3,600 frames during a 500ms wait, and a 60-second Motion animation had finished when the probe read it. Each protocol call also takes about 30ms, so a 300ms sheet rise is usually over before a touch arrives.
- **Impact:** A check of "a touch during a rise" read the sheet at rest and failed for the probe's reason, not the code's.
- **Remedy:** Do not race an animation from Node. Hold the movement still instead: start it in the page, then set its controls' `time` and `pause()` (Motion controls support both) and touch it. The code under test takes over a paused movement the same way as a running one. Read frame data with a sampler in the page, not with timed reads from Node. See `sheet_drag.mjs`, "a touch during a rise".
- **Scope:** Probes that drive Chrome directly. Playwright's WebKit was not measured.

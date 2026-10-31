# A control in a closed disclosure still has client rects

- **Trigger:** count or check "visible" controls with `getClientRects()` on a page with closed `<details>`.
- **Observed:** Chrome hides closed content with `content-visibility: hidden`, so it keeps its boxes. On Settings, 36 of 46 "visible" controls were inside closed rows. A person could press 10.
- **Impact:** a measure of what a person can press reads high, and a check that a control is hidden can pass or fail for the wrong reason.
- **Evidence:** 2026-11-01, `journey.mjs` on Settings, seeded group.
- **Remedy:** use `element.checkVisibility({contentVisibilityAuto: true})`. `journey.mjs` does this for its control count.

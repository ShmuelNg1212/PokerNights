# Mobile overflow checks can accept an overflowing page

## Trigger

Use Chrome device emulation with `mobile: true`, and compare `document.documentElement.scrollWidth` with `window.innerWidth` to check a phone layout.

## Observed behavior and impact

During visual redesign slice 2, the initial 390 px large-content check returned true while its full-page capture was 466 px wide. Long unbroken names overflowed the pending-player paragraph and balance explanation. The comparison accepted the overflow because mobile Chrome could expand the reported layout viewport with the content. A separate 320 px check against the requested width and the finish reviewer caught it.

## Evidence and remedy

The [slice 2 plan](../../plan/1791050738_redesign_slice_2.md) records the initial failure and confirmation. `web/tests/browser/end_set.mjs` now compares scroll width with the requested device width, rather than `innerWidth`. Its full-page capture uses CDP content dimensions, so an oversized image remains visible evidence. The corrected 320/390/1280 checks pass after names wrap within their containers.

For a responsive check, keep the requested width as the independent reference. Capture and inspect long names and large amounts; a passing comparison alone does not verify the layout.

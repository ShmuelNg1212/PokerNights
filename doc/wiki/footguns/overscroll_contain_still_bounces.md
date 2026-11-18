# `overscroll-behavior: contain` still lets a sheet's content bounce

- **Trigger:** A surface that scrolls and is also dragged, such as a sheet that closes by a downward drag, with `overscroll-behavior: contain`.
- **Observed behavior:** `contain` stops the scroll from passing to the page behind, but it keeps the element's own overscroll effect. On an iPhone, a finger that pulls down at the top of the content makes the content rubber-band down inside the sheet while the script moves the sheet itself. The content seems to pull away from the sheet's top as it closes.
- **Impact:** Reported by the human on a phone on 2026-11-18, after the release of the sheet drag: "the pop up menus still have some weird artifacting when it is swiped down". Nothing stored was affected.
- **Evidence:** Desktop Chromium and Playwright's WebKit do not rubber-band, so no probe showed it. `sheet_drag.mjs` and `sheet_drag_webkit.mjs` now check that `overscroll-behavior-y` is `none` and that the content's `overflow-y` is `hidden` while a drag runs. Those checks failed against the released CSS. They prove the properties, not the iPhone's bounce; the phone check does.
- **Remedy:** Use `overscroll-behavior: none` on a dragged surface, and stop its scroll for the length of the drag (`overflow-y: hidden`; the scroll position is kept). See `.sheet-draggable` in `static/css/app.css`.
- **Scope:** Each scrolling surface that a finger also drags.

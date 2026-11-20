# A grid item that spans rows makes the other column's rows taller

- **Trigger:** A two-column grid with `align-items: start` puts a tall item in one column across two rows (`grid-row: 1 / span 2`). The other column has one item in each row.
- **Observed behavior:** The browser shares the tall item's extra height across both rows. The first row grows past its own item, so the second item in the other column starts far below the first.
- **Impact:** On the session page from 900 px, the left column had a 133 px gap between the lead (with the recap card) and Share results. Nothing overlapped, so no check failed.
- **Evidence:** 2026-11-20, `/n/12/` at 1280 px: the lead was 306 px high, but the second row started 439 px down. With `grid-template-rows: auto 1fr` it starts 334 px down (306 px plus the 28 px gap). [Plan](../../plan/1795152458_final_polish.md).
- **Remedy:** Give the grid explicit rows and let the last row take the slack: `grid-template-rows: auto 1fr` (`.night-layout` in `static/css/app.css`). Measure the top of each item in the short column; a screenshot alone hides it in a tall page.
- **Not changed:** The count-up layout (`.count-layout`) has the same shape and about 14 px of slack above "The books". It already ends its rows with `1fr`.

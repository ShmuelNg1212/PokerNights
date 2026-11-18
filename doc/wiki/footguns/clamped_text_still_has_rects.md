# Clamped text still has rectangles for its hidden lines

- **Trigger:** A browser check measures text with `Range.getClientRects()` inside an element that shows two lines at most (`-webkit-line-clamp`, `.name-fit`).
- **Observed behavior:** The range returns a rectangle for each line of the text, also for the lines the clamp hides. The hidden lines sit below the visible box, on top of whatever comes next.
- **Impact:** Found on 2026-11-19. `marks.mjs` said "the badge covers the name" on a row with a long name. The badge sat under the two visible lines; only the hidden third line touched it.
- **Evidence:** Same page, same badge: the false finding went away when the check kept only the rectangles inside the element's `getBoundingClientRect()`.
- **Remedy:** Before an overlap check, drop the text rectangles that are outside the clamped element's box. `marks.mjs` does this for player names.
- **Scope:** Any clipped text: `line-clamp`, `overflow: hidden` with `text-overflow`, and a closed disclosure ([closed details](closed_details_still_have_rects.md)).

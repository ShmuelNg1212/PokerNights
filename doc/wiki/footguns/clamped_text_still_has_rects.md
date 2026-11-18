# Clamped text still has rectangles for its hidden part

- **Trigger:** A browser check measures text with `Range.getClientRects()` inside an element that clips its text: two lines at most (`-webkit-line-clamp`), or one line with an ellipsis (`.name-fit` since 2026-11-19).
- **Observed behavior:** The range returns rectangles for all of the text, also for the part the element hides. Hidden lines sit below the visible box. Hidden text on one line runs past its right edge, on top of the chevron or the button.
- **Impact:** Found on 2026-11-19. `marks.mjs` said "the badge covers the name" on a row with a long name. The badge sat under the two visible lines; only the hidden third line touched it.
- **Evidence:** Same page, same badge: the false finding went away when the check kept only the rectangles inside the element's `getBoundingClientRect()`.
- **Remedy:** Before an overlap check, cut each text rectangle to the clipped element's box and drop what is left empty. `marks.mjs` does this for player names.
- **Scope:** Any clipped text: `line-clamp`, `overflow: hidden` with `text-overflow`, and a closed disclosure ([closed details](closed_details_still_have_rects.md)).

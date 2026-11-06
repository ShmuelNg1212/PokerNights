# A poll's morph removes inline styles in the set page

- **Trigger:** A script writes an inline style on an element inside `#live` and expects it to stay for longer than one poll: a hidden token, a first keyframe, a held position.
- **Observed behavior:** `live.js` applies each snapshot with `Turbo.morphChildren`. The morph keeps the same element but makes its attributes match the server's HTML. The server sends no `style`, so the inline style is removed. Without Turbo, `live.js` replaces `#live` with `innerHTML`, and every element captured before is detached: `getBoundingClientRect()` on it gives zeros.
- **Impact:** Found while building the set start overture (2026-11-06). A token hidden by an inline style would show in the middle of the overture. Chips sent to tokens captured before a replacement landed 557 px from their rows.
- **Evidence:** A WebKit check on a running set: an inline `opacity` on a row chip, then a morph with the server's snapshot. The element was the same (`same: true`) and its `style` was `null`. `overture.mjs` checks a morph and a full replacement during the overture.
- **Remedy:**
  - Put a layer that must last outside `#live`, in `#table-sheets` (Turbo keeps it), as `seats.js` and `overture.js` do.
  - Hide or mark elements in `#live` with an attribute on `<html>` and a CSS rule, not with inline styles on them.
  - Find elements again by a stable key (`data-m`, `data-fact`, a selector) when you measure them, not by a node kept from earlier.
  - To keep one attribute through a morph, cancel `turbo:before-morph-attribute` for it, as `turbo-setup.js` does for `open`.
- **Scope:** Short movements that end before the next poll (1.5 to 4 s) are safe, which is why most set-page motion writes inline styles.

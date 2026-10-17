# A link stretched over a card prefetches twice

- **Trigger:** a link made to cover its card with a positioned `::after`, on a page that Turbo prefetches on touch (`turbo-setup.js` passes `touchstart` on as a `mouseenter`).
- **Observed:** one tap gave the link two `mouseenter` events. Turbo's prefetch cache keeps only its latest timer, and `clear()` cancels only that one, so the first timer ran out after the click and fetched the page again. Measured on the Sessions tab, 2026-10-17: requests at 2 ms and 190 ms for one tap.
- **Impact:** every tap on a card made the server render the set page twice.
- **Remedy:** make the whole card one `<a>` with the content inside it (`templates/web/_session_card.html`). Put a button look on a `<span>` inside the link, not a second link. `navigate.mjs` ("touch for 60ms: the screen is asked for once") catches it.

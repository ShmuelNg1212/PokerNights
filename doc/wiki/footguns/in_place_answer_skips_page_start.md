# An action's answer redraws the set in place; page start does not run

- **Trigger:** A script on the set page reacts to the page through `pokerPage.register` only. The host then sends a form with `data-turbo="true"`, for example **Finalize set N**.
- **Observed behavior:** The answer redraws `#live` in place (`turbo-setup.js`). The page is not loaded again, so the registered start function does not run. The script misses the new state. The redraw says `live:updating` before and `live:updated` after, as a poll does.
- **Impact:** Found on 2026-10-20 while building the "What next?" arrival: the two cards did not rise after finalizing. Nothing stored was affected.
- **Evidence:** A browser probe sampled the cards for 1.6 s after finalizing: opacity stayed 1 and no inline style was written until `nextstep.js` also listened to `live:updated`.
- **Remedy:** Run the same function from `pokerPage.register` and from a `live:updated` listener added once, outside the start function. Guard it so that a poll does not repeat it (for example a `localStorage` key). Spend that guard only after the elements are drawn.
- **Not changed:** `turbo-setup.js`. Other modules (`changes.js`, `counts.js`, `dock.js`) already listen to `live:updated`.

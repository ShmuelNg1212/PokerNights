# A sheet opener can come back with the number keys

- **Trigger:** Opening a sheet from a button outside the page region, such as the Chips key in the number keys' bottom panel (2026-10-28, count chip flow).
- **Observed behavior:** When the sheet closes, the native dialog first puts focus back on the count field. That focus opens the number keys again. The panel is reused, so the Chips key is connected again. Then the sheet's `close` handler finds `opener.isConnected` true and moves focus to the Chips key.
- **Impact:** Focus lands on a key in the panel, not in the field. Typing then goes nowhere.
- **Evidence:** A focus trace in the browser probe: `in:count-1`, then `close`, then `in:chips`.
- **Remedy:** `sheets.js` records an opener outside the region as the field that names the sheet (`data-sheet-return`). Give any new trigger outside the region a matching `data-sheet-return` field.

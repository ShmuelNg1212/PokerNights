# A cancelled submit still makes the buttons busy

- **Trigger:** A script handles a POST form's submit in place and calls only `event.preventDefault()`. Example: Fill on the chip-values page, which fills the rows from a group preset.
- **Observed behavior:** `forms.js` listens for every submit on `document` and does not check `defaultPrevented`. It marks the form as sent, disables its submit buttons, sets the text to "Sending…" and sets `aria-busy`. The busy line under the button then runs forever, because no page load follows to reset it.
- **Impact:** Reported by the human on 2026-10-30: Fill stayed on its busy animation after it filled the rows. A second Fill could not run.
- **Evidence:** `chip_presets.mjs` checks "session: Fill is usable again". It fails when the handler calls only `preventDefault()`.
- **Remedy:** A script that answers a submit in place also calls `event.stopPropagation()`, so the event does not reach `forms.js` or Turbo. The chip sheet's capture handler in `denominations.js` does the same.
- **Not changed:** `forms.js` itself. Turbo cancels each submit it takes over, so a `defaultPrevented` check there would need care about listener order.

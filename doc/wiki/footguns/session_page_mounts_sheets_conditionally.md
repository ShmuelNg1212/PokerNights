# The session page mounts sheets only when it needs them

`templates/web/night.html` writes `<div id="table-sheets">` only under a condition: the recap, the next set, settle-up or the table-payment form. `static/js/sheets.js` does nothing on a page without that mount.

A new sheet source on the session page must also enter that condition. If it does not, the opener stays hidden, the `<details>` fallback is hidden by `.sheets-enabled .sheet-source`, and the button does nothing. Tests that render HTML do not see this. Only a browser check does.

Found 2026-10-26 when the “Paid at the table” sheet did not open on a session with a set in play.

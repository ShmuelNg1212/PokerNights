# Amount fields hold commas

An amount field (`data-numpad="pesos|chips|amount"`) shows its value grouped: "1,500", not "1500". `static/js/grouping.js` groups it on each `input` and `change`, on a quick-amount click, on `live:updated` and `inplace:updated`, and when the page loads.

- A script that reads such a field must strip commas first (`window.pokerGroup.raw`, or `.replace(/,/g, "")`). A plain string compare with an ungrouped total fails. Example: `denominations.js` `holdChips()` dropped the chip breakdown for totals of 1,000 or more until it compared the digits.
- A script that writes such a field should send `input` or `change`, so the field is grouped at once.
- A server value is grouped as the field's `defaultValue` too, so `live.js`, `turbo-setup.js` and `app.js` still see an untouched field.
- `numpad.js` edits the digits without commas and maps the caret. Its drawn figure appends new characters at the end of the DOM and places them by position, so a probe must read the figure left to right, not in DOM order.
- Count fields of one chip colour (`data-numpad="count"`) stay plain: `denominations.js` reads them with `/^[0-9]{1,12}$/`.
- The server accepts commas and "₱" (`ledger/money.py`). A page without the script sends the same amount.

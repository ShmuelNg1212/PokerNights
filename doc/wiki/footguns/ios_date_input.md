# The iPhone draws a date input at its own size

## Trigger

Put `<input type="date">` in a form and style it with the same `width: 100%; min-height; padding` rule as text fields.

## Observed behaviour and impact

On an iPhone (every browser there uses Safari's engine) the date field keeps an intrinsic width, centres its value and is shorter when empty. It ends short of the fields above and below it. The human reported this on the New session form on 2026-10-04. Chrome on a computer and on Android draw the field like a text field, so the browser checks did not catch it.

## Remedy

The shared field rule in `static/css/app.css` ("One field box for every form") sets `appearance: none`, `display: block`, `min-width: 0`, a fixed line height and `text-align: left` on text, date and select controls, gives the date input a fixed height, and left-aligns `::-webkit-date-and-time-value`. The native date picker still opens.

Selects also lose their native look there and get the app's own chevron as a background image.

## Limits of the evidence

No browser on the development machine reproduces Safari's date control. `web/tests/browser/session_form.mjs` proves the field edges, heights and text size in Chrome only. A change to the shared field rule needs a look on a real iPhone. See the [session form plan](../../plan/1791121411_session_form.md).

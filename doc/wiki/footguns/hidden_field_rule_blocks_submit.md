# A hidden field's browser rule can block the submit button

- **Trigger:** A form hides a field with CSS, and the field has a browser rule such as `step`, `min` or `required`. Example: the start time on New session, while Announce is not ticked (2026-10-30).
- **Observed behavior:** The browser still checks a field with `display: none`. If the value breaks the rule, the browser cannot focus the field to report it. It stops the submit and shows nothing.
- **Impact:** The button seems dead. The server never sees the form, so a server rule that ignores the hidden field does not help.
- **Evidence:** `session_options.mjs` checks "a start time left behind does not block the button". It enters 20:33, then clears the box.
- **Remedy:** Do not put a browser rule on a field that CSS can hide. Let the server read the chosen option, as the rake fields do.

# Copy link button: study

Date: 2026-10-06, Asia/Manila.

## Request

The human asked for "a simple copy to clipboard button whenever an invite link or a password reset link is created."

## What exists today

- Both links are shown once, in Group settings, in a green notice with a read-only text field (`templates/web/_group_settings.html`): the invite link under "Invite players", the reset link at the top of "Players".
- The field selects its text when it gets focus (`onfocus="this.select()"`). On a phone the host must then use the system's Copy bubble. The address is longer than the field, so most of it is out of sight and it is hard to tell whether all of it was selected.
- Neither link can be shown again; only its hash is stored. A copy that silently fails costs the host a new link.

## Constraints

1. **The clipboard is a browser feature.** `navigator.clipboard.writeText` works only on https or localhost and only from a tap. The live site is https. It can still be refused, so the button must say whether it worked, and the field must stay as the fallback.
2. **Without JavaScript** the button can do nothing. It stays hidden, as the password Show button does, and the field works as today.
3. **Scripts register with `page.js`** ([footgun](../wiki/footguns/scripts_run_once_per_tab.md)) with a start and a stop.
4. **Success is shown only when it happened** (PRODUCT.md): "Copied" appears after the browser confirms, never before.
5. **48 px targets, plain words, not colour alone** (DESIGN.md). The result must also reach a screen reader.
6. **No preview deployments.** The change must fail safe: if the script fails, the field is still there.
7. Nothing on the server changes. No model, service, migration or new address.

## Options

- **A. A "Copy link" button under the field (recommended).** Full width, 48 px. It reads "Copied" for two seconds after the browser confirms. If the browser refuses, the field's text is selected and a line says "Could not copy. The link is selected: copy it from the menu."
- **B. Copy automatically when the link appears.** Browsers refuse a clipboard write that does not come from a tap.
- **C. The phone's share sheet** (send straight to a chat). Useful, but it is a second feature with its own failure cases; the request is for a simple copy.

One script and one attribute (`data-copy`) serve both links and any later one.

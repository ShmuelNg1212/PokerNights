# Fixed elements sit under the iPhone keyboard

## Trigger

Fix an element to the bottom of the screen (`position: fixed; bottom: 0`) on a page that also has text fields.

## Observed behaviour and impact

On an iPhone (every browser there uses Safari's engine, and so does the installed app) the keyboard does not resize the page. It covers the bottom of it. The fixed element stays at the bottom of the page, under the keyboard. The human reported this for the host dock during count-up on 2026-10-05: the bar with the count verdict was hidden exactly while typing counts. Android Chrome resizes the page, and headless Chrome has no keyboard, so the browser checks did not catch it.

## Remedy

`static/js/dock.js` reads `window.visualViewport`. The covered height is the fixed element's bottom edge minus `offsetTop + height` of the visual viewport. It writes that to `--kb` on `<html>` and the CSS raises the dock by it. It ignores a zoomed page (`scale` not 1) and changes under 80px. The page's bottom padding and the fields' scroll margin include `--kb`, or a field near the end cannot scroll clear.

`interactive-widget=resizes-content` and the VirtualKeyboard API do not work on iOS.

A new fixed bottom element (a sheet, a toast, a second dock) needs the same treatment. The sheets and toasts do not have it yet.

## Checking

`web/tests/browser/dock.mjs` replaces `visualViewport` with a stand-in that reports a 336px keyboard. This proves the script and layout, not that an iPhone reports those values. Only a real iPhone confirms it.

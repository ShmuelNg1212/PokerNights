# Fixed elements sit under the iPhone keyboard

## Trigger

Fix an element to the bottom of the screen (`position: fixed; bottom: 0`) on a page that also has text fields.

## Observed behaviour and impact

On an iPhone (every browser there uses Safari's engine, and so does the installed app) the keyboard does not resize the page. It covers the bottom of it. The fixed element stays at the bottom of the page, under the keyboard. The human reported this for the host dock during count-up on 2026-10-05: the bar with the count verdict was hidden exactly while typing counts. Android Chrome resizes the page, and headless Chrome has no keyboard, so the browser checks did not catch it.

## Remedy

**Not every browser on an iPhone behaves this way.** Chrome on an iPhone shortens the page itself when its keyboard opens, so a fixed element is already on top of the keyboard. A script that raises it by the keyboard's height sends it off the top of the screen. The human reported exactly that on 2026-10-05, after the second version of the fix.

`static/js/dock.js` reads `window.visualViewport` and keeps **two numbers apart**:

- **The keyboard's height** (`--kb-h`, class `kb-open`): how much shorter the visible frame is than it was with no field in use. It does not change while the person scrolls. It decides whether the dock is the bar, and how much room the page reserves.
- **The dock's offset** (`--kb`): the page frame's bottom edge *as it is now* minus `offsetTop` minus the visible frame's height, never below 0. The edge is read from the dock's own position while the two frames coincide (`offsetTop` 0), and otherwise from the full height less however much `documentElement.clientHeight` has shortened. Where the keyboard shortens the page, the edge is already at the keyboard and the offset is 0. The room the page reserves (`--kb-h`) is measured from the same edge. It falls to 0 as the visible frame slides down inside the page's frame. It only positions the dock.

The first version used one number for both, measured with `offsetTop`. With the keyboard open an iPhone slides the visible frame inside the page's frame, both when the person scrolls and when a low field is tapped, so that number fell to 0 and the script concluded the keyboard had closed: the menu opened in full over the field, and the page's length changed under the finger. The human reported this on 2026-10-05 in the installed app during count-up.

Other rules the second version follows:

- A covered field is scrolled clear only when it gains focus or the keyboard opens. Doing it on every viewport event pulls the page back while the person scrolls.
- While the keyboard is open the script reads the visible frame every frame. An iPhone sends `visualViewport` scroll events sparsely, so an event-only dock drifts and then jumps. One watcher only: book the next frame before calling the function that may start the watcher, or it doubles every frame.
- "No keyboard" is decided by focus: with no text field in use the current height is the full height. A height change under 80px is a browser toolbar. A zoomed page (`scale` not 1) is ignored.

`interactive-widget=resizes-content` and the VirtualKeyboard API do not work on iOS.

A new fixed bottom element (a sheet, a toast, a second dock) needs the same treatment. The sheets and toasts do not have it yet.

## Checking

`web/tests/browser/dock.mjs` replaces `visualViewport` with a stand-in that reports a 336px keyboard. The check also shortens the real page (the device height) together with the stand-in, to act as a browser whose keyboard resizes the page. The stand-in must also **move**: `__pan(offsetTop)` slides the visible frame, with or without an event. The first version's stand-in never moved, so its checks passed while the phone misbehaved. This proves the script and layout, not that an iPhone reports those values. Only a real iPhone confirms it.

A set page opened with `?kb=1` shows what the script reads (keyboard height, offset, visible and full height, the dock's edges, whether it runs as the installed app) in a label at the top of the visible frame. Ask for a screenshot of it before changing this code again.

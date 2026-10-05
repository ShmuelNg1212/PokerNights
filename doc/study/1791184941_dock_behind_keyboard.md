# Host dock behind the iPhone keyboard: study

Date: 2026-10-05, Asia/Manila.

## Report

The human reports a bug on an iPhone: during count-up, while typing a player's chip or peso count, the collapsible bottom menu (the host dock) goes behind the on-screen keyboard.

## Why it matters

The collapsed dock bar carries the live count verdict ("₱200 still to account for. 2 still to count."). The [collapsible dock plan](../plan/1791111069_collapsible_host_dock.md) promised that the bar "still tells the host whether the counts match as they type". On an iPhone it cannot, because the bar is hidden exactly while the host types. That plan listed "the on-screen keyboard over the count fields" as not verified.

## Cause

Not reproduced by the agent: there is no iPhone available and headless Chrome has no on-screen keyboard. The cause below follows from the code and from documented iOS behaviour.

- Below 900px the dock is `position: fixed; bottom: 0` (`static/css/app.css`, `.table-layout .host-controls`).
- On iOS, in Safari, Chrome and an installed app alike, the keyboard does not resize the page. It shrinks only the *visual* viewport. Fixed elements stay attached to the *layout* viewport, whose bottom edge is now under the keyboard.
- Android Chrome resizes the page by default, so the dock rides above the keyboard there. This explains why the bug is iPhone-only.
- Nothing in the app reads `window.visualViewport` today.

## Options

1. **Lift the dock with `window.visualViewport`** (recommended). A small script computes how much of the layout viewport the keyboard covers and writes it to a CSS variable; the dock's `bottom` uses it. Supported on iOS 13 and later. No dependency.
2. `interactive-widget=resizes-content` in the viewport meta tag. Not supported by iOS Safari.
3. The VirtualKeyboard API. Not supported by iOS Safari.
4. Make the dock non-fixed during count-up. The verdict would then sit at the end of the list, off screen while typing; this drops the feature instead of fixing it.

## Constraints and findings

1. **An expanded dock is too tall to lift as it is.** In count-up it is about 370px and may reach `75dvh`. An iPhone with the keyboard up has roughly 400px of visible page. Lifted whole, it would cover the field being typed in.
2. **The dock has fields of its own** ("Or add one player", the cancel reason). When the focus is inside the dock, the dock must stay expanded and fit the visible area.
3. **The safe-area padding** at the bottom of the dock is for the home indicator. Above the keyboard it is wasted space.
4. **`.next-action` is fixed separately** at the bottom (`app.css` line 240) and needs the same offset.
5. **Scroll clearance.** `.count-entry input` already has a `scroll-margin` equal to the dock height, so a focused field scrolls clear of the dock. It must follow the dock's size while the keyboard is up.
6. **Pinch zoom also changes the visual viewport.** The offset must apply only when the page is not zoomed, or the dock would float mid-screen.
7. **Script lifetime.** Scripts register with `window.pokerPage` and must remove their listeners on stop ([footgun](../wiki/footguns/scripts_run_once_per_tab.md)).
8. **No preview deployment.** The human tests on the live build. The change must do nothing when no keyboard is detected, so a wrong guess about iOS leaves today's behaviour, not a worse one.
9. **Verification limit.** A browser check can replace `visualViewport` with a stand-in and prove the script and layout respond correctly. It cannot prove that a real iPhone reports the values assumed. Only the human's phone can.

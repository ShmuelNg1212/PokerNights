# Host dock while scrolling with the iPhone keyboard open: study

Date: 2026-10-05, Asia/Manila. Follows [Host dock behind the iPhone keyboard](1791184941_dock_behind_keyboard.md).

## The report

The human, 2026-10-05: the collapsible host menu "has buggy interactions during scrolling while the native iOS keyboard is open", in the home screen app, "especially noted during the count up menus". No further detail was given. The agent has no iPhone, so nothing below was reproduced; it is read from `static/js/dock.js` and from how iOS is documented to behave.

## How an iPhone scrolls with the keyboard open

The page has two frames. The **layout frame** is the whole screen; a fixed element such as the dock is pinned to it. The **visible frame** is the part above the keyboard. With the keyboard open, the visible frame is shorter than the layout frame and can slide up and down inside it. A scroll first slides the visible frame; only when it reaches the end does the page itself scroll. iOS also slides the visible frame by itself when a tapped field is low on the screen. The browser reports the visible frame's position as `visualViewport.offsetTop`: 0 at the top, the keyboard's height at the bottom.

## What `dock.js` does today

On every change of the visible frame, and on every focus change, `keyboard()`:

1. computes `covered` = the layout frame's height − `offsetTop` − the visible frame's height;
2. treats `covered` under 80px as "no keyboard";
3. writes `covered` to `--kb`, which raises the dock and adds the same amount to the page's bottom padding;
4. shows the dock as its one-line bar while `covered` is above 0;
5. if the focused field is under the bar, scrolls the page until it is clear.

## Faults found

**1. The script decides whether the keyboard is open from a number that changes as you scroll.** `covered` equals the keyboard's height only while the visible frame is at the top (`offsetTop` 0). As the visible frame slides down, `covered` falls, and at the bottom it is 0. So during a scroll with the keyboard open:

- the page's bottom padding shrinks and grows with the scroll, which changes the page's length under the finger;
- below 80px the script concludes the keyboard has closed: the bar class is removed, and a dock that was left expanded opens to its full height (up to three quarters of the screen) over the field being typed in;
- scrolling back flips it again.

This also happens without a scroll: tapping a count field low in the list makes iOS slide the visible frame down, so the dock can open in full the moment the keyboard appears. Count-up is where the fields are, and with several players the lower fields are always in that position.

**2. The script pulls the focused field back on every scroll event.** Step 5 runs on each change, not only when a field gains focus. Scrolling up to read another player's row, with the cursor still in a field, moves that field under the bar, and the script scrolls the page back. The page fights the finger.

**3. The dock follows the keyboard late.** iOS sends the visible frame's scroll events sparsely, often only when the movement ends. Between events the dock keeps its old offset, so it drifts with the page and then jumps.

**4. The browser check could not see any of this.** `dock.mjs` replaces `visualViewport` with a stand-in whose `offsetTop` is always 0.

## One assumption that is not proven

Fault 1's arithmetic assumes that element positions are reported relative to the layout frame, which is what the standard says and what current iOS is documented to do. The first fix worked at `offsetTop` 0, where both frames start at the same place, so it did not prove this. If an iPhone reports positions relative to the visible frame, the numbers differ and a second fix made blind could miss again.

## Options

**A. Separate "is the keyboard open" from "where is the dock".** Keyboard height = layout frame height − visible frame height; this does not change during a scroll. The bar state and the page padding use it. The dock's offset = layout frame height − `offsetTop` − visible frame height, never below 0; this follows the visible frame. Scroll a covered field clear only when a field gains focus or the keyboard opens. While the keyboard is open, read the visible frame's position every frame instead of waiting for events.

**B. Hide the bar while the visible frame is moving** and show it when it rests. Hides fault 3 instead of fixing it. The running total disappears during a scroll.

**C. Stop the visible frame from sliding** by making the page exactly as tall as the visible frame and scrolling an inner box. Removes the cause, but changes how the whole set page scrolls and risks the screen-change and scroll-restoration work.

**D. An on-phone readout.** A set page opened with `?kb=1` shows the numbers the script reads in a small corner label. If the fix is still wrong, one screenshot says why.

## Recommendation

A with D. B only if the bar still jitters on the phone after A. C is not recommended.

A fails safe: with no keyboard detected, or without `visualViewport`, the dock is as it is today.

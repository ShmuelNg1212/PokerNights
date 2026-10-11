# The session recap opens at its bottom: study

Date: 2026-10-11, Asia/Manila.

## Report

The human said: "when the session recap opens it opens the bottom part of the pop up menu instead of starting at the top."

## Root cause

Found by reading the code and its history; not yet reproduced in a browser.

1. `static/js/sheets.js`, `open()`: after the sheet shows it sets `scrollTop = 0`, then puts focus on the element marked `data-sheet-focus`, or failing that on the first `input` or `button` inside the sheet's content.
2. A browser scrolls a focused element into view.
3. Until 2026-10-11 the recap's content held no input and no button (its set links are `<a>`), so nothing was focused and the sheet stayed at its top.
4. The share feature (`89de7ef`, released as `2557f50`) added one button to the recap, "Share results", as its last line. It is now the first button in the content, so it takes the focus and the sheet scrolls to it: the bottom.

The same happens when the recap opens by itself after a session closes and when "View session recap" is tapped.

## An earlier miss

`night.mjs` has a check for exactly this, "recap reopens at its top". It has failed since the share feature. In three later cycles the agent recorded it as "fails the same way on `main`, not looked into". It failed on `main` because the share feature was already there. The check was right and the agent's note was wrong.

## Other sheets

Every other sheet either marks its focus or starts with its field or its first action at the top, so none of them scrolls. The share sheet's first button follows the card; on a long session it may sit below the first screen. To be measured in the fix.

## Options

| Option | For | Against |
|---|---|---|
| A. A sheet that is for reading (the recap) starts its focus on the sheet's own Close button, at the top | Focus is visible and at the top; a keyboard or screen reader starts where the content starts | One new attribute on the recap |
| B. Focus the Share button without scrolling | One word changed | Focus sits on a control that is off the screen |
| C. Set `scrollTop = 0` after the focus | Smallest | Same as B |

Recommend A.

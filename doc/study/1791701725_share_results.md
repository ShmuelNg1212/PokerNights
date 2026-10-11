# Share a session's results to the group chat: study

Date: 2026-10-11, Asia/Manila.

## Request

The human said: "lets add a feature for sharing a result to the group chat. implement good ui design and dynamic animations."

SPEC.md lists it under nice-to-have: "Export results as CSV or a shareable image for the group chat."

Asked three questions, the human chose:

- **What:** the closed session: everyone's result ranked, plus who pays whom.
- **Format:** an image card and a text summary. Where a browser cannot share a picture, save the image and copy the text.
- **Who:** any member of the session, with the transfers on the card.

## What happens today

- A closed session's page shows the viewer's part, who pays whom, the results and the sets. "View session recap" opens a sheet with the whole night.
- Nothing leaves the app. People take a screenshot of the session page, which crops the list, shows the host's Paid buttons and the browser's bars, and differs on every phone.
- `copy.js` copies a link shown once. The copy-link study (`1791265489`) set the phone's share sheet aside as "a second feature with its own failure cases".

## Constraints

1. **No new dependency** (AGENTS.md, stack). A picture drawn on the server would need an imaging library and fonts on Vercel. A picture drawn in the browser needs neither.
2. **Amounts are formatted in one place** (rule 8). The card and the text must use the server's strings, not a second formatter in JavaScript.
3. **No write.** Sharing reads a closed session. No service, no migration, no `request_id`, no audit event.
4. **Access is unchanged** (rule 5). The share data is on the session page, which already resolves through the viewer's membership. No public link, so nothing is readable without a login.
5. **DESIGN.md.** The Rack palette, Archivo, signed amounts with icons, the chip tokens. Money appears at its accepted value; nothing counts.
6. **The user tests on the live build on a phone.** A failure must leave the session page as it is today.

## Findings

1. **The data is already loaded.** `night_outcome()` and `night_recap()` give the ranking, the buy-in total, the sets and the transfers, each amount an integer. The session page test allows 14 queries; the card needs none more.
2. **Sharing a picture from a web page works on the phones in use.** `navigator.share({files})` is in Safari on iOS 15 and later, in the installed app, and in Chrome on Android. Desktop Chrome on macOS and Firefox do not share files; they can download and copy.
3. **The share call must come straight from the tap.** Safari drops the permission if the page first waits for something slow. So the picture must be drawn when the sheet opens, and the tap only hands over a file that already exists.
4. **A canvas can draw the card in the page's own font.** Archivo is already loaded as one variable file. `document.fonts.load()` confirms it before drawing; if it is not there the card is not offered and the text still is.
5. **Canvas does not take oklch colours on every browser, and has no layout.** The script reads the page's computed colours once (the browser hands them back in a form canvas accepts) and measures text to fit long names, as the transfer rows do in CSS.
6. **A session can have many players.** Twelve seats per set and several sets. A fixed 4:5 picture would shrink the text. The card keeps its width (1080px) and grows in height; chats show tall pictures whole.
7. **A corrected session.** Since reopening shipped, a closed session's results can change. A picture already in the chat cannot. The card says when the session was closed, so a second card is seen to be the later one.
8. **Paid marks change after sharing.** The card lists who pays whom without the paid state, which would be stale within minutes.
9. **Rake.** Results are after rake; the transfer list excludes rake already collected. The card says "Results are after rake" only when the session collected any, as the session page does.
10. **Chips games** share the same card with `1,600 chips`. Nothing converts.
11. **Without JavaScript,** or when the card cannot be drawn, the text summary is still in the page in a field that can be selected and copied by hand, as the copy-link field is.

## Options for the picture

| Option | For | Against |
|---|---|---|
| A. Draw on a canvas in the browser | No dependency; the page's font and colours; works offline once loaded; nothing new on the server but a block of data | Layout is written by hand; needs a browser check on real output |
| B. Draw on the server (PNG) | Same picture for everyone; a link preview is possible later | A new imaging dependency and font files in the build; a new public or signed address; slower on Vercel's free plan |
| C. Turn the page's HTML into a picture (SVG `foreignObject` or a library) | Reuses the CSS | Unreliable in Safari with web fonts; a library is a new dependency |

Recommend A.

## Risks

| Risk | Effect | Answer |
|---|---|---|
| The share sheet is refused or missing | Nothing happens on tap | The sheet always offers Save image and Copy text; Share appears only where the browser says it can share this file |
| The font is late or the canvas fails | A card in the wrong font, or a blank one | Draw only after the font is confirmed; check the canvas is not blank; otherwise offer the text alone |
| A long name or a 9-digit amount | Text runs over the amount | Measure and shorten the name with an ellipsis; amounts are never shortened |
| Results shared, then corrected | Two different pictures in the chat | "Closed" date and time on the card |
| A member shares figures others would not | Names and amounts leave the app | The same people already see them in the app; the human chose "any member". Not offered on an archived session |

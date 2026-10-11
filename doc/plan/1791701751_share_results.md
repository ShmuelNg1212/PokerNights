# Share a session's results to the group chat: plan

Status: approved 2026-10-11 ("approved"); all five decisions as recommended. Date: 2026-10-11, Asia/Manila. Study: [Share a session's results](../study/1791701725_share_results.md).

## Outcome

After a session is closed, any member taps "Share results" and sends the night to the group chat as one designed picture with a short text under it: who won and lost, and who pays whom. Where the phone cannot share a picture, the member saves it or copies the text. Nothing is written, and nothing is readable without a login.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new colour, font or asset. No migration and no new dependency.

## The card

A picture 1080px wide, as tall as its content, in the Rack's dark ground:

1. The chip-and-crescent mark and "PokerNights", small.
2. The table name, large. Under it the date, the place if any, and "N players · N sets · ₱X bought in".
3. **Results**: one row per player in rank order: place, the player's chip token, name, and the signed result with its up or down arrow in the win or loss colour. A thin bar under each row shows the size of the result, as in the recap. The top result's row is larger.
4. **Who pays whom**: one row per transfer: payer's chip, name, an arrow, payee's chip and name, amount. "Nobody owes anything." when there is none.
5. A foot line: "Closed Oct 11, 9:40 PM" and, when rake was collected, "Results are after rake."

The card has no Paid marks and no buttons. Amounts are the server's own strings. Long names are shortened with an ellipsis; amounts never are.

## The text

```
Friday table · Sun, Oct 11
Results
1. Ben +₱600
2. Maria ₱0
3. Carlo −₱300
3. Miguel −₱300
Who pays whom
Carlo → Ben ₱300
Miguel → Ben ₱300
PokerNights
```

Built on the server and tested there.

## Behaviour

| Moment | After |
|---|---|
| Closed session, any member | "Share results" sits with "View session recap" at the end of the session overview, and at the foot of the recap sheet |
| Tap it | A sheet rises: "Share results", the card as a preview, then the actions |
| Phone that can share a picture | Primary "Share" opens the phone's share sheet with the picture and the text. Under it, quiet "Save image" and "Copy text" |
| Browser that cannot share a picture | Primary "Save image"; quiet "Copy text"; "Share text" where the browser can share text |
| The member cancels the phone's share sheet | Nothing is said; the sheet stays |
| Shared, saved or copied | The button says "Shared", "Saved" or "Copied" for two seconds; a status line says it for a screen reader |
| The card cannot be drawn (font missing, canvas refused) | The preview is replaced by the text in a field with "Copy text". No error page |
| No JavaScript | The text is in the page under a "Share results" disclosure, to select and copy by hand |
| Open, archived or never-closed session | No share control |
| Session reopened and closed again | The card shows the corrected figures and the new "Closed" time |

## Motion

One authored moment, in the sheet, with the existing presets:

- The sheet rises as every sheet does.
- **The card is dealt.** The preview starts 16px low, at 96% and slightly turned (−1.5°), and settles flat with the `arrive` spring. Its shadow grows as it lands.
- **The results are revealed** top to bottom by a clip that opens over 420ms after the card lands, so the eye reads rank 1 first. The picture itself is finished before this starts; the clip only uncovers it. No amount counts or changes.
- **Accepted actions pulse** once (`pulse` preset) as the label changes to "Shared", "Saved" or "Copied".
- Everything ends within 900ms and never blocks a tap: the actions work while the card lands.
- Reduced motion, a hidden tab or Motion not loaded: the card is simply there.

Built with the design and motion skills.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **Names on the card are display names as the group sees them,** and every player with a result is listed, losses included. Recommended: it is the same list the session page shows.
2. **No Paid state on the card.** Recommended: it would be out of date minutes later.
3. **Shares are not logged.** Recommended: sharing writes nothing. Say if you want "X shared the results" in the session's record.
4. **A switch, `SHARE_RESULTS`, on by default,** to remove the control in Vercel without a release.
5. **CSV export is left out.** SPEC.md names it beside the image; say if you want it in this cycle.

## Implementation

Branch `feat/share-results` from `main`. Tests first for the server part.

1. **`settlement/queries.py`: `share_card(night, outcome, recap)`.** Returns a plain structure from what the page already loaded: title, date line, facts line, ranked rows (place, name, chip label and colour number, signed amount string, sign, bar share), transfers (payer and payee name and chip, amount string), foot lines, the text summary and a file name (`pokernights-friday-table-2026-10-11.png`). No query of its own.
2. **`web/views.py`.** On a closed, unarchived session with `SHARE_RESULTS` on, put the structure in the context. The template writes it with `json_script` and renders the text in the fallback disclosure.
3. **`templates/web/_share.html`** included in `night.html`: the opener, the sheet source (preview holder, actions, status line, the text field), and a second opener at the foot of the recap sheet.
4. **`static/js/share.js`,** registered with `page.js` like every page script:
   - on sheet open: confirm Archivo with `document.fonts.load`, read the palette from computed styles, draw the card on a canvas at 1080px wide, check it is not blank, turn it into a PNG file kept in memory, show it in the preview;
   - Share: `navigator.share({files, text})` called directly in the tap, offered only when `navigator.canShare({files})` is true; a cancelled share is silent;
   - Save image: a download link; Copy text: the clipboard, with the selected-field fallback `copy.js` uses;
   - any failure leaves the text field and Copy.
5. **CSS (`app.css`).** The preview frame, the action stack, the dealt-card and reveal animations, reduced-motion rules.
6. **Tests.**
   - Django: the text for a pesos session, a chips session, ties, a session where nobody owes, rake; the structure's rows match the session page's ranking and transfers; the control is absent on open and archived sessions, for a non-member (404), and with the switch off; the session page stays within its query budget.
   - Browser (`share.mjs`, new, 390 and 1280px): the sheet and preview; the drawn picture is 1080px wide, not blank, and uses Archivo; with a stubbed share the file handed over is a PNG with the text, and a cancel says nothing; without file sharing the primary is Save image; Copy text puts the server's text on the clipboard; a twelve-player session and a long name fit; the dealt card ends at rest; reduced motion; 48px targets; no horizontal overflow; no script error. Captures of the card itself are looked at for hierarchy and spacing.
   - Both suites: SQLite and PostgreSQL.
7. **Documents.** Wiki (features, architecture), PRODUCT.md and DESIGN.md addenda, deployment (the switch), browser README, TODO.md with the phone checklist. SPEC.md is not edited.

## Out of scope

- A public link or a link preview.
- Sharing one set's results, or one player's card.
- CSV export (decision 5).
- Choosing what the card includes, themes, or a light card.

## Acceptance

1. On a closed session, a member opens Share results and sees the card with every player ranked and every transfer.
2. On a phone, Share hands the picture and the text to the share sheet; the picture reads clearly in a chat.
3. Where pictures cannot be shared, Save image and Copy text work.
4. The card's names and amounts equal the session page's.
5. If the card cannot be drawn, the text can still be copied and the page is otherwise as today.
6. Both test suites pass.

## Release

Kept local on its branch until you say to push. No migration. The first response to trouble is `SHARE_RESULTS=False`.

## Progress

2026-10-11: Study and plan written after three answers from the human (closed session; image card and text; any member, with transfers). Approved with "approved". Built on `feat/share-results` from `main`; kept local.

Changes from the plan:

- **The data builder is `web/share.py`,** not `settlement/queries.py`: it needs the chip label rule, which lives in `web`, and `settlement` may not depend on `web`. The label rule became `table_tags.token()`.
- **The top result's row is larger only when it is a win.**
- **A long table name wraps to a second line** after shrinking to 60px; the plan only said names are shortened.
- **In a transfer row a short name gives its unused room to the other name.**
- **The reveal uses `clip-path`,** with transform and opacity. All three are CSS animations with the existing spring curve, so they run without Motion; only the pulse uses Motion.
- **`sheets.js` now announces a shown sheet** (`sheet:shown`), which the drawing waits for.
- **"Share text"** is offered where a browser can share text but not files; the plan had it.
- **No line under the card about where it goes.** One was written and removed: it pushed Copy text off a phone screen.
- **One existing test changed:** the script order in `web/tests/test_inplace.py` names `share`.

Verification:

- 1003 tests pass on SQLite (15 skipped), 11 of them new (`web/tests/test_share.py`). PostgreSQL was not run: no model, query or migration changed.
- `share.mjs`: 29 of 29 on a fresh temporary database. The first run had two failures: one in the check (it looked at the wrong sibling), one real (the card kept a clip after landing; the animations now fill backwards only).
- The drawn cards for a four-player, a twelve-player and an all-even chips session were looked at, and the sheet at 390px, in two rounds.
- Skills: the design skill's context and craft floor, and the motion skill's guidance, as loaded earlier in the same working session.

Acceptance: 1, 3, 4, 5 and 6 are met in tests and headless Chrome. 2 is met only against a stand-in for the phone's share sheet.

Not verified: a real phone's share sheet (iPhone Safari, the installed app, Android Chrome); how the picture looks inside Messenger, Viber or WhatsApp, and whether each keeps the text; the condensed money width in Safari's canvas (if Safari ignores it the amounts are wider and names give way sooner); a screen reader. A fresh reviewer did not read the branch.

Documentation synced: wiki (features, architecture, deployment), PRODUCT.md, DESIGN.md, browser README, TODO.

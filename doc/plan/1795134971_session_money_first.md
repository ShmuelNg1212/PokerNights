# Plan: session page, the money first

Study: [1795101392_ui_critique.md](../study/1795101392_ui_critique.md), issue 3 (P2). Reconstituted 2026-11-20 from `doc/roadmap/plan_queue/ui_4_session_money_first.md` against main `09c8a31`. Mode: design. Skills: `/impeccable layout` (tasks 1 to 3); `animate` for the card's arrival (task 2); `code-review`, `/impeccable critique`, `review-animations`, `break-ui` (rendezvous).

Branch: `feat/session-money-first`, from main `09c8a31`.

## OPEN QUESTIONS

1. **Does the recap open by itself?** Today it opens once per session and viewer, after the finale (`static/js/sheets.js:279-292`). The finale exists to lead into it (`static/js/finale.js:1-4`, your decision of 2026-11-10: "the sheet never covers the finale").
   - **A (recommended).** The recap does not open by itself. The finale still plays once, then the stage goes and the page stays: "You pay ₱850" is in view. A "Session recap" card under the lead rises as the stage goes. A tap opens the recap. Tasks 1 to 4 apply.
   - **B.** The recap still opens by itself. Fix only the focus ring and the scroll (task 5). Tasks 1 to 4 drop.
2. **The bottom button.** With A, the card under the lead opens the recap. Recommendation: **remove** "View session recap" at the bottom (`templates/web/night.html:174`). Share results stays where it is. If no: keep both openers.

## Evidence (main `09c8a31`)

- The recap opens by itself once per `rack-recap:{session}:{viewer}` key, after the finale (`sheets.js:282-292`).
- On close, focus goes to "Who pays whom" (`data-recap-lands`, `night.html:52`). Before the sheet rises, the page scrolls that heading to the top when it is in the lower half of the screen (`sheets.js:287`). On a phone this pushes "You pay ₱850" off the top. This is the "ben's page was not at the top" capture: it is the design, not a fault.
- The sheet's focus starts on its Close (`sheets.js:27-33`). On a load with no tap, the browser shows the focus ring.
- The only opener is a quiet button at the end of the page, after Payment records (`night.html:174`; DESIGN.md line 972).
- **Already built, so dropped from the queue:** "Everyone is square". When every transfer is settled, the host's lead says "Settled" and a player's says "You're settled", each with the Up double hairline (`templates/web/_night_lead.html:5`, `:13`). It draws once per browser (`static/js/settle.js:6-11`, `app.css:1835`). Reduced motion shows the end state. The critique's capture was a session with unpaid transfers.

## Outcome

- On a closed session, the first screen shows what the person pays or gets, and nothing covers it.
- The recap is one tap away, directly under that figure.
- The finale still marks the end of the night, once.

## Non-goals

- No change to services, queries, transfers, payments or the recap's content.
- No change to the finale's motion, its timing, or when it plays.
- No change to the settled moment.

## Tasks

- [ ] **1. A recap card under the lead.** `tests: alongside`.
  - In `night-overview`, directly after the felt, when the session has a recap: a card button with `data-sheet-open="recap"`. Title "Session recap". One line under it: the top result's name and figure, then the number of players and sets. Example: "Miguel +₱2,400 · 6 players · 2 sets". A chevron at the right.
  - Without dialog support the card is hidden and the recap shows inline, as the bottom button does today (`app.css:501-502`).
  - 48 px target or more; single column on a phone; in the 400 px column from 900 px.
  - Done when: a view test finds the card and its line on a closed session, and none on an open one. A browser probe at 320, 390 and 1280 px finds the card inside the first screen, no overflow with long names and large amounts, and the card opens the recap with focus on Close. Close returns focus to the card.
- [ ] **2. No automatic opening.** `tests: alongside`. Depends on open question 1 (A).
  - `sheets.js`: the `rack-recap` key now marks only "the finale has played". The finale plays once per key, as today. Its end (`then`) does not open the sheet. Remove `me.lands` and the scroll before the sheet.
  - When the stage goes, the card rises once with the `arrive` preset. Reduced motion: no finale, no rise; the card is there.
  - A page left before the finale ends gives the key back, as today (`me.owed`).
  - Remove `data-recap-lands` if nothing else uses it.
  - Done when: `finale.mjs` checks that the finale plays once, that no sheet opens at any frame, that the page scroll is 0 after the stage goes, and that the card rises after the stage. `night_live.mjs` checks that a player's phone plays the finale on the redraw and opens no sheet.
- [ ] **3. One opener.** `tests: alongside`. Depends on open question 2.
  - Remove the bottom "View session recap" button. The recap sheet keeps Share as its last control.
  - Done when: a view test finds one `data-sheet-open="recap"` on a closed session. `night.mjs`, `share.mjs` and `surfaces.mjs` use the card.
- [ ] **4. Docs in DESIGN.md.** `tests: alongside`.
  - Update "Closing recap" (line 331), "Order on a phone" (line 972), Share results "The opener" (line 1001) and "Session finale" (lines 1137 and 1149): the finale ends on the page; the recap opens from the card.
  - Done when: no DESIGN.md line says that the recap opens by itself.
- [ ] **5. Only if open question 1 is B: focus and scroll.** `tests: alongside`.
  - Focus on Close with no visible ring when the sheet opened by itself. On close, keep the page at the top: remove the scroll to "Who pays whom".
  - Done when: `finale.mjs` finds no `:focus-visible` on Close after an automatic opening, and the page scroll is 0 after Close.

## Rendezvous checks

- [ ] SQLite suite passes.
- [ ] `finale.mjs`, `night.mjs`, `night_live.mjs`, `share.mjs`, `surfaces.mjs`, `settled.mjs` pass, or fail only on checks that fail on main too.
- [ ] As a player on a phone-width page: close a session as host on a second page. The player's page plays the finale, then shows "You pay" at the top with the card under it. A tap on the card opens the recap. This check fails on main, where the sheet opens.
- [ ] `/impeccable critique` on the closed session page; `review-animations` on the card's rise; `break-ui` with long names.

## Completion

All tasks ticked, the rendezvous checks recorded here, and a verified branch `feat/session-money-first`. Then the TODO.md phone check.

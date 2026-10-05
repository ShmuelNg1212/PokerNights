---
target: count-up to finalize flow
total_score: 25
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 5
target_identity: "file:/Users/shm/PokerNights/templates/web/_count_up.html"
target_fingerprint: "sha256:0ebe928d0f3286666f690eb8009b5e4fcbe62cf6488722c9e59fca1a56e70eac"
target_path: /Users/shm/PokerNights/templates/web/_count_up.html
timestamp: 2026-10-05T12-15-40Z
slug: templates-web-count-up-html
---
Method: dual-agent (A: design review · B: detector and measurements)

## 3. Critique: count-up to finalize

Method: two separate passes (design review, and detector plus measurements). The flow is four screens: count-up, the cash-out review, count-up again with every player cashed out ("Finalize results"), and the final results.

### Score

| # | Heuristic | Score (0 to 4) | Main issue |
|---|---|---|---|
| 1 | Visibility of system status | 3 | The success message covers the dock's verdict and its button; the one-line bar shows unsaved figures with no "Preview" label |
| 2 | Match with the real world | 2 | "Recorded cash-outs" and "Total cashed out" name one figure; "batch" and "accounted" are ledger words |
| 3 | User control and freedom | 2 | Finalize is one tap with no confirmation and no undo; typed counts are lost on leaving the page |
| 4 | Consistency and standards | 2 | A row's "Confirm count" confirms every row; two or three primary buttons at once; three totals blocks with different labels |
| 5 | Error prevention | 2 | The review does not say when a batch leaves the books off; the dock's main button ignores typed counts |
| 6 | Recognition rather than recall | 3 | A confirmed count is not shown in its field |
| 7 | Flexibility and efficiency | 3 | One form confirms all counts and one batch cashes everyone out, but there is no move to the next field and rows are tall |
| 8 | Aesthetic and minimalist design | 2 | The same equation twice; rake rows at zero; three instruction paragraphs |
| 9 | Error recovery | 3 | The discrepancy panel is very good; the count field's error does not say what the allowed amount is |
| 10 | Help and documentation | 3 | Inline and in context, but too much of it, and host instructions are shown to players |
| | **Total** | **25 of 40** | Acceptable; the money model is strong, the phone layout is not |

Cognitive load: four of eight checks fail (single focus, chunking, visual hierarchy, minimal choices).

### What works

- **The discrepancy panel.** The signed amount at large size, a plain cause, where to look and a next step. The override asks who absorbs the difference and requires a note.
- **The one-line bar while typing.** "₱1,950 of ₱2,000 bought in / ₱50 missing. 0 still to count." updates as the host types. It is the right instrument for the moment.
- **Honest money.** Figures show accepted values only, the preview is labelled, and the review states that it "does not finalize the set and it marks no payment".
- **Measured basics hold.** No text pair is under 4.5:1. No horizontal overflow at 320, 360 or 390px, including the long-name fixture. With reduced motion nothing animates. No console errors.

### Priority issues

**1. The phone screen puts three summaries ahead of the work. (P1)**
At 390 × 844 no player row is in the first screen. The first count field is 1,220px down the page. The expanded dock is 288px, 34% of the screen, and at most one of two rows is fully visible at any scroll position. The "Confirmed counts" block is on the page twice, once in the overview and once in the dock directly below it, with identical figures until the host types; then only the dock's copy changes. "2,000 chips bought in" appears in four blocks. A count row is about 315px tall, so nine players are about 2,800px of scrolling.

**2. The dock's main button ignores typed counts and loses them. (P1)**
With a count typed but not confirmed, the dock shows "Preview · unsaved counts … 0 still to count" directly above "Cash out counted players (1)". Tapping it opens the review without the typed player, and on return the field is empty. The largest button on the screen does the wrong thing at the moment the host is most likely to press it.

**3. The review does not say whether the batch balances the books. (P1)**
With a count ₱50 short, the review shows "After this batch ₱1,950" and "Total bought in ₱2,000" as two ordinary rows and one small grey sentence, and the button reads "Cash out 2 players" exactly as it does when the books balance. This is the last cheap moment to catch a miscount. After it the fix is a reversal with a typed reason, or an override.

**4. The success message covers the next action. (P1)**
After the cash-outs are recorded, the message "2 players cashed out; everyone is cashed out." sits on top of "Finalize results" for six seconds, with "Dismiss" above the button. Finalize has no confirmation and no undo in the app. A tap aimed at Dismiss as the message leaves lands on Finalize.

**5. A discrepancy gets the least signal when it matters most. (P1)**
In the first screen of a set whose books are ₱100 off: "2 of 2 players counted or cashed out" at 48px, "₱100 missing." in ordinary text, and a greyed "Cash out counted players (0)". The red panel is below, behind the dock. With an override, the dock says "₱100 missing" directly above an enabled "Finalize results".

**6. The count row repeats itself and hides the confirmed value. (P2)**
Each row has a label "Final count (₱)", a placeholder "Final count", its own button and three lines of detail. A confirmed row shows "Counted ₱900 at 8:02 PM" beside an empty field. Each row's button submits every row.

**7. The final page buries its proof. (P2)**
A host who did not play sees "The set is finalized." as the headline, and "The books balance" is the last line of the page. The total cashed out is labelled "Available to play". A "Live" status stays on a set that can no longer change.

**8. Smaller points. (P3)**
- The one-line bar does not say "Preview" when it shows unsaved figures.
- "Missing", "extra" and "match" look the same: no colour, no icon.
- Heading order is h1, h3, h2, h2, h3, h2. Keyboard focus reaches the dock's buttons before any count field.
- Rake rows show at ₱0 when rake is off.
- A player sees the host's instructions.
- "Full set log" is a 17px-high link.
- The flow uses 18 distinct text sizes, seven of them between 12 and 14.4px.
- An even result reads "– ₱0".

### Detector

The skill's command-line detector reported ten advisory findings, all the same rule ("colour outside DESIGN.md"), and all false: it renders each template partial alone, without the stylesheet, and sees the browser's default black. In the running page it reported low contrast on player chips (false: it compared the initial with the striped rim, real ratios are 5.7 to 10.3), covered text inside closed disclosures (false), and three true but minor points: the skipped heading level, the wide shadow on the dock's main button, and close heading sizes on the review (16, 18.4 and 22px).

### Who is hurt most

- **The host at 1 a.m. with the table waiting** cannot see the players' fields and the running total together unless the dock is folded, and has nothing on the review to read aloud that says "we are square".
- **A one-handed user** scrolls two screens to the first field, and loses typed counts after a visit to the review.
- **A keyboard or screen-reader user** meets two regions both called "Confirmed counts", one of them out of date, and a verdict whose severity is in the words only.

### How the three requests connect

The numpad and the critique meet on the count-up screen. The numpad gives count-up a "Next player" key, removes the decimal key in a chips game, and removes the need to keep a bar above the phone's keyboard for count fields. The critique's first two issues are about the same bottom area of the same screen. Designing the dock, the numpad and the row together avoids building the numpad around a layout that then changes.

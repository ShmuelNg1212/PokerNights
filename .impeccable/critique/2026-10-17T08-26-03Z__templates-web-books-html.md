---
target: end-of-set screens when the books do not balance
total_score: 25
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 2
target_identity: "file:/Users/shm/PokerNights/templates/web/_books.html"
target_fingerprint: "sha256:358dfa41981779505821275fe97a744ae66018b39dd1d921cb8c5a0fc8b28be6"
target_path: /Users/shm/PokerNights/templates/web/_books.html
timestamp: 2026-10-17T08-26-03Z
slug: templates-web-books-html
---
# When the books do not balance: critique after the fixes (2026-10-17)

Method: dual-agent (A: design review · B: detector and browser). Branch feat/books-off.

| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility | 3 | "Counting up" badge and green marks under a red panel |
| 2 | Real world | 3 | "override from Miguel" does not say what Miguel did |
| 3 | Control | 3 | Fix is reverse then re-enter in a sheet |
| 4 | Consistency | 2 | Desktop running total still "₱150 extra." with the old equation |
| 5 | Error prevention | 2 | Suspect mark ignores the gap's direction (count_gaps) |
| 6 | Recognition | 3 | In · out · net on rows |
| 7 | Efficiency | 2 | One jump target, no ranking |
| 8 | Minimalist | 2 | ₱900 three times in a row; override sentence three times |
| 9 | Recovery | 2 | Says the size, not which record |
| 10 | Help | 3 | "Where to look" closed by default |
| Total | | 25/40 | Acceptable |

Detector: templates 4 false positives (no stylesheet); app.css 190 advisory, pre-existing drift; live overlay 3–5 per page, false positives or page decoration. Contrast 7.3–13.6:1; no target under 44px; panel 143px at 390; no overflow.

## Priority issues
- [P1] Suspect mark ignores direction and size; the button can lead away from the fix. Mark only same-sign rows, rank full explanations first, else open "Where to look".
- [P1] Desktop running total keeps "extra" and the old equation (status_text, counts.js).
- [P2] Players get the host's coral alarm; give them a smaller Brass line.
- [P2] The override is stated four times; one sentence with the note.
- [P3] At 320 the host bar cuts the first row.

## Minor
Badge stays "Counting up"; timer in the money block; ring over dividers; repeated "₱900"; 320 wrap of "in · out — Even"; role="alert" inside the polled region (pre-existing).

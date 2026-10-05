---
target: count-up to finalize flow
total_score: 32
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 0
target_identity: "file:/Users/shm/PokerNights/templates/web/_count_up.html"
target_fingerprint: "sha256:2219e0c16450f1dbc566ca97f5f3cfd93ad301bbc21c82663ae5a1853f0d45f4"
target_path: /Users/shm/PokerNights/templates/web/_count_up.html
timestamp: 2026-10-05T13-47-15Z
slug: templates-web-count-up-html
---
Method: dual-agent (A: /root/design_review · B: /root/detector_review)

## Count-up to finalize: repeat critique

Mode: Operate. Visual authority: The Rack in DESIGN.md. Assessed the approved host gaps, numpad and count-up implementation on 2026-10-05, Asia/Manila.

| # | Heuristic | Score | Evidence or remaining issue |
|---|---|---:|---|
| 1 | Visibility of system status | 3 | One persistent total, coverage and Preview label; row status distinguishes counted from cashed out. |
| 2 | Match with the real world | 4 | Players first, explicit zero, native units and cash-out separate from payment. |
| 3 | User control and freedom | 3 | Back, resume, correction and cancellable Finalize; no reopening after freezing. |
| 4 | Consistency and standards | 4 | Shared player tokens, figures, surfaces and actions. |
| 5 | Error prevention | 3 | Constrained keys, invalid-count blocking, review verdict and Finalize confirmation; warned short cash-outs remain permitted. |
| 6 | Recognition rather than recall | 3 | Names, bought-in figures, saved counts and cash-outs visible; recount requires returning to the set. |
| 7 | Flexibility and efficiency | 3 | Batch counts and cash-outs; Next through number fields. |
| 8 | Aesthetic and minimalist design | 3 | Focused phone flow; desktop repeats reference money facts. |
| 9 | Error recovery | 3 | Exact shortage, likely causes, reversals and override; review recovery link could be closer. |
| 10 | Help and documentation | 3 | Contextual guidance; the empty-field instruction needed to distinguish saved counts. |
| | **Total** | **32/40** | **Good; no observed P0 or P1 issue.** |

### Specificity and strengths

The player-first composition, bought-in figure beside each count, running equation and separation of set results from session payment make this a home poker bank, not an interchangeable dashboard. Warm dark rails and chip identities support the dim-room brief.

- The number panel names the player, repeats the total and offers Next and Done. The active field stays clear of it.
- Review places the consequence beside the action: books balance, exact shortage, or players still to count.
- Finalize restates the books and permanence, takes focus on Not yet, and ends with a visible in/out proof and a route to the session.

### Priority issues

1. **P2: empty-field help.** The earlier instruction said every blank stays Awaiting count, but a blank with `data-saved` retains its confirmed count. Corrected during verification to: "Leave an uncounted player blank. A saved count stays until you replace it." The original 32/40 score is retained; it is not rescored after the wording fix.
2. **P2: desktop repetition.** Host controls, Set totals and Balance check repeat money facts. A later layout cycle could make reference figures quieter while preserving the running equation.
3. **P2: recount entry point.** A short review recommends recounting, but Back to set is at the top. A nearby Back to counts link would make recovery easier. The warned recording path remains intentional.

### Cognitive load and emotional journey

The phone has one entry task, one running total and one main next action. Secondary controls stay behind a disclosure. No consequential decision observed had more than four choices; keypad digits are a familiar input pattern. Desktop duplication is the main attention cost. At 320×640, wrapped rows and the panel leave one complete player row visible; Next makes sequential work possible.

Unfinished counting stays neutral. Exact mismatches identify a problem with recovery guidance. Review predicts the result before commitment. Finalize gives reassurance and an honest permanence warning. The final proof gives a calm ending.

### Persona red flags and minor observations

- A first-time host needed accurate guidance about blanks and saved counts; the wording is corrected.
- A distracted host on a narrow phone depends on Next to reduce repeated scrolling.
- Explicit labels and verdict words support accessibility. Rejected keys have a visual refusal/nudge but no explanatory live announcement; no screen-reader failure was verified.
- Repeated Details controls add row height. Final proof repeats in a totals list, which is less costly on a reading screen.
- Real iPhone keyboard behavior and Safari rendering remain unverified.

### Independent detector and browser evidence

Assessment B scanned six markup targets once: `_count_up.html`, `_players_count.html`, `_host_controls.html`, `_final_set.html`, `_results.html`, and `ledger/cash_out_counted.html`. Six `design-system-color` advisories at line 0 report default black on standalone fragments. Rendered pages load the base stylesheet and inherit Bone text; these are false positives.

Independent CDP measurements across seven routes at 320, 390 and 1280px gave 21 captures without horizontal overflow. Visible main controls and count fields were at least 48px high. Headings followed H1 to H2, with the desktop Confirmed counts H3 under Host controls H2.

A temporary detector overlay ran on four pages, reporting 12, 5, 5 and 3 signals. Low contrast locations were not resolved to exact source elements, so they do not establish a WCAG failure. Border/shadow, chip/felt gradients, shared stylesheet animation and review type-ratio warnings are advisory signals, not verified defects in this flow. Behavioral contrast, touch, reduced motion and update checks are recorded separately in the plan.

Assessment A read source and independently inspected live count, discrepancy, override, empty and confirmation states, plus current review/final captures. Assessment B did not see A's findings; the parent received B after A finished. B did not emulate touch and did not observe final results; the parent browser checks cover both. Shared synthetic fixtures changed during behavioral tests; B's state captures are observations, not invariant baselines.

### Questions for a later cycle

Which desktop money facts must stay visible during counting? Can review recovery begin beside the warning? Can rejected-key feedback explain the reason to assistive technology?

Questions skipped: this is the acceptance critique inside an already approved implementation cycle; these P2 refinements do not require a new decision to finish it.

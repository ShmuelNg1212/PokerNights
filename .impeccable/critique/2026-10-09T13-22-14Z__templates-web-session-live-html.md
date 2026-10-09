---
target: the set page while a set is prepared and in play
total_score: 28
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 4
target_identity: "file:/Users/shm/PokerNights/templates/web/_session_live.html"
target_fingerprint: "sha256:d2a676054c60a03c6bc9e90b5cb45103c1f5d2be3f4247c88a0e3eff40042d19"
target_path: /Users/shm/PokerNights/templates/web/_session_live.html
timestamp: 2026-10-09T13-22-14Z
slug: templates-web-session-live-html
---
# Critique: the set page while a set is prepared and in play (2026-10-09)

Assessed from ten captures (320, 390 and 1280px; host and player; draft, open, in play) and the source.

## Heuristics: 28 of 40

| # | Heuristic | Score | Reason |
|---|---|---|---|
| 1 | System status | 3 | Badge, Live dot and Done/Next marks are clear. |
| 2 | Real-world match | 3 | Table words. The stakes step is ticked before the host chose a rake rule. |
| 3 | Control and freedom | 3 | Reversal with a reason; Back to draft. |
| 4 | Consistency | 3 | Felt ink on a rail panel; ragged amount column. |
| 5 | Error prevention | 2 | Rake locks at the first buy-in, yet its step is pre-ticked and muted. |
| 6 | Recognition | 2 | On a phone, Cash out is behind a small chevron. |
| 7 | Efficiency | 3 | One-tap Rebuy, folded dock, six rows on the first screen. |
| 8 | Minimalist design | 3 | The 320px pot wraps; the open set is mostly checklist. |
| 9 | Error recovery | 3 | Judged from source; no refusal was captured. |
| 10 | Help | 3 | Step lines work as inline help. |

## Specific or generic

In play it is specific: felt, the compressed pot, chip tokens, buy-in edges. Preparing is a plain checklist that another product could use.

## Priority issues

1. P1 The pot breaks across two lines at 320px. **Fixed:** one line, smaller at under 360px and for long figures.
2. P1 Cash out is hard to discover on a phone. **Fixed in part:** hosts read "Tap a player to cash out or correct an entry." under the list. The chevron stays beside the name.
3. P1 No primary action in the draft's checklist. **Not a fault:** the capture had the menu folded by an earlier step; a draft shows the menu with Add players as its main button.
4. P1 The rake step is pre-ticked. **Fixed in part:** its button reads "Choose rake" until a rule is chosen. The step stays ticked, because defaults are valid stakes.
5. P2 An open set shows no whole player row at 390px. **Fixed:** finished steps of an open set take one line.
6. P2 The start step speaks of buy-ins while the option is in the menu. **Fixed:** the step says only that the timer starts.
7. P2 Felt-coloured hint on the rail in a player's open set. **Fixed.**
8. P3 Amounts are ragged on rows without a button; open Details leaves a lone toggle line; the draft's empty state has no action. **Open.**

## Detector

Four advisory findings, all false: "rgb(0, 0, 0) outside DESIGN.md" on four templates, which carry no colour. No other finding.

## Keep

The 220px felt panel; the 65px row with one Rebuy button; a player's own row first; marks in bone, brass and rule only; money shown only when there is money.

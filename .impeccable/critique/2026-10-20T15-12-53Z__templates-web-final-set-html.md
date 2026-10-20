---
target_identity: "file:/Users/shm/PokerNights/templates/web/_final_set.html"
target_fingerprint: "sha256:259931e353c5b74fe1089a678e0a6a69536720f6f226f3fa2fd10435a2f81592"
target_path: /Users/shm/PokerNights/templates/web/_final_set.html
timestamp: 2026-10-20T15-12-53Z
slug: templates-web-final-set-html
---
⚠️ DEGRADED: single-context (AGENTS.md allows subagents only during execute; this ran at rendezvous)

Target: templates/web/_final_set.html, with _next_step.html, _results.html, night.html (open), cash_out_counted.html, _books.html, _host_controls.html.

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Proof line and verdict lead; the "Set 1 is final." toast floats over the second result row on a phone (existing toast behaviour). |
| 2 | Match System / Real World | 4 | "Play set 2" and "Settle up" are the host's own words. |
| 3 | User Control and Freedom | 3 | Settle-up asks once with Not yet; Play set N has no confirm by decision (an empty set can be cancelled). |
| 4 | Consistency and Standards | 3 | The two-up choice is a new pattern; the settle sheet reuses the reopen/finalize sheet. |
| 5 | Error Prevention | 3 | Close is behind a sheet with focus on Not yet; a blocked settle-up names the set to finish. |
| 6 | Recognition Rather Than Recall | 4 | Both next steps are visible together; no page in between. |
| 7 | Flexibility and Efficiency | 3 | One tap to the next set. |
| 8 | Aesthetic and Minimalist Design | 3 | Fixed in this run: Reopen set sat directly under the choices on a phone and competed with them. |
| 9 | Error Recovery | 3 | Reopen set and reopen session remain. |
| 10 | Help and Documentation | 3 | The settle sheet states the three consequences. |
| **Total** | | **32/40** | Good |

## Design Specificity Verdict

LLM: grounded in the product. The proof line (players · in · out) and the two equal choices are specific to a home-game bank; nothing is generic decoration. Detector: 8 advisories, all `design-system-color` rgb(0,0,0); false positives because the detector renders bare templates without app.css. Browser captures at 390 and 1280 px show Bone on Ground and no horizontal overflow.

## Priority issues

1. [P2] Reopen set competed with the choice on a phone. Fixed: below 900 px "Found a mistake?" follows the results.
2. [P3] Card line broke as "new / buy-ins." Fixed: text-wrap balance.
3. [P3] The finalize toast covers a result row for 6 s on a phone. Existing behaviour; not changed here.

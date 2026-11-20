# 0016: Count-up without a cash-out step

Date: 2026-11-20. Status: accepted. Plan: [count-up without a cash-out step](../plan/1795155860_count_up_without_cash_out.md). Study: [count-up without a cash-out step](../study/1795155860_count_up_without_cash_out.md).

## Context

Before this decision, count-up had two steps for each player. The host confirmed a count, then recorded a batch of cash-outs from the confirmed counts on a separate review page. The batch step moved no money and told nobody anything new: payments come at settle-up. But the books-off search and the override needed it, because both required every player to have a final cash-out (`Balance.counted`).

## Decision

- Count-up asks for counts and a confirmation only. The host interface has no batch cash-out and no per-player cash-out during count-up. A cash-out recorded during play stays and needs no count.
- One finishing action, `settlement.services.finish_set`, records the final cash-outs from the reviewed counts and freezes the results in one transaction. Any refusal records nothing.
- A set can finish when every player with money has a confirmed count or a final cash-out, and the counts plus earlier cash-outs, rake and active overrides equal the buy-ins (`ledger.queries.finishes_the_set`). The review page discloses an active override.
- When every count is in and the counts do not add up (`ledger.queries.counts_off`), the host can finish with an override. `finish_set` then voids any active override, records the new one from the full gap, writes the cash-outs and finalizes, in one transaction. One override explains one gap.
- The review page (`cash_out_counted`) records nothing. It answers GET only and opens only when the set can finish.

## Consequences

- The ledger model does not change: a finalized set still has one final cash-out per player with money, and earlier sets stay valid.
- `ledger.services.cash_out_counted` remains, as an internal step of `finish_set`.
- Finalize results stays for a set whose players were all cashed out during play.
- The books-off rows that compare a typed cash-out with its count apply only to sets cashed out during play or before this decision.

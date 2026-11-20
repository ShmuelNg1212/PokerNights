# Study: count-up without a cash-out step

Date: 2026-11-20. Mode: mixed.

## Request

The human: "Cashing out during the count-up screens does not have a use. Fix the animations and the UI to include only inputting counts and confirming them. Cashing out is done at later steps."

## Current flow (main 8a7d22b)

1. Play ends. The set goes to `reconciliation` (count-up).
2. The host types counts and taps **Confirm counts**. Each player becomes `ready` ("Ready to cash out").
3. The dock shows **Cash out counted players (N)**. It opens `cash_out_counted` ([ledger/views.py:208](../../ledger/views.py)). That page records one `CashOut` per confirmed count (`ledger.services.cash_out_counted`). Each player becomes `cashed_out`.
4. When every count is in and the counts balance, the dock shows **Review and finish** instead. It posts to `session_finish`, which runs `settlement.services.finish_set`: the batch cash-out and finalize in one transaction.
5. If the books are off, the host must cash everyone out first. Only then does `Balance.counted` become true. Then the dock shows **Find the ₱X difference**, the rows show in / out / net, and **Finalize with an override** becomes available (`record_override` refuses unless `balance.counted`).

## What the human sees in step 3

- A status word per row: "Ready to cash out", then "Cashed out".
- Pips: half filled at `ready`, full green at `cashed_out` (`static/css/app.css:1757-1758`, `pip-fill` animation at 1857).
- Progress line: "N of M players counted or cashed out".
- A second page and a second confirmation that changes nothing a person cares about. The cash-out rows are bookkeeping; payment comes at settle-up.

## What the batch step still does

- It is the only way to reach the books-off state (`Balance.counted`). The gap search and the override depend on it.
- It lets a host freeze some counts before others are in. Confirmed counts already stay until replaced, so this has no use.

## What must stay

- A cash-out recorded during play (a player leaves early) is real. That row keeps "Cashed out ₱X" and needs no count.
- The ledger model is unchanged: finalize still needs one final `CashOut` per player with money. The finish action writes them from the confirmed counts, as `finish_set` does now.
- Sets already cashed out in batches stay valid. Reopen still works.

## Conclusion

Remove the batch step from the UI. Treat a confirmed count as the end of a player's count-up. Move the books-off search and the override onto confirmed counts, so the host reaches them without a cash-out. Write the cash-outs inside the one finishing action, with or without an override.

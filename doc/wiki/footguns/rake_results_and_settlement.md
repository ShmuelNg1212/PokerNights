# After-rake results and settlement balances follow the group's rake rule

- **Trigger:** A set deducts rake from gross buy-ins.
- **Observed behavior:** Two players buying in ₱1,000 at 5% and cashing out ₱950 each have results of −₱50 each. Player results sum to −₱100. What settle-up does with that depends on the group's rake rule (ADR 0007):
  - "In cash at buy-in" (default): no further payment is owed. Each player's settle-up balance is `net + rake_total`.
  - "At settle-up, into the rake fund": each player pays ₱50 to the Rake fund. Each balance is `net`, and the fund is one more party with the session's rake.
- **Impact:** Passing player nets to the zero-sum transfer algorithm without the fund refuses closure. Returning the fee under the fund rule makes settle-up differ from the standings.
- **Evidence:** `ledger/tests/test_rake.py` (returned rule) and `settlement/tests/test_rake_fund.py` (fund rule, the database constraint, carry exclusion, the page).
- **Remedy:** Keep `PlayerResult.net = cash_out − gross buy-ins` for display and statistics. Use `settlement.services.settlement_balances(night, to_fund=…)` only for transfers. A closed session reads its own rule from `SettlementPlan.rake_to_fund`, not the group's current rule. A transfer into the fund has no payee: name it with `payee_label` or `payee_party`, never `payee.display_name`. Payment marks and Undo do not alter the rake totals.

Once fee records exist, retain rake columns and conservation. Disable new configuration and use a forward fix instead of dropping records or reverting to the old no-rake constraint.

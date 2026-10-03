# Balance overrides are stored in chips, not pesos

- **Trigger:** Reading or changing `BalanceAdjustment`, or adding statistics on overrides.
- **Observed behavior:** The plan described the override as an amount in centavos. The code stores `chips_delta`.
- **Impact:** Code that expects centavos reads a chip count as money.
- **Evidence:** With a chip rate such as ₱1,000 for 30,000 chips, a chip is worth a fraction of a centavo. A difference of an odd number of chips has no exact centavo value. An override in chips makes the adjusted chips equal the chips issued, so `money.allocate()` still gives values that sum to the total bought in.
- **Remedy:** Add `chips_delta` to the player's cashed-out chips, then convert once with `money.allocate()`. Do not convert an adjustment to pesos by itself, except for display with `money.value_floor()`.

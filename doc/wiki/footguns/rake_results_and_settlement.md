# After-rake results differ from remaining settlement balances

- **Trigger:** A set deducts rake from gross buy-ins, with the fee already collected separately.
- **Observed behavior:** Two players buying in ₱1,000 at 5% and cashing out ₱950 each have results of −₱50 each, but no further payment is owed. Player results sum to −₱100 while the rake account gains ₱100.
- **Impact:** Passing actual player nets directly to the zero-sum transfer algorithm refuses closure, or collecting the rake again overcharges players.
- **Evidence:** `ledger/tests/test_rake.py` checks equal fee-only losses and mixed rake/Off sessions. `web/tests/browser/rake.mjs` and `rake_extra.mjs` verify native finalization and closure without a second charge.
- **Remedy:** Keep displayed/statistical `PlayerResult.net = cash_out − gross buy-ins`. Use `settlement.services.settlement_balances()` (`net + rake_total`) only for remaining player transfers. Enforce `player nets + rake = 0` and `cash-outs + overrides + rake = gross`. The group account is not a Member or payee. Payment marks and Undo do not alter the rake pool.

Once fee records exist, retain rake columns and conservation. Disable new configuration and use a forward fix instead of dropping records or reverting to the old no-rake constraint.

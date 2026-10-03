# A partial unique constraint cannot be deferred

- **Trigger:** A `UniqueConstraint` with a `condition`, for example "one active payment per transfer" or "one current result per participant", and code that changes two rows in one transaction so that they are briefly both active.
- **Observed behavior:** Django does not allow `deferrable` together with `condition`. The database checks the constraint after each statement.
- **Impact:** An in-place swap fails with `IntegrityError` in the middle of the transaction.
- **Evidence:** Django model constraint rules; found during the design study (study §15).
- **Remedy:** Deactivate the old row first, then insert or activate the new one. `ledger.services.write_results()` and `settlement.services.mark_unpaid()` follow this order. The seating stage must do the same for seat swaps.

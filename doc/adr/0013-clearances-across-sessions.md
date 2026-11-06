# 0013: Clear the net debt between two players across sessions

Date: 2026-11-06. Status: accepted. Plan: [debts across sessions](../plan/1793948627_debts_across_sessions.md). The human approved this plan on 2026-11-06.

A player can owe another player money from several closed sessions. Some transfers can point each way. The group shows the net for each pair and unit. A host sees all pairs. A player sees only their own pairs. Pesos and chips stay separate. Rake fund transfers stay separate from player pairs.

One `Clearance` records the net amount that the pair settled. It links to each original transfer through `ClearedTransfer`. The net can be zero. A host or the receiver confirms a nonzero net. Either player or a host can clear a zero net. A host or the recorder can undo it. Undo keeps the clearance, deactivates its links, and adds one `ClearanceReversal` with a reason. The original transfers do not change.

We chose this record over a `Payment` for each transfer. For example, Ana owes Ben ₱600 and Ben owes Ana ₱400. They settle ₱200. Recording both gross transfers as payments would claim that ₱1,000 moved. Putting the net payment on one session would assign it there by chance. A clearance states the net and keeps the source of each debt.

[ADR 0002](0002-payments-at-the-table.md) still applies. A `Payment` belongs to one session. A clearance does not replace table payments or change any result. A cleared transfer is done. It cannot be paid or carried. Its session cannot reopen until the clearance is undone.

The service locks the group before it checks current access. It then locks the affected sessions in id order. It reads the unpaid transfers again and compares their ids and net with the confirmation. A changed list refuses the whole action. A unique group request id makes retries safe. The undo identity and one-to-one reversal make repeated undo safe. Each action records one audit event and raises the affected set versions.

`DEBTS_VIEW` is off by default. While off, it hides the new balances, refuses clearance writes and keeps paid marks host only. Existing clearances still count as done. Enabling the switch is a separate release decision.

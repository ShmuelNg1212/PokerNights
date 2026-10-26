# Study: payments recorded before a session closes

Date: 2026-10-26. Mode: mixed.

## The need

A player leaves early. Someone at the table pays that player in cash before they go, or the player pays before they go. Today the app cannot record this. When the host closes the session, the transfer list assumes that no money moved. So the list tells someone to pay again. The host must remember the cash and fix it by hand with **Mark paid**, which works only if the list happens to contain that exact transfer.

The roadmap lists this item under stage 2: "payments recorded before finalization (early leavers)". `spec.md` lists it under "High-value additions".

## What exists

- `settlement.models.Payment` already has `night`, an optional `transfer`, optional `payer` and `payee`, `amount`, `active`, `request_id` and `recorded_by`. A payment with no transfer is legal in the schema. No code writes one yet.
- `PaymentReversal` already voids a payment with a reason. Rule 4 (append-only) holds.
- `settlement.algorithm.balances(nets, payments)` already folds earlier payments into the balances. Its tests cover an early leaver who paid on the way out, a part payment and an overpayment that flows back (`settlement/tests/test_algorithm.py`).
- `close_night()` does not call `balances()`. It settles `settlement_balances(night)` plus carried transfers.
- `ledger.services.record_cash_out(..., left=True)` marks a player as gone for the night. At that moment the app knows that player's figure for the set: cash-out minus buy-ins.
- The architecture study chose direct settlement (option D) and noted: "Early leavers need a recorded payment or must wait." Its permission table lets the host record or reverse a payment in every state from scheduled to finalized.

## Who reads payment rows today

| Reader | Effect of a payment with no transfer |
|---|---|
| `queries.py:60` paid-transfer subquery | Filters `transfer__isnull=False`. No effect |
| `queries.py:278` session outcome `payments` | Lists every payment of the night under "Payment records". The new rows show there. Good, but the wording must fit |
| `queries.py:283` paid map | Filters `transfer_id is not None`. No effect |
| `reopen_night()` paid check | Counts payments on the current plan only. A table payment does not block a reopen. This is correct: closing again re-reads the same payments |
| `night_stamp()` / `stamp_from()` | Counts payments only while a current plan exists. **A new table payment would not change the stamp, so other phones would not see it.** Must change |
| `hub_stamp()` | Counts all payments of the group. Changes. Good |
| `has_money` check (`queries.py:648`) | A table payment makes the session count as having money, so it can be archived but not deleted. Correct |
| Sessions tab, profile, stats | Read transfers and results, not payments. Results are play, not payments, so they must not change |

## Domain facts

1. A table payment is money that moved between two players of one session, before it closed. It belongs to the session (rule 10), not to a set.
2. It does not change any result. Results describe play. It changes only what is still owed.
3. At close, the balances are: results + rake add-back + carried transfers, then each active table payment (payer is owed more, payee is owed less). The transfer list settles what remains. The sum stays zero, because each payment adds and subtracts the same amount.
4. After close, a table payment is part of the list's history. It cannot change unless the session is reopened.
5. The amount is the host's word. The app can suggest the leaver's figure, but the real cash may differ (rounding, a part payment, a debt from another night). An overpayment is legal: the algorithm sends the difference back.

## Options

### A. Free payment form on the session page (REC)

The host picks a payer, a payee and an amount, all from the session's players. One service, `record_table_payment()`, and one reversal, `reverse_table_payment()`. `close_night()` folds active table payments into the balances.

- Pros: one place, any case (early leaver, part payment, a player who pays the host for a rebuy). Uses the existing schema. No migration, except possibly a constraint (see below).
- Cons: the host must choose two names and type an amount.

### B. "Paid out at the table" on the leave action in the set

When the host records a leaving cash-out, offer "Who paid them?" with the figure prefilled.

- Pros: fastest at the moment it happens.
- Cons: the leaver's session figure is not final until every set is finalized. The cash-out sheet is already busy. Couples the ledger app to settlement, against the one-way dependency rule (`ledger → settlement`), unless the web layer joins them.

### C. Both: A as the record, B as a shortcut that opens A prefilled

The set page shows a link "Record a payment at the table" next to a player who left. It opens A with the leaver and their figure filled in.

**REC: build A first. Add the shortcut from B as a link only (option C), with the payee or payer set from the sign of the leaver's figure so far.** The link lives in `web`, so no app depends the wrong way.

## Database

- Today `transfer` null means "table payment". That is implicit. A check constraint can make it explicit: a payment with no transfer needs both `payer` and `payee`, and `payer` ≠ `payee`. The banker (later) would loosen this with its own field. One migration, additive, safe on existing rows (no row has a null transfer today; verify on production data before release).
- No new model.

## Rules to carry

- Host only, in the service (rule 5).
- Session open only. After close, use **Mark paid**.
- Both players must have a participant row in a set of this session.
- Amount > 0, integer, in the session's unit (rule 1). A chips game records chips.
- `request_id` per write (rule 3). `audit.record()` per write (rule 6). Bump each set's `version` so open set pages refresh, as `close_night()` does.
- Reverse with a reason, session open only.
- Close: fold active table payments, assert the sum is zero, then settle.

## Risks

- **Double counting.** If the host records a table payment and also marks the resulting transfer paid, nothing is double counted: the transfer was already reduced. The risk is the opposite: a host who forgets the table payment exists. The closed page must show table payments next to the list, and "How this is worked out" must stop saying "assumes no earlier player payments".
- **Reopen.** A reopened session keeps its table payments. Closing again re-reads them. Correct by construction.
- **Stamp.** Must change, or phones go stale (see the table above).
- **Carry.** A carried earlier transfer and a table payment can both move one player's balance. The algorithm adds them in order; the sum stays zero. Needs one test.

## Design questions for the shape pass

- Where the form opens: a sheet from the session page, like other action sheets.
- How a recorded table payment shows before close ("Paid at the table" list) and after close (in the list's explanation, and in Payment records).
- What a player sees: their own table payment, and the change to "Your result so far" wording ("Still owed").

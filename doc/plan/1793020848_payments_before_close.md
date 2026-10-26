# Plan: payments recorded before a session closes

Study: [1793020815_payments_before_close.md](../study/1793020815_payments_before_close.md). Mode: mixed. Branch: `feat/payments-before-close`, from `main` (nothing is unreleased).

## Goal

The host records money that moved at the table while the session is open. Closing the session subtracts it, so nobody is told to pay twice. Results do not change.

## OPEN QUESTIONS

1. **Who may record?** REC: the host only, like **Mark paid**. Alternative: the two players named in it may also record it.
2. **Which form?** REC: option C. A free form on the session page (payer, payee, amount), and a link "Paid at the table?" beside a player who left a set, which opens the form prefilled. Alternative: the session-page form only.
3. **Prefill.** REC: the link prefills the leaver's figure in that set (cash-out minus buy-ins) and sets the leaver as payee when it is positive, payer when it is negative. The other player stays empty for the host to choose. Alternative: no prefill.
4. **Who can be a party?** REC: any player with a seat in a set of this session. Not the host as a "bank": the banker is a later item.
5. **What a player sees.** REC: every member sees the table payments on the session page, the same as Payment records today. A player's own payment also shows under "Your result so far" as "Paid at the table: ₱X to Ana".
6. **Spec change.** This changes settlement logic, so `spec.md` and an ADR change after approval. REC wording for spec section 3: "Before a session closes, the host can record a payment made at the table. Closing subtracts it from what is still owed. Results do not change."

## Tasks

### Technical

- [ ] **T1. Model constraint.** Add a check constraint: a payment with no transfer has a payer and a payee, and they differ. One migration. Check that no production row has a null transfer before release.
  - Done when: the migration applies on SQLite and PostgreSQL, and a test shows the database refuses a half-filled table payment.
- [ ] **T2. Services.** In `settlement/services.py` add `record_table_payment(night_id, actor, payer_id, payee_id, amount, request_id)` and `reverse_table_payment(night_id, actor, payment_id, reason)`.
  - Acceptance: host only; session open only; both are players of the session; amount is a positive integer; a repeated `request_id` returns the same row; reversal needs a reason and writes a `PaymentReversal`; each write calls `audit.record()` and bumps every set's `version`.
  - Done when: tests cover each rule and the repeated tap.
- [ ] **T3. Close folds payments in.** `close_night()` passes active table payments to `algorithm.balances()` after the carried transfers, asserts the sum is zero, then settles.
  - Acceptance: an early leaver paid in full has no transfer; a part payment leaves the rest; an overpayment flows back; a reversed payment counts for nothing; a carried transfer and a table payment together still clear; results and stats are unchanged; reopen and close again gives the same list.
  - Done when: these are tests in `settlement/tests/test_table_payments.py`, and they pass on SQLite and PostgreSQL.
- [ ] **T4. Queries and stamp.** The session outcome lists table payments apart from paid marks. `night_stamp()` and `stamp_from()` count payments while the session is open too.
  - Done when: a test shows a new table payment changes the stamp of an open session, and the stamp of a session with no payments is unchanged.
- [ ] **T5. Views and URLs.** `table_payment` (GET form, POST record) and `table_payment_undo` (POST with reason) in `web`. Membership resolution and 404 on a miss (rule 5).
  - Done when: view tests cover host, player (refused), other group (404), closed session (refused with a message).

### Design (after `/impeccable shape payments before close`)

- [ ] **D1. Shape brief.** Run the shape pass. Fold its decisions into D2–D4 before building.
- [ ] **D2. Record sheet.** A sheet from the session page: payer, arrow, payee, amount on the existing numpad, one primary button. 48 px targets; one column on a phone.
  - Done when: it works with JavaScript off (plain form page) and on (sheet).
- [ ] **D3. "Paid at the table" list** on the open session page, under the results. Each row: payer → payee, amount, time, who recorded it, **Undo** for the host.
- [ ] **D4. Closed page.** "How this is worked out" names the table payments instead of "assumes no earlier player payments". Payment records label each row "At the table" or "Marked paid".
- [ ] **D5. Leaver link** (if Q2 is accepted). On the set page, beside a player who left: "Paid at the table?" opens D2 prefilled.

### Rendezvous

- [ ] Full suite on SQLite and PostgreSQL.
- [ ] `code-review`, `verification-before-completion`, `security-review` (money changes).
- [ ] `/impeccable critique`, `audit`, then `polish`; `break-ui` with long names and a 7-digit amount.
- [ ] Phone checks added to TODO.md.

### Sync docs

- [ ] `spec.md` section 3 and "High-value additions"; ADR for table payments; `features.md`; a footgun on the stamp counting payments only after close, if it still applies anywhere; roadmap stage 2 row.

## Completion criterion

On a phone, the host records a table payment for an early leaver, closes the session, and the transfer list does not ask anyone to pay that amount again. Every check above is ticked.

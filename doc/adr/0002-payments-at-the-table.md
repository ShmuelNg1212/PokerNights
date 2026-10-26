# 0002: Payments at the table

Date: 2026-10-26. Status: accepted. Plan: [payments before close](../plan/1793020848_payments_before_close.md).

## Context

A player who leaves early is often paid in cash at the table, or pays before going. Before this decision, closing a session assumed that no money had moved. The transfer list then told someone to pay again.

## Decision

While a session is open, the host records a table payment: a payer, a payee and an amount, both players of the session. Closing the session subtracts each standing table payment from the balances before it works out who pays whom. A table payment never changes a result. Only the host records or undoes one, and only while the session is open.

## Reasons

- Results describe play. A payment is money that moved, not play, so stats and results stay as they are.
- The settle-up formula already accepts earlier payments (`settlement.algorithm.balances`), so the list stays minimal and sums to zero.
- The amount is the host's word. The real cash can differ from the leaver's figure. An overpayment flows back in the list.

## Consequences

- A table payment is a `Payment` with no transfer. The database requires both players on such a row.
- Reopening a session keeps its table payments. Closing again uses them again.
- The banker (a later item) is a different party and needs its own rule.

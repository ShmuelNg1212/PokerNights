# 0010: A balanced set finishes in one action

Date: 2026-10-31. Status: accepted. Plan: [UI revamp](../plan/1793431937_ui_revamp.md), slice C.

## Context

With the counts confirmed and the books balanced, a host tapped Cash out counted players, Cash out N players, Finalize results and Finalize set N. Three of these confirmed a fact that the screen already stated. The human chose one review page with one button.

## Decision

- **Finish set.** When recording every confirmed count leaves nobody to count and the books balanced (`ledger.queries.finishes_the_set`), the review's one button is Finish set N. The set page's button says Review and finish.
- **One transaction.** `settlement.services.finish_set` locks the session row first, then runs `ledger.cash_out_counted` and `finalize` in one transaction. It adds no rule. A count that changed since the review, or books that do not balance, refuse the action, and nothing is recorded.
- **The records stay the same.** One `CashOutBatch`, one final `CashOut` per player and one `Finalization`, with the same audit events as the two steps. The review is the confirmation, so no sheet asks again.
- **A repeated request** changes nothing: the batch's `request_id` marks it as done. It returns the results, or says the review was already used once the set was reopened.
- **Another host's finish.** A different request on a set that is already final is refused with "already final". It does not count as a repeat, because that host reviewed other counts.
- **Other paths stay.** A set that does not balance, or has players still to count, keeps Cash out N players. A set whose players are all cashed out keeps Finalize results and its sheet. An override stays on that path, because the Finalize sheet discloses it. `finish_set` refuses an override from a page that was drawn before it.

## Consequences

`settlement` calls `ledger`, as dependencies require, so the review's template posts to a `settlement` URL. A refusal redirects to a fresh review with the refusal as a message. The review page's older POST still records a batch without finalizing, so a page that was open during a release keeps working.

Finalizing no longer always asks in a sheet. This revises the rule in spec.md that finalizing a set asks for confirmation once: the review page now is that one confirmation.

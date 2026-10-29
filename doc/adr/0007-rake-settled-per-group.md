# 0007: Each group chooses how settle-up treats rake

Date: 2026-10-30. Status: accepted. Plan: [table rake and multi-host live screens](../plan/1793299490_table_rake_and_multi_host_live.md).

## Context

Rake is taken from each gross buy-in. A player's result (`net`) includes their fee as a loss, so player results sum to minus the collected rake. Settle-up must sum to zero. Until now settle-up gave each player back their own fee (`net + rake_total`): the model was that each player paid their fee at buy-in. A group that treats the rake as the table's, not per player, saw settle-up figures that differ from the standings.

## Decision

- The group's rake account (`GroupRakeAccount`) holds the group's choice, `settlement`: `returned` (the earlier rule, the default) or `fund`.
- Under `fund`, each player settles their result as the standings show it. The **Rake fund** is one more party in settle-up, with the session's collected rake as its balance. It only receives.
- A transfer into the fund has no payee and `to_rake_fund` set. The database allows exactly one of the two. Its payment has no payee.
- Each settle-up list records the rule it used (`SettlementPlan.rake_to_fund`). A closed session keeps its list and its rule. The group's current rule applies at the next close, also after a reopen.
- A transfer into the fund is never carried into a later session. It stays open until a host marks it paid.
- Only a host changes the choice. A repeated choice writes nothing.

## Consequences

The fund is not a member. Pages that name a payee use `payee_label` or `payee_party`. Player results, statistics and the group's rake totals do not change. The app records who pays the fund; it does not say who holds the fund's money.

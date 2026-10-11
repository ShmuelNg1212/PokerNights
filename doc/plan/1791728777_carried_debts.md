# Unpaid transfers carried into a later session: plan

Status: awaiting approval. Date: 2026-10-11, Asia/Manila. Study: [Unpaid transfers carried into a later session](../study/1791728776_carried_debts.md).

## Outcome

When a host closes a session, unpaid transfers from earlier sessions between people who both played tonight can be folded into tonight's settle-up. The session then has one list of who pays whom that covers tonight and those debts. The old transfers say "Carried" and stop counting as unpaid.

One migration that adds one table. No existing row changes.

## Behaviour

| Moment | What happens |
|---|---|
| A session is ready to close and earlier unpaid transfers qualify | Above Close session: "Carry unpaid transfers from earlier sessions", each one listed with its session ("Ana pays Ben ₱500 · Garage table, Oct 4") and ticked. The host can untick any. With none that qualify, closing looks as it does today |
| Close session | Each person's balance is tonight's result plus what they are owed and minus what they owe in the ticked transfers. The fewest transfers that clear those balances are written, as today |
| The closed session's page | "Who pays whom" is the netted list. A line under it: "Includes 2 unpaid transfers from earlier sessions", which opens the list of them, each with a link to its session. "Your part" shows how your figure is made up: tonight's result, then each carried debt |
| The earlier session's page | The carried transfer's row says "Carried to Garage table, Oct 11" with a link, in place of the Paid button. The session counts as settled once every transfer is paid or carried, and its status says how many of each |
| Your groups | "You owe" and "you are owed" no longer count a carried transfer; the amount is inside the later session's transfers |
| Mark a carried transfer paid | Refused: "This transfer was carried into the session of Oct 11. Mark it paid there." |
| Reopen the later session | Its list is retired, as today, and every transfer it had carried is unpaid again. Closing it again asks again. Still refused while one of its transfers is marked paid |
| Reopen the earlier session while one of its transfers is carried | Refused: "A transfer of this session was carried into the session of Oct 11. Reopen that session first." |
| The later session's own transfers stay unpaid | They can be carried into the next session in the same way |
| A ticked transfer was paid or carried elsewhere before Close was tapped | Nothing is closed. The page says which transfer changed and shows the list again |
| Results, stats, the recap's ranking | Unchanged. They describe play |
| The recap and the share card | Their transfers are the netted list, with the line "Includes unpaid transfers from earlier sessions" |
| `CARRY_DEBTS=False` | Nothing is listed at close and the service ignores any ticked transfer. Transfers already carried stay carried |

## What qualifies

A transfer of the same group that is in its session's current list, not marked paid, not already carried, in a closed session that is not archived, in the same unit as tonight's session (pesos into pesos, chips into chips), and whose payer and payee both have a result in tonight's session.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **The new list can change who pays whom.** If Ana owed Ben ₱500 and tonight Ben lost ₱500 to Carlo, the list says Ana pays Carlo ₱500. This follows from "one netted list". Say if a carried debt must always stay between the same two people.
2. **A transfer is carried whole or not at all.** No partial amounts.
3. **An earlier session counts as settled when every transfer is paid or carried.** Its badge then reads "Settled", and the page says how many were carried.
4. **Order of reopening.** The later session first, then the earlier one. Recommended over undoing the carry silently, which would change a closed session's list without anyone asking.
5. **Any table of the same group.** A debt from the garage table can be carried into a session at the kitchen table.
6. **A switch, `CARRY_DEBTS`, on by default.**

## Implementation

Branch `feat/carried-debts` from `main`. Tests first.

1. **Model (`settlement`), one migration.** `CarriedTransfer`: the earlier transfer, the plan that took it over, who and when. Unique per transfer and plan. It is in force while that plan is its session's current one; nothing marks it ended.
2. **`settlement/queries.py`.**
   - `carryable(night)`: the transfers that qualify, oldest first.
   - "Carried" joins "paid" wherever unpaid is worked out: `unpaid_transfers`, `unpaid_in`, `settle_states` (new counts: carried, carried amount), the viewer's part, and the outcome a session page shows.
   - `stamp_from`, `night_stamp` and `hub_stamp` count carries in force, so open pages update when one is made or released.
3. **`settlement/services.py`.**
   - `close_night(night_id, actor, carry_ids=())`: locks tonight's session and the sessions of the ticked transfers in a fixed order, checks each transfer again, adds them to the balances, runs the existing netting and its two invariant checks, writes the plan, the transfers and the carry rows, and records each in the log of both sessions.
   - `mark_paid` refuses a carried transfer. `reopen_night` refuses while one of the session's transfers is carried by a current plan, and refuses as today while one of its own is paid.
4. **Views and templates.** The close form's list; the session page's "Includes…" line, the carried list and the make-up of "Your part"; the "Carried to…" row on the earlier session; the status wording; the recap and share line. In the built design, with no new colour or component.
5. **Tests.**
   - Service: balances with carries sum to zero and the list clears them; the worked cases (debts cancel to nothing; debt changes direction; three people); only ticked transfers are carried; every disqualifying case is refused (paid, carried already, other unit, other group, archived, open session, payer or payee absent tonight, retired list); a changed transfer refuses the whole close; a repeated close writes nothing twice; chain over three sessions; reopen later releases and unpaid totals return to the cent; reopen earlier is refused; mark paid on a carried transfer is refused; the switch.
   - Totals: for a group, the sum each person owes and is owed over all sessions is the same before and after a carry.
   - Pages: who sees what; the query budgets of the session page, Your groups and the polls.
   - Browser (`carried_debts.mjs`, new): close with two ticked and one unticked; the netted list and "Your part"; the earlier session updating by itself to "Carried"; Your groups' figures; reopen and release; 320, 390 and 1280px; no JavaScript. `night.mjs`, `settled.mjs`, `night_live.mjs`, `hub_live.mjs` and `reopen.mjs` rerun, and any failure is looked into, not assumed old.
   - Both suites: SQLite and PostgreSQL.
6. **Documents.** Wiki (features, architecture, deployment), PRODUCT.md, DESIGN.md addendum, browser README, TODO.md with the phone checklist.

## Out of scope

- Paying part of a transfer.
- Carrying between groups, or between pesos and chips.
- A running balance per person outside sessions.
- Carrying into a session that is already closed (reopen it and close it again).

## Acceptance

1. Closing a session with a ticked earlier transfer gives one list that clears tonight's results and that debt, and the earlier transfer reads "Carried" with a link.
2. No amount is counted twice: Your groups shows the same total owed before and after, when nothing else changed.
3. Reopening the later session makes the earlier transfer unpaid again.
4. Each refusal in the table above is refused with its sentence.
5. With nothing to carry, and with the switch off, closing is as it is today.
6. Both test suites pass.

## Release

Kept local on its branch until you say to push. One migration that adds one table. The first response to trouble is `CARRY_DEBTS=False`.

# Unpaid transfers carried into a later session: study

Date: 2026-10-11, Asia/Manila.

## Request

The human said: "Lets add the feature where debts are carried across sessions in case there are unpaid transfers."

SPEC.md lists it under Later: "IOUs and credit carried across sessions".

Asked three questions, the human chose:

- **When:** the host decides when closing a session. The unpaid transfers that qualify are listed, ticked by default; the host can untick any.
- **Whose:** a transfer is carried only when its payer and its payee both played in the new session.
- **Result:** one netted list. Old debts and tonight's results are added per person and worked out again.

## What happens today

- Closing a session (`settlement.services.close_night`) adds each player's results over its finalized sets, checks they sum to zero, and writes one `SettlementPlan` with the fewest `Transfer` rows that clear every balance.
- A transfer is unpaid until a host marks it paid, which writes a `Payment`. Undoing writes a `PaymentReversal`. Nothing is edited.
- Each session settles alone. An unpaid transfer stays on its own session's page for good. Your groups adds a person's unpaid transfers over all sessions into "you owe" and "you are owed".
- Reopening a session retires its plan (kept, not current) and is refused while one of its transfers is marked paid.

## Findings

1. **Carrying is netting with more input.** A carried transfer of ₱500 from Ana to Ben lowers Ana's balance in the new session by ₱500 and raises Ben's by ₱500. The balances still sum to zero, so the existing algorithm and its checks apply unchanged.
2. **A carried transfer is neither paid nor unpaid.** Marking it paid would be false: no money moved. Leaving it unpaid would count the debt twice, once in the old session and once inside the new list. It needs its own state, "Carried", with a link to the session that took it over.
3. **No record is edited.** One new kind of row says "this transfer was carried into that plan". The carry is in force while that plan is the session's current one. Reopening the new session retires its plan, as today, and every transfer it had carried is unpaid again by that fact alone.
4. **The netted list can change who pays whom.** If Ana owed Ben ₱500 and tonight Ben lost ₱500 to Carlo, the new list says Ana pays Carlo. That is what netting is for, and it is what was chosen; the page must show each person how their figure is made up, or the list looks wrong.
5. **Results do not change.** A session's results describe play. Stats, the recap's ranking and the share card's results stay as they are. Only the transfers differ, and they must say they include earlier debts.
6. **Chains work by themselves.** A debt carried into session B sits inside B's transfers. If those stay unpaid, closing session C can carry them on.
7. **Reopening has two new cases.**
   - The new session is reopened: its carries end and the old transfers are unpaid again. Already refused while one of its transfers is paid.
   - The old session is reopened while one of its transfers is carried: its list would be replaced while a later list depends on it. This must be refused until the later session is reopened first.
8. **Units.** Chips have no peso value (design rule 1). A pesos debt can only be carried into a pesos session, chips into chips.
9. **Which sessions.** Any earlier closed session of the same group, at any table, that is not archived. An archived session's transfers are already left out of every unpaid total.
10. **Two hosts at once.** A transfer could be marked paid, or carried by another closing session, between the page being shown and Close being tapped. The close must check every ticked transfer again under lock and refuse the whole close if one changed, as adding several players does.
11. **Live pages.** The old session's page and Your groups must update by themselves when a later session carries or releases a transfer. Their change stamps count payments today and must count carries too.
12. **The user tests on the live build.** A switch; with it off, closing works as today and nothing is listed.

## Options for the record

| Option | For | Against |
|---|---|---|
| A. A new row, "transfer carried into plan", in force while that plan is current | Nothing edited; reopening releases it with no extra write; the reason an old transfer is settled is explicit | One new table |
| B. A `Payment` with a "carried" kind | No new table | A payment that moved no money; "paid" counts and the reopening rule would need exceptions everywhere |
| C. Copy the old transfer's amount into the new session as an adjustment | Simple netting | The link between the two sessions is lost; undoing is guesswork |

Recommend A.

## Risks

| Risk | Effect | Answer |
|---|---|---|
| A debt is counted twice or lost | Wrong money | A carried transfer leaves every unpaid total; the new list is checked to clear every balance, as today; tests on totals before and after, and after a reopen |
| People do not recognise the new list | Disputes | Each person's figure is shown as tonight's result plus each carried debt; the carried transfers are listed with their sessions |
| A carried debt is also paid in cash | Paid twice | The old transfer has no Paid button while carried; it says where it went |
| Reopening in the wrong order | A list that depends on a replaced list | The old session cannot be reopened while one of its transfers is carried |

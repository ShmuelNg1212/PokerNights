# Unpaid debts across sessions: study

Date: 2026-11-06, Asia/Manila.

## Request

The human said: "lets build the unpaid debts across session feature. execution will be done in codex."

The feature came from a list of suggestions: one balance per person per group, made from the transfers that nobody marked paid.

## Decisions of the human

Four questions were asked. The human chose:

1. **Visibility.** A player sees only their own debts. A host sees the debts of every member of the group.
2. **Place.** A Debts section on the group page, at the top of the Sessions tab.
3. **Netting.** Debts between two people that go both ways are netted. One tap settles them all: it records the net money that moved and closes every transfer behind it. This needs a new append-only record and an ADR, because closing a transfer this way is not a payment of that transfer.
4. **Who marks.** A host, and also the person who receives the money.

## What happens today

- Closing a session writes one `SettlementPlan` with the fewest `Transfer` rows. A transfer is unpaid until a host marks it paid (`settlement.services.mark_paid`, a `Payment`). Undo writes a `PaymentReversal`.
- Closing can carry earlier unpaid transfers into the new list (`CarriedTransfer`, switch `CARRY_DEBTS`). It carries a transfer only when the payer and the payee both have a result in the new session.
- `settlement.queries.unpaid_transfers(member_ids)` lists the transfers of closed, unarchived sessions that are not paid and not carried. Three screens use it:
  - **Your groups**, "To settle": three rows at most, one row per transfer, then "And N more". Each row links to its session.
  - **Sessions tab**: under each past session, one line for each transfer of the viewer.
  - **Remove a player**: "Still to pay".
- Marking paid is host only (`require_host`), and only on the session page of that transfer.
- No screen adds up a person's debts per other person. No screen shows a host all the debts of the group.

## Findings

1. **The data exists.** Each debt is an unpaid transfer. A per-person balance is a query over `unpaid_transfers`, grouped by the other person and by unit. No snapshot is necessary (design rule 7).
2. **Units stay apart.** A group can have pesos sessions and chips sessions. A balance is per unit. Pesos and chips never add (design rule 1).
3. **The rake fund is not a person.** A transfer into the rake fund has no payee. It cannot be netted against a person. It shows to hosts as its own row, and a host marks it paid one transfer at a time, as today.
4. **A pair is the unit of netting.** For two members A and B and one unit, the net is the sum of A→B minus the sum of B→A, over their unpaid transfers. The net can be zero.
5. **The one-tap settle needs a new record.** A `Payment` belongs to one session and pays one transfer. A settle across sessions closes several transfers with one movement of money, possibly in the other direction, possibly zero. Recommended record:
   - `Clearance`: group, unit, the member who paid the net, the member who received it, the net amount (zero or more), `request_id`, who recorded it, when, and `active`.
   - `ClearedTransfer`: one row per transfer that the clearance closed, with `active` copied from the clearance, so the database allows one active clearance per transfer.
   - `ClearanceReversal`: undoes one clearance, with a reason. Nothing is edited except `active`, as for `Payment`.
6. **A cleared transfer is done.** It leaves every unpaid total, as a paid or carried transfer does. It counts toward "Settled" on its session. It cannot be marked paid, carried, or included in a second clearance.
7. **Reopening.** A session whose transfer is cleared cannot be reopened. The host undoes the clearance first. This is the same rule as for paid transfers.
8. **Stale pages and two people at once.** Between the page and the tap, another person can mark a transfer paid or clear it. The settle form sends the transfer ids it showed and the net. The service locks every session concerned, in id order, and checks again. If the set of open transfers between the two, or the net, changed, it refuses everything: "These debts changed. Look again."
9. **Locks.** A clearance writes to several sessions. It locks each `GameNight` row with `games.services.lock_night`, sorted by id, so two writes cannot deadlock. An archived session takes no write; its transfers are already outside every unpaid total.
10. **The payee may confirm.** Today `mark_paid` calls `require_host`. The new rule: a host, or the member with a login who is the payee of that transfer. For a clearance: a host, or the member who receives the net. When the net is zero, either of the two. The payer cannot confirm their own payment. Undo: a host, or the person who recorded it.
11. **Live pages.** The session page and the Sessions tab poll a stamp (`night_stamp`, `hub_stamp`). Today the stamps count payments. They must count clearances too, or a settle on one phone does not show on another phone.
12. **Your groups.** "To settle" lists transfers one by one. It should list the netted balance per person and link to the Debts section.
13. **Fail safe.** The human tests on the live build. A switch, `DEBTS_VIEW`, turns the section and the new writes off. With it off, every screen works as today.

## Options for the record

| Option | For | Against |
|---|---|---|
| A. `Clearance` with link rows and a reversal (finding 5) | Nothing edited; one record says what money moved; undo is exact | Three new tables |
| B. One `Payment` per transfer, with the amount of the transfer | No new table | False: that money did not move. A net of ₱200 would show as ₱800 paid |
| C. A `Payment` of the net on one session, plus "closed" marks on the others | Fewer tables | The record of money sits on one session by chance; the other sessions point to it |

Recommend A.

## Risks

| Risk | Effect | Answer |
|---|---|---|
| A debt is counted twice or lost | Wrong money | Tests on balances before and after a clearance, after an undo, after a carry, and after a paid mark |
| People do not recognise the net | Disputes | Each row opens to the transfers behind it, with session date and direction |
| A player confirms money they never got | Wrong record | Only the receiver of the money, or a host, can confirm; each write goes to the audit log; undo exists |
| Two people settle at once | A transfer closed twice | Locks in id order, a check again under lock, and a partial unique constraint on the active link row |
| The new section is wrong on the live build | Bad numbers on phones | `DEBTS_VIEW=False` hides it and the services refuse |

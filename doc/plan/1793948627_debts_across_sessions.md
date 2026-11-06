# Unpaid debts across sessions: plan

Study: [1793948599_debts_across_sessions.md](../study/1793948599_debts_across_sessions.md).

Executor: Codex. Codex has no claude-mem and no impeccable. Read `doc/adr/`, this plan, the study and `git log`. For the design tasks, use taste-skill `design-taste-frontend` with DESIGN.md as the reference.

Mode: mixed. Do the technical tasks (1 to 5) first, then the design tasks (6 to 8), then rendezvous.

Branch: `feat/debts-across-sessions`, from `main`.

## Goal

A person sees, in one place per group, what they owe each other person and what each person owes them, over all closed sessions. A host sees this for the whole group. A host or the receiver of the money settles all the debts between two people with one tap.

## Decisions (from the human, 2026-11-06)

- A player sees only their own debts. A host sees all debts of the group.
- The Debts section is at the top of the group's Sessions tab.
- Debts that go both ways between two people are netted. One tap settles them all with a new `Clearance` record (study, option A).
- A host, or the person who receives the money, can mark paid and can settle.

## OPEN QUESTIONS

Each question has a default. The executor uses the default unless the human changes it before approval.

1. **Undo.** Who can undo a clearance or a paid mark? Default: a host, or the person who recorded it.
2. **Zero net.** Debts that cancel exactly (A owes B ₱500, B owes A ₱500). Default: allowed. The button says "Clear ₱0: these cancel out". Either of the two people, or a host, can tap it.
3. **Your groups.** Default: "To settle" changes from one row per transfer to one row per person, netted, three at most, with a link "See all debts" to the Debts section.
4. **Words.** Default: section title "Debts". Player row: "You pay Ana ₱200" or "Ana pays you ₱200". Receiver's button: "Got ₱200 from Ana". Host's button: "Settle ₱200". Confirm sheet title: "Settle with Ana?".

## Rules for every task

- Follow AGENTS.md design rules 1 to 11. Amounts are integers. Only `services.py` writes. Each write runs in `transaction.atomic()`, locks the session rows with `select_for_update()`, carries a `request_id`, calls `audit.record()`, and bumps the version of the sets concerned.
- Run `DEBUG=True .venv/bin/python manage.py test` before each commit that changes code. Run the PostgreSQL suite before rendezvous.
- One Conventional Commit per task.
- Code-writing subagents: tasks 1 to 5 edit the same files (`settlement/models.py`, `queries.py`, `services.py`). Do them in one agent, in order.

## Tasks

### 1. Records — tests: first

- [ ] Add `Clearance` to `settlement/models.py`: `group` (FK), `unit`, `payer` (Member, paid the net), `payee` (Member, received the net), `amount` (BigInteger, `>= 0`), `request_id` (UUID), `recorded_by`, `created_at`, `active` (default True).
- [ ] Constraints on `Clearance`: unique `(group, request_id)`; `amount >= 0`; `payer != payee`.
- [ ] Add `ClearedTransfer`: `clearance` (FK), `transfer` (FK, `related_name="clearances"`), `active`. Partial unique constraint: one active row per `transfer`. Unique `(clearance, transfer)`.
- [ ] Add `ClearanceReversal`: one-to-one `clearance`, `reason` (255), `recorded_by`, `created_at`.
- [ ] Migration. Read [footguns/partial_unique_constraints_are_not_deferrable.md](../wiki/footguns/partial_unique_constraints_are_not_deferrable.md) first.
- **Acceptance:** model tests show that the database refuses a second active `ClearedTransfer` for one transfer, a negative amount, and a repeated `request_id` in one group.
- **Done when:** the migration applies on SQLite and PostgreSQL, and the tests pass.

### 2. Queries — tests: first

- [ ] Add `cleared_ids()` to `settlement/queries.py`: the transfers with an active `ClearedTransfer`, as a subquery.
- [ ] Exclude `cleared_ids()` in `unpaid_transfers`, `unpaid_in` and `carryable`.
- [ ] `settle_states` and `NightOutcome`: count a cleared transfer as done, as `carried` is counted now. Add `cleared` and `cleared_amount`. `status` uses `paid + carried + cleared`.
- [ ] Add `debts(group, viewer)`. It returns rows of `(unit, member A, member B, net, transfers)`, one per pair and unit with at least one unpaid transfer. `net > 0` means A pays B. A player gets only the pairs that contain them. A host gets every pair. Rake fund transfers are separate rows with no netting, for hosts and for their payer.
- [ ] Order: the viewer's own rows first, then by the largest amount, then by name.
- **Acceptance:** tests cover: one transfer; two transfers in one direction (sum); two transfers in opposite directions (net); an exact cancel (net 0); pesos and chips apart; a paid, a carried and a cleared transfer each left out; an archived session left out; a player who sees only their pairs; a host who sees all; the rake fund row.
- **Done when:** the tests pass, and the number of queries for `debts` does not grow with the number of sessions (`assertNumQueries`).

### 3. Settle a pair — tests: first

- [ ] Add `settle_pair(group_id, actor, unit, member_a_id, member_b_id, transfer_ids, net, request_id)` to `settlement/services.py`.
- [ ] Find the nights of the given transfers. Lock each one with `games.services.lock_night`, sorted by id.
- [ ] Under the lock, read the unpaid transfers between A and B in this unit again. Refuse with "These debts changed. Look again." if the ids differ from `transfer_ids` or the net differs from `net`.
- [ ] Permission: a host; or, when `net != 0`, the member who receives the net; or, when `net == 0`, either of the two. Refuse others with `NotAllowed`.
- [ ] Write one `Clearance` and one `ClearedTransfer` per transfer. A repeated `request_id` returns the first clearance and writes nothing.
- [ ] `audit.record("debts.cleared", ...)` once, with a summary such as "Ana paid Ben ₱200 to settle 3 transfers", and the transfer ids in `data`.
- [ ] Bump the version of the sets of each night concerned (`_bump_sets`).
- [ ] Add `undo_clearance(group_id, actor, clearance_id, reason)`: a host or the recorder (OPEN QUESTION 1). Lock the nights as above. Set `active=False` on the clearance and on its link rows. Write a `ClearanceReversal`. Audit "debts.uncleared". Bump the versions. A second undo changes nothing.
- [ ] `mark_paid`: refuse a cleared transfer ("This transfer was settled with {name} on {date}. Undo that first."). `close_night` carry: `carryable` already leaves cleared transfers out (task 2).
- [ ] `reopen_night`: refuse while a transfer of the plan is cleared ("{n} transfers were settled across sessions. Undo that first.").
- [ ] Switch `DEBTS_VIEW` in `config/settings.py` (env, default False until the phone checks pass). With it off, `settle_pair` and `undo_clearance` refuse.
- **Acceptance:** tests cover: settle by a host; settle by the receiver; refusal for the payer and for a third member; a zero net; a stale id list; a stale net; a repeated request; undo, then the transfers are unpaid again and can be settled again; mark paid refused on a cleared transfer; reopen refused while cleared and allowed after undo; carry leaves a cleared transfer out; the switch off.
- **Done when:** the tests pass on SQLite and on PostgreSQL.

### 4. The payee may mark paid — tests: first

- [ ] `mark_paid`: allow a host, or the member who is the transfer's payee. A rake fund transfer stays host only.
- [ ] `mark_unpaid`: allow a host, or the user who recorded that payment (OPEN QUESTION 1).
- [ ] Behind `DEBTS_VIEW`: with the switch off, the rules are as today (host only).
- **Acceptance:** tests: the payee marks paid; the payer is refused; another player is refused; the payee cannot mark a rake fund transfer; undo by the recorder; undo by another player refused.
- **Done when:** the tests pass.

### 5. Live stamps — tests: first

- [ ] `night_stamp` and `stamp_from`: add the number of active clearances that touch this session's current plan. Leave it out at zero, so a session that nobody cleared keeps its mark (as `carried` does).
- [ ] `hub_stamp`: add the count of clearances made and standing in these groups.
- **Acceptance:** a test shows that a clearance and its undo each change both stamps, and that a group without clearances keeps the same `hub_stamp` as before this change.
- **Done when:** the tests pass.

### 6. Debts section — tests: alongside

- [ ] Add `web/debts.py` that builds the section from `settlement.queries.debts`. Add it to `sessions_context` when `DEBTS_VIEW` is on and the group has at least one row for the viewer.
- [ ] Template `templates/web/_group_debts.html`, at the top of `_group_sessions.html`, above the cards. Title "Debts".
- [ ] One row per pair and unit: the other person's token and name, the net, and the line "from N sessions". A tap opens the transfers behind it (native disclosure, as the rest of the app): session date with link, direction, amount.
- [ ] The receiver sees "Got ₱200 from Ana". A host sees "Settle ₱200" on each row. The payer sees no button, only "Ana confirms when paid".
- [ ] The button opens a confirm sheet: "Settle with Ana?", the net and its direction, the list of transfers, **Settle** and **Not yet** (focus on Not yet). Without scripts, the same content opens in place. The form posts the shown transfer ids, the net and a `request_id`.
- [ ] After a settle, the row leaves and a short status line says "Settled with Ana: ₱200". Hosts and the recorder see **Undo** on that line until the next reload.
- [ ] View and URLs in `settlement/views.py` and `settlement/urls.py`: `POST g/<group>/debts/settle/` and `POST g/<group>/debts/<clearance>/undo/`. Resolve the group through the requester's active membership; a miss is 404.
- [ ] Follow DESIGN.md: dark, one column on phones, 48 px targets, the amount format of rule 8, reduced motion with no movement.
- **Acceptance:** view tests: a player sees only their rows; a host sees all; a non-member gets 404; a post from a stale page shows the refusal and keeps the section; the switch off hides the section. Browser probe: log in as a receiver on a phone width, open the group, tap "Got ₱200 from Ana", confirm, and see the row leave. A second browser on the session page sees the transfers change state without a reload.
- **Done when:** the view tests pass and the browser probe passes. The probe must fail on `main`.

### 7. Session page and Your groups — tests: alongside

- [ ] Session page: a cleared transfer shows "Settled with {name} on {date}" with no Paid button. A host or the recorder sees "Undo", which calls `undo_clearance`.
- [ ] Your groups "To settle": one row per person and unit, netted, three at most, with "See all debts" to the Debts section (OPEN QUESTION 3). With the switch off, the card is as today.
- [ ] Sessions tab per-session lines: leave cleared transfers out (they leave `unpaid_transfers` by task 2). Check the "Not settled" filter counts.
- **Acceptance:** view tests for both pages; the existing home and sessions tests still pass with the switch off.
- **Done when:** the tests pass.

### 8. Design pass

- [ ] Run `design-taste-frontend` on the Debts section and the confirm sheet against DESIGN.md. Fix what it finds that is inside DESIGN.md's tokens.
- [ ] Check worst cases: 20 pairs; a long name; a net of ₱1,000,000.50; a chips game and a pesos game in one group; a viewer with no debts (the section is not shown).
- **Done when:** the findings are fixed or recorded here with a reason.

### 9. Docs

- [ ] ADR 0013: clearances across sessions (study, options and choice). Mention that ADR 0002 stays: a `Payment` still belongs to one session.
- [ ] `doc/wiki/spec.md`: the Debts section, the payee rule, the clearance. Approved by the human on this plan.
- [ ] `GLOSSARY.md`: **Clearance**, **Debt** (an unpaid transfer seen across sessions).
- [ ] `doc/wiki/features.md`, `architecture.md` (the new records), a footgun file if one appears.
- [ ] TODO.md: phone checks for this feature, under the unreleased heading.
- **Done when:** the wiki matches the code.

## Rendezvous

- [ ] Full test suite on SQLite and on PostgreSQL.
- [ ] Review: code review of the branch; security review (money, permission and user data change).
- [ ] First user action: with `DEBTS_VIEW=True` locally, log in as a player who is owed money from two sessions and owes money from a third. Open the group, check the net against a hand sum, tap "Got …", confirm. Then log in as the payer and check that the row is gone and that the three session pages say Settled. Undo as the recorder and check that all three are unpaid again.
- [ ] Record each check here with its result.
- [ ] Two fix-and-recheck rounds at most. After that, stop and ask the human.

## Release

- Ship with `DEBTS_VIEW=False` in Vercel, then set it to True after the human says so. Or ship with True if the human prefers. Ask at "ship".

## Phone checks (for TODO.md)

- Open a group where you are owed money: Debts shows one row per person with the net.
- Tap a row: the sessions behind it show. The sum matches the net.
- Tap "Got ₱… from …", then Settle: the row leaves. The session pages say Settled.
- As the payer: no button; the row says the other person confirms.
- As a host: every pair shows, with Settle.
- Undo: the transfers are unpaid again.

# Session settled indicator: plan

Status: approved 2026-10-04 ("approved. i am ok with the suggestions."). Date: 2026-10-04, Asia/Manila. Study: [Session settled indicator](../study/1791120013_session_settled_indicator.md).

## Outcome

A host or player can see, without opening a session, whether a closed session is fully settled and how much is still to pay.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new token, colour or asset. No migration; nothing is stored.

## Behaviour

**Group → Sessions → Past sessions.** Each row changes:

| Status | Badge | Second line |
|---|---|---|
| Settled | "Settled" with a check, green | "Sep 27, 2026 · 2 sets" |
| Partly settled | "Partly settled", warning colour | "Sep 27, 2026 · 2 sets · ₱2,650 still to pay" |
| Unsettled | "Unsettled", warning colour | "Sep 27, 2026 · 2 sets · ₱4,650 still to pay" |

- The set count moves from the badge to the second line.
- The heading reads "Past sessions" and, when any are not settled, a muted "2 not settled" beside it.
- A closed session with no transfer counts as Settled.
- Order stays newest first.

**Session page, top bar.** The badge "Session closed" becomes the status for a closed session: "Settled" with a check, "Partly settled" or "Unsettled". An open session keeps "Session open"; an archived one keeps "Archived". The overview below is unchanged.

**Unchanged.** Open sessions, the archived list, the home page, who can mark a transfer paid, and what "settled" means.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **Show the amount still to pay in the list.** Recommended. The alternative is the badge alone.
2. **Words.** Recommended: "Settled", "Partly settled", "Unsettled", the words the session page already uses.
3. **Home page.** Recommended: no change. It already lists what you personally owe or are owed under "To settle". Say so if you want a group-wide "N sessions not settled" line for hosts there; it adds a query to a page with a fixed query budget.
4. **Players see it too.** Recommended: yes. They can already see every transfer on the session page.

## Implementation

1. **One rule (`settlement/queries.py`).** `settle_status(count, paid_count)` returns `settled`, `partly` or `unsettled`. `NightOutcome.status` calls it.
2. **One batched read.** `settle_states(night_ids) -> {night_id: SettleState}` with `status`, `label`, `still_to_pay`, `transfers`, `paid`. Two queries for any number of sessions: transfers grouped by session (count and sum), and transfers that have an active payment grouped by session (count and sum). No join that multiplies rows (study, constraint 3). A closed session without transfers gets a settled state.
3. **View (`web/views.py`).** The group Sessions tab attaches the state to each closed session and passes the not-settled count. The session page passes its existing outcome status to the top bar.
4. **Templates.** `_group_sessions.html`: the badge, second line and heading count. `night.html`: the top-bar badge. A small partial for the badge so both render it the same way.
5. **CSS.** At most a rule for the icon inside a badge and the heading count.
6. **Tests first.**
   - `settlement/tests`: `settle_states` for settled, partly, unsettled, no transfers, a transfer paid then undone then paid again (counted once), an undone payment (not counted), pesos and chips, several sessions in one call with a fixed query count, and agreement with `night_outcome(...).status` for each case.
   - `web/tests`: the Past sessions rows and heading count for each status as a host and as a player; the list changes after mark paid and after undo; the top-bar badge for open, each closed status and archived; the group page query count does not grow with the number of past sessions.
   - Browser check at 320, 390 and 1280 px: rows with long table names and ₱199,999,999.98 still to pay do not overflow; badge text contrast; rows stay 48 px targets.
7. **Verify.** SQLite and PostgreSQL suites; the browser check; captures inspected.
8. **Sync docs.** DESIGN.md addendum, wiki features, browser README, TODO.

## Acceptance criteria

- AC1. Every past session in the list shows Settled, Partly settled or Unsettled, with the amount still to pay when it is not settled.
- AC2. The list and the session page never disagree, including after a paid mark is undone.
- AC3. The status is not conveyed by colour alone.
- AC4. The number of queries on the group page does not grow with the number of past sessions.
- AC5. No model, migration or write path changes. Existing tests pass on SQLite and PostgreSQL.

## Out of scope

- A filter or a separate section for sessions that are not settled.
- Reminders or notifications about unpaid transfers.
- Any change to the home page (see decision 3).
- Letting players mark their own transfers paid.

## Rollback

Revert the feature commit. No data change.

## Progress and blockers

2026-10-04: Study and plan complete. The human approved with “approved. i am ok with the suggestions.”

2026-10-04 execution on `feat/settled-indicator`, tests first. No change from the plan, except that two older tests that looked for the text “Session closed” on a closed session page now look only for the status, since the top bar no longer carries that text.

2026-10-04 verification:

- 589 tests pass on SQLite (ten PostgreSQL-only skips) and all 589 on local PostgreSQL 17, started for the run and stopped after. Nine new tests in `settlement/tests/test_settle_states.py`, including a paid-undone-paid transfer counted once, agreement with `night_outcome`, two queries for several sessions, and a group page whose query count does not grow with past sessions.
- `settled.mjs`: 24 of 24 on a fresh temporary database; the 320px capture was inspected with ₱199,999,999.98 still to pay.

Not verified: a physical phone and a screen reader.

AC1 to AC5 are met. Documentation synced: DESIGN.md, wiki features, browser README, TODO.

2026-10-04 rendezvous: merged into local main as `eefa65f feat(ui): merge the session settled indicator`. Main SQLite: 589 pass, ten PostgreSQL-only skips. No migration. The temporary server and PostgreSQL are stopped. Not pushed.

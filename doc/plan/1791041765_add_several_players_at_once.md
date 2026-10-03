# Plan: add several players to a game at once

- **Date:** 2026-10-03 23:36 (Asia/Manila), Unix timestamp `1791041765`
- **Status:** `in-progress`
- **Study:** [../study/1791041698_add_several_players_at_once.md](../study/1791041698_add_several_players_at_once.md)
- **Workflow:** `agentic-workflow`. Phase 2 starts only after explicit human approval of this plan.
- **Approval record:** Approved by the human on 2026-10-03: "for players who have a login are irrelevant for this feature. I am ok with q2. proceed with the remaining steps." Q2 = yes. Q1: read by the AI as "whether a player has a login does not matter for this feature"; the default applies (all eligible members are listed alike; no new-names box). This reading is flagged in the rendezvous report.

Edit this file directly, or add a line that starts with `NOTE:`.

---

## OPEN QUESTIONS

| # | Question | Default (recommended) | Affects |
|---|---|---|---|
| **Q1** | **Guests.** Should the picker also take several new names (one per line) and create them as roster players? | **No, not in this change.** Roster players without logins already appear in the list. Typing new names in the picker is a possible follow-up with its own plan. No new guest-account system in either case | Scope |
| Q2 | May a host re-add players who left or withdrew through the picker, as the single flow allows? | Yes. They show the tag "Left earlier" | Eligibility |

---

## Goal

A host adds several eligible group members to a game with one confirmation. Either each selected player joins, or nobody does.

## Scope

- An "Add players" button in the players card of the game page, for hosts.
- A picker page with a searchable checkbox list, the selection count, the free seats, a review line and one confirm button.
- A service that validates and adds the selection in one transaction.
- A stored `request_id` per batch, so that a retry adds nothing twice.
- Tests, a browser check and docs.

## Exclusions

- Typing new guest names in the picker (Q1).
- Seat numbers and seat draws. Adding players gives no seat number, as today.
- Any change to buy-ins, cash-outs, payments or results.
- Any change to the single-player flow or to self-join.
- Live polling on the picker page.

## Acceptance criteria

| # | Criterion |
|---|---|
| AC1 | A host sees "Add players" on a game in setup, open or running. A player does not. The dropdown "Add from the roster" still works |
| AC2 | The picker lists each active group member with a labeled checkbox. A member at the table is shown as "At the table" and cannot be ticked |
| AC3 | The page shows the free seats and the number selected. The button reads "Add 4 players" for four ticks |
| AC4 | Typing in the search field hides rows that do not match. Ticks made before the search are still ticked after the search is cleared, and are submitted |
| AC5 | With eight free seats, the host ticks Ana, Ben, Carlo and Dani and confirms once. All four are in the roster. The page says "Added 4 players: Ana, Ben, Carlo, Dani." |
| AC6 | With three free seats and four ticks, the page says that only three seats are free and to remove one player. The button is disabled. A hand-made request is refused and adds nobody |
| AC7 | If another host adds Ben while the picker is open, the confirm adds nobody. The page names Ben, shows him as "At the table", and keeps the other ticks |
| AC8 | Sending the same confirmed request again adds nobody twice and shows the same success |
| AC9 | A player gets "forbidden" and a person outside the group gets "not found", for the page and for the request |
| AC10 | Another member's open game page shows the new players within about 5 seconds |
| AC11 | After the action, the game has no new buy-in, cash-out, payment or result, and the total bought in is unchanged |
| AC12 | The page is usable with a keyboard and at phone width |

## Dependencies and external inputs

None new. PostgreSQL 17 is started for the test run and stopped after it. The dev server stops for the migration and restarts at the end.

## Branch strategy and rollback

- Branch `feat/add-players` from `main`. Tests green before each commit.
- The migration only adds one table. Before it runs on the dev database, a backup is made with the SQLite backup API.
- Rollback: revert the merge commit. The new table can stay or be dropped; no existing row changes.
- Local merge to `main` at rendezvous. No push.

## Tasks

- [ ] **1. Add the batch action.** Model `ParticipantBatch` (session, `request_id` unique per session, added by, time) with its migration. Service `games.services.add_participants()` as the study describes. View and URL `/s/<id>/players/add/` (GET the picker, POST the confirm; a refused confirm shows the picker again with the selection kept). Template `games/add_players.html`. Script `static/js/pick.js` for search, count, capacity message and button text. "Add players" button in `templates/web/_players.html`. Tests for the service, the page and the races.
  - Commit: `feat(games): let a host add several players in one action`
  - Done when: the tests listed under Verification pass on SQLite and on PostgreSQL, and the existing tests pass unchanged.
- [ ] **2. Verify in a browser.** Headless Chrome at phone width: search keeps ticks, count and button text follow the selection, the capacity message, keyboard ticking with Tab and Space, no horizontal scroll, and the live update on a second client. Look at the screenshots. Record results in this plan.
  - Commit: `docs(plan): record verification results`
  - Done when: each acceptance criterion has a recorded result.
- [ ] **3. Rendezvous and docs.** Back up and migrate the dev database. Merge to `main`. Update `doc/wiki/features.md`, `architecture.md` and `TODO.md`; add the guest-names follow-up to the roadmap if Q1 stays "no". Restart the server. Set this plan to `done`.
  - Commit: `docs: sync living documentation`
  - Done when: `main` has the work, the tests pass on `main`, and the server answers.

## Verification

| Topic | Test |
|---|---|
| Success | Four of eight seats: four participants in list order with consecutive `join_order`, four audit events, one version increment |
| Capacity | Three seats and four ids: refused, with the numbers in the message; no participant added |
| Existing participant | One selected member is at the table: refused, named; no participant added |
| Eligibility | An id from another group, a removed member, an unknown id: refused; no participant added |
| Re-add | A member who left or withdrew returns to `joined` with the same row |
| States and roles | Refused in `reconciliation`, `finalized`, `canceled`. A player is refused. Another group's host is refused |
| Empty and repeated ids | An empty selection is refused. A repeated id counts once |
| Atomic | A failure forced in the middle of the loop leaves no participant, no batch, no audit event and the same version |
| Retry | The same `request_id` twice: one batch, no new rows the second time, the same players returned |
| Concurrency (both engines) | Two hosts submit overlapping selections at once: one succeeds, the other adds nobody. Two batches of two race for three seats: one succeeds. One `request_id` from six threads: one batch |
| No coupling | After the action: zero `BuyIn`, `CashOut`, `Payment`, `PlayerResult` rows; `has_money` is false |
| Access | Page and request: 403 for a player, 404 for a stranger, redirect to login when signed out |
| Conflict page | The refused confirm shows the picker again with the remaining ticks, the named player disabled, and the new seat count |
| Live | The polling endpoint returns a new snapshot with the added names |
| Single flow | The existing participant tests pass without edits |

## Rendezvous

The report gives what is ready against AC1–AC12, user test steps, the checks with results on both engines, the commits, assumptions and gaps, and the merge status. The merge is local. Nothing is pushed.

## Documentation sync

`doc/wiki/features.md` (the new action), `doc/wiki/architecture.md` (the batch service and its idempotency), `doc/roadmap/README.md` (guest names follow-up), `TODO.md`.

## Blockers

None. If Q1 is answered "yes", the plan is revised before work starts.

## Progress log

| Date | Entry |
|---|---|
| 2026-10-03 23:36 | Study and plan written and committed. Status `awaiting-approval`. |
| 2026-10-03 | Human approved. Q2 yes. Q1 default, with the AI's reading recorded above. Dev server stopped for the work. |

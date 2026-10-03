# Plan: sessions with sets, end-of-set cash-outs and playing time

- **Date:** 2026-10-03 23:51 (Asia/Manila), Unix timestamp `1791042668`
- **Revised:** 2026-10-03 23:56 (Unix `1791042979`), after the human stated that a session can have several sets
- **Status:** `awaiting-approval`
- **Study:** [../study/1791042572_end_of_set_cash_outs_and_timers.md](../study/1791042572_end_of_set_cash_outs_and_timers.md). Its **review addendum** controls where it differs from the earlier sections.
- **Workflow:** `agentic-workflow`. Phase 2 starts only after explicit human approval of this revised plan.
- **Approval record:** _none yet_

Edit this file directly, or add a line that starts with `NOTE:`.

---

## Decisions already made by the human (2026-10-03)

| # | Decision |
|---|---|
| S1 | Each set has its own buy-ins, final counts, cash-outs and balance check. A new set starts with fresh buy-ins |
| S2 | Who-pays-whom is calculated once per session. It nets all sets |
| S3 | The host starts the next set. Players still at the table carry over |
| S4 | Sets of one session run one after another, never at the same time |

## OPEN QUESTIONS

These were in the first version of this plan and have no answer yet. Each has a default. Q1, Q2 and Q3 change what is built.

| # | Question | Default (recommended) | Affects |
|---|---|---|---|
| **Q1** | **Chip conversion.** The request mentions "calculated peso cash-outs" and "the set's recorded chip conversion". The app has no conversion; you removed it on 2026-10-03. Is the final count typed in the session's unit, with the cash-out equal to that count? | **Yes.** No conversion returns | Tasks 5, 6 |
| **Q2** | **Stricter finalization of a set.** Today a partial cash-out during play counts as "this player has a cash-out". May finalizing a set require a **final** cash-out for each player? | **Yes.** The message names who is missing | Task 5 |
| **Q3** | **Resume a set after counting has started.** (a) Allowed for the latest set, while no later set exists; confirmed counts that are not yet cashed out are voided; players with a final cash-out stay cashed out until the host reverses it. (b) Refused once any batch cash-out exists | **(a)** | Tasks 4, 5 |
| Q4 | **Breaks.** The app has none. Leave them out? "Left" already stops a player's time | Yes | Scope |
| Q5 | **End-time correction.** No rule exists. Leave editing of a set's end time out? | Yes. Listed as a follow-up | Scope |
| Q6 | **Older games.** Fill their end time from the log, and show their playing time as "not recorded"? | Yes | Task 4 |

Consequences of S1 to S4 that you should know before approving:

- **Finalizing a set no longer lists transfers.** It freezes that set's results. Transfers appear when the host closes the session. A session with one set needs one more tap than a game needs today.
- **The unit is per session.** Each set of a session counts in the session's unit.
- **Your existing games** each become a session with one set. Finalized ones become closed sessions and keep their transfers and paid marks.
- **A closed session cannot get another set.**
- **In the code**, a set stays the `GameSession` model and the session is a new `GameNight` model. Screens say "Session" and "Set".

---

## Goal

A session holds several sets played one after another. Each set has its own money and ends with stopped playing time, confirmed final counts and batch cash-outs. The session ends with one settle-up over all its sets.

## Scope

**Part I, sessions with sets**

- A session (`GameNight`) above the existing game model. Each set has a number.
- One set in play per session, enforced in the database.
- "Start next set" with carried-over players.
- Set finalization freezes results only. "Close session and settle up" nets the sets and lists transfers. Transfers and payments belong to the session and point to members.
- A session page; the group page lists sessions.

**Part II, end of a set**

- End time per set and playing-time intervals per player per set. A player's session time is the sum.
- Final counts with versions, the three statuses, and `CashOut.kind`.
- "Cash out counted players (N)" with a review page and an atomic batch.
- Playing time stored with each frozen result.

## Exclusions

- Chip-to-peso conversion (Q1), breaks (Q4), end-time editing (Q5).
- Two sets in play at once, or a session over several tables.
- Reopening a closed session or a finalized set (Stage 2).
- Hourly statistics and leaderboards (Stage 3).
- A rename of `GameSession` in the code.

## Acceptance criteria

**Sessions and sets**

| # | Criterion |
|---|---|
| AC1 | Creating a game creates a session with "Set 1". The session page lists its sets with their states |
| AC2 | After play of a set has ended, the host can tap "Start next set". Set 2 opens with the same table and settings and with the players who were still at the table. It has no buy-ins |
| AC3 | "Start next set" is refused while a set of that session is in setup, open or running. Two hosts tapping it at once create one set |
| AC4 | Finalizing a set shows that set's results and no transfer list. It says that payment is settled at the end of the session |
| AC5 | "Close session and settle up" is refused while a set is not finalized or canceled, and names it |
| AC6 | Two sets: in set 1 A wins ₱600 from B and C (−₱300 each); in set 2 B wins ₱400 from A. Closing the session shows A +₱200, B +₱100, C −₱300, and the transfers "C pays A ₱200" and "C pays B ₱100" |
| AC7 | Paid marks work on the session's transfers. The session shows unsettled, partly settled or settled |
| AC8 | Your existing games appear as sessions with one set. Finalized ones are closed and show the same transfers and paid marks as before |

**End of a set**

| # | Criterion |
|---|---|
| AC9 | When the host ends a set, it shows "Play ended" with one time. Each player's "Played" figure for that set stops and does not grow while counting goes on |
| AC10 | A player who left earlier keeps the time up to the moment they left. Ending set 2 does not change any time of set 1 |
| AC11 | Sending "End play" twice, reloading, or opening a second tab shows the same playing time |
| AC12 | While counting up, each player shows "Awaiting count", "Ready to cash out" or "Cashed out" |
| AC13 | A confirmed count of 0 makes a player ready. An empty field is refused |
| AC14 | The button reads "Cash out counted players (4)" with four ready players. With none it is disabled and says why |
| AC15 | The review lists the four players, each count, each cash-out and the total, and names the two still to count |
| AC16 | One confirmation records four cash-outs and says "4 players cashed out; 2 awaiting final counts." The set is still counting up. Nothing is finalized or marked paid |
| AC17 | After the other two are counted, the same action cashes them out. The set can then pass the balance check and be finalized |
| AC18 | A stale review (a count changed, or a player cashed out elsewhere) records nothing, explains why and reloads. Counts are kept |
| AC19 | The same confirmation sent twice, or by two hosts at once, records each cash-out once |
| AC20 | The individual cash-out still works during play and, under "Details", while counting up |
| AC21 | Finalizing a set is refused while a player lacks a final cash-out, and names them. The balance check and override work as before |
| AC22 | A player cannot confirm counts, run the batch, start a set or close a session. A person outside the group gets "not found" |
| AC23 | Another member's open page shows new statuses and the stopped time within about 5 seconds |
| AC24 | The log shows separately: when play ended, when each count was confirmed and by whom, when each cash-out was recorded, and when a payment was marked |

## Dependencies and external inputs

None new. PostgreSQL 17 for the test run. The dev server stops for the work and restarts at the end.

## Branch strategy and rollback

- Branch `feat/sets-and-end-of-set` from `main`. One Conventional Commit per task, tests green before each.
- Migrations add tables and columns, give each existing game a session, and move transfers and payments to sessions and members. No amount changes. A backup with the SQLite backup API comes first. The data migration is tested on a copy of the dev database before it runs on the real one.
- Rollback: revert the merge commit and restore the backup.
- Local merge to `main` at rendezvous. No push.

## Tasks

### Part I: sessions with sets

- [ ] **1. Group sets into a session.** `GameNight` (group, table, date, location, game type, unit, status `open` or `closed`); `GameSession.night` and `set_number`; one-set-in-play constraint; data migration (one session per existing game); creating a game creates the session and set 1; session page; group page lists sessions; screens say "Session" and "Set".
  - Commit: `feat(games): group sets into a session`
  - Done when: tests cover creation, numbering, access (404 outside the group), the migration, and unchanged behavior of a single set.
- [ ] **2. Start the next set.** `start_next_set()`: host only, under a lock on the session row; refused while a set is in setup, open or running, or when the session is closed; copies table, seats, latest settings and players with status "joined"; the new set is open with no buy-ins.
  - Commit: `feat(games): start the next set with the players still at the table`
  - Done when: tests cover carry-over, players who left, refusal cases, a repeated request, and two hosts at once.
- [ ] **3. Settle up once per session.** Set finalization writes results only. `close_session()` nets each member's results over the finalized sets, runs the existing algorithm, and writes the session's plan and transfers. `SettlementPlan` belongs to the session; `Transfer` and `Payment` point to members. Data migration for existing plans, transfers and payments. Session page shows running results, then transfers and paid marks. Set page shows set results and "Payment: at the end of the session".
  - Commit: `feat(settlement)!: settle up once per session across its sets`
  - Done when: tests cover AC4 to AC8, a session with a canceled set, results that sum to zero over the session, the migration on a copy of the dev database, and an atomic close.

### Part II: end of a set

- [ ] **4. Record the end of play and track playing time.** `GameSession.ended_at`; `PlayInterval` per set and player with the one-open constraint; hooks in start, end, resume, join, batch add, left, return, withdraw and next-set carry-over; set and session playing time on the pages and in the log; a small script that advances minutes while a set runs; `ended_at` filled from the log for existing sets.
  - Commit: `feat(games): record when a set ends and track playing time per player`
  - Done when: tests cover each event, one shared end timestamp, early leavers, returns, resume, repeats, and that ending set 2 leaves set 1 untouched.
- [ ] **5. Confirm final counts apart from cash-outs.** `FinalCount` with versions and voiding; `CashOut.kind` with a data migration; the three statuses; count entry while counting up; individual cash-out under "Details"; the gate on final cash-outs (Q2); the resume rule (Q3).
  - Commit: `feat(ledger): confirm final counts separately from cash-outs`
  - Done when: tests cover zero against empty, replace and clear, statuses, the gate message, resume, access and unchanged totals.
- [ ] **6. Cash out counted players in one action.** `CashOutBatch`; `cash_out_counted()`; the button with its count and disabled reason; the review page; the stale-review refusal; the success line.
  - Commit: `feat(ledger): cash out all counted players in one reviewed action`
  - Done when: tests cover success, a second run for the rest, a stale count, a player cashed out elsewhere, rollback on a forced failure, retry by `request_id`, access, and no finalization or payment as a side effect.
- [ ] **7. Store playing time with results.** `PlayerResult.play_seconds`, written when a set is finalized.
  - Commit: `feat(ledger): store playing time with each frozen result`
  - Done when: a test shows the figure equals the interval sum at the end of play, not at finalization.

### Verification and close

- [ ] **8. Races and end-to-end.** Threaded tests on both engines: two hosts start the next set; two hosts close the session; overlapping batches; a batch against an individual cash-out; a batch against a count change; "End play" twice. Page-driven tests: the six-player example, and the two-set example of AC6.
  - Commit: `test: cover sets, session settle-up, end-of-set batches and their races`
  - Done when: the tests pass on SQLite and PostgreSQL, and fail on PostgreSQL with the locks removed.
- [ ] **9. Verify in a browser.** Headless Chrome at phone width over a two-set session: statuses, zero count, button, review, success line, stale review, frozen time, next set with carried players, session settle-up, second client update, keyboard, no horizontal scroll. Screenshots reviewed. Results recorded here.
  - Commit: `docs(plan): record verification results`
  - Done when: each acceptance criterion has a recorded result.
- [ ] **10. Rendezvous and docs.** Backup, migrate the dev database, merge to `main`, update `features.md`, `architecture.md`, a footgun page for the `GameSession`/"set" naming, the roadmap and `TODO.md`, restart the server, set this plan to `done`.
  - Commit: `docs: sync living documentation`
  - Done when: `main` has the work, the tests pass on `main`, and the server answers.

## Verification

| Topic | Test |
|---|---|
| One set in play | The database refuses a second set in setup, open or running for one session. The service gives a clear message |
| Carry-over | Joined players carry over in their order. Left and withdrawn players do not. No buy-in, cash-out or count is copied |
| Session settle-up | Member sums over sets are zero in total. Transfers clear each balance. The count equals the proven minimum. Ties follow first-join order in the session |
| Set results only | After finalizing a set: results exist, no plan, no transfer, no payment |
| Migration | Each old game has one session and set number 1. Old transfers and payments point to the right members and session. Amounts, results and paid marks are identical before and after |
| One end timestamp | Six players: six intervals share one `ended_at`, equal to the set's |
| No inflation | With the clock moved 10 minutes after the end, each `play_seconds` is unchanged |
| Set isolation | Ending or resuming set 2 changes no interval of set 1 |
| Zero against missing | Count 0 is ready. Empty is refused. No count is never in a batch |
| Batch | Atomic on a forced failure. A second run handles the rest. A stale review is refused. One cash-out per player under retries and simultaneous hosts |
| Gates | The batch works with a discrepancy present, as individual cash-outs do today. Finalizing a set still needs balance or an override, and a final cash-out for each player |
| Access | Player 403, stranger 404, for each new action |
| Regression | Existing tests for buy-ins, individual cash-outs, reversals, override, units, add players and live updates pass. Tests that expected transfers at game finalization are updated for S2 and listed in the progress log |

## Rendezvous

The report gives what is ready against AC1–AC24, user test steps, checks with results on both engines, the commits, each open question that used its default, gaps, and the merge status. Nothing is pushed.

## Documentation sync

`doc/wiki/features.md`, `doc/wiki/architecture.md` (session and set, lifecycle of both, playing time, counts, batch, session settle-up), `doc/wiki/footguns/` (naming), `doc/roadmap/README.md`, `TODO.md`. `SPEC.md` is not edited by the AI.

## Blockers

None. An answer other than the default to Q1, Q2 or Q3 means a plan revision before work starts.

## Progress log

| Date | Entry |
|---|---|
| 2026-10-03 23:51 | Study and plan written and committed. Status `awaiting-approval`. |
| 2026-10-03 23:56 | The human stated that a session can have several sets, and answered four questions (S1–S4). Study addendum added. Plan revised: Part I (sessions with sets, session settle-up) added before Part II. Q1–Q6 still open. Status stays `awaiting-approval`. |

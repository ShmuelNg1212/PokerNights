# Plan: end-of-set cash-outs and playing time

- **Date:** 2026-10-03 23:51 (Asia/Manila), Unix timestamp `1791042668`
- **Status:** `awaiting-approval`
- **Study:** [../study/1791042572_end_of_set_cash_outs_and_timers.md](../study/1791042572_end_of_set_cash_outs_and_timers.md)
- **Workflow:** `agentic-workflow`. Phase 2 starts only after explicit human approval of this plan.
- **Approval record:** _none yet_

Edit this file directly, or add a line that starts with `NOTE:`.

---

## OPEN QUESTIONS

Each has a default. Q1, Q2 and Q3 change what is built.

| # | Question | Default (recommended) | Affects |
|---|---|---|---|
| **Q1** | **Chip conversion.** The request mentions "calculated peso cash-outs" and "the set's recorded chip conversion". The app has no conversion; you removed it on 2026-10-03. Is the final count typed in the game's unit (pesos, or chips in a chips game), with the cash-out equal to that count? | **Yes.** No conversion returns. The review shows one figure per player. Bringing back a chip rate would reverse the earlier decision and need its own plan | Tasks 2, 3 |
| **Q2** | **Stricter finalization.** Today a partial cash-out during play counts as "this player has a cash-out". May finalization require a **final** cash-out for each player, so that nobody's remaining stack is assumed? | **Yes.** The message names who is missing | Task 2 |
| **Q3** | **Resume after counting has started.** Resume exists, but no rule covers counts and cash-outs. Which rule? (a) Resume is allowed; confirmed counts that are not yet cashed out are voided, because stacks will change; players with a final cash-out stay cashed out until the host reverses it. (b) Resume is refused once any batch cash-out exists | **(a)** | Tasks 1, 2 |
| Q4 | **Breaks.** The app has no break feature. Leave it out? "Left" already stops a player's time, and a host can bring the player back | Yes, leave it out | Scope |
| Q5 | **End-time correction.** No rule exists. Leave editing of the end time out of this change? The end time is the moment the host taps "End play" | Yes, leave it out. Listed as a follow-up | Scope |
| Q6 | **Older games.** Fill their end time from the log, and show their playing time as "not recorded"? | Yes. No interval is invented | Task 1 |

---

## Goal

Playing time stops at one server timestamp when play ends. The host confirms final counts and cashes out all counted players in one reviewed, all-or-nothing action, as many times as needed.

## Scope

- `GameSession.ended_at` and per-player `PlayInterval` rows, opened and closed by the lifecycle services.
- Playing time on the game page and in the log, and stored with each frozen result.
- `FinalCount` records with versions; the three statuses "Awaiting count", "Ready to cash out", "Cashed out".
- `CashOut.kind` (`partial` or `final`), with links to its count and batch.
- The button "Cash out counted players (N)", a review page, and an atomic batch service with a stored `request_id`.
- The stricter finalization gate (Q2) and the resume rule (Q3).
- Tests, a browser check and docs.

## Exclusions

- Chip-to-peso conversion (Q1).
- Breaks (Q4) and end-time editing (Q5).
- Hourly statistics and leaderboards (Stage 3). Only the stored playing time is added.
- Reopening a finalized game and result revisions (Stage 2).
- Any change to payment marks, settle-up, or the override.

## Acceptance criteria

| # | Criterion |
|---|---|
| AC1 | When the host ends play, the game shows "Play ended" with one time. Each player's "Played" figure stops and does not grow afterwards, however long counting takes |
| AC2 | A player who left earlier keeps the playing time up to the moment they left |
| AC3 | Sending "End play" twice, reloading, or opening a second tab shows the same playing time. No time is counted twice |
| AC4 | While counting up, each player shows one of "Awaiting count", "Ready to cash out", "Cashed out" |
| AC5 | Confirming a count of 0 makes a player "Ready to cash out". An empty count field is refused, and the player stays "Awaiting count" |
| AC6 | The button reads "Cash out counted players (4)" with four ready players. With none it is disabled and says why |
| AC7 | The review lists the four players, each confirmed count, each cash-out amount and the total, and names the two players still to count |
| AC8 | One confirmation records four cash-outs. The page says "4 players cashed out; 2 awaiting final counts." The game is still counting up, and no payment is marked |
| AC9 | After the other two are counted, the same action cashes them out. The six cash-outs then feed the existing balance check and finalization |
| AC10 | If a count changes, or a player is cashed out elsewhere, after the review opened, the confirmation records nothing, explains why, and shows a fresh review. Confirmed counts are kept |
| AC11 | Sending the same confirmation twice, or from two hosts at once, records each cash-out once |
| AC12 | The individual cash-out still works during play (early departure) and while counting up (under "Details") |
| AC13 | Finalization is refused while any player lacks a final cash-out, and names them. The balance check and override work as before |
| AC14 | A player cannot confirm counts or run the batch. A person outside the group gets "not found" |
| AC15 | Another member's open game page shows the new statuses and the stopped time within about 5 seconds |
| AC16 | The log shows, apart from each other: when play ended, when each count was confirmed and by whom, when each cash-out was recorded, and when a payment was marked |
| AC17 | Your existing games keep their buy-ins, cash-outs, results and transfers |

## Dependencies and external inputs

None new. PostgreSQL 17 for the test run. The dev server stops for the work and restarts at the end.

## Branch strategy and rollback

- Branch `feat/end-of-set` from `main`. One Conventional Commit per task, tests green before each.
- Migrations add tables and columns and fill `ended_at` and `CashOut.kind` for existing rows. No existing amount changes. A backup with the SQLite backup API comes first.
- Rollback: revert the merge commit and restore the backup.
- Local merge to `main` at rendezvous. No push.

## Tasks

- [ ] **1. Record the end of play and track playing time.** `GameSession.ended_at`; `PlayInterval` with the one-open constraint; open and close hooks in start, end, resume, join, batch add, left, return and withdraw; `play_seconds` queries; "Played" and "Play ended" on the game page and in the log, with a small script that advances minutes while the game runs; data migration for `ended_at` from the audit log.
  - Commit: `feat(games): record when play ends and track playing time per player`
  - Done when: tests cover each event in the study's table, one shared end timestamp, early leavers, returns, resume, repeated requests, and the same figure on a reload.
- [ ] **2. Confirm final counts apart from cash-outs.** `FinalCount` with versions and voiding; `CashOut.kind` with a data migration; the three statuses; count entry on the counting-up screen; the individual cash-out under "Details" while counting up; the finalization gate on final cash-outs (Q2); resume voids uncashed counts (Q3); reversing a batch cash-out voids its count.
  - Commit: `feat(ledger): confirm final counts separately from cash-outs`
  - Done when: tests cover zero against empty, replace and clear, the statuses, the gate message, resume, access, and unchanged totals.
- [ ] **3. Cash out counted players in one action.** `CashOutBatch`; `cash_out_counted()`; the button with its count and disabled reason; the review page; the stale-review refusal; the success line.
  - Commit: `feat(ledger): cash out all counted players in one reviewed action`
  - Done when: tests cover success, a repeat run for the rest, stale count, player cashed out elsewhere, atomic rollback on a forced failure, retry by `request_id`, access, and no finalization or payment as a side effect.
- [ ] **4. Store playing time with results.** `PlayerResult.play_seconds`, written at finalization.
  - Commit: `feat(ledger): store playing time with each frozen result`
  - Done when: a test shows the stored figure equals the interval sum at the end of play, not at finalization.
- [ ] **5. Races and end-to-end.** Threaded tests on both engines: two hosts confirm overlapping batches; a batch against an individual cash-out; a batch against a count change; end play twice at once. One page-driven test of the six-player example.
  - Commit: `test: cover end-of-set batches, playing time and their races`
  - Done when: the tests pass on SQLite and PostgreSQL, and fail on PostgreSQL with the game lock removed.
- [ ] **6. Verify in a browser.** Headless Chrome at phone width: statuses, zero count, button count and disabled state, review, success line, stale review, playing time frozen after the end, second client update, keyboard, no horizontal scroll. Screenshots reviewed. Results recorded here.
  - Commit: `docs(plan): record verification results`
  - Done when: each acceptance criterion has a recorded result.
- [ ] **7. Rendezvous and docs.** Backup, migrate the dev database, merge to `main`, update `features.md`, `architecture.md`, the roadmap (breaks and end-time correction as follow-ups; playing time ready for Stage 3) and `TODO.md`, restart the server, set this plan to `done`.
  - Commit: `docs: sync living documentation`
  - Done when: `main` has the work, the tests pass on `main`, and the server answers.

## Verification

| Topic | Test |
|---|---|
| One end timestamp | Six players: after "End play", six intervals share one `ended_at`, equal to the game's |
| No inflation | With the clock moved 10 minutes forward after the end, each `play_seconds` is unchanged |
| Early leaver | A player marked left at T1 keeps T1 after the end at T2 |
| Return and resume | New intervals open; closed ones stay; totals add up; no overlap for one player |
| Idempotent | "End" twice, "start" hooks twice: no second interval, no changed timestamps |
| Zero against missing | Count 0 → ready. Empty → refused. No count → never in a batch |
| Versions | A new count raises the version. A review built on the old version is refused |
| Batch atomic | A forced failure in the middle leaves no cash-out, no batch, the same version |
| Batch repeat | Four, then two: six final cash-outs, two batches |
| Duplicates | The same `request_id`, and two hosts at once: one cash-out per player |
| Gates | The batch works with a discrepancy present (as individual cash-outs do today). Finalization is still refused until balanced or overridden, and until each player has a final cash-out |
| No side effects | After a batch: state `reconciliation`, zero `Finalization`, zero `Payment` |
| Access | Player 403, stranger 404, for count, review and batch |
| Regression | The existing tests for buy-ins, individual cash-outs, reversals, override, finalization, settle-up, paid marks, units, add players and live updates pass. Tests that assumed "any cash-out is enough" are updated for Q2 and listed in the progress log |
| Migration | Existing cash-outs get the right `kind`. `ended_at` is filled from the log. Amounts, results and transfers are unchanged |

## Rendezvous

The report gives what is ready against AC1–AC17, user test steps, checks with results on both engines, the commits, each open question that used its default, gaps, and the merge status. Nothing is pushed.

## Documentation sync

`doc/wiki/features.md`, `doc/wiki/architecture.md` (lifecycle, playing time, counts, batch, gates), `doc/roadmap/README.md`, `TODO.md`. `SPEC.md` is not edited by the AI.

## Blockers

None. An answer other than the default to Q1, Q2 or Q3 means a plan revision before work starts.

## Progress log

| Date | Entry |
|---|---|
| 2026-10-03 23:51 | Study and plan written and committed. Status `awaiting-approval`. |

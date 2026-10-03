# Plan: Poker home game architecture — Stage 1, game night

- **Date:** 2026-10-03 22:27 (Asia/Manila), Unix timestamp `1791037623`
- **Revised:** 2026-10-03 22:30 (Unix `1791037809`), after the human supplied `SPEC.md`
- **Status:** `done`
- **Study:** [../study/1791037419_poker_home_game_architecture.md](../study/1791037419_poker_home_game_architecture.md). Its **review addendum** controls where it differs from the earlier sections.
- **Workflow:** `agentic-workflow`. Phase 1 is complete with this file. Phase 2 (`execute plan => rendezvous => sync docs`) starts only after explicit human approval of this revised plan.
- **Approval record:** Approved by the human on 2026-10-03 22:35 (Asia/Manila): "ok i approve of the plan. proceed with the next steps." No answers were given to Q1–Q8, so each default applies.

This file is an editable task board. Edit a default, a criterion or a task directly, or add a line that starts with `NOTE:`. The AI preserves `NOTE:` lines.

---

## OPEN QUESTIONS

Each question has a default. If you approve the plan without an answer, the default applies and is recorded in the progress log.

| # | Question | Default (recommended) | Affects |
|---|---|---|---|
| **Q1** | **Settlement model, flagged for confirmation.** `SPEC.md` describes direct settle-up with an optional banker for the night. Is that the model? | **Yes.** Direct settle-up in Stage 1. The banker option in Stage 2 | Stage 1 results. Stage 2 scope |
| **Q2** | **Balance override.** `SPEC.md` allows "an explicit override with a note" when the books do not balance, and also requires that settle-up sums to zero. Both hold only if the override states who absorbs the difference. Is this rule correct: the host writes a note and selects (1) one named player, default the host, or (2) an equal share for all players? | Yes. The app never applies either option without the host's action | Stage 1 finalization |
| Q3 | **Tables per session.** Is a night with two tables two separate sessions, each with its own money? | Yes | Data model |
| Q4 | **Audience.** Is this for your own group, not a public release? | Own group. Sign-up is open, but a user sees nothing without an invite. Each member can join each open session, and each host can manage each session | Stage 1 access |
| Q5 | **Seating.** `SPEC.md` does not mention seat draws. The first request requires them. Do they stay in the roadmap after the `SPEC.md` MVP? | Yes, as Stage 4 | Roadmap order |
| Q6 | **Whole pesos.** Must transfers be rounded to whole pesos? | No. Exact centavos. A rate such as ₱1,000 for 10,000 chips gives whole pesos already | Stage 1 rounding |
| Q7 | **Win rate.** `SPEC.md` says "win rate". The first request says "wins" and "cash rate". Are win rate and cash rate one measure: the percentage of finalized sessions that ended in profit? | Yes. One measure, labeled "Win rate" | Stage 3 |
| Q8 | **Ranking threshold.** Is 3 sessions the default minimum to be ranked, changeable per group? | Yes | Stage 3 |

Stated for clarity, not questions:

- Approval of this plan also approves `git init` in `/Users/shm/PokerNights` (task 1). No remote is added. Nothing is pushed or deployed.
- `SPEC.md` is not in the project folder. Task 1 stores it at the repository root, unchanged, from the text you supplied. If you prefer, place your own copy there first and the AI uses that.
- The "starter prompt" inside `SPEC.md` is not treated as approval.

---

## Goal

Deliver Stage 1: **one cash-game night from creation to settle-up, with correct money.** This covers `SPEC.md` build steps 1 to 3.

A host creates a session, adds players from the roster, logs buy-ins and rebuys, records cash-outs as players leave, sees whether the books balance, finalizes, and gets the minimum list of who pays whom. The host marks each transfer paid. Each member sees the live figures on their own phone.

## Scope

### Full product architecture (context, not submitted for execution)

The study and its addendum define the full design. The roadmap follows the `SPEC.md` build order:

| Stage | Outcome | `SPEC.md` step | Status |
|---|---|---|---|
| **1. Game night** | Buy-ins and rebuys, cash-outs with balance check, settle-up with paid marks | 1, 2, 3 | **Submitted for approval in this plan** |
| 2. Roster, history, banker, corrections | Roster management, history list, optional banker, payments before finalization, reopen a finalized session | 4 | Future cycle |
| 3. Leaderboard and stats | Seasons; month, season, year and all-time filters; player stats | 5 | Future cycle |
| 4. Seating | Manual seats and random draws | First request | Future cycle |
| 5. Shared use | Guest claim links, password reset, deployment, design pass | — | Future cycle |
| Later | RSVP and waitlist, recurring games, reminders, IOUs across sessions, rake and tips, session timer, notes, export, chip denominations, bankroll graph | "Later" | Not planned |

Each later stage needs its own study, plan and approval.

### Stage 1 scope (submitted for execution approval)

- Repository setup, `SPEC.md`, Django project foundation, docs skeleton.
- Apps: `config`, `accounts`, `groups`, `games`, `ledger`, `settlement`, `audit`.
- Accounts: sign-up, login, logout.
- One group per host to start: roles `host` and `player`, invite links, and a roster in which a host adds players by name without a login.
- Tables with a seat count. Reusable presets: stakes, game type, minimum and maximum buy-in, default buy-in, chip rate.
- Sessions with date, location, table, stakes, game type, versioned settings, and the lifecycle `setup → open → running → reconciliation → finalized`, plus `canceled`.
- Adding players and joining, with capacity and duplicate protection. Late joins.
- Buy-ins and rebuys with amount, chips and time, with reversals. A running total per player.
- Live view with polling: player count, buy-in count, total pesos bought in, chips in play.
- Cash-outs in one or several steps, with reversals.
- Balance check with the difference and its direction. Finalization is blocked until balanced, or until the host records an override with a note (Q2).
- Finalization with immutable result snapshots.
- Settle-up with the proven minimum number of transfers. Each player sees their net result and what they owe or are owed.
- Mark a transfer paid, and undo it. Unpaid transfers stay visible.
- Session detail page with the full log.

Each `SPEC.md` step is usable when its tasks are complete: step 1 after task 14, step 2 after task 16, step 3 after task 19.

### Exclusions from Stage 1

- Roster management pages beyond add and rename, and the history list with filters (Stage 2). The group page lists past sessions.
- Banker option, payments recorded before finalization, reopening a finalized session (Stage 2).
- Leaderboards, statistics across sessions, seasons (Stage 3).
- Seats and draws (Stage 4).
- Guest claim links, password reset by email, deployment, visual design work (Stage 5).
- Tournaments, blind timer, payments, public discovery (out of product scope).

## Acceptance criteria (Stage 1)

A person can check each criterion in the browser, without reading code.

| # | Criterion |
|---|---|
| AC1 | A new user signs up, logs in and creates a group. That user is a host |
| AC2 | A host creates an invite link. A second user opens it and becomes a player. Opening it again changes nothing |
| AC3 | A user who is not in the group gets "not found" for the group, its tables and its sessions |
| AC4 | A host adds a player to the roster by name, without a login |
| AC5 | A host creates a preset with stakes, game type, minimum and maximum buy-in, and a chip rate |
| AC6 | A host creates a session with date, location, table and preset, and opens it. Players are added from the roster or join themselves. A second tap on "Join" does not add a second entry. A player joins after the game starts |
| AC7 | When the table is full, the next join is refused with a clear message |
| AC8 | A host logs a buy-in and two rebuys for one player. The row shows each amount with its time, the rebuy count and the running total |
| AC9 | A buy-in below the minimum or above the maximum is refused |
| AC10 | The live view shows player count, buy-in count and total pesos bought in, with ₱. Chips are shown as chips, never with ₱. A second phone shows a change within 5 seconds |
| AC11 | A double tap on "Buy-in" records one buy-in |
| AC12 | A host reverses a buy-in with a reason. The totals change. The reversed buy-in stays in the log |
| AC13 | After a preset is edited, the buy-ins already recorded keep their amounts and chips |
| AC14 | A player cashes out part of a stack, plays on, and cashes out the rest later. The total is the sum of both |
| AC15 | With books that do not balance, "Finalize" is refused. The screen states the amount of the difference in chips and pesos and whether chips are missing or extra |
| AC16 | The host records an override with a note and a named player who absorbs the difference. Finalization then succeeds. The results show the adjustment on its own line, and the net results sum to ₱0 |
| AC17 | With the worked example (A ₱1,000 → 16,000 chips, B ₱1,000 → 7,000, C ₱500 → 2,000, at ₱1,000 per 10,000 chips), finalization shows A +₱600, B −₱300, C −₱300, and the transfers "B pays A ₱300" and "C pays A ₱300" |
| AC18 | Each player sees their own net result and what they owe or are owed |
| AC19 | The host marks one transfer paid. It shows as paid with a time. The other transfer stays visible as unpaid. The session shows "partly settled", then "settled" when both are paid |
| AC20 | After finalization, the buy-in and cash-out controls are gone, and direct requests to them are refused |
| AC21 | A player cannot record a buy-in, a cash-out, a paid mark or a state change, even with a hand-made request |
| AC22 | The session detail page lists players, settings, each buy-in, reversal and cash-out, the results and the transfers, with who did what and when |
| AC23 | The screens are usable with one hand at phone width and use a dark color scheme |

## Sources and current repository state

- **Source study:** linked above, with the review addendum of 2026-10-03 22:30.
- **Canonical source:** `SPEC.md`, human-written, supplied on 2026-10-03. Not yet in the folder.
- **First request:** the architecture brief of this cycle. Where it and `SPEC.md` differ, the study addendum (A3) and the OPEN QUESTIONS list the difference.
- **Reference:** LightChat at commit `2f5d10ad86f8e04e5a6b47ea0516b86d708b0927`.
- **Repository state on 2026-10-03:** `/Users/shm/PokerNights` contains only `doc/study/` and `doc/plan/` with one file each. It is not a Git repository. The two files are not committed. No `AGENTS.md`, wiki or `TODO.md` exists.

## Dependencies and external inputs

| Item | Detail | Status |
|---|---|---|
| Python | 3.14 (local 3.14.8) | Verified |
| `Django` | `==6.1.1` | Verified: LightChat pin and latest on PyPI, 2026-10-03 |
| `django-environ` | `==0.14.0` | Verified, same |
| `dj-database-url` | `==3.1.2` | Verified, same |
| `psycopg[binary]` | `==3.3.6` | Verified, same |
| Other packages | None | — |
| PostgreSQL 17 | Installed with Homebrew. Not running. Phase 2 starts it and creates a local role and database `pokernights` for tests | AI does this after approval |
| Secrets | None for Stage 1. `.env.example` lists each variable name and purpose | — |
| `SPEC.md` text | Supplied in the conversation | Verified |
| Answers to Q1–Q8 | Defaults apply if not answered | Human |

At execution, the AI runs `pip index versions` again and records any newer release in the progress log.

## Branch strategy and rollback

- Task 1 creates the repository on `main` and commits `SPEC.md` and the two Phase 1 documents.
- Tasks 2 onward run on branch `feat/game-night`.
- Each task is one Conventional Commit. The tests run before each commit and must pass.
- At rendezvous, the branch merges to `main` locally. Nothing is pushed.
- Rollback: `git revert` of a task commit, or abandon the branch. Stage 1 has no deployed data.

## Design rules that each task must follow

1. Money is integer centavos. Chips are integer chip units. No `float`.
2. Only `services.py` functions write. Each write to a session runs in `transaction.atomic()` and locks the session row with `select_for_update()` first.
3. Each write that a person starts carries a `request_id` with a unique constraint.
4. Money records are append-only. A correction is a reversal or a new row with a reason.
5. Each view resolves objects through the requester's active membership. A miss returns 404. Host actions check the role in the service.
6. Each write service calls `audit.record()` and increments `GameSession.version`.
7. Totals are queries. Only finalization writes snapshots.
8. Dates use Asia/Manila. Money displays as `₱1,600` or `₱1,600.50`.
9. Screens are single-column, dark by default, with large touch targets.

## Tasks

Check a box only when its completion criterion is met.

### A. Repository and foundation

- [x] **1. Initialize the repository and commit the source documents.** `git init` on `main`. Add `.gitignore`. Add `SPEC.md` unchanged. Commit the study, then the plan with the approval recorded.
  - Commits: `chore: initialize repository` · `docs: add project spec` · `docs: study poker home game architecture` · `docs: plan poker home game architecture`
  - Done when: `git log --oneline` shows the four commits and `git status` is clean.
- [x] **2. Scaffold the Django project.** `config/` package, `requirements.txt` with the four pins, `.python-version`, `.env.example`, env-based settings, `config/deploy.py` database options (SQLite `IMMEDIATE` + WAL; PostgreSQL), `TIME_ZONE = "Asia/Manila"`, `LoginRequiredMiddleware`, `/healthz`, a smoke test.
  - Commit: `build: scaffold Django project`
  - Done when: `manage.py check` and `manage.py test` pass, and `/healthz` returns `ok`.
- [x] **3. Add `TODO.md`, a short `AGENTS.md` and the wiki index.**
  - Commit: `docs: add working agreement, todo and wiki index`
  - Done when: the files exist and link to `SPEC.md`, the study and this plan.
- [x] **4. Add the custom user model and auth pages.** `accounts.User(AbstractUser)` first. Sign-up, login, logout. `templates/base.html` with the dark, single-column shell and `static/css/app.css`.
  - Commit: `feat(accounts): add user model, sign-up, login and logout`
  - Done when: tests cover sign-up, login, logout and the login-required redirect.
- [x] **5. Add the audit app.** `AuditEvent` and `audit.record()`. Read-only admin.
  - Commit: `feat(audit): add append-only audit events`
  - Done when: a test shows that an event rolls back with its caller's transaction.

### B. Group and roster

- [x] **6. Add groups and members.** `GameGroup`, `Member` (roles, optional user, optional contact text), the access helper, group create and group page, last-host protection.
  - Commit: `feat(groups): add groups, members and roles`
  - Done when: tests cover the unique constraints, last-host protection, and 404 for a non-member.
- [x] **7. Add invite links.** Hashed token, expiry, use limit, revoke, accept flow.
  - Commit: `feat(groups): add invite links`
  - Done when: tests cover valid, expired, revoked, used-up and repeated acceptance.
- [x] **8. Add roster players without logins.** A host adds and renames a player by name.
  - Commit: `feat(groups): add roster players without logins`
  - Done when: tests show that only a host can add a player and that a duplicate active name is refused.

### C. `SPEC.md` step 1: session with buy-ins and rebuys

- [x] **9. Add `money.py`.** Parse peso input to centavos, format centavos, chip-rate reduction, chips for an amount, value of chips, largest-remainder allocation, equal split with remainder. Pure functions.
  - Commit: `feat(ledger): add integer money and chip-rate functions`
  - Done when: unit tests cover parsing limits, formatting, and allocation sums that equal the total for random inputs and for amounts that do not divide evenly.
- [x] **10. Add tables and presets.**
  - Commit: `feat(games): add tables and settings presets`
  - Done when: tests cover the checks (minimum ≤ default ≤ maximum, positive rate), host-only writes and group isolation.
- [x] **11. Add sessions, settings versions and the lifecycle.** `GameSession` with date, location, table, game type. `SettingsVersion` with stakes, minimum, maximum, default buy-in and chip rate. The state machine service. Cancel rule.
  - Commit: `feat(games): add sessions with versioned settings and lifecycle`
  - Done when: a table-driven test covers each allowed and each refused transition per role.
- [x] **12. Add session players and joining.** `Participant`, host add from the roster, self join, withdraw, capacity under the session lock, late join.
  - Commit: `feat(games): add session players with capacity and duplicate protection`
  - Done when: tests cover duplicate join, rejoin, a full table, late join and state rules.
- [x] **13. Add buy-ins, rebuys and reversals.** `BuyIn`, `BuyInReversal`, chip-rate lock at the first buy-in, minimum and maximum check, whole-chip check, `request_id` uniqueness, running totals.
  - Commit: `feat(ledger): add buy-ins and rebuys with reversals`
  - Done when: tests cover several rebuys by one player, the rate lock, refused amounts, a repeated `request_id`, reversal, and total = Σ recorded amounts.
- [x] **14. Add the host console and the live view with polling.** Session page, `state` endpoint with version check (HTTP 204 when unchanged), `static/js/live.js` (4 s poll, visibility pause, backoff, "last updated" notice), `static/js/forms.js` (double-submit guard).
  - Commit: `feat(games): add live session view with polling`
  - Done when: tests cover the endpoint (unchanged, changed, non-member 404), and a check with two browser windows shows an update within 5 seconds. **`SPEC.md` step 1 is usable.**

### D. `SPEC.md` step 2: cash-outs with balance check

- [x] **15. Add cash-outs.** `CashOut`, `CashOutReversal`, several cash-outs per player, explicit zero cash-out, the `left` mark, chips-in-play calculation.
  - Commit: `feat(ledger): add cash-outs in one or several steps`
  - Done when: tests cover a player who cashes out in several steps, a zero cash-out, a reversal and chips in play.
- [x] **16. Add the balance check and override.** The checks of study §7.8 with addendum A3.3 and A3.4. The difference with its direction. `BalanceAdjustment` with a required note and a named player or an equal share. The reconciliation screen.
  - Commit: `feat(ledger): add balance check with explained discrepancies`
  - Done when: tests cover a balanced session, a small surplus, a small shortfall, a missing cash-out, each override option, an equal share that does not divide evenly, and the absence of any automatic adjustment. **`SPEC.md` step 2 is usable.**

### E. `SPEC.md` step 3: settle-up

- [x] **17. Add the settle-up algorithm.** Pure functions: balances from nets and payments, the zero-sum partition by dynamic programming over subsets, transfers inside each group, deterministic order, greedy fallback above 16 parties (study addendum A3.5).
  - Commit: `feat(settlement): add minimum-transfer settle-up`
  - Done when: tests cover the worked example, a winner paid by several losers, two independent pairs (2 transfers, not 3), the prior-payment case, the banker case, tie order, a zero sum for each output, and equality with a brute-force minimum on random inputs of up to 7 parties.
- [x] **18. Add finalization.** The transaction of study §7.9: `Finalization`, `PlayerResult`, `SettlementPlan`, `Transfer`, conservation asserts, state change. Results screen with each player's net and what they owe or are owed.
  - Commit: `feat(ledger): add finalization with result snapshots and transfers`
  - Done when: tests cover refused finalization on an unbalanced session, the worked example end to end, a fractional chip rate with centavo remainders, immutability after finalization, and an aborted transaction that leaves no partial rows.
- [x] **19. Add paid marks.** `Payment` linked to a `Transfer`, `PaymentReversal`, the settlement status.
  - Commit: `feat(settlement): mark transfers paid`
  - Done when: tests cover mark, undo, a repeated request, host-only access and the three status values. **`SPEC.md` step 3 is usable.**
- [x] **20. Add the session detail log.** One page with players, settings versions, buy-ins, reversals, cash-outs, adjustments, results, transfers, payments and audit events. Past sessions on the group page.
  - Commit: `feat(games): add session detail log`
  - Done when: tests show the full log for a member and 404 for a non-member.

### F. Concurrency and verification

- [x] **21. Add concurrency tests.** Threads with a barrier: simultaneous joins for the last seat, one `request_id` from several threads, simultaneous buy-ins, finalize against a simultaneous buy-in, two simultaneous paid marks on one transfer.
  - Commit: `test: cover concurrent joins, duplicate writes and finalization races`
  - Done when: the tests pass on SQLite **and** on PostgreSQL 17.
- [x] **22. Add an end-to-end acceptance test.** One test drives the worked example through the views, from sign-up to "settled".
  - Commit: `test: add end-to-end acceptance for the worked example`
  - Done when: the test passes on both engines.
- [x] **23. Verify.** Run the full suite on both engines. Run `manage.py check --deploy` with production-like settings. Run the application and walk AC1–AC23 in a browser at phone width. Record results in the progress log.
  - Commit: `docs(plan): record verification results`
  - Done when: each acceptance criterion has a recorded result.

### G. Rendezvous and documentation sync

- [x] **24. Rendezvous.** Merge `feat/game-night` to `main` locally. Report what is ready, the user test steps, expected results, checks, commits, assumptions and gaps.
  - Done when: `main` has the work, the tests pass on `main`, and the report is delivered.
- [x] **25. Sync living docs.** Write `doc/wiki/setup.md`, `architecture.md` (as built), `features.md`, `external-dependencies.md`, and `doc/wiki/footguns/`. Add `doc/roadmap/` with Stages 2 to 5 and the "Later" list. Update `TODO.md`. Set this plan to `done`.
  - Commit: `docs: sync living documentation`
  - Done when: each wiki page matches the code and the index links to each page.

## Verification matrix

| Topic | Criterion | Test | Stage |
|---|---|---|---|
| Duplicate buy-ins | Two requests with one `request_id` create one `BuyIn`. Ten threads with one `request_id` create one | Unit + threaded, both engines | 1 |
| Concurrent joins | With one free seat and ten simultaneous joins, one succeeds. Ten simultaneous joins by one member create one row | Threaded, both engines | 1 |
| Access isolation | A non-member gets 404 for each group URL. A player is refused each host action, including hand-made POSTs | View tests over a URL list | 1 |
| Chip mismatches | A surplus and a shortfall each block finalization and show the amount and the direction. Nothing changes without a host record | Service + view tests | 1 |
| Settlement conservation | Σ cash-outs + Σ adjustments = Σ buy-ins. Σ net = 0. Applying the transfers makes each balance zero. Fractional rates lose no centavo | Unit + random-input tests | 1 |
| Minimum transfers | The transfer count equals the brute-force minimum on random inputs | Unit test | 1 |
| Prior payments (algorithm) | With C → A ₱200 recorded, the transfers are B → A ₱300 and C → A ₱100 | Unit test on the pure function | 1 |
| Paid marks | A paid transfer and an undone mark change the status as stated | Service + view tests | 1 |
| Prior payments (records) | A payment recorded before finalization changes the transfers as the formula states | Service + view tests | 2 |
| Corrections before finalization | A reversal restores the totals and stays in the log. No money row is updated or deleted | Service tests | 1 |
| Corrections after finalization | A reopen creates revision 2. Revision 1 stays. Payments under revision 1 count as prior payments | Service tests | 2 |
| Leaderboard accuracy | A fixed data set gives known profit/loss, sessions, average result, wins, win rate and aggregate ROI for month, season, year and all-time. Canceled and break-even sessions, zero denominators, ties, the threshold, Manila boundaries and corrected results behave as the study states | Unit tests on a fixture | 3 |
| Seat uniqueness | A draw gives each eligible player one seat and no seat twice. Two simultaneous draws leave one valid arrangement | Unit + threaded, both engines | 4 |

`SPEC.md` money tests and where they are covered:

| `SPEC.md` test | Task |
|---|---|
| Perfectly balanced sessions | 16, 18 |
| Small discrepancies | 16 |
| Players who cash out in several steps | 15 |
| Players who rebuy several times | 13 |
| A winner paid by multiple losers | 17 |
| Rounding when amounts do not divide evenly | 9, 16, 18 |
| Settle-up sums to zero across all players | 17, 18 |

Checks that run in Stage 1: `manage.py test` on SQLite, the same suite on PostgreSQL 17, `manage.py check --deploy`, and a browser walk of AC1–AC23. A check that cannot run is reported as unavailable, not as passed.

## Rendezvous

At the end of execution, the AI reports:

- What is ready, mapped to AC1–AC23 and to `SPEC.md` steps 1 to 3.
- Exact steps to test as a user, with expected results.
- Checks run, with results, on both database engines.
- The commit list.
- Assumptions, including each open question that used its default.
- Known gaps, including the Stage 1 exclusions.
- Branch and merge status.

The merge to `main` is local. A push, a remote and a deployment each need a separate instruction.

## Documentation sync

| Document | Content |
|---|---|
| `SPEC.md` | Not edited by the AI |
| `doc/wiki/README.md` | Index and current state |
| `doc/wiki/setup.md` | Install, `.env`, run, test on both engines |
| `doc/wiki/architecture.md` | Apps, data model, lifecycle, money rules, live updates, as built |
| `doc/wiki/features.md` | What hosts and players can do today |
| `doc/wiki/external-dependencies.md` | Pins and local PostgreSQL |
| `doc/wiki/footguns/` | Confirmed footguns |
| `doc/roadmap/` | Stages 2 to 5 and "Later" |
| `TODO.md` | Short active items with links |

The study is not rewritten. A changed finding gets a dated addendum.

## Blockers

None. Q1 and Q2 have defaults. An answer other than the default to Q1 or Q2 needs a plan revision before execution.

## Progress log

| Date | Entry |
|---|---|
| 2026-10-03 22:27 | Study and plan written. No repository exists, so neither file is committed. Status `awaiting-approval`. |
| 2026-10-03 22:30 | The human supplied `SPEC.md` as context. Study addendum added. Plan revised: roadmap follows the `SPEC.md` build order; cash-outs in several steps; balance override with a named absorber; proven minimum transfers; paid marks moved into Stage 1; session fields for location, game type, minimum and maximum buy-in. Status stays `awaiting-approval`. |
| 2026-10-03 22:35 | Human approved the revised plan. Defaults apply to Q1–Q8. Status `in-progress`. `SPEC.md` stored at the repository root from the supplied text. |
| 2026-10-03 22:40 | `pip index versions`: the four pins are still the latest releases. Tasks 1–20 executed on `feat/game-night`, one Conventional Commit each, tests green before each commit. |
| 2026-10-03 23:05 | Verification (task 23). See "Verification results" below. |
| 2026-10-03 23:15 | Rendezvous: `feat/game-night` merged to `main` locally with a merge commit. 213 tests pass on `main` on SQLite and PostgreSQL 17. Living docs synced. Nothing was pushed or deployed; no remote exists. Status `done`. |

## Verification results (2026-10-03)

### Checks

| Check | Result |
|---|---|
| `manage.py test` on SQLite | 213 tests, pass |
| Same suite on PostgreSQL 17.11 (`DATABASE_URL=postgres://…/pokernights`) | 213 tests, pass |
| Concurrency tests have teeth | With `select_for_update()` removed, 8 of 9 failed on PostgreSQL. Lock restored, 9 pass |
| `manage.py check --deploy` with `DEBUG=False`, a random `SECRET_KEY`, `HTTPS_ONLY=True` | No issues (3 silenced by design: HSTS subdomains, HSTS preload, console mail) |
| `makemigrations --check` | No changes |
| `pip check` | No broken requirements |
| Headless Chrome at 390 × 844 against `runserver` | 13 of 13 checks pass: dark background, no horizontal scroll (login, group, session, log), no host controls for a player, controls at least 40 px high, live update on a second client in 4.0 s, double tap records one buy-in, an update waits while the host types and applies after, no chip count shown with ₱ |
| Screenshots of the session, balance, results and log screens | Reviewed by the AI. One defect found and fixed: after finalization the page still showed "Chips in play", "seats free" and an empty host card (`fix(web)` commit) |

Not checked: a physical phone, a real network between devices, and a production web server. The browser check used desktop Chrome in phone emulation on this machine.

### Acceptance criteria

| # | Result | Evidence |
|---|---|---|
| AC1 | Met | `accounts.tests.test_auth`, `groups.tests.test_groups`, acceptance test |
| AC2 | Met | `groups.tests.test_invites`, acceptance test |
| AC3 | Met | 404 tests in each app's view tests |
| AC4 | Met | `groups.tests.test_roster` |
| AC5 | Met | `games.tests.test_tables_presets` |
| AC6 | Met | `games.tests.test_sessions`, `test_participants` (late join, double tap) |
| AC7 | Met | `test_participants`, concurrency test "last seat" |
| AC8 | Met | `ledger.tests.test_buy_ins` |
| AC9 | Met | `test_buy_ins` (range and whole-chip checks) |
| AC10 | Met | `web.tests.test_live`; browser check: 4.0 s on a second client |
| AC11 | Met | `test_buy_ins`, concurrency test, browser double-tap check |
| AC12 | Met | `test_buy_ins.ReversalTests` |
| AC13 | Met | `test_buy_ins` (settings change, preset edit) |
| AC14 | Met | `ledger.tests.test_cash_outs` |
| AC15 | Met | `ledger.tests.test_balance`, `settlement.tests.test_finalize` |
| AC16 | Met | `test_balance.OverrideTests`, `test_finalize` (results sum to zero) |
| AC17 | Met | `test_finalize`, `web.tests.test_acceptance` |
| AC18 | Met | `test_finalize.FinalizeViewTests` |
| AC19 | Met | `settlement.tests.test_payments` |
| AC20 | Met | `test_finalize.AfterFinalizationTests` |
| AC21 | Met | 403 tests for each host action |
| AC22 | Met | `web.tests.test_log` |
| AC23 | Met in emulation | Browser check and screenshots. Not tried on a physical phone |

### Differences from the plan

| Topic | Plan | Built | Reason |
|---|---|---|---|
| Apps | Seven apps | An eighth app, `web`, with no models | The session page reads from `games`, `ledger` and `settlement`. Placing it in one of them would reverse the dependency direction |
| `Payment` | In `ledger` | In `settlement` | A payment links to a `Transfer`. In `ledger` it would make `ledger` depend on `settlement` |
| Balance override | `BalanceAdjustment.amount_centavos` | `BalanceAdjustment.chips_delta` | A chip can be worth a fraction of a centavo. An override in chips keeps the centavo rule exact |
| "Has money" rule | Count accepted buy-ins | The session's locked chip rate | `games` can apply the cancel rule without importing `ledger`. The rate unlocks when the last accepted buy-in is reversed |
| Task 21 race | Finalize against a simultaneous buy-in | Finalize against a simultaneous cash-out and against a buy-in reversal; a buy-in against the end of play | A buy-in is already refused in the counting stage, so that race has one outcome. The tested races can go either way |
| Task 23 | Walk AC1–AC23 in a browser | Automated headless Chrome run plus the end-to-end test | The AI has no hands-on phone. The human test steps are in the rendezvous report |
| Extra commit | — | `fix(web): hide live-only figures and empty host controls after finalization` | Found in the screenshot review |

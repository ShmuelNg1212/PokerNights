# Plan: cash amounts and a unit option

- **Date:** 2026-10-03 23:11 (Asia/Manila), Unix timestamp `1791040305`
- **Status:** `done`
- **Study:** [../study/1791040240_cash_amounts_and_unit_option.md](../study/1791040240_cash_amounts_and_unit_option.md)
- **Workflow:** `agentic-workflow`. Phase 2 starts only after explicit human approval of this plan.
- **Approval record:** Approved by the human on 2026-10-03 23:14 (Asia/Manila): "yes, the chip games mean that the chips have no peso value. for cash games, all metrics are based on the peso value of the chips. continue with the workflow." Q1 = A. Q2 not answered, so the default applies (keep and convert).

Edit this file directly, or add a line that starts with `NOTE:`.

---

## OPEN QUESTIONS

| # | Question | Default (recommended) | Affects |
|---|---|---|---|
| **Q1** | **What does a chips game mean?** (A) A game is in pesos or in chips, with no conversion. A chips game shows buy-ins, cash-outs, results and transfers as chip numbers. Or (B) a chips game still converts chips to pesos at a rate, as the app does today | **A.** No conversion anywhere. The unit is a label on one number system | The whole plan. B needs a different plan |
| Q2 | **Your test games.** The dev database has 2 groups and 2 sessions, one finalized. Keep them and convert the chip cash-outs to pesos, or start empty? | Keep and convert. A backup of `db.sqlite3` is made first | Task 3 |

Stated for clarity:

- This replaces two lines of `SPEC.md` step 2 ("final chip count", "convert chips to cash"). The AI does not edit `SPEC.md`. The wiki will record the difference unless you update the file.
- The dev server stops during the work and starts again at the end, because the code and the database change under it.

---

## Goal

Cash-outs are recorded as amounts, not chip counts. The app has no chip-to-peso conversion. Each game has a unit: pesos by default, or chips.

## Scope

- A `unit` on presets and sessions: `php` (default) or `chips`.
- Buy-ins, cash-outs, overrides, results and transfers are amounts in the game's unit.
- Removal of chips per buy-in, the chip rate, the whole-chip check, chip columns and the chip rounding rule.
- Balance check in the unit: total cashed out equals total bought in.
- Unit-aware input and display on each screen and in the log.
- Conversion of existing data to pesos.
- Updated tests and living docs.

## Exclusions

- A chip-to-peso rate for chips games (option B).
- Chip denominations.
- Leaderboards and statistics. The roadmap gets one rule: boards are per unit.
- Stage 2 items (banker, payments before finalization, reopening).

## Acceptance criteria

| # | Criterion |
|---|---|
| AC1 | A preset and a new game have a "Unit" choice: Pesos (₱) or Chips. Pesos is selected by default. No screen asks for "chips per buy-in" |
| AC2 | In a pesos game, the host cashes a player out by typing a peso amount. The player line shows "Cashed out ₱1,600" |
| AC3 | The pesos worked example gives the same result as before: A buys in ₱1,000 and cashes out ₱1,600; B ₱1,000 and ₱700; C ₱500 and ₱200. Results +₱600, −₱300, −₱300. "B pays A ₱300" and "C pays A ₱300" |
| AC4 | When total cash-outs differ from total buy-ins, "Finalize" is refused and the screen shows the difference as an amount with its direction |
| AC5 | A player cashes out in two steps. The total is the sum |
| AC6 | In a chips game, each amount shows as "1,600 chips". No ₱ appears on that game's screens or log. Chip input with decimals is refused |
| AC7 | A chips game finalizes and lists transfers in chips, for example "B pays A 3,000 chips" |
| AC8 | The unit of a game cannot change after the first accepted buy-in |
| AC9 | The live view shows players, buy-ins, total bought in and "Still in play" (bought in minus cashed out). No "Chips in play" tile exists in a pesos game |
| AC10 | Your existing finalized test game shows the same results and transfers after the change. Your open test game shows its cash-outs in pesos |
| AC11 | The override, reversals, paid marks, access rules and live updates work as before |

## Dependencies and external inputs

None new. PostgreSQL 17 is started for the test run and stopped after it.

## Branch strategy and rollback

- Branch `feat/cash-units` from `main`. One Conventional Commit per task, tests green before each.
- Before task 3 touches the real database: copy `db.sqlite3` to `db.sqlite3.before_cash_units` (gitignored).
- Rollback of code: revert the merge commit. Rollback of data: restore the copy. The data migration itself is one-way, because chip counts are dropped.
- Local merge to `main` at rendezvous. No push.

## Tasks

- [x] **1. Add unit-aware amounts to `ledger/money.py`.** `parse_amount(text, unit)`, `format_amount(value, unit)`, signed format, input-field format. Template filters take the unit.
  - Commit: `feat(ledger): add unit-aware amount parsing and formatting`
  - Done when: unit tests cover pesos and chips, including refused decimals for chips.
- [x] **2. Move the "this game has money" rule off the chip rate.** `games` gets a guard list that `ledger` registers with, as the withdraw guard does. Cancel uses it.
  - Commit: `refactor(games): detect money in a session with a guard, not the chip rate`
  - Done when: the lifecycle and cancel tests pass without reading the rate.
- [x] **3. Record amounts instead of chips.** Models: add `unit` to presets, sessions, finalizations and results; turn `CashOut.chips` and `BalanceAdjustment.chips_delta` into amounts; drop `BuyIn.chips`, `chips_per_buy_in`, the session rate and the chip columns on results; rename `…_centavos` columns to neutral names. One schema-and-data migration converts existing chip values to centavos per session with the largest-remainder rule. Services, queries, balance check, finalization, forms, templates and tests follow. All games are pesos games at this point.
  - Commit: `feat!: record cash-outs and overrides as amounts, without chip conversion`
  - Done when: the full suite passes on both engines; a migration test converts a session with a fractional chip rate and the amounts still sum to the buy-ins; the migration runs on a copy of your database and AC10 holds.
- [x] **4. Add chips as a unit.** Unit choice on the preset form and the new-game form; unit change refused once money is in the game; each screen and the log format by the game's unit.
  - Commit: `feat(games): add chips as a session unit`
  - Done when: tests cover AC6, AC7 and AC8, and a test asserts that a chips game's pages contain no ₱.
- [x] **5. Remove dead chip arithmetic.** `reduce_rate`, `chips_for_amount`, `value_floor`, `allocate` and their tests, where nothing uses them after task 3. The migration keeps its own frozen copy.
  - Commit: `refactor(ledger): remove chip-rate arithmetic`
  - Done when: the suite passes and a search for these names finds only the migration.
- [x] **6. Update the end-to-end and concurrency tests, and verify.** Both engines, `check --deploy`, the headless-browser run at phone width with a pesos game and a chips game, and a look at the screenshots.
  - Commit: `test: cover cash amounts and the chips unit end to end`
  - Done when: each acceptance criterion has a recorded result in this plan.
- [x] **7. Rendezvous and docs.** Apply the migration to the real dev database after the backup. Merge to `main`. Update `architecture.md`, `features.md`, the footguns (remove `adjustments_are_in_chips.md`), the roadmap (per-unit leaderboards; the `SPEC.md` difference) and `TODO.md`. Restart the server. Set this plan to `done`.
  - Commit: `docs: sync living documentation`
  - Done when: `main` has the work, the tests pass on `main`, and the server answers.

## Verification

| Topic | Criterion |
|---|---|
| Conservation | Total cash-outs + overrides = total buy-ins at finalization. Results sum to zero. Database checks stay |
| Migration | Converted amounts per session sum to the old converted total. A finalized session's results and transfers are unchanged |
| Units | A chips game never shows ₱. A pesos game never shows a chip count. Chip input must be whole |
| No float | Amounts stay integers in parsing, storage and arithmetic |
| Regression | Duplicate submissions, concurrent joins, finalize races, access isolation, reversals and paid marks pass on SQLite and PostgreSQL |

## Documentation sync

`doc/wiki/architecture.md`, `features.md`, `README.md`, `footguns/`, `doc/roadmap/README.md`, `TODO.md`. `SPEC.md` is not edited by the AI.

## Blockers

None. If Q1 is answered "B", this plan is replaced before any work starts.

## Progress log

| Date | Entry |
|---|---|
| 2026-10-03 23:11 | Study and plan written and committed. Status `awaiting-approval`. |
| 2026-10-03 23:14 | Human approved. Q1 answered: a chips game has no peso value; a pesos game shows each figure in pesos. Dev server stopped. Database backed up to `db.before_cash_units.sqlite3` with the SQLite backup API (a plain file copy would have missed data still in the write-ahead log). |
| 2026-10-03 23:27 | Tasks 1–6 done on `feat/cash-units`. Migration applied to the real dev database after the backup. Docs synced. Merged to `main` locally. Dev server restarted. Status `done`. |

## Verification results (2026-10-03)

| Check | Result |
|---|---|
| `manage.py test` on SQLite | 227 tests, pass |
| Same suite on PostgreSQL 17.11 | 227 tests, pass |
| Lock mutation check | With `select_for_update()` removed, 8 of 9 concurrency tests failed on PostgreSQL. Restored, all pass |
| `manage.py check --deploy` with production-like settings | No issues |
| `makemigrations --check` | No changes |
| Migration test (`ledger.tests.test_migrations`) | A whole-rate game with an override, a fractional-rate game and a running game convert; each finalized game still balances |
| Migration on a copy of the dev database, then on the real one | Finalized game: results and transfers identical before and after. Running game: buy-ins unchanged, unit pesos |
| Headless Chrome at 390 × 844, a pesos game and a chips game | 18 of 18 checks pass. A cash-out reached a second client in 4.0 s |
| Screenshots | Reviewed by the AI. One defect found and fixed: "Still in play" showed −₱50 while counting up with a surplus. The tile now shows "Total cashed out" in that stage |

Not checked: a physical phone and a production web server.

| # | Result | Evidence |
|---|---|---|
| AC1 | Met | `web.tests.test_units.UnitChoiceTests`; browser check |
| AC2 | Met | `ledger.tests.test_cash_outs`; browser check |
| AC3 | Met | `web.tests.test_acceptance`; browser check |
| AC4 | Met | `ledger.tests.test_balance`, `settlement.tests.test_finalize`; browser check |
| AC5 | Met | `test_cash_outs` |
| AC6 | Met | `test_units.ChipsGameTests`; browser check |
| AC7 | Met | `test_units`, `test_acceptance.ChipsGameAcceptanceTest` |
| AC8 | Met | `test_units.UnitChangeTests` |
| AC9 | Met | `ledger.tests.test_buy_ins`, `test_units.PesosGameShowsNoChipsTests` |
| AC10 | Met | Comparison of the dev database before and after |
| AC11 | Met | The Stage 1 tests for overrides, reversals, paid marks, access and live updates, updated and passing |

## Differences from the plan and findings

| Topic | Detail |
|---|---|
| Whose test games | The plan called both games in the dev database "your test games". Only the running one ("Kyler Tan Gambling Den") is the human's. The finalized one ("Browser Check", accounts `hana` and `ben`) is left over from the AI's Stage 1 browser check. A shell command that should have deleted that database did not run, and the Stage 1 report wrongly said the database was empty. Both games were kept and converted. Removal of the leftover data waits for a human decision |
| Backup | The first backup was a plain file copy that missed the write-ahead log. It was replaced with a backup through the SQLite API before any change |
| Unit change | Allowed until the first accepted buy-in, through the game settings page. Older settings versions of that game then display in the new unit |
| Settings rule | With the chip rate gone, a settings change after buy-ins has no restriction other than the unit |
| Extra fix | "Still in play" is hidden while counting up |

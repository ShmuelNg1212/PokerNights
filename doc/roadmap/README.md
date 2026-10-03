# Roadmap

Each stage needs its own study, plan and approval. The design for all stages is in the [architecture study](../study/1791037419_poker_home_game_architecture.md) and its review addendum. Product intent is in [SPEC.md](../../SPEC.md).

| Stage | Outcome | `SPEC.md` step | Status |
|---|---|---|---|
| 1. Game night | Buy-ins and rebuys, cash-outs with balance check, settle-up with paid marks | 1, 2, 3 | Done, 2026-10-03 |
| 2. Roster, history, banker, corrections | Roster management, history list with filters, optional banker for the night, payments recorded before finalization (early leavers), reopen a finalized game as a new revision | 4 | Next |
| 3. Leaderboard and stats | Seasons; month, season, year and all-time filters; profit/loss, sessions, average result, win rate, ROI | 5 | Planned |
| 4. Seating | Manual seats and random draws with history | First request, item 10 | Planned |
| 5. Shared use | Deployment, password reset, claim links for roster players, design pass | — | Planned |

## What Stage 1 already prepares

- `PlayerResult` carries `member`, `group` and `game_date`, with indexes for leaderboard queries.
- `Finalization` has `revision` and `is_current`, and `write_results()` already retires an older revision. Reopening needs a lifecycle action and a rule for payments made under the old revision.
- `Payment` has optional `payer`, `payee` and `transfer`, so a banker and a payment before finalization fit the same table. `algorithm.balances()` already accepts payments, and its tests cover the prior-payment and banker cases.

## Decisions that changed the design

- **2026-10-03, cash amounts and units.** Chip counts and the chip-to-peso rate were removed. A game counts in pesos or in chips, and a chips game has no peso value. This replaces `SPEC.md` step 2 ("final chip count", "convert chips to cash") and the "chips per buy-in" item of the first request. `SPEC.md` itself is unchanged; its owner can update it.
- **Consequence for Stage 3:** leaderboards and statistics are per unit. A pesos board includes only pesos games. `PlayerResult.unit` supports this.
- The "chip denominations" item under "Later" no longer applies to pesos games.

## Open product decisions

These used the plan's defaults in Stage 1. They can still change.

| Decision | Default in use |
|---|---|
| Settlement model | Direct settle-up. Banker optional in Stage 2 |
| Balance override | A note, and one named player or an equal share |
| Tables per session | One. A two-table night is two sessions |
| Audience | One private group. Sign-up is open; access needs an invite |
| Seating | Stays in the roadmap as Stage 4 |
| Whole-peso rounding | None. Exact centavos |
| Win rate | Percentage of finalized sessions with profit; the same measure as "cash rate" |
| Ranking threshold | 3 sessions, per group |

## Later (from `SPEC.md`, not planned)

RSVP with a waitlist, recurring games, reminders, IOUs across sessions, rake and tips, session timer, session notes, CSV or image export, chip denominations, bankroll graph.

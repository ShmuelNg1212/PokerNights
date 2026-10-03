# Wiki: PokerNights

Living documentation. It describes the project **as it exists now**. For decisions and their history, see `doc/study/` and `doc/plan/`. For product intent, see [SPEC.md](../../SPEC.md). For the working agreement, see [AGENTS.md](../../AGENTS.md).

## Current state

**PokerNights** is a web app for home poker cash games in Philippine pesos. A host creates a game, records buy-ins, rebuys and cash-outs, and checks that the books balance. The app then freezes the results and lists who pays whom with the minimum number of transfers. Players follow the game live on their phones. The app records who owes what. It does not move money.

Stage 1 ("game night", `SPEC.md` build steps 1 to 3) is complete. The app runs locally. It is not deployed.

## Pages

| Page | Contents |
|---|---|
| [setup.md](setup.md) | Install, `.env`, run, test on SQLite and PostgreSQL |
| [architecture.md](architecture.md) | Apps, data model, money rules, lifecycle, balance check, finalization, settle-up, live updates |
| [features.md](features.md) | What hosts and players can do today, and the limits |
| [external-dependencies.md](external-dependencies.md) | Pinned packages and services |
| [footguns/](footguns/) | Behavior that surprised us, with evidence and remedy |
| [../roadmap/README.md](../roadmap/README.md) | Stages 2 to 5 and open product decisions |

## Footguns

| Page | Summary |
|---|---|
| [sqlite_hides_missing_locks.md](footguns/sqlite_hides_missing_locks.md) | A missing row lock passes on SQLite and races on PostgreSQL |
| [partial_unique_constraints_are_not_deferrable.md](footguns/partial_unique_constraints_are_not_deferrable.md) | Deactivate the old row before activating the new one |
| [adjustments_are_in_chips.md](footguns/adjustments_are_in_chips.md) | Balance overrides are stored in chips, not pesos |

## Journal

| Request | Study | Plan | Status |
|---|---|---|---|
| Architecture and Stage 1, game night | [study](../study/1791037419_poker_home_game_architecture.md) | [plan](../plan/1791037623_poker_home_game_architecture.md) | Done, 2026-10-03 |

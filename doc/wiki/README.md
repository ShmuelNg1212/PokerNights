# Wiki: PokerNights

Living documentation. It describes the project **as it exists now**. For decisions and their history, see `doc/study/` and `doc/plan/`. For product intent, see [SPEC.md](../../SPEC.md). For the working agreement, see [AGENTS.md](../../AGENTS.md).

## Current state

**PokerNights** is a web app for home poker cash games. Each game counts in Philippine pesos or, as an option, in chips with no peso value. A host runs a session of one or more sets. In each set the host records buy-ins and rebuys, ends play, confirms final counts, cashes players out and checks that the books balance. Each set has its own timer. When the session is closed, the app lists who pays whom over all sets with the minimum number of transfers. Players follow the game live on their phones. The app records who owes what. It does not move money.

Stage 1 ("game night", `SPEC.md` build steps 1 to 3) is complete. It differs from `SPEC.md` step 2 in one point, by a later decision of the owner: cash-outs are typed as amounts, and the app has no chip-to-cash conversion. The app runs locally. It is not deployed.

The Rack covers the shared foundation, compact active table, action sheets, count-up, cash-out review and finalized sets. [DESIGN.md](../../DESIGN.md) records the built system. Later screens keep their earlier composition.

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
| [sqlite_copy_misses_the_wal.md](footguns/sqlite_copy_misses_the_wal.md) | A plain copy of `db.sqlite3` can miss recent data |
| [session_means_set_in_the_code.md](footguns/session_means_set_in_the_code.md) | `GameSession` is a set; the session is `GameNight` |
| [template_cache_during_browser_checks.md](footguns/template_cache_during_browser_checks.md) | A verification server without autoreload can keep old compiled templates |
| [mobile_browser_overflow_checks.md](footguns/mobile_browser_overflow_checks.md) | Mobile layout viewport width can grow with overflowing content; compare with the requested width |
| [one_form_per_row_loses_typing.md](footguns/one_form_per_row_loses_typing.md) | A form per row, or a live refresh, loses unsaved typing |

## Journal

| Request | Study | Plan | Status |
|---|---|---|---|
| Architecture and Stage 1, game night | [study](../study/1791037419_poker_home_game_architecture.md) | [plan](../plan/1791037623_poker_home_game_architecture.md) | Done, 2026-10-03 |
| Cash amounts and a unit option | [study](../study/1791040240_cash_amounts_and_unit_option.md) | [plan](../plan/1791040305_cash_amounts_and_unit_option.md) | Done, 2026-10-03 |
| Add several players at once | [study](../study/1791041698_add_several_players_at_once.md) | [plan](../plan/1791041765_add_several_players_at_once.md) | Done, 2026-10-03 |
| Sessions with sets, end-of-set cash-outs, timers | [study](../study/1791042572_end_of_set_cash_outs_and_timers.md) | [plan](../plan/1791042668_end_of_set_cash_outs_and_timers.md) | Done, 2026-10-04 |
| Visual redesign, The Rack slice 1 | [study](../study/1791045491_visual_redesign.md) | [plan](../plan/1791046015_visual_redesign.md) | Slice 1 done, 2026-10-04; later slices need approval |
| Fix: typed counts lost when confirming | [study](../study/1791044894_count_fields_cleared.md) | [plan](../plan/1791044911_count_fields_cleared.md) | Done, 2026-10-04 |
| Visual redesign slice 2 | [study](../study/1791050655_redesign_slice_2.md) | [plan](../plan/1791050738_redesign_slice_2.md) | Verified; rendezvous pending |

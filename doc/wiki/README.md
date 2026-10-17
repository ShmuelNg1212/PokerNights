# Wiki: PokerNights

Living documentation. It describes the project **as it exists now**. For decisions and their history, see `doc/study/` and `doc/plan/`. For product intent, see [spec.md](spec.md). For the working agreement, see [AGENTS.md](../../AGENTS.md).

## Current state

**PokerNights** is a web app for home poker cash games. Each game counts in Philippine pesos or, as an option, in chips with no peso value. A host runs a session of one or more sets. In each set the host records buy-ins and rebuys, ends play, confirms final counts, cashes players out and checks that the books balance. Each set has its own timer. When the session is closed, the app lists who pays whom over all sets with the minimum number of transfers. Players follow the game live on their phones. The app records who owes what. It does not move money.

Stages 1, 3, 4 and 5 of the [roadmap](../roadmap/README.md) are built, and Stage 2 except the banker, payments before a session closes and filters on the list of past sessions. Beyond game night the app has roster management, claim links, host-issued password reset links, a stats board with a page per player, reopening of sets and sessions, an optional seat draw, earlier unpaid transfers carried into a later settle-up, sharing of results, and a session recap. Optional per-set rake is deducted from every buy-in and collected separately; balance checks include it and settle-up does not charge it again. Cash-outs are typed as amounts, and the app has no chip-to-cash conversion. [spec.md](spec.md) was brought in line with the app on 2026-10-12 at its owner's request.

The app is live at https://pokernights-five.vercel.app on Vercel and Neon since 2026-10-04. A push to `main` is a release; see [deployment.md](deployment.md). Sign-up there needs an invite link.

The Rack redesign covers all current screens: active sets, count-up, review, finalized and canceled sets, session settle-up and recap, home, groups, accounts, invitations, supporting forms and the set log. [DESIGN.md](../../DESIGN.md) records the built system.

## Pages

| Page | Contents |
|---|---|
| [spec.md](spec.md) | Product intent and current behaviour; living, intent changes need approval |
| [setup.md](setup.md) | Install, `.env`, run, test on SQLite and PostgreSQL |
| [architecture.md](architecture.md) | Apps, data model, money rules, lifecycle, balance check, finalization, settle-up, live updates |
| [features.md](features.md) | What hosts and players can do today, and the limits |
| [deployment.md](deployment.md) | Vercel and Neon: what runs where, releasing, rollback, leaked secrets, limits |
| [external-dependencies.md](external-dependencies.md) | Pinned packages and services |
| [footguns/](footguns/) | Behavior that surprised us, with evidence and remedy |
| [../roadmap/README.md](../roadmap/README.md) | The stages, what remains and open product decisions |

## Footguns

| Page | Summary |
|---|---|
| [build_tests_see_production_settings.md](footguns/build_tests_see_production_settings.md) | The Vercel build tests with production's variables; run the suite with them before a release |
| [sqlite_hides_missing_locks.md](footguns/sqlite_hides_missing_locks.md) | A missing row lock passes on SQLite and races on PostgreSQL |
| [partial_unique_constraints_are_not_deferrable.md](footguns/partial_unique_constraints_are_not_deferrable.md) | Deactivate the old row before activating the new one |
| [motion_starts_a_frame_late.md](footguns/motion_starts_a_frame_late.md) | Write the first keyframe inline and restore sideways scroll before animating a swapped screen |
| [sqlite_copy_misses_the_wal.md](footguns/sqlite_copy_misses_the_wal.md) | A plain copy of `db.sqlite3` can miss recent data |
| [session_means_set_in_the_code.md](footguns/session_means_set_in_the_code.md) | `GameSession` is a set; the session is `GameNight` |
| [template_cache_during_browser_checks.md](footguns/template_cache_during_browser_checks.md) | A verification server without autoreload can keep old compiled templates |
| [scripts_run_once_per_tab.md](footguns/scripts_run_once_per_tab.md) | A script that starts once per page load keeps polling after the screen changes; register it with `page.js` |
| [ios_date_input.md](footguns/ios_date_input.md) | The iPhone draws a date input at its own size; the shared field box fixes it and Chrome cannot prove it |
| [mobile_browser_overflow_checks.md](footguns/mobile_browser_overflow_checks.md) | Mobile layout viewport width can grow with overflowing content; compare with the requested width |
| [count_status_moves_the_field.md](footguns/count_status_moves_the_field.md) | A wrapped saved-count status moves its field even when document scroll stays fixed |
| [one_form_per_row_loses_typing.md](footguns/one_form_per_row_loses_typing.md) | A form per row, or a live refresh, loses unsaved typing |
| [rake_results_and_settlement.md](footguns/rake_results_and_settlement.md) | After-rake player results are not remaining settlement balances |
| [service_worker_user_agent.md](footguns/service_worker_user_agent.md) | A page the service worker fetched was asked for with the worker's user agent, not a chat app's |

| [ios_keyboard_covers_fixed.md](footguns/ios_keyboard_covers_fixed.md) | Fixed elements at the bottom sit under the iPhone keyboard |
| [opening_buy_ins_lock_rake.md](footguns/opening_buy_ins_lock_rake.md) | Configure rake before default opening buy-ins lock the rule |

## Agent workflow

See [AGENTS.md](../../AGENTS.md).

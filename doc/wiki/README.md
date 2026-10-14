# Wiki: PokerNights

Living documentation. It describes the project **as it exists now**. For decisions and their history, see `doc/study/` and `doc/plan/`. For product intent, see [SPEC.md](../../SPEC.md). For the working agreement, see [AGENTS.md](../../AGENTS.md).

## Current state

**PokerNights** is a web app for home poker cash games. Each game counts in Philippine pesos or, as an option, in chips with no peso value. A host runs a session of one or more sets. In each set the host records buy-ins and rebuys, ends play, confirms final counts, cashes players out and checks that the books balance. Each set has its own timer. When the session is closed, the app lists who pays whom over all sets with the minimum number of transfers. Players follow the game live on their phones. The app records who owes what. It does not move money.

Stages 1, 3, 4 and 5 of the [roadmap](../roadmap/README.md) are built, and Stage 2 except the banker, payments before a session closes and filters on the list of past sessions. Beyond game night the app has roster management, claim links, host-issued password reset links, a stats board with a page per player, reopening of sets and sessions, an optional seat draw, earlier unpaid transfers carried into a later settle-up, sharing of results, and a session recap. Optional per-set rake is deducted from every buy-in and collected separately; balance checks include it and settle-up does not charge it again. Cash-outs are typed as amounts, and the app has no chip-to-cash conversion. [SPEC.md](../../SPEC.md) was brought in line with the app on 2026-10-12 at its owner's request.

The app is live at https://pokernights-five.vercel.app on Vercel and Neon since 2026-10-04. A push to `main` is a release; see [deployment.md](deployment.md). Sign-up there needs an invite link.

The Rack redesign covers all current screens: active sets, count-up, review, finalized and canceled sets, session settle-up and recap, home, groups, accounts, invitations, supporting forms and the set log. [DESIGN.md](../../DESIGN.md) records the built system.

## Pages

| Page | Contents |
|---|---|
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

| [ios_keyboard_covers_fixed.md](footguns/ios_keyboard_covers_fixed.md) | Fixed elements at the bottom sit under the iPhone keyboard |
| [opening_buy_ins_lock_rake.md](footguns/opening_buy_ins_lock_rake.md) | Configure rake before default opening buy-ins lock the rule |

## Journal

| Request | Study | Plan | Status |
|---|---|---|---|
| Architecture and Stage 1, game night | [study](../study/1791037419_poker_home_game_architecture.md) | [plan](../plan/1791037623_poker_home_game_architecture.md) | Done, 2026-10-03 |
| Cash amounts and a unit option | [study](../study/1791040240_cash_amounts_and_unit_option.md) | [plan](../plan/1791040305_cash_amounts_and_unit_option.md) | Done, 2026-10-03 |
| Add several players at once | [study](../study/1791041698_add_several_players_at_once.md) | [plan](../plan/1791041765_add_several_players_at_once.md) | Done, 2026-10-03 |
| Sessions with sets, end-of-set cash-outs, timers | [study](../study/1791042572_end_of_set_cash_outs_and_timers.md) | [plan](../plan/1791042668_end_of_set_cash_outs_and_timers.md) | Done, 2026-10-04 |
| Visual redesign, The Rack slice 1 | [study](../study/1791045491_visual_redesign.md) | [plan](../plan/1791046015_visual_redesign.md) | All four slices done, 2026-10-04 |
| Fix: typed counts lost when confirming | [study](../study/1791044894_count_fields_cleared.md) | [plan](../plan/1791044911_count_fields_cleared.md) | Done, 2026-10-04 |
| Visual redesign slice 2 | [study](../study/1791050655_redesign_slice_2.md) | [plan](../plan/1791050738_redesign_slice_2.md) | Done, 2026-10-04 |
| Visual redesign slice 3 | [study](../study/1791053103_redesign_slice_3.md) | [plan](../plan/1791053204_redesign_slice_3.md) | Done, 2026-10-04 |
| Visual redesign slice 4 | [study](../study/1791084725_redesign_slice_4.md) | [plan](../plan/1791084843_redesign_slice_4.md) | Done, 2026-10-04 |
| Add a player during play | [study](../study/1791091289_add_player_during_play.md) | [plan](../plan/1791091385_add_player_during_play.md) | Done, 2026-10-04 |
| Live counted total | [study](../study/1791089661_live_counted_total.md) | [plan](../plan/1791089905_live_counted_total.md) | Done, 2026-10-04 |
| Set rake and group pool | [study](../study/1791093189_set_rake_and_group_pool.md) | [plan](../plan/1791093380_set_rake_and_group_pool.md) | Done, 2026-10-04 |
| Default opening buy-ins | [study](../study/1791088066_default_opening_buy_ins.md) | [plan](../plan/1791088166_default_opening_buy_ins.md) | Done, 2026-10-04 |
| Password reset by a host-issued link | [study](../study/1791263946_host_issued_password_reset.md) | [plan](../plan/1791263947_host_issued_password_reset.md) | Done, released 2026-10-06 as `d573ba0` |
| Player rebuys and player-entered counts | [study](../study/1791266618_player_rebuys_and_counts.md) | [plan](../plan/1791266619_player_rebuys_and_counts.md) | Done, released 2026-10-06 as `283ecc2` |
| Copy button on a new link | [study](../study/1791265489_copy_link_button.md) | [plan](../plan/1791265490_copy_link_button.md) | Done, released 2026-10-06 as `7639c8f` |
| Rake setup controls | [study](../study/1791096071_rake_controls.md) | [plan](../plan/1791096125_rake_controls.md) | Done, 2026-10-04 |
| UI evolution: tabs, wording, branding, first stats | [study](../study/1791098885_ui_evolution.md) | [plan](../plan/1791098885_ui_evolution.md) | Done, 2026-10-04 |
| Your groups home | [study](../study/1791102379_your_groups_home.md) | [plan](../plan/1791102439_your_groups_home.md) | Done, 2026-10-04 |
| Deployment on Vercel and Neon | [study](../study/1791104094_vercel_deployment.md) | [plan](../plan/1791104210_vercel_deployment.md) | Done, live since 2026-10-04 |
| Collapsible host dock | [study](../study/1791111003_collapsible_host_dock.md) | [plan](../plan/1791111069_collapsible_host_dock.md) | Done, released 2026-10-04 as `19c9744` |
| Archive and delete groups and sessions | [study](../study/1791114128_archive_and_delete_groups_and_sessions.md) | [plan](../plan/1791114191_archive_and_delete_groups_and_sessions.md) | Done, released 2026-10-04 as `19c9744` |
| Entry pages revamp | [study](../study/1791115770_entry_pages.md) | [plan](../plan/1791115804_entry_pages.md) | Done, released 2026-10-04 as `19c9744` |
| Session settled indicator | [study](../study/1791120013_session_settled_indicator.md) | [plan](../plan/1791120060_session_settled_indicator.md) | Done, released 2026-10-04 as `e5a7ed2` |
| Stakes forms revamp | [study](../study/1791121357_session_form.md) | [plan](../plan/1791121411_session_form.md) | Done, 2026-10-04 |
| Entry flow fixes from the critique | [study](../study/1791134589_entry_flow_critique_fixes.md) | [plan](../plan/1791134687_entry_flow_critique_fixes.md) | Done, 2026-10-05 |
| App-like experience (parent plan) | [study](../study/1791172718_app_like_experience.md) | [plan](../plan/1791172782_app_like_experience.md) | Stages 1 to 4 and the motion stages 1 to 3 done, 2026-10-05 |
| Installable app | [study](../study/1791176837_installable_app.md) | [plan](../plan/1791176898_installable_app.md) | Done, 2026-10-05 |
| Actions in place | [study](../study/1791178826_actions_in_place.md) | [plan](../plan/1791178826_actions_in_place.md) | Done, 2026-10-05 |
| Screen changes without a reload | [study](../study/1791181036_screen_changes_without_reload.md) | [plan](../plan/1791181102_screen_changes_without_reload.md) | Done, 2026-10-05 |
| Fix: host dock behind the keyboard | [study](../study/1791184941_dock_behind_keyboard.md) | [plan](../plan/1791184990_dock_behind_keyboard.md) | Done, 2026-10-05 |
| Motion overhaul | [study](../study/1791186418_motion_overhaul.md) | [plan](../plan/1791186717_motion_overhaul.md) | Stage 1 released 2026-10-05 as `680c3b1`; stage 4 has no plan |
| Motion on the live set page | [study](../study/1791188203_motion_live_set_page.md) | [plan](../plan/1791188269_motion_live_set_page.md) | Done, released 2026-10-05 as `1106548` |
| Fix: host dock, keyboard and scroll | [study](../study/1791191973_dock_keyboard_scroll.md) | [plan](../plan/1791192015_dock_keyboard_scroll.md) | Done, 2026-10-05 |
| Motion between screens | [study](../study/1791194279_motion_between_screens.md) | [plan](../plan/1791194279_motion_between_screens.md) | Done, released 2026-10-05 as `648cca8` |
| Your groups redesign | [study](../study/1791200012_your_groups_redesign.md) | [plan](../plan/1791200012_your_groups_redesign.md) | Done, released 2026-10-05 as `f044805` |
| Host control gaps, numpad and count-up rework | [study](../study/1791201933_host_gaps_numpad_count_up.md) | [plan](../plan/1791202390_host_gaps_numpad_count_up.md) | Done, released 2026-10-05 as `4a80de9` |
| Fix: transfer alignment | [study](../study/1791210055_transfer_alignment.md) | [plan](../plan/1791210163_transfer_alignment.md) | Done, 2026-10-06 |
| Phone performance and smoothness | [study](../study/1791214796_phone_performance_and_smoothness.md) | [plan](../plan/1791214849_phone_performance_and_smoothness.md) | Done, released 2026-10-06 as `c84f45a`, `fedaeb0` and `53de23b`; accepted 2026-10-06 |
| Fewer queries and one-trip actions | [study](../study/1791219090_fewer_queries_and_one_trip_actions.md) | [plan](../plan/1791219154_fewer_queries_and_one_trip_actions.md) | Done, released 2026-10-06 as `60faac0` |
| Roster management | [study](../study/1791525548_roster_management.md) | [plan](../plan/1791525658_roster_management.md) | Done, released 2026-10-09 as `8b51506` |
| Claim links | [study](../study/1791527468_claim_links.md) | [plan](../plan/1791527506_claim_links.md) | Done, released 2026-10-09 as `8b51506` |
| Stats revamp | [study](../study/1791528884_stats_revamp.md) | [plan](../plan/1791528961_stats_revamp.md) | Done, released 2026-10-09 as `c08d711` |
| Numpad motion | [study](../study/1791533294_numpad_motion.md) | [plan](../plan/1791533332_numpad_motion.md) | Done, released 2026-10-09 as `ee18667` |
| Numpad digit motion | [study](../study/1791538181_numpad_digit_motion.md) | [plan](../plan/1791538209_numpad_digit_motion.md) | Done, released 2026-10-09 as `6119dd4` |
| Front door revamp | [study](../study/1791542264_front_door_revamp.md) | [plan](../plan/1791542366_front_door_revamp.md) | Done, released 2026-10-09 as `394b4f3` |
| Arrival after login | [study](../study/1791546703_arrival_after_login.md) | [plan](../plan/1791546778_arrival_after_login.md) | Done, released 2026-10-09 as `f2bd882` |
| Set page revamp | [study](../study/1791548918_set_page_revamp.md) | [plan](../plan/1791549025_set_page_revamp.md) | Done, released 2026-10-09 as `e812dfc` |
| Session recap with more detail | [study](../study/1791625335_session_recap_details.md) | [plan](../plan/1791625392_session_recap_details.md) | Done, released 2026-10-10 as `0c736fb` |
| Count-up and who pays whom, revamp | [study](../study/1791630956_count_up_and_settle_up_revamp.md) | [plan](../plan/1791630963_count_up_and_settle_up_revamp.md) | Done, released 2026-10-10 as `08a49b5`; accepted 2026-10-12 |
| Pot figure motion | [study](../study/1791647037_pot_figure_motion.md) | [plan](../plan/1791647086_pot_figure_motion.md) | Done, released 2026-10-11 as `800e29e` |
| Reopen a set or a session | [study](../study/1791699745_reopen_set_and_session.md) | [plan](../plan/1791699815_reopen_set_and_session.md) | Done, released 2026-10-11 as `be3bcf2` |
| Share results | [study](../study/1791701725_share_results.md) | [plan](../plan/1791701751_share_results.md) | Done, released 2026-10-11 as `2557f50` |
| Home screen suggestion and Join with a link | [study](../study/1791703645_install_prompt.md) | [plan](../plan/1791703670_install_prompt.md) | Done, released 2026-10-11 as `6090ce1` |
| The session page updates by itself | [study](../study/1791706965_session_page_live.md) | [plan](../plan/1791706983_session_page_live.md) | Done, released 2026-10-11 as `243ce78` |
| Fix: the "Your count" card | [study](../study/1791710363_your_count_gap.md) | [plan](../plan/1791710364_your_count_gap.md) | Done, released 2026-10-11 as `6cae533` |
| Your groups and a group's sessions update by themselves | [study](../study/1791711534_hub_pages_live.md) | [plan](../plan/1791711535_hub_pages_live.md) | Done, released 2026-10-11 as `1da9bfd` |
| Fix: the session recap opens at its top | [study](../study/1791715365_recap_opens_at_bottom.md) | [plan](../plan/1791715366_recap_opens_at_bottom.md) | Done, released 2026-10-11 as `f3b321f` |
| Seat draw before a set starts | [study](../study/1791717120_seat_draw.md) | [plan](../plan/1791717121_seat_draw.md) | Done, released 2026-10-11 as `dc6e00c`; accepted 2026-10-12 |
| Unpaid transfers carried into a later session | [study](../study/1791728776_carried_debts.md) | [plan](../plan/1791728777_carried_debts.md) | Done, released 2026-10-11 as `c91dc68`; accepted 2026-10-12 |
| The look of the table in the seat draw | [study](../study/1791735775_draw_table_look.md) | [plan](../plan/1791735776_draw_table_look.md) | Done, released 2026-10-12 as `0c168bc`; accepted 2026-10-12 |
| Switch cleanup: remove the earlier copies of revamped screens | [study](../study/1791788387_switch_cleanup.md) | [plan](../plan/1791788388_switch_cleanup.md) | Done, released 2026-10-12 as `70c939a` |
| A picture for the link: the card chat apps show | [study](../study/1791861227_link_preview.md) | [plan](../plan/1791861228_link_preview.md) | Done, released 2026-10-13 as `d3b8d1d` |
| Session setup polish and the More host controls flyout | [study](../study/1791872138_session_setup_polish.md) | [plan](../plan/1791872139_session_setup_polish.md) | Done, released 2026-10-13 as `899a93e` |
| Several new names at once on Add players | [study](../study/1791948615_new_names_at_once.md) | [plan](../plan/1791948616_new_names_at_once.md) | Done, released 2026-10-14 as `f51f4ac` |
| A splash screen for the installed app | [study](../study/1791953082_launch_splash.md) | [plan](../plan/1791953083_launch_splash.md) | Built 2026-10-14 on `feat/launch-splash`, not released |

# TODO

Short active items. The detail is in the linked documents.

## Active

Rake controls are in progress ([plan](doc/plan/1791096125_rake_controls.md)): explicit choices at creation and active-value validation.

Set rake and group pool is done ([plan](doc/plan/1791093380_set_rake_and_group_pool.md)). Configure percentage or flat rake before the first buy-in; balances include collected rake and group totals keep units separate.

Add a player during play is done ([plan](doc/plan/1791091385_add_player_during_play.md)). Add players offers a new-name form during play; late buy-ins stay separate.

Live counted total is done ([plan](doc/plan/1791089905_live_counted_total.md)). Count-up previews remaining stacks plus cash-outs against buy-ins while typing.

Default opening buy-ins are done ([plan](doc/plan/1791088166_default_opening_buy_ins.md)). Start the game adds the usual amount for joined players without an accepted buy-in; uncheck to opt out.

Visual redesign slice 4 is done ([plan](doc/plan/1791084843_redesign_slice_4.md)). The Rack redesign is complete for current screens.

Visual redesign slice 3 (session page, settle-up and recap) is done ([plan](doc/plan/1791053204_redesign_slice_3.md)). Visual redesign slice 2 (count-up, cash-out review and finalized sets) is done ([plan](doc/plan/1791050738_redesign_slice_2.md)). The Rack visual redesign slice 1 is done ([plan](doc/plan/1791046015_visual_redesign.md)). Stage 1 is done ([plan](doc/plan/1791037623_poker_home_game_architecture.md)). Cash amounts and the unit option are done ([plan](doc/plan/1791040305_cash_amounts_and_unit_option.md)). Adding several players at once is done ([plan](doc/plan/1791041765_add_several_players_at_once.md)). Sessions with sets, end-of-set cash-outs and timers are done ([plan](doc/plan/1791042668_end_of_set_cash_outs_and_timers.md)).

## Next (each needs its own study and plan)

- [ ] Stage 2: roster management, history list, optional banker, payments before finalization, reopen a finalized game. See the [roadmap](doc/roadmap/README.md).
- [ ] Stage 3: leaderboard and stats.
- [ ] Stage 4: seating.
- [ ] Stage 5: shared use (deployment, password reset, claim links).

## Waiting for the human

- [ ] Try rake: before starting a set, choose Change settings → Percentage (5%) or Flat amount. Check each buy-in’s gross/rake/in-play split, cash out the remaining stacks, and check group totals. Equal losses from rake alone should owe no further transfer.

- [ ] Try a late arrival: during play, choose Add players, enter a new name and add them. Check they appear with no buy-in, then record their buy-in.

- [ ] Try the live stack counter: end play, enter counts and watch the total/difference. Include 0 and clear an unsaved field. Confirm counts, review cash-outs and check the accounted total stays the same.

- [ ] Try opening buy-ins: add players to an open set, start it and check one usual buy-in each. For another set, uncheck the option and confirm no opening money is added.

- [ ] Try the group and forms: open a current session, create a table, and submit a duplicate roster name. Check that the name stays beside its error. Read a set log.

- [ ] Try the redesigned session page: close a finished session, dismiss/reopen the recap, mark a transfer paid, then Undo. Check that Still to pay changes and Session results stay fixed.

- [ ] Try the new active set: tap `+`, confirm a rebuy, tap a player name for cash-out/details, and use the bottom host action.

- [ ] Try the redesigned count-up and final results: type several counts (including 0), confirm once, review and cash out, then finalize.

- [ ] Test a session with two sets as a user: end a set, confirm counts, cash out counted players, start the next set, close the session.
- [ ] Test a pesos game and a chips game as a user.
- [ ] Decide whether to keep the leftover check data in the dev database (accounts `hana` and `ben`, group "Browser Check").
- [ ] Update `SPEC.md` step 2 if it should match the app (cash-outs as amounts, no chip conversion).
- [ ] Confirm or change the open product decisions in the [roadmap](doc/roadmap/README.md), mainly the settlement model and the balance override rule.

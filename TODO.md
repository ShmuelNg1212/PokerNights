# TODO

Short active items. The detail is in the linked documents.

## Active

Visual redesign slice 3 (session page, settle-up and recap) is done ([plan](doc/plan/1791053204_redesign_slice_3.md)). Visual redesign slice 2 (count-up, cash-out review and finalized sets) is done ([plan](doc/plan/1791050738_redesign_slice_2.md)). The Rack visual redesign slice 1 is done ([plan](doc/plan/1791046015_visual_redesign.md)). Stage 1 is done ([plan](doc/plan/1791037623_poker_home_game_architecture.md)). Cash amounts and the unit option are done ([plan](doc/plan/1791040305_cash_amounts_and_unit_option.md)). Adding several players at once is done ([plan](doc/plan/1791041765_add_several_players_at_once.md)). Sessions with sets, end-of-set cash-outs and timers are done ([plan](doc/plan/1791042668_end_of_set_cash_outs_and_timers.md)).

## Next (each needs its own study and plan)

- [ ] Visual redesign slice 4: remaining screens. See the [parent plan](doc/plan/1791046015_visual_redesign.md).

- [ ] Stage 2: roster management, history list, optional banker, payments before finalization, reopen a finalized game. See the [roadmap](doc/roadmap/README.md).
- [ ] Stage 3: leaderboard and stats.
- [ ] Stage 4: seating.
- [ ] Stage 5: shared use (deployment, password reset, claim links, design pass).

## Waiting for the human

- [ ] Try the redesigned session page: close a finished session, dismiss/reopen the recap, mark a transfer paid, then Undo. Check that Still to pay changes and Session results stay fixed.

- [ ] Try the new active set: tap `+`, confirm a rebuy, tap a player name for cash-out/details, and use the bottom host action.

- [ ] Try the redesigned count-up and final results: type several counts (including 0), confirm once, review and cash out, then finalize.

- [ ] Test a session with two sets as a user: end a set, confirm counts, cash out counted players, start the next set, close the session.
- [ ] Test a pesos game and a chips game as a user.
- [ ] Decide whether to keep the leftover check data in the dev database (accounts `hana` and `ben`, group "Browser Check").
- [ ] Update `SPEC.md` step 2 if it should match the app (cash-outs as amounts, no chip conversion).
- [ ] Confirm or change the open product decisions in the [roadmap](doc/roadmap/README.md), mainly the settlement model and the balance override rule.

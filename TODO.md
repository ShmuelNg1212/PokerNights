# TODO

Short active items. The detail is in the linked documents.

## Active

Phone performance and smoothness ([plan](doc/plan/1791214849_phone_performance_and_smoothness.md), [study](doc/study/1791214796_phone_performance_and_smoothness.md)): stages 1 and 2 are built on branch `perf/phone-smoothness` and verified locally on 2026-10-06. Every response carries a `Server-Timing` header and `?perf=1` shows a readout on the phone; the host dock slides without laying the page out (3 layouts per slide, from 27 to 55); links look pressed from the first frame of a touch; a changed row's mark stays inside the row and "Rebuy added" sits under the name. No migration. 682 tests pass on SQLite and PostgreSQL 17. Released 2026-10-06 as `c84f45a` (previous production commit `90ff346`); the live site answers with the `Server-Timing` header and serves `perf.js`. Phone acceptance remains open. Stage 3 (the server) is decided from the phone's numbers. The phone's numbers arrived on 2026-10-06 and are in the study's addendum. The tab fix was released as `fedaeb0`. Stage 3: **A** (fetch a touched link at once) is built on branch `perf/stage-3`, **not released**; **B** (kept database connection) is a Vercel variable for the human to set; **C** and **D** have a [plan](doc/plan/1791219154_fewer_queries_and_one_trip_actions.md) **awaiting approval**.

Host control gaps, the in-app numpad and the count-up rework are built ([plan](doc/plan/1791202390_host_gaps_numpad_count_up.md)), merged locally to `main` as `0dc4c37`: host controls 8px apart; the app's own number keys for every typed number on a phone; count-up with the players first, one total and a main button that follows the state; a review that says whether the books will balance; Finalize asks once; the final page leads with its proof. No migration. Released 2026-10-05 as `4a80de9`; Vercel build passed 677 tests and had no migrations to apply. 677 tests pass on SQLite and PostgreSQL 17; repeat critique 32/40 with no P1 issue. Phone acceptance remains open.

App-like experience ([plan](doc/plan/1791172782_app_like_experience.md)): stage 1 (static caching) and stage 2 ([installable app](doc/plan/1791176898_installable_app.md)) are done. Stage 3 ([actions in place](doc/plan/1791178826_actions_in_place.md)) is done: set and session page actions update without a reload, using Turbo 8.0.23. Stage 4 ([screen changes without a reload](doc/plan/1791181102_screen_changes_without_reload.md)) is done: links change the screen in the app, with every script given a start and a stop. Stage 6, the motion overhaul with Motion (motion.dev), has a [study](doc/study/1791186418_motion_overhaul.md) and a [plan](doc/plan/1791186717_motion_overhaul.md) in four stages. Stage 1 (foundation, buttons, sheets, toasts) was released on 2026-10-05 as `680c3b1`. Stage 2 ([motion on the live set page](doc/plan/1791188269_motion_live_set_page.md)) was released on 2026-10-05 as `1106548`. Stage 3 ([motion between screens](doc/plan/1791194279_motion_between_screens.md)) was released on 2026-10-05 as `648cca8`. Stage 4 needs its own plan.

The Your groups redesign is done ([plan](doc/plan/1791200012_your_groups_redesign.md)): each group is a card with one settings button, and the viewer's figures are large. No migration. Merged and pushed as `f044805` on 2026-10-05, as recorded by local `main` and `origin/main`. The phone check remains open.

The entry flow fixes from the critique are done ([plan](doc/plan/1791134687_entry_flow_critique_fixes.md)): invite links open Sign up, a new account joins at once, plain wording, and honest lost-password lines. Critique score 24 → 25 of 40. No migration. Not pushed yet.

The stakes forms revamp is done ([plan](doc/plan/1791121411_session_form.md)): one field box for every form, and New session, Set settings and presets in titled groups with pairs. No migration.

The session settled indicator is done ([plan](doc/plan/1791120060_session_settled_indicator.md)): Past sessions rows and the session top bar say Settled, Partly settled or Unsettled, with the amount still to pay. No migration. Released 2026-10-04 as `e5a7ed2` (previous production commit `19c9744`).

Released 2026-10-04 as `19c9744`: the collapsible host dock with its motion, archive and delete (migrations `games.0012`, `groups.0004`) and the entry pages. The previous production commit was `8e75aaf`.

PokerNights is live at https://pokernights-five.vercel.app ([plan](doc/plan/1791104210_vercel_deployment.md), [deployment page](doc/wiki/deployment.md)). A push to `main` is a release.

The entry pages revamp is done ([plan](doc/plan/1791115804_entry_pages.md)): Log in, Sign up, the invite pages share a branded front door, name the inviting group and have a Show password button. No migration.

Archive and delete are done ([plan](doc/plan/1791114191_archive_and_delete_groups_and_sessions.md)): hosts archive, restore and delete sessions and groups; anything with money can be archived only. Two migrations.

The collapsible host dock is done ([plan](doc/plan/1791111069_collapsible_host_dock.md)): on a phone the host's bottom menu folds to one bar and the choice is remembered.

Your groups home is done ([plan](doc/plan/1791102439_your_groups_home.md)): each group reports its state, next action, what you owe or are owed, your record and last result.

UI evolution is done ([plan](doc/plan/1791098885_ui_evolution.md)): shared tokens, SVG branding, Sessions / Stats / Group settings tabs, Session and Set wording, written row actions, neutral non-play states, clearer discrepancy and settle-up, and first player stats.

Rake controls are done ([plan](doc/plan/1791096125_rake_controls.md)): explicit choices at creation and active-value validation.

Set rake and group pool is done ([plan](doc/plan/1791093380_set_rake_and_group_pool.md)). Configure percentage or flat rake before the first buy-in; balances include collected rake and group totals keep units separate.

Add a player during play is done ([plan](doc/plan/1791091385_add_player_during_play.md)). Add players offers a new-name form during play; late buy-ins stay separate.

Live counted total is done ([plan](doc/plan/1791089905_live_counted_total.md)). Count-up previews remaining stacks plus cash-outs against buy-ins while typing.

Default opening buy-ins are done ([plan](doc/plan/1791088166_default_opening_buy_ins.md)). Start the game adds the usual amount for joined players without an accepted buy-in; uncheck to opt out.

Visual redesign slice 4 is done ([plan](doc/plan/1791084843_redesign_slice_4.md)). The Rack redesign is complete for current screens.

Visual redesign slice 3 (session page, settle-up and recap) is done ([plan](doc/plan/1791053204_redesign_slice_3.md)). Visual redesign slice 2 (count-up, cash-out review and finalized sets) is done ([plan](doc/plan/1791050738_redesign_slice_2.md)). The Rack visual redesign slice 1 is done ([plan](doc/plan/1791046015_visual_redesign.md)). Stage 1 is done ([plan](doc/plan/1791037623_poker_home_game_architecture.md)). Cash amounts and the unit option are done ([plan](doc/plan/1791040305_cash_amounts_and_unit_option.md)). Adding several players at once is done ([plan](doc/plan/1791041765_add_several_players_at_once.md)). Sessions with sets, end-of-set cash-outs and timers are done ([plan](doc/plan/1791042668_end_of_set_cash_outs_and_timers.md)).

## Next (each needs its own study and plan)

- [ ] After the next release, on your phone: press a few buttons, open and close a buy-in sheet (also close it while it is still rising), and open the host menu. Say what feels wrong: too bouncy, too slow, too much ([plan](doc/plan/1791186717_motion_overhaul.md)).
- [ ] After the Your groups redesign is released: open Your groups on your phone. Say whether it now reads as finished, whether the gear is where you expect it, and whether any of the removed wording is missed (the player count, the table name beside a due or a last session) ([plan](doc/plan/1791200012_your_groups_redesign.md)).
- [ ] Stage 3 is live. On your phone: tap Your groups → a group → a session → a set and back with the on-screen links, then with the Back gesture; tap through a group's three tabs; open a set from a closed session's results. Say whether the direction tells you where you went, whether the carried name and chips read as one thing moving, and whether anything plays twice or feels slow ([plan](doc/plan/1791194279_motion_between_screens.md)).
- [ ] Stage 2 is live. On your phone with a second device on the same set: add a player, record a rebuy and a cash-out with Left from the other device, end play, confirm counts and balance the books. Say whether the movement helps you see what changed or gets in the way ([plan](doc/plan/1791188269_motion_live_set_page.md)).

- [ ] After the next release, on your iPhone, in the home screen app: open a set that is counting up with the host menu left open. Tap the last count field: the menu should be the one-line bar on the keyboard, with the running total. Scroll up and down with the keyboard open: the bar stays a bar on the keyboard, and the page follows your finger without jumping back. If it misbehaves, add `?kb=1` to the end of the set page's address in Safari, repeat, and send a screenshot ([plan](doc/plan/1791192015_dock_keyboard_scroll.md)).

- [ ] **Password reset.** The repeat critique still rates account recovery P1. A host-issued reset link (hosts already issue invite links) is the candidate; it needs a token model and a migration.
- [ ] Entry pages: make the invitation the subject (group name as the heading, compact mark), shorten the password help, and give a new player a first step on the group page. From the repeat critique.

- [ ] Repair the stale browser scripts (`rack.mjs`, `end_set.mjs`, `opening.mjs`, `opening_drafts.mjs`, `counts.mjs`, `remaining.mjs`); see the note at the end of the [browser checks README](web/tests/browser/README.md).
- [ ] Stage 2: roster management, history list, optional banker, payments before finalization, reopen a finalized game. See the [roadmap](doc/roadmap/README.md).
- [ ] Stage 3: leaderboard and stats.
- [ ] Stage 4: seating.
- [ ] Stage 5: shared use (deployment, password reset, claim links).

## Waiting for the human

- [ ] **Set `DB_CONN_MAX_AGE` to `60` in Vercel** (Settings → Environment Variables → Production; it is `0`), before the next release. Afterwards the readout's `open` figure should be 0 on most taps. If anything errors, set it back to `0` and redeploy ([plan](doc/plan/1791214849_phone_performance_and_smoothness.md)).
- [ ] **Approve or change the plan for fewer queries and one-trip actions** ([plan](doc/plan/1791219154_fewer_queries_and_one_trip_actions.md)).
- [ ] **After the tab fix is released:** with `?perf=0`, switch a group's tabs a few times and say whether it feels as it did before.
- [x] **After the smoothness release, send the phone's numbers** (done 2026-10-06; the marks and the host menu still want a word) ([plan](doc/plan/1791214849_phone_performance_and_smoothness.md)):
  1. Open the app with `?perf=1` added to the address. A small readout appears at the top.
  2. Walk Your groups → a group → a session → a set in play. Record a rebuy. Fold and unfold the host menu. Go back to Your groups.
  3. Screenshot the readout after each few taps (it keeps five lines). Do it once on Wi-Fi and once on mobile data if you can. `?perf=0` removes it.
  4. Say whether a tap on a card or row now feels answered, whether the host menu slides cleanly (also during count-up), and whether the yellow marks and "Rebuy added" still cover anything. Have two players change at once if you can.

- [ ] **Try the numpad and the new count-up on your phone** (now live; only an iPhone confirms that the phone's keyboard stays closed):
  1. On a running set tap Rebuy: the amount shows with twelve keys under it and no phone keyboard. Type an amount, try a third decimal place (nothing should happen), hold delete, tap Max, confirm.
  2. Tap Cash out on a player: amount, keys, "Leaving the set", then the button.
  3. End play. The players' fields should be on the first screen. Tap the first one: the keys rise in place of the bottom bar, with the player's name and the running total. Use Next down the table, then Done, then "Confirm N counts".
  4. Leave the page with a count typed and come back: it should still be there.
  5. Make one count wrong on purpose and open "Cash out counted players": the review should say how much the books are short before you record anything.
  6. Fix it, cash out, and tap "Finalize results": it should ask once, with the totals. Try "Not yet", then finalize.
  7. Open New session and tap a blind or buy-in field: the same keys, with Next between fields.
  8. Say what feels wrong: key size, the panel's height, how Next scrolls, anything you miss from the phone's keyboard. If the phone's keyboard appears anywhere for a number, say where. `NUMPAD=False` in Vercel turns the numpad off without a release.
- [ ] `SPEC.md` does not mention the numpad or that Finalize asks for confirmation. Add them if the spec should match the app.

- [ ] **Try screen changes on your phone:** tap Your groups → a group → a session → a set and back; screens should no longer blink. Use the phone's Back gesture, in Safari and in the installed app. Leave a set page and come back a few times, then record a rebuy. Turn on Airplane Mode and tap a link: the "You're offline" page should appear.

- [ ] **Try actions in place on your phone:** on a running set, scroll to the last player, record a rebuy and check you stay there. During count-up, open a player's Details and type a reversal reason, then confirm a count: the reason should still be there and Details still open. Mark a transfer paid on a session page. Turn on Airplane Mode and try a rebuy: nothing should be sent.

- [ ] **iPhone checklist for the installable app** (only you can do this):
  1. Safari → Share → Add to Home Screen. The icon is the chip-and-crescent on a dark square, named PokerNights.
  2. Open it from the home screen: no address bar or toolbar.
  3. Log in (once more, inside the app).
  4. Walk Your groups → a group → a session → a set → the set log, and back, using only on-screen links.
  5. Switch to another app for a minute and return: the page refreshes.
  6. Turn on Airplane Mode: the offline line appears. Tap a link: the "You're offline" page appears. Turn it off and tap Try again.
  7. Look at the top of the screen around the clock and the bottom around the home bar on the set page.

- [ ] Try the new way in: create an invite, open it in a private window, sign up and check you land in the group with the welcome. Open the same link signed out as an existing player and use “Already have an account? Log in”. Say when to push.

- [ ] **Check on your iPhone:** open New session. The Date field should be as wide and as tall as Table and Location, with its date at the left. Check the dropdowns too. Chrome on the development machine cannot show this, so yours is the only confirmation.

- [ ] Try the settled indicator: open a group's Sessions tab and read the Past sessions badges; mark the last transfer of a session paid and check its row turns to Settled; undo it.

- [ ] Try the entry pages: log out and look at Log in; create an invite in Group settings, open the link in a private window and go through Sign up to Join group. Try Show / Hide and a wrong password. Check that your phone's password manager still offers to fill and save.

- [ ] Try archive and delete as a host: on a closed session open “Manage this session” and archive it, check Stats and Your groups, then restore it from “Archived sessions”. Delete a canceled session. In Group settings try “Manage this group”. It is live.
- [ ] `SPEC.md` does not mention archiving or deleting. Add it if the spec should match the app.

- [ ] Try the collapsible menu on a phone as a host: tap “Host controls” on a set that is counting up, type counts and watch the bar, then confirm. Check it stays folded when you open, start and end another set. Watch it slide, and open “More host controls” to see the options as buttons.

- [ ] Create your superuser against production (command in the [deployment page](doc/wiki/deployment.md)), then add the first host in `/admin/` → Users and play a game on the live site from a phone.

- [ ] Try the new Your groups page as a host and as a player: with a set in play, with a set counting up, after closing a session with unpaid transfers, and with no session. Check “To settle” against the session page.

- [ ] Try the evolved UI: on a group open Sessions, Stats and Group settings. On a running set use the Rebuy and Cash out buttons on a row. End play with a wrong cash-out and read the discrepancy panel. Close a session, mark every transfer paid and check it says Settled. Check Stats for all time and one month.

- [ ] Decide on the logo: `static/branding/` has the chip-and-crescent mark, horizontal, app icon and one-colour versions.

- [ ] Try rake: in New session choose Percentage of buy-in (5%) or Flat amount. For a later empty set, choose Choose rake before buy-ins before starting. Check each buy-in’s gross/rake/in-play split, cash out the remaining stacks, and check group totals. Equal losses from rake alone should owe no further transfer.

- [ ] Try a late arrival: during play, choose Add players, enter a new name and add them. Check they appear with no buy-in, then record their buy-in.

- [ ] Try the live stack counter: end play, enter counts and watch the total/difference. Include 0 and clear an unsaved field. Confirm counts, review cash-outs and check the accounted total stays the same.

- [ ] Try opening buy-ins: add players to an open set, start it and check one usual buy-in each. For another set, uncheck the option and confirm no opening money is added.

- [ ] Try the group and forms: open a current session, create a table, and submit a duplicate roster name. Check that the name stays beside its error. Read a set log.

- [ ] Check transfer alignment on your iPhone after release ([plan](doc/plan/1791210163_transfer_alignment.md)): open Who pays whom in Safari and the installed app with long names. Mark paid, then Undo. Check first-line chips, full amounts and right-aligned actions. Still to pay must change; Session results must stay fixed.

- [ ] Try the redesigned session page: close a finished session, dismiss/reopen the recap, mark a transfer paid, then Undo. Check that Still to pay changes and Session results stay fixed.

- [ ] Try the new active set: tap `+`, confirm a rebuy, tap a player name for cash-out/details, and use the bottom host action.

- [ ] Try the redesigned count-up and final results: type several counts (including 0), confirm once, review and cash out, then finalize.

- [ ] Test a session with two sets as a user: end a set, confirm counts, cash out counted players, start the next set, close the session.
- [ ] Test a pesos game and a chips game as a user.
- [ ] Decide whether to keep the leftover check data in the dev database (accounts `hana` and `ben`, group "Browser Check").
- [ ] Update `SPEC.md` step 2 if it should match the app (cash-outs as amounts, no chip conversion).
- [ ] Confirm or change the open product decisions in the [roadmap](doc/roadmap/README.md), mainly the settlement model and the balance override rule.

# TODO

Short active items. The detail is in the linked documents.

## Active

Arrival after login ([plan](doc/plan/1791546778_arrival_after_login.md), [study](doc/study/1791546703_arrival_after_login.md)): built on `feat/arrival-after-login` on 2026-10-09. Released 2026-10-09 as `f2bd882` (previous production commit `394b4f3`), with the fix for the login sheet staying over the app; the live stylesheet and `door.js` carry both. The one page after a log in, sign up, reset link or claim settles into place: on Your groups the cards rise in turn, the players are set down in a row, the "In play" badge springs in and "To settle" is underlined once; the top bar's mark lands with the chip. No migration, no new words. 915 tests pass on SQLite and PostgreSQL 17; `welcome.mjs` 36 of 36; `door.mjs` 134, `home.mjs` 60, `screens.mjs` 46, `motion.mjs` 34, `navigate.mjs` 52 pass. `DOOR_MOTION=False` stops it. Phone acceptance is open.

Front door revamp ([plan](doc/plan/1791542366_front_door_revamp.md), [study](doc/study/1791542264_front_door_revamp.md)): built on `feat/front-door` on 2026-10-09. Released 2026-10-09 as `394b4f3` (previous production commit `6119dd4`); the live login page serves the new frame, `door.js` and the arrival styles. Log in, Sign up and the other entry screens share a new frame: the chip above, the task in a raised sheet. The chip arrives once per browser session, turns as you type, spins while a form is sent, shakes on a refusal and travels into the top bar on getting in. An invited Sign up is headed "Join {group}". No migration. 905 tests pass on SQLite and PostgreSQL 17. `door.mjs` 134 of 134; `entry.mjs` 91, `reset.mjs` 43, `claim.mjs` 30, `motion.mjs` 34, `screens.mjs` 46, `navigate.mjs` 52 pass. Critique 29 of 40 (was 25). `DOOR_MOTION=False` in Vercel stops the movement. Phone acceptance is open.

Numpad digit motion ([plan](doc/plan/1791538209_numpad_digit_motion.md), [study](doc/study/1791538181_numpad_digit_motion.md)): built on `feat/numpad-digit-motion` on 2026-10-09. Released 2026-10-09 as `6119dd4` (previous production commit `ee18667`); the live site was not checked from here. The pulse of the whole field on every key is replaced: the box stays still, a typed digit fades and rises into place, a deleted one fades out, and digits in a right-aligned field glide. No migration, no server change. 891 tests pass on SQLite; `numpad.mjs` 120 of 120, `count_flow.mjs` 89 of 89, `player_entries.mjs` passes; 891 pass on PostgreSQL 17. Phone acceptance remains open.

Numpad motion ([plan](doc/plan/1791533332_numpad_motion.md), [study](doc/study/1791533294_numpad_motion.md)): built on `feat/numpad-motion` on 2026-10-09. Released 2026-10-09 as `ee18667` (previous production commit `455faab`); the live site was not checked from here. A hit key lights and the amount pulses; holding Delete shows a fill before it clears; a refused key is marked; the keys rise into a sheet; Next brings the next field's name in. No migration, no server change. 891 tests pass on SQLite; `numpad.mjs` 105 of 105, `count_flow.mjs` 89 of 89. Phone acceptance remains open.

Stats revamp ([plan](doc/plan/1791528961_stats_revamp.md), [study](doc/study/1791528884_stats_revamp.md)): built on `feat/stats-revamp` on 2026-10-09. Released 2026-10-09 as `c08d711` (previous production commit `8b51506`); the live site was not checked from here. Stats opens with your own summary; the board orders by profit, average, return, per hour or sessions over four kinds of period, with a minimum to be ranked and movement marks; each player has a page with a running profit chart, eight figures, highlights and sessions. No migration. 891 tests pass on SQLite and PostgreSQL 17; `stats.mjs` 75 of 75. `STATS_PAGES=False` in Vercel returns the old tab. Phone acceptance remains open.

Claim links ([plan](doc/plan/1791527506_claim_links.md), [study](doc/study/1791527468_claim_links.md)): built on `feat/claim-links` on 2026-10-09 and merged to `main` with roster management. Released 2026-10-09 as `8b51506` (previous production commit `283ecc2`); the live site was not checked from here. A host creates a claim link for a player without a login; whoever opens it signs up or confirms and becomes that player with the same history. One migration (`groups.0005`, a new table). 855 tests pass on SQLite and PostgreSQL 17; `claim.mjs` 30 of 30. `CLAIM_LINKS=False` in Vercel turns it off. Phone acceptance remains open.

Roster management ([plan](doc/plan/1791525658_roster_management.md), [study](doc/study/1791525548_roster_management.md)): built on `feat/roster-management` on 2026-10-09. Released 2026-10-09 as `8b51506` with claim links. Removing a player asks first and lists unpaid transfers; a player at the table of an unfinished set cannot be removed; hosts bring removed players back, save a contact note and add up to 30 names at once; anyone changes their own name; rows show sessions played and the last date. No migration. 831 tests pass on SQLite and PostgreSQL 17; `roster.mjs` 44 of 44. `ROSTER_TOOLS=False` in Vercel turns the new tools off. Phone acceptance remains open.

Player rebuys and player-entered counts ([plan](doc/plan/1791266619_player_rebuys_and_counts.md), [study](doc/study/1791266618_player_rebuys_and_counts.md)): built on `feat/player-entries` and merged to local `main` on 2026-10-06. A player with a login records their own rebuy and, after End play, sends their own final count; the host confirms it or types over it; a rebuy recorded from two phones is recorded once. One migration (`ledger.0013`: a new table and one empty column). 789 tests pass on SQLite and PostgreSQL 17; `player_entries.mjs` 48 of 48. `PLAYER_ENTRIES=False` in Vercel turns it off. Released 2026-10-06 as `283ecc2` (previous production commit `7639c8f`); the live site serves the new `counts.js`. Phone acceptance remains open.

Copy button on a new link ([plan](doc/plan/1791265490_copy_link_button.md), [study](doc/study/1791265489_copy_link_button.md)): built on `feat/copy-link` and merged to local `main` on 2026-10-06. A new invite link and a new reset link have a Copy button inside their field. No migration. 748 tests pass on SQLite and PostgreSQL 17; `copy.mjs` 33 of 33. Released 2026-10-06 as `7639c8f` (previous production commit `d573ba0`); the live site serves `copy.js`. Phone acceptance remains open.

Host-issued password reset ([plan](doc/plan/1791263947_host_issued_password_reset.md), [study](doc/study/1791263946_host_issued_password_reset.md)): built on branch `feat/password-reset` and merged to local `main` on 2026-10-06. A host creates a one-use, 24-hour reset link in Group settings → Players; the player sets a new password with it and is logged in. One migration (`accounts.0002`, a new table). 744 tests pass on SQLite and PostgreSQL 17; `reset.mjs` 43 of 43. `RESET_LINKS=False` in Vercel turns it off. Released 2026-10-06 as `d573ba0`, pushed by the human (previous production commit `be53e29`). Phone acceptance remains open.

Phone performance and smoothness ([plan](doc/plan/1791214849_phone_performance_and_smoothness.md), [study](doc/study/1791214796_phone_performance_and_smoothness.md)): stages 1 and 2 are built on branch `perf/phone-smoothness` and verified locally on 2026-10-06. Every response carries a `Server-Timing` header and `?perf=1` shows a readout on the phone; the host dock slides without laying the page out (3 layouts per slide, from 27 to 55); links look pressed from the first frame of a touch; a changed row's mark stays inside the row and "Rebuy added" sits under the name. No migration. 682 tests pass on SQLite and PostgreSQL 17. Released 2026-10-06 as `c84f45a` (previous production commit `90ff346`); the live site answers with the `Server-Timing` header and serves `perf.js`. Phone acceptance remains open. Stage 3 (the server) is decided from the phone's numbers. The phone's numbers arrived on 2026-10-06 and are in the study's addendum. The tab fix was released as `fedaeb0`. Stage 3: **A** (fetch a touched link at once) was released as `53de23b`. **B** (kept database connection) is a Vercel variable for the human to set. **C** (fewer queries: the session page 23 → 14 and no longer growing with sets) and **D** (an in-place action answered in one trip) are built and verified on branches `perf/fewer-queries` and `perf/one-trip-actions` ([plan](doc/plan/1791219154_fewer_queries_and_one_trip_actions.md)) were released together on 2026-10-06 as `60faac0`. `DB_CONN_MAX_AGE` was set to `60` by the human before that release. The human accepted the result on the phone on 2026-10-06 ("runs smoothly now"); the readout's figures after this release were not sent.

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

- [x] After the next release, on your phone: press a few buttons, open and close a buy-in sheet (also close it while it is still rising), and open the host menu. Say what feels wrong: too bouncy, too slow, too much ([plan](doc/plan/1791186717_motion_overhaul.md)).
- [x] After the Your groups redesign is released: open Your groups on your phone. Say whether it now reads as finished, whether the gear is where you expect it, and whether any of the removed wording is missed (the player count, the table name beside a due or a last session) ([plan](doc/plan/1791200012_your_groups_redesign.md)).
- [x] Stage 3 is live. On your phone: tap Your groups → a group → a session → a set and back with the on-screen links, then with the Back gesture; tap through a group's three tabs; open a set from a closed session's results. Say whether the direction tells you where you went, whether the carried name and chips read as one thing moving, and whether anything plays twice or feels slow ([plan](doc/plan/1791194279_motion_between_screens.md)).
- [x] Stage 2 is live. On your phone with a second device on the same set: add a player, record a rebuy and a cash-out with Left from the other device, end play, confirm counts and balance the books. Say whether the movement helps you see what changed or gets in the way ([plan](doc/plan/1791188269_motion_live_set_page.md)).

- [x] After the next release, on your iPhone, in the home screen app: open a set that is counting up with the host menu left open. Tap the last count field: the menu should be the one-line bar on the keyboard, with the running total. Scroll up and down with the keyboard open: the bar stays a bar on the keyboard, and the page follows your finger without jumping back. If it misbehaves, add `?kb=1` to the end of the set page's address in Safari, repeat, and send a screenshot ([plan](doc/plan/1791192015_dock_keyboard_scroll.md)).

- [ ] Front door, from the critique of 2026-10-09: put one line about the app under the Sign up heading and drop or shorten the description on Log in (it reverses a decision of the front door plan, so it is yours); name who invited and how many play on an invited Sign up; a live tick for the password rules.
- [ ] A “change my password” screen for a logged-in person, and claim links for roster players. Both were left out of the password reset cycle.
- [ ] Entry pages: shorten the password help, and give a new player a first step on the group page. From the repeat critique. (The invitation as the subject was done with the front door, 2026-10-09.)

- [ ] Repair the stale browser scripts (`rack.mjs`, `end_set.mjs`, `opening.mjs`, `opening_drafts.mjs`, `counts.mjs`, `remaining.mjs`); see the note at the end of the [browser checks README](web/tests/browser/README.md).
- [ ] Stage 2: roster management, history list, optional banker, payments before finalization, reopen a finalized game. See the [roadmap](doc/roadmap/README.md).
- [ ] Stage 3: leaderboard and stats.
- [ ] Stage 4: seating.
- [ ] Stage 5: shared use (deployment, password reset, claim links).

## Waiting for the human

2026-10-09: the human reported that all checks in this file are done. Every phone and try-it check here, and the five phone checks under Next, were ticked on that word. The `SPEC.md` updates, the decisions and the superuser step are not checks and stay open.

- [ ] **The arrival after login was released on 2026-10-09 (`f2bd882`).** On your phone, after closing and reopening the app:
  1. Log out and log in. On Your groups the cards should rise one after another and the players should slide into their row. Check your figures are readable at once and no number changes.
  2. With a set in play, look for the "In play" badge springing in; with money owed, the line under "To settle".
  3. Log in and tap a card's button straight away: it should open without waiting.
  4. Pull to reload, and come back with Back: nothing should move.
  5. Watch the moment of getting in: nothing of the login screen should stay over the new one.
  6. Say whether it reads as one movement with the chip's flight or as two, and whether it is too much on the tenth login.

- [ ] **The front door was released on 2026-10-09 (`394b4f3`).** On your phone, after closing and reopening the app:
  1. Log out. The chip should travel from the top bar to the middle of the screen.
  2. Close the browser tab, open the site again: the chip should drop and settle, and the form should rise. Check you can type at once.
  3. Type a username and a password: the chip's ring should turn with each key. Say whether the keyboard hides the chip, on Log in and on Sign up.
  4. Tap Show: the crescent should tip.
  5. Log in with a wrong password: the chip should shake once with the message. Then log in: the chip should travel into the top bar.
  6. Tap Sign up and back: the chip and the sheet should move, with no flash of the whole screen.
  7. Check your password manager still offers to fill Log in and to save on Sign up.
  8. Open an invite link signed out: the heading should be "Join" and the group's name.
  9. Say what is too much, too slow or missing. `DOOR_MOTION=False` in Vercel stops all of it without a release.

- [x] **Numpad digit motion was released on 2026-10-09 (`6119dd4`).** On your phone, after closing and reopening the app:
  1. Open Rebuy on a running set and type an amount, slowly and then fast. The field's box should stay still and each digit should fade and rise into place.
  2. Tap Delete: the digit should fade out. Hold Delete: all digits should leave together.
  3. On count-up, type a final count: the digits already there should glide left as each new one arrives.
  4. Watch for a digit that shifts when the movement ends, or a caret that disappears while typing. Say where you see either. `NUMPAD=False` in Vercel returns the phone's keyboard without a release.

- [x] **Numpad motion was released on 2026-10-09 (`ee18667`).** On your phone, after closing and reopening the app:
  1. Open Rebuy on a running set: the keys should rise in with the sheet.
  2. Type an amount fast. Every digit should land and each key should light.
  3. Hold Delete: a fill should run across the key and the amount should clear when it reaches the end. Hold again and let go early: nothing should clear.
  4. Type a third decimal place: the key and the field should both shake and turn red for a moment.
  5. On count-up or New session, tap Next: the name above the keys should slide in.
  6. Say what is too much or too little: the light on the keys, the speed of the rise.


- [x] **The fix for the Stats pills was released on 2026-10-09 (`455faab`).** On your phone, after closing and reopening the app: scroll the Profit … Sessions row sideways and tap Sessions, then Profit. The row should stay where you left it and the highlight should slide without a flicker. Say if any jitter remains, and on which pills.

- [x] **The stats revamp was released on 2026-10-09 (`c08d711`).** First check the Vercel build passed. Then on your phone:
  1. Open a group's Stats tab. Your own figure, rank and last result should lead.
  2. Scroll down the board, then tap Average, Return, Per hour and Sessions: the page should stay where it is, the chosen pill should slide across, and rows should move to their new places.
  3. Tap This year and Last 3 months, then pick a month from the list.
  4. Tap a player. Read the Running profit line, then drag a finger across the chart: the line under it should name each session.
  5. Check a few figures against a session you remember: best night, average, total bought in.
  6. Say what feels wrong: which figures you would drop or add, the minimum to be ranked (3, 2 and 1), the size of the chart, the movement. `STATS_PAGES=False` in Vercel returns the old tab without a release.
- [ ] `SPEC.md` step 5 lists profit, sessions, average and win rate, and a "season" filter. Update it if the spec should match the app (return, per hour, rebuys, the four periods, no seasons yet).



- [x] **Roster management was released on 2026-10-09 (`8b51506`).** On your phone in Group settings → Players:
  1. Read a few rows: the sessions and last-played line should match Stats.
  2. Open "Change your name", try a name someone else has, then a new one.
  3. Open "Manage" on a player, save a contact note, and check a player's phone does not show it.
  4. Tap "Remove from group" on a player who owes money: the page should list the transfer. Tap Keep, then do it again and remove.
  5. Try to remove someone who is at the table of a running set: it should refuse and name the set.
  6. Open "Removed players" and tap Bring back: the row should return with the same sessions.
  7. Add three names in one go, then a batch with one name that is already in the group: nobody should be added and the text should stay.
  8. Say what feels wrong, including the movement of new rows. `ROSTER_TOOLS=False` in Vercel turns the new tools off without a release.
- [x] **Claim links were released on 2026-10-09 (`8b51506`).** First check the Vercel build passed and applied migration `groups.0005`. Then, with two phones:
  1. As a host open Manage on a player without a login, tap Create claim link, and Copy it into a chat to yourself.
  2. On the other phone, signed out, open the link: it should go to Sign up and name the group. Sign up and check you land in the group as that player, with their sessions on the roster row.
  3. Record a rebuy from that phone in a running set.
  4. Open the same link again on a third account: it should say it has been used.
  5. Create a link, then Cancel link, and open it: it should not work. `CLAIM_LINKS=False` in Vercel turns the feature off without a release.
- [ ] `SPEC.md` step 4 says only "Saved player roster for fast session setup". Add removing, restoring and own names if the spec should match the app.

- [x] **Player rebuys and counts are live. With two phones on one set** (a host and a player with a login):
  1. In play, on the player's phone tap Rebuy on your own row and confirm. Watch the host's phone: the row should change within about 5 seconds and say "Rebuy added".
  2. Open the Rebuy sheet for that player on the host's phone and leave it open. Record another rebuy from the player's phone, then confirm on the host's phone: it should be refused and say who recorded the other one.
  3. End play. On the player's phone type a count and tap Send to host. The host's row should show "Entered" and the number, and the main button "Confirm 1 count".
  4. Change the number on the player's phone while the host has typed another player's count: the host's typing should stay.
  5. Type a different number over the player's on the host's phone and confirm. The player's phone should say what the host confirmed.
  6. Say what feels wrong. `PLAYER_ENTRIES=False` in Vercel turns it off without a release.
- [ ] `SPEC.md` says nothing about players recording their own rebuy or count. Add it if the spec should match the app.

- [x] **The copy button is live. On your iPhone:** create an invite link and tap Copy, then paste it into a chat; do the same with a reset link. Try it in Safari and in the installed app. Say whether it reads Copied and whether the pasted link is complete.
- [x] **After it is released, try it on two phones:** as a host open Group settings → Players → Manage a player → Create password reset link, and send yourself the link. Open it signed out on the other phone, try a short password, then a good one. Check you land on Your groups, that the old password no longer works, and that the same link then says it has been used. Create another link and tap Cancel link. If anything misbehaves, `RESET_LINKS=False` in Vercel turns it off.
- [ ] `SPEC.md` does not mention password reset. Add it if the spec should match the app.

- [x] **Set `DB_CONN_MAX_AGE` to `60` in Vercel** (done 2026-10-06; the readout's `open` figure is still to be read) (Settings → Environment Variables → Production; it is `0`), before the next release. Afterwards the readout's `open` figure should be 0 on most taps. If anything errors, set it back to `0` and redeploy ([plan](doc/plan/1791214849_phone_performance_and_smoothness.md)).
- [x] **After C and D are released:** with `?perf=1`, open a session with two or more sets (the count in brackets should be about 14 or less), record a rebuy and mark a transfer paid ("wait" should be near 200 where it was near 400). Play one whole set and say if anything behaves differently. `ANSWER_IN_PLACE=False` in Vercel turns one-trip answers off without a release.
- [x] **After the tab fix is released:** with `?perf=0`, switch a group's tabs a few times and say whether it feels as it did before.
- [x] **After the smoothness release, send the phone's numbers** (done 2026-10-06; the marks and the host menu still want a word) ([plan](doc/plan/1791214849_phone_performance_and_smoothness.md)):
  1. Open the app with `?perf=1` added to the address. A small readout appears at the top.
  2. Walk Your groups → a group → a session → a set in play. Record a rebuy. Fold and unfold the host menu. Go back to Your groups.
  3. Screenshot the readout after each few taps (it keeps five lines). Do it once on Wi-Fi and once on mobile data if you can. `?perf=0` removes it.
  4. Say whether a tap on a card or row now feels answered, whether the host menu slides cleanly (also during count-up), and whether the yellow marks and "Rebuy added" still cover anything. Have two players change at once if you can.

- [x] **Try the numpad and the new count-up on your phone** (now live; only an iPhone confirms that the phone's keyboard stays closed):
  1. On a running set tap Rebuy: the amount shows with twelve keys under it and no phone keyboard. Type an amount, try a third decimal place (nothing should happen), hold delete, tap Max, confirm.
  2. Tap Cash out on a player: amount, keys, "Leaving the set", then the button.
  3. End play. The players' fields should be on the first screen. Tap the first one: the keys rise in place of the bottom bar, with the player's name and the running total. Use Next down the table, then Done, then "Confirm N counts".
  4. Leave the page with a count typed and come back: it should still be there.
  5. Make one count wrong on purpose and open "Cash out counted players": the review should say how much the books are short before you record anything.
  6. Fix it, cash out, and tap "Finalize results": it should ask once, with the totals. Try "Not yet", then finalize.
  7. Open New session and tap a blind or buy-in field: the same keys, with Next between fields.
  8. Say what feels wrong: key size, the panel's height, how Next scrolls, anything you miss from the phone's keyboard. If the phone's keyboard appears anywhere for a number, say where. `NUMPAD=False` in Vercel turns the numpad off without a release.
- [ ] `SPEC.md` does not mention the numpad or that Finalize asks for confirmation. Add them if the spec should match the app.

- [x] **Try screen changes on your phone:** tap Your groups → a group → a session → a set and back; screens should no longer blink. Use the phone's Back gesture, in Safari and in the installed app. Leave a set page and come back a few times, then record a rebuy. Turn on Airplane Mode and tap a link: the "You're offline" page should appear.

- [x] **Try actions in place on your phone:** on a running set, scroll to the last player, record a rebuy and check you stay there. During count-up, open a player's Details and type a reversal reason, then confirm a count: the reason should still be there and Details still open. Mark a transfer paid on a session page. Turn on Airplane Mode and try a rebuy: nothing should be sent.

- [x] **iPhone checklist for the installable app** (only you can do this):
  1. Safari → Share → Add to Home Screen. The icon is the chip-and-crescent on a dark square, named PokerNights.
  2. Open it from the home screen: no address bar or toolbar.
  3. Log in (once more, inside the app).
  4. Walk Your groups → a group → a session → a set → the set log, and back, using only on-screen links.
  5. Switch to another app for a minute and return: the page refreshes.
  6. Turn on Airplane Mode: the offline line appears. Tap a link: the "You're offline" page appears. Turn it off and tap Try again.
  7. Look at the top of the screen around the clock and the bottom around the home bar on the set page.

- [x] Try the new way in: create an invite, open it in a private window, sign up and check you land in the group with the welcome. Open the same link signed out as an existing player and use “Already have an account? Log in”. Say when to push.

- [x] **Check on your iPhone:** open New session. The Date field should be as wide and as tall as Table and Location, with its date at the left. Check the dropdowns too. Chrome on the development machine cannot show this, so yours is the only confirmation.

- [x] Try the settled indicator: open a group's Sessions tab and read the Past sessions badges; mark the last transfer of a session paid and check its row turns to Settled; undo it.

- [x] Try the entry pages: log out and look at Log in; create an invite in Group settings, open the link in a private window and go through Sign up to Join group. Try Show / Hide and a wrong password. Check that your phone's password manager still offers to fill and save.

- [x] Try archive and delete as a host: on a closed session open “Manage this session” and archive it, check Stats and Your groups, then restore it from “Archived sessions”. Delete a canceled session. In Group settings try “Manage this group”. It is live.
- [ ] `SPEC.md` does not mention archiving or deleting. Add it if the spec should match the app.

- [x] Try the collapsible menu on a phone as a host: tap “Host controls” on a set that is counting up, type counts and watch the bar, then confirm. Check it stays folded when you open, start and end another set. Watch it slide, and open “More host controls” to see the options as buttons.

- [ ] Create your superuser against production (command in the [deployment page](doc/wiki/deployment.md)), then add the first host in `/admin/` → Users and play a game on the live site from a phone.

- [x] Try the new Your groups page as a host and as a player: with a set in play, with a set counting up, after closing a session with unpaid transfers, and with no session. Check “To settle” against the session page.

- [x] Try the evolved UI: on a group open Sessions, Stats and Group settings. On a running set use the Rebuy and Cash out buttons on a row. End play with a wrong cash-out and read the discrepancy panel. Close a session, mark every transfer paid and check it says Settled. Check Stats for all time and one month.

- [ ] Decide on the logo: `static/branding/` has the chip-and-crescent mark, horizontal, app icon and one-colour versions.

- [x] Try rake: in New session choose Percentage of buy-in (5%) or Flat amount. For a later empty set, choose Choose rake before buy-ins before starting. Check each buy-in’s gross/rake/in-play split, cash out the remaining stacks, and check group totals. Equal losses from rake alone should owe no further transfer.

- [x] Try a late arrival: during play, choose Add players, enter a new name and add them. Check they appear with no buy-in, then record their buy-in.

- [x] Try the live stack counter: end play, enter counts and watch the total/difference. Include 0 and clear an unsaved field. Confirm counts, review cash-outs and check the accounted total stays the same.

- [x] Try opening buy-ins: add players to an open set, start it and check one usual buy-in each. For another set, uncheck the option and confirm no opening money is added.

- [x] Try the group and forms: open a current session, create a table, and submit a duplicate roster name. Check that the name stays beside its error. Read a set log.

- [x] Check transfer alignment on your iPhone after release ([plan](doc/plan/1791210163_transfer_alignment.md)): open Who pays whom in Safari and the installed app with long names. Mark paid, then Undo. Check first-line chips, full amounts and right-aligned actions. Still to pay must change; Session results must stay fixed.

- [x] Try the redesigned session page: close a finished session, dismiss/reopen the recap, mark a transfer paid, then Undo. Check that Still to pay changes and Session results stay fixed.

- [x] Try the new active set: tap `+`, confirm a rebuy, tap a player name for cash-out/details, and use the bottom host action.

- [x] Try the redesigned count-up and final results: type several counts (including 0), confirm once, review and cash out, then finalize.

- [x] Test a session with two sets as a user: end a set, confirm counts, cash out counted players, start the next set, close the session.
- [x] Test a pesos game and a chips game as a user.
- [ ] Decide whether to keep the leftover check data in the dev database (accounts `hana` and `ben`, group "Browser Check").
- [ ] Update `SPEC.md` step 2 if it should match the app (cash-outs as amounts, no chip conversion).
- [ ] Confirm or change the open product decisions in the [roadmap](doc/roadmap/README.md), mainly the settlement model and the balance override rule.

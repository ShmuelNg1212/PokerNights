# TODO

Active and next items only, 40 lines at most. History is in `doc/plan/`, git, and claude-mem.

## Phone checks (unreleased: `feat/front-door-2`)

- [ ] Front door ([plan](doc/plan/1792250537_front_door_second_pass.md)): Log in shows the chip, the form and "Forgot your password?…" with no description. Open an invite link in a private tab: "Join {group}", "{you} invited you · N players", then the description, then the form.
- [ ] Sign up: one password field. Type: the two rings fill as you pass 8 characters and add a letter. With the keyboard up, can you see them? Your password manager offers to save.
- [ ] Send a common password such as "password1": the reason shows directly under the field. An invited Sign up's button says "Create account and join"; the username hint lists @ . + - _.

## Phone checks (released 2026-10-17)

- [ ] Sessions tab ([plan](doc/plan/1792243014_sessions_tab_redesign.md)): open a group during a game. Your table in play is the first card, on felt, with "You're playing" and **Open the table**; a tap anywhere on the card opens the set, once. Other tables follow; a draft is last, for hosts only.
- [ ] Past sessions: months, newest first, last year folded. Each row shows your result and "You pay …" or "… pays you …". Pay one transfer: within 5 seconds the line goes.
- [ ] Profile ([plan](doc/plan/1792238274_profile_page.md)): tap your chip, then **Your profile**. Your pesos total from all groups, the chart, four tiles, then each group; chips groups are separate. All time and This year switch in place.
- [ ] Change your name there: every group shows the new name. Change your password: this phone stays in, another browser is logged out.
- [ ] Override button: on a set where the books are off, under the books' figures, "Cannot find the error?" then an outlined **Finalize with an override** button. Tap it: it darkens, the chevron turns, the form opens. Tap again: it closes.
- [ ] Books off ([plan](doc/plan/1792225143_books_off.md)): the gap reads "₱100 missing"; each cashed-out player shows in, out and net; **See the ₱100 difference** goes to the suspect player (or the books) with a brass ring. An override line is brass and names who took it.
- [ ] Header ([plan](doc/plan/1792222305_header_redesign.md)): the way back is in the top bar with nothing under it; on a set the green dot is beside it. Your chip at top right opens username and Log out; tap outside closes it; on a set it stays open for ten seconds. A seat draw's mark is on the felt.

## Next (each needs its own study and plan)

- [ ] Entry pages: shorter password help; a first step for a new player on the group page.
- [ ] Repair the stale browser scripts (`rack.mjs`, `end_set.mjs`, `opening.mjs`, `opening_drafts.mjs`, `counts.mjs`, `remaining.mjs`), and the checks that fail on `main` too: `navigate.mjs` (22 screen changes; a poll after leaving the set) and `home.mjs` (48 px targets in a card); see the [browser checks README](web/tests/browser/README.md).
- [ ] Chip k6: dark initials on the orange fill measure 3.8:1 (found by the Sessions tab critique).
- [ ] Stats board rows: the rounded `.stat-row` curls its hairline at both ends (found in the profile critique; fixed on the profile only).
- [ ] Stage 2, what remains: optional banker, payments before a session closes, filters on past sessions. See the [roadmap](doc/roadmap/README.md).
- [ ] Stage 3, what remains: seasons.
- [ ] Fold `doc/wiki/features.md` into `doc/wiki/spec.md` ([queued plan](doc/roadmap/plan_queue/fold_features_into_spec.md)).

## Waiting for the human

- [ ] Create your superuser against production (command in [deployment](doc/wiki/deployment.md)), add the first host in `/admin/` → Users, and play a game on the live site.
- [ ] Decide on the logo: `static/branding/` has the chip-and-crescent mark, horizontal, app icon and one-colour versions.
- [ ] Clear the leftover check data from the dev database: group "Kamuning Card Club" (13 sessions), accounts `hana` and `ben`. Asked 2026-10-12; the agent's delete was refused by the permission check.
- [ ] Confirm or change the open product decisions in the [roadmap](doc/roadmap/README.md), mainly the settlement model and the balance override rule.

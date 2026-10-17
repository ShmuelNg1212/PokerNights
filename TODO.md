# TODO

Active and next items only, 40 lines at most. History is in `doc/plan/`, git, and claude-mem.

## Phone checks (released 2026-10-17)

- [ ] Override button: on a set where the books are off, under the books' figures, "Cannot find the error?" then an outlined **Finalize with an override** button. Tap it: it darkens, the chevron turns, the form opens. Tap again: it closes.
- [ ] Books off ([plan](doc/plan/1792225143_books_off.md)): the gap reads "₱100 missing"; each cashed-out player shows in, out and net; **See the ₱100 difference** goes to the suspect player (or the books) with a brass ring. An override line is brass and names who took it.
- [ ] Header ([plan](doc/plan/1792222305_header_redesign.md)): the way back is in the top bar with nothing under it; on a set the green dot is beside it. Your chip at top right opens username and Log out; tap outside closes it; on a set it stays open for ten seconds. A seat draw's mark is on the felt.

## Next (each needs its own study and plan)

- [ ] Front door, from the 2026-10-09 critique: one line about the app under Sign up; shorter description on Log in (reverses a front door decision, so yours); name the inviter and player count on an invited Sign up; a live tick for password rules.
- [ ] A "change my password" screen for a logged-in person.
- [ ] Entry pages: shorter password help; a first step for a new player on the group page.
- [ ] Repair the stale browser scripts (`rack.mjs`, `end_set.mjs`, `opening.mjs`, `opening_drafts.mjs`, `counts.mjs`, `remaining.mjs`); see the [browser checks README](web/tests/browser/README.md).
- [ ] Stage 2, what remains: optional banker, payments before a session closes, filters on past sessions. See the [roadmap](doc/roadmap/README.md).
- [ ] Stage 3, what remains: seasons.
- [ ] Fold `doc/wiki/features.md` into `doc/wiki/spec.md` ([queued plan](doc/roadmap/plan_queue/fold_features_into_spec.md)).

## Waiting for the human

- [ ] Say whether the 69 merged local branches should be deleted.
- [ ] Create your superuser against production (command in [deployment](doc/wiki/deployment.md)), add the first host in `/admin/` → Users, and play a game on the live site.
- [ ] Decide on the logo: `static/branding/` has the chip-and-crescent mark, horizontal, app icon and one-colour versions.
- [ ] Clear the leftover check data from the dev database: group "Kamuning Card Club" (13 sessions), accounts `hana` and `ben`. Asked 2026-10-12; the agent's delete was refused by the permission check.
- [ ] Confirm or change the open product decisions in the [roadmap](doc/roadmap/README.md), mainly the settlement model and the balance override rule.

# TODO

## Next (each needs its own study and plan)

- [ ] Entry pages: shorter password help; a first step for a new player on the group page.
- [ ] Chip k6: dark initials on the orange fill measure 3.8:1 (found by the Sessions tab critique).
- [ ] Stats board rows: the rounded `.stat-row` curls its hairline at both ends (found in the profile critique; fixed on the profile only).
- [ ] Stages 2 and 3, what remains: optional banker, seasons. See the [roadmap](doc/roadmap/README.md).
- [ ] Fold `doc/wiki/features.md` into `doc/wiki/spec.md` ([queued plan](doc/roadmap/plan_queue/fold_features_into_spec.md)).

## Phone checks (released 2026-10-30 as `5a207e2`)

- [ ] Group settings → Group rake account → Rake in settle-up: choose "Paid into the rake fund" and save.
- [ ] Close a session with rake: each player's settle-up figure equals their standing; a "Rake fund" line with a brass R chip takes the rake; mark it paid.
- [ ] Two hosts count up one set on two phones: one host's saved count shows on the other phone within about 2 seconds, also while that phone's numpad is open.
- [ ] Both hosts type a count for the same player: the second phone says "… saved ₱…".
- [ ] One host finalizes and starts the next set: the other host's phone goes to the new set; a player's phone shows the notice.

## Waiting for the human

- [ ] Create your superuser against production (command in [deployment](doc/wiki/deployment.md)), add the first host in `/admin/` → Users, and play a game on the live site.
- [ ] Decide on the logo: `static/branding/` has the chip-and-crescent mark, horizontal, app icon and one-colour versions.
- [ ] Clear the leftover check data from the dev database: group "Kamuning Card Club" (13 sessions), accounts `hana` and `ben`. Asked 2026-10-12; the agent's delete was refused by the permission check.
- [ ] Confirm or change the open product decisions in the [roadmap](doc/roadmap/README.md), mainly the settlement model and the balance override rule.

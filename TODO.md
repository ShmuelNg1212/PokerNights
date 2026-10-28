# TODO

## Next (each needs its own study and plan)

- [ ] Entry pages: shorter password help; a first step for a new player on the group page.
- [ ] Repair the browser scripts that still fail on `main`: `table.mjs` (two sheet checks, then stops at "a player on an open set"), `late_player.mjs` (2 checks), `rake.mjs` (3 checks, then stops) and `flow.mjs` (3 motion checks); see the [browser checks README](web/tests/browser/README.md).
- [ ] Chip k6: dark initials on the orange fill measure 3.8:1 (found by the Sessions tab critique).
- [ ] Stats board rows: the rounded `.stat-row` curls its hairline at both ends (found in the profile critique; fixed on the profile only).
- [ ] Stages 2 and 3, what remains: optional banker, filters on past sessions, seasons. See the [roadmap](doc/roadmap/README.md).
- [ ] Fold `doc/wiki/features.md` into `doc/wiki/spec.md` ([queued plan](doc/roadmap/plan_queue/fold_features_into_spec.md)).

## Waiting for the human

- [ ] Create your superuser against production (command in [deployment](doc/wiki/deployment.md)), add the first host in `/admin/` → Users, and play a game on the live site.
- [ ] Decide on the logo: `static/branding/` has the chip-and-crescent mark, horizontal, app icon and one-colour versions.
- [ ] Clear the leftover check data from the dev database: group "Kamuning Card Club" (13 sessions), accounts `hana` and `ben`. Asked 2026-10-12; the agent's delete was refused by the permission check.
- [ ] Confirm or change the open product decisions in the [roadmap](doc/roadmap/README.md), mainly the settlement model and the balance override rule.

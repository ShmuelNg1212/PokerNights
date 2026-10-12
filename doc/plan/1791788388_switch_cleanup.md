# Switch cleanup: plan

Date: 2026-10-12, Asia/Manila. [Study](../study/1791788387_switch_cleanup.md).

Status: **waiting for the human's approval.** Nothing below is built.

## Outcome

Each screen has one copy. The earlier count-up, and with the human's word the earlier set page and the earlier Stats tab, are removed with their switches. Nothing a person sees on the live site changes.

## Decisions for the human

1. **Is the set page accepted?** Its phone checks were ticked on 2026-10-12. If yes, stage 2 removes `TABLE_REVAMP` and the earlier set page.
2. **Is the Stats tab accepted?** Its phone checks were ticked on 2026-10-09. If yes, stage 3 removes `STATS_PAGES` and the earlier single list.
3. **Before the release, look at Vercel → Settings → Environment Variables → Production.** `COUNT_REVAMP`, `TABLE_REVAMP` and `STATS_PAGES` should be absent or `True`. If one is `False`, say so before the release: removing it would change the live screen.
4. **The 69 merged local branches.** Say if they should be deleted (`git branch -d`, which refuses any branch that is not merged).

The 13 switches that turn a feature off stay.

## Stages

One branch, `chore/switch-cleanup`, one commit per stage, stacked locally and not pushed until told.

### Stage 1: `COUNT_REVAMP` (accepted 2026-10-12)

1. Delete `templates/web/_count_up.html`.
2. In `templates/web/_session_live.html` and `templates/web/_session_live_classic.html`, the counting-up branch includes `web/_count_v2.html` with no condition.
3. Remove `count_revamp` from the set page's context in `web/views.py` and `COUNT_REVAMP` from `config/settings.py`.
4. Remove `test_the_switch_returns_the_earlier_count_up` from `web/tests/test_count_flow.py`.
5. Remove the `count-facts` and `count-stages` rules from `static/css/app.css`, after confirming again that no template, script or test names them.
6. Words: the `COUNT_REVAMP` row in `doc/wiki/deployment.md`, the two lines in `doc/wiki/features.md`, the line in `web/tests/browser/README.md`, and the sentences in `DESIGN.md` and `.impeccable/surfaces/templates-web-end-set.md` that describe the earlier layout as still reachable.

### Stage 2: `TABLE_REVAMP` (only if decision 1 is yes)

1. Delete `templates/web/_session_live_classic.html` and `templates/web/_players_classic.html`. Remove the first branch of `_session_live.html`.
2. In `web/views.py`: remove `table_revamp` from the context, compute `prep` always, and drop `settings.TABLE_REVAMP` from the seat draw's condition.
3. Remove the setting and the tests that turn it off. Remove any style that only the two deleted templates use, found the same way as in stage 1.
4. Words: `doc/wiki/deployment.md`, `doc/wiki/features.md`, `doc/wiki/architecture.md`, `DESIGN.md`.

### Stage 3: `STATS_PAGES` (only if decision 2 is yes)

1. Delete `templates/web/_group_stats_legacy.html`. `templates/web/group.html` includes `_group_stats.html` with no condition.
2. Remove the setting, its two uses in Python (the tab and the player page's "not found"), and the tests that turn it off.
3. Words: `doc/wiki/deployment.md`, `doc/wiki/features.md`.

## Verification, by the agent

After each stage:

1. `grep` finds the switch's name nowhere outside `doc/study/`, `doc/plan/` and the dated history in `TODO.md`.
2. `.venv/bin/python manage.py test` passes on SQLite, and on PostgreSQL before the release. The count of tests falls only by the tests removed.
3. The rendered page is the same as before the stage: for a seeded set in each state (open, in play, counting up, finalized) and for the Stats tab, the HTML fetched before and after is compared and differs in nothing.
4. Browser checks: `count_flow.mjs` after stage 1, `table.mjs` and `seat_draw.mjs` after stage 2, `stats.mjs` after stage 3, each with the same passes as on `main` before the stage.

## Release and the way back

No migration. The release changes nothing a person sees, so there is no phone check. If something is wrong after the release, the way back is `git revert` of the stage's commit and a push; a switch in Vercel no longer exists for these three screens.

## Not in this plan

- Repairing the six stale browser scripts: its own study.
- The 13 feature switches: looked at again after each feature has been through a few game nights.

## Sync docs

`doc/wiki/README.md` journal row, the roadmap's Cleanup section, `TODO.md`.

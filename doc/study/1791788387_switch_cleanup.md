# Switch cleanup: study

Date: 2026-10-12, Asia/Manila.

## Request

The human said: "Start Cleaning up the code." Earlier the same day they said "the count revamp was successful", which is the acceptance the count-up plan was waiting for before its earlier templates and switch are removed.

## What is there

`config/settings.py` reads 16 on/off switches from the environment. All default to on. They are of two kinds.

**Switches that keep an earlier copy of a screen.** With the switch off, the app serves the screen as it was before a revamp. The earlier copy is code that nobody sees, that every later change to the screen has to keep working, and that the tests still cover.

| Switch | Earlier copy it keeps | Size | State of the revamp |
|---|---|---|---|
| `COUNT_REVAMP` | `templates/web/_count_up.html` | 29 lines, one test, two styles used by nothing else (`count-facts`, `count-stages`) | Accepted 2026-10-12 |
| `TABLE_REVAMP` | `_session_live_classic.html`, `_players_classic.html` | 87 lines, 3 uses in `web/views.py`, one test file | Phone checks ticked 2026-10-12; no acceptance in words |
| `STATS_PAGES` | `_group_stats_legacy.html` | 38 lines, 2 uses in Python, two test files | Phone checks ticked 2026-10-09; no acceptance in words |

**Switches that turn a feature off.** With the switch off, the feature is absent and nothing else replaces it: `NUMPAD` (the phone's keyboard returns), `SERVICE_WORKER`, `ANSWER_IN_PLACE`, `RESET_LINKS`, `PLAYER_ENTRIES`, `CLAIM_LINKS`, `ROSTER_TOOLS`, `INSTALL_PROMPT`, `SHARE_RESULTS`, `REOPENING`, `CARRY_DEBTS`, `SEAT_DRAW`, `DOOR_MOTION`. These cost one condition each and no second copy of a screen.

## Where `COUNT_REVAMP` is read

1. `config/settings.py:201`: the setting.
2. `web/views.py:210`: passed to the set page as `count_revamp`.
3. `templates/web/_session_live.html:73` and `templates/web/_session_live_classic.html:24`: choose `_count_v2.html` or `_count_up.html`.
4. `web/tests/test_count_flow.py:259`: `test_the_switch_returns_the_earlier_count_up`.
5. Words: `doc/wiki/deployment.md:35`, `doc/wiki/features.md:471` and `:496`, `web/tests/browser/README.md:162`, `DESIGN.md:854`, `.impeccable/surfaces/templates-web-end-set.md:72`.

`_count_up.html` includes `_players_count.html`, `_count_total.html`, `_rake_totals.html`, `_balance.html`, `_correction.html` and `_host_controls.html`. Every one of them is also included by a template that stays, so only `_count_up.html` itself goes. Of its styles, `count-facts` (6 rules) and `count-stages` (1 rule) appear in no other template, script or test. The others (`count-layout`, `count-workspace`, `count-progress`, `end-balance`, `books-known`, `set-totals`, `section-heading`) are used elsewhere and stay.

## The order matters

`_session_live_classic.html` also reads `count_revamp`. Removing `COUNT_REVAMP` first leaves the classic page choosing `_count_v2.html` always, which is what it does today with the defaults. Removing `TABLE_REVAMP` afterwards deletes that file whole. `SEAT_DRAW` only draws when `TABLE_REVAMP` is on, so that condition shortens too.

## Risk

- The live site runs with every switch at its default, as far as the repository records. If `COUNT_REVAMP=False` were set in Vercel, removing the switch would change the live count-up on the next release. The human can see this in Vercel; the agent cannot.
- After removal there is no way back to the earlier count-up without a release. The way back becomes a revert of the release commit, as for any other change.
- Removing a switch moves no data and needs no migration.

## Also piling up, not part of this cycle

- Six browser check scripts no longer match their screens (`rack.mjs`, `end_set.mjs`, `opening.mjs`, `opening_drafts.mjs`, `counts.mjs`, `remaining.mjs`). Repairing them means deciding, check by check, whether the check or the screen is right. That is its own study.
- 69 local branches are merged into `main`. Deleting them is not a code change and loses nothing, but it is the human's repository to tidy.

## Options

| Option | For | Against |
|---|---|---|
| A. Remove `COUNT_REVAMP` only | Accepted in words; smallest; it was promised in the count-up plan | The two other earlier copies stay |
| B. Remove the three switches that keep an earlier copy, one commit each, one release | The app has one copy of each screen; later changes to the set page and Stats get cheaper | Needs the human's word that the set page and Stats are accepted; no way back to either without a release |
| C. Remove all 16 | Fewest conditions | The human tests on the live build with no preview; the feature switches are how a bad release is made safe without another release. Several guard features released in the last two days |

Recommend B if the human accepts the set page and Stats, otherwise A. Keep the 13 feature switches for now, and look at them again once each feature has been through a few real game nights.

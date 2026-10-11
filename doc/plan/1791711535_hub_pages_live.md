# Your groups and a group's sessions update by themselves: plan

Status: approved 2026-10-11 ("approved"); the reading of the report stands uncorrected. Built and released. Date: 2026-10-11, Asia/Manila. Study: [An open session does not update on players' screens](../study/1791711534_hub_pages_live.md).

## Outcome

A player sitting on Your groups or on a group's Sessions tab sees, within about 5 seconds and without a reload, a session appear when the host opens it, its set change state, the number at the table change, and the session move to "to settle" when it closes. Hosts see the same.

No migration, nothing stored, no new dependency.

## Behaviour

| Moment | Today | After |
|---|---|---|
| Host creates a session and opens its set | Nothing on a player's Your groups or group page until a reload | The group's card shows the table and "Open the table"; the group page lists it under Current sessions |
| The set starts, ends, is finalized | The old state word | The new one |
| A player joins or is added | "N at the table" stays | It follows |
| The session is closed | Still listed as current; no "you owe" | Moves to past sessions with its settle badge; "To settle" appears on Your groups |
| A transfer is marked paid | The old "you owe" and badge | They follow |
| A field has focus or typing, or New group is open | — | The update waits until that ends |
| Group settings, Stats | — | Never redrawn by themselves |
| The tab is hidden | — | No requests; one at once on return |
| Two quiet minutes | — | Every 20 seconds instead of every 5 |
| No JavaScript | Reload by hand | Unchanged |

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **Which screens:** Your groups and the Sessions tab of a group. Not Stats (it changes only when a session closes; the next visit shows it) and not Group settings (it shows links once). Say if Stats should follow too.
2. **Same rhythm as the session page:** 5 seconds, 20 after two quiet minutes, none while hidden.
3. **A sub-second gap is accepted:** a change made in the instant between the page being drawn and its first question is picked up at the next change or visit. Closing it would cost every load of Your groups four more queries.
4. **If you meant the set page or the session page,** say so before I start: both measured as updating for a player here, so that would be a different fault.

## Implementation

Branch `fix/hub-pages-live` from `main`. Tests first.

1. **`settlement/queries.py`: `hub_stamp(group_ids)`.** A short hash over those groups of: each set's id, state and `finalized_at` with its session's id, status and archive mark; the number of players at the table of each unfinished set; each plan's id and whether it is current; how many payments exist and stand. About five small queries however many groups.
2. **`web/views.py`:** `home_state` (`state/`, over the requester's active memberships in unarchived groups, plus the list of those group ids) and `group_state` (`g/<id>/state/`, membership as on the page). Each answers 204 when `?v=` matches, else the stamp.
3. **Templates:** `home.html` and the Sessions view of `group.html` declare the in-place redraw (`turbo-refresh-method: morph`, scroll kept) and carry `data-state-url` with no stamp. Their disclosures get a kept-open key.
4. **`static/js/nightlive.js`** becomes the one script for every page that carries `data-state-url`: with no stamp on the page it asks at once and takes the answer as its baseline. It also waits while a disclosure without a kept state is open, and never redraws a page that answered a form (`data-method` not GET).
5. **Tests.**
   - Django: the stamp changes when a session is created, its set opened, started, ended, finalized, a player added or withdrawn, the session closed, reopened, archived, a transfer marked; not on a buy-in; one group's change does not alter another group's stamp; both endpoints answer 204 and 200, 404 or a redirect to strangers, and stay under a stated number of queries; Your groups still costs exactly 11.
   - Browser (`hub_live.mjs`, new): a player on Your groups and on a group page while the host creates and opens a session, starts the set, adds a player, ends, finalizes and closes: each arrives within about 7 seconds without a reload and with the scroll position kept; New group open and half typed is not disturbed and the update lands after; Settings and Stats ask nothing; a redraw during the arrival after login does not replay it; hidden tab; no script error. `night_live.mjs`, `home.mjs` and `welcome.mjs` rerun.
   - Both suites: SQLite and PostgreSQL.
6. **Documents.** Wiki (features, architecture), browser README, TODO.md.

## Out of scope

- Stats and Group settings.
- Showing money in play on Your groups.
- Push notifications when a session opens.

## Acceptance

1. A player on Your groups sees a newly opened session's card within about 5 seconds.
2. A player on a group's Sessions tab sees a set's state change and the session's close the same way.
3. An open New group form with typing survives an update.
4. Group settings never redraws by itself.
5. Both test suites pass; Your groups still costs 11 queries.

## Release

Kept local until you say to push. No migration.

## Progress

2026-10-11: Approved with "approved". Built on `fix/hub-pages-live` from `main`; kept local.

Changes from the plan:

- **The disclosures were not given a kept-open key.** An existing test pins New group's markup. An open disclosure that holds a form and has no key is treated as in use instead, which protects the same thing.
- **The stamp also counts each group's active members,** because the cards show them.
- **`web/tests/test_inplace.py` changed:** it pinned that no page but the set and session pages declares the in-place redraw. Your groups and the Sessions tab now do; Group settings, New session and Log in are still held to not doing so.
- **With that setting, tapping a link to the page one is already on redraws it in place.** Not in the plan; noted in the wiki.
- **The poll is held to 9 queries,** five for the stamp and the rest for login and membership.

Verification:

- 1029 tests pass on SQLite (15 skipped) and on PostgreSQL 17, 9 of them new (`web/tests/test_hub_live.py`).
- `hub_live.mjs`: 19 of 19 on a fresh temporary database, a player's Your groups and group page watching while the host acted through the services. The first run stopped on two faults in the script itself (a scroll target the short page could not reach, and a name declared twice).
- `night_live.mjs`: 22 of 22 with the generalized script. `welcome.mjs`: 35 of 35.
- `home.mjs`: 57 of 60. The three failures ("every link and button in a card is at least 48px tall", with an empty list of offenders) fail the same way on `main` without this change. Not looked into.

Acceptance: 1 to 5 are met in headless Chrome with signed-in browsers.

Not verified: real phones; whether this is the screen the report was about (the human approved the reading without comment); the cost on Vercel and Neon of many phones idle on Your groups; a screen reader. A fresh reviewer did not read the branch.

Documentation synced: wiki (features, architecture), browser README, TODO.

2026-10-11 release: the human said "push". `fix/hub-pages-live` was merged to `main` as `1da9bfd` and pushed (previous production commit `6cae533`). 1029 tests passed on SQLite and on PostgreSQL 17 on the merged `main` before the push. No migration. About three minutes later the live `/state/` address answered a signed-out request with a redirect to the login, so the route exists, and the live `nightlive.js` reads `data-state-url`. No page was opened signed in on the live site, so an update arriving there was not seen.

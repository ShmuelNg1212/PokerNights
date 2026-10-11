# The session page updates by itself: plan

Status: approved 2026-10-11 ("approved"); all four decisions as recommended. Built and released. Date: 2026-10-11, Asia/Manila. Study: [The session page does not update by itself](../study/1791706965_session_page_live.md).

## Outcome

A player with a session page open sees, within a few seconds and without touching the phone, what the host does: a transfer marked paid or unpaid, the session closed or reopened, a set started, finalized or reopened. Nothing typed or opened on the page is lost.

No migration, no new stored state, no new dependency.

## Behaviour

| Moment | Today | After |
|---|---|---|
| Host marks a transfer paid | A player sees it after a reload | Within about 5 seconds the row settles on the player's page, as it does on the host's, and "N of M paid" and "you still pay" follow |
| The last transfer is marked | — | "Settled" arrives once, as on the host's page |
| Host closes the session | The player stays on "Session open" | The page becomes the settle-up page; the recap opens by itself once, as on a fresh load |
| Host reopens the session or a set | The retired list stays | The page shows the open session and the reason line |
| A set is started or finalized | Old list of sets | The list of sets and "results so far" update |
| A sheet is open (recap, share, reopen) or a field is being typed in | — | The update waits until the sheet closes and the field is left |
| The tab is hidden | — | No requests. On return it asks at once |
| Nothing changes for two minutes | — | It asks every 20 seconds instead of every 5, and returns to 5 at the next change |
| The request fails | — | It tries again more slowly, as the set page does. No message for a single miss |
| Archived session | No change is possible | Not polled |
| No JavaScript | Reload by hand | Unchanged |

The host's page is polled the same way, so two hosts see each other's marks.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **Every 5 seconds, slowing to 20 after two quiet minutes.** The set page asks every 4. Recommended as a balance between "live" and the free plan's limits; say a number if you want it faster.
2. **The whole session page, open or closed,** not only the closed one. Recommended: a player waiting on "Session open" is the one who misses the close.
3. **Your groups (the home page) stays as it is.** Its "you owe" line updates on the next visit. Say if it should be live too.
4. **No switch.** If the poll fails or is refused, the page behaves as today. Say if you want `SESSION_LIVE` in Vercel as the other features have.

## Implementation

Branch `fix/session-page-live` from `main`. Tests first.

1. **`settlement/queries.py`: `night_stamp(night)`.** A short hash of: the session's status and archive mark; each set's id and state; the id of the current results revision of each set; the current plan's id; the number of payments and of active payments. Three small queries. Nothing is stored.
2. **`web/views.py`: `night_state`** at `n/<id>/state/`: resolves through membership like the session page; answers 204 when `?v=` equals the stamp, else `{"stamp": …}`. The session page writes its stamp and this address on `.night-layout`.
3. **`static/js/nightlive.js`,** registered with `page.js`: asks on the timer above; on a new stamp it asks Turbo for the same page and lets it morph, then raises the events the page's scripts already listen to. It waits while a dialog is open or a field in `main` has focus or unsaved typing, and stops when the page is left.
4. **`settle.js`:** a row whose mark changed in a redraw it did not send settles the same way as one the host tapped.
5. **`app.js`:** the 30-second return reload skips a page that polls itself, as it does for the set page.
6. **Tests.**
   - Django: the stamp changes on mark paid, mark unpaid, close, reopen session, reopen set, finalize, next set and a set transition; it does not change on a plain second read or on a buy-in; the endpoint answers 204 and 200 as described, 404 to a non-member, and costs at most 6 queries; the session page stays within 14.
   - Browser (`night_live.mjs`, new): a player's page and a host's page side by side: paid mark, unpaid, the last mark and "Settled", close, reopen; scroll position and an open disclosure survive; an open sheet defers the update and it lands on close; a hidden tab asks nothing; the slow-down after quiet; no script error. `night.mjs` and `settled.mjs` rerun.
   - Both suites: SQLite and PostgreSQL.
7. **Documents.** Wiki (features: remove the limit, describe the behaviour; architecture: live updates), DESIGN.md if the row's settle on a remote change needs a line, browser README, TODO.md with the phone checklist.

## Out of scope

- The home page and the group page.
- Push notifications when a transfer is marked.
- Changing how often the set page asks.

## Acceptance

1. With a player's phone on a closed session, the host marks a transfer paid: the player's row shows Paid within about 5 seconds, without a reload and without losing their scroll position.
2. The host closes a session: a player on its page sees the settle-up within about 5 seconds.
3. An open recap or share sheet is not disturbed by an update.
4. A phone left on the page asks less often after two quiet minutes and not at all in the background.
5. Both test suites pass.

## Release

Kept local on its branch until you say to push. No migration.

## Progress

2026-10-11: Root cause found (the session page was never polled; see the study). Approved with "approved". Built on `fix/session-page-live` from `main`; kept local.

Changes from the plan:

- **The stamp uses each set's `finalized_at`, not the id of its results revision, and counts retired transfer lists.** The page then works the same stamp out from rows it has already read, so it stays within its 14 queries. The first version cost three more queries and failed that test. A test also showed that a reopened session had the same stamp as one never closed; the count of retired lists separates them.
- **After a redraw in place the page's scripts are started again.** Not in the plan; without it a session closed by the host showed the settle-up page to a waiting player with no working sheet.
- **A stamp is redrawn for once.** If the page and the server ever disagreed on a stamp, the page would otherwise redraw every 5 seconds.
- **A redraw that never arrives resumes the asking after 10 seconds.**
- **The poll costs at most 8 queries, not 6** as the plan said: three for the stamp, the rest for the login and membership that every view pays.
- **One existing test changed:** the script order in `web/tests/test_inplace.py` names `nightlive`.

Verification:

- 1018 tests pass on SQLite (15 skipped) and on PostgreSQL 17, 7 of them new (`web/tests/test_night_live.py`).
- `night_live.mjs`: 22 of 22 on a fresh temporary database, with a player's page watching while the host acts through the services. Two checks failed on the way: one expected the wrong thing (a player's own "You're settled" arrives when their transfers are paid, not when the last one is), one was a fault in the check's timer that reported an instant success as a failure; a trace of the page showed the recap had opened.
- `settled.mjs`: 24 of 24. `night.mjs`: 82 of 83; the one failure, "recap reopens at its top", fails the same way on `main` without this change. Not looked into.

Acceptance: 1 to 5 are met in headless Chrome with two signed-in browsers.

Not verified: two real phones; a phone whose screen locks and unlocks (the hidden-tab rule was tested by telling the page it was hidden); the cost on Vercel and Neon of several phones left on the page; a screen reader's announcement of a redraw. A fresh reviewer did not read the branch.

Documentation synced: wiki (features, architecture), browser README, TODO.

2026-10-11 release: the human said "push". `fix/session-page-live` was merged to `main` as `243ce78` and pushed (previous production commit `6090ce1`). 1018 tests passed on SQLite and on PostgreSQL 17 on the merged `main` before the push. No migration. About two and a quarter minutes later the live login page named `nightlive.js`, which is served, and the new state address answered a signed-out request with a redirect to the login, so the route exists. No session page was opened signed in on the live site, so an update arriving there was not seen.

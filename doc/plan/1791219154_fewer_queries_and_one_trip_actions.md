# Fewer queries and one-trip actions: plan

Status: approved 2026-10-06. Stage C built and verified, not released. Date: 2026-10-06, Asia/Manila. Study: [fewer queries and one-trip actions](../study/1791219090_fewer_queries_and_one_trip_actions.md). Base: `main` at `fedaeb0`. A was released as `53de23b` before this work began.

## Outcome

The Session page makes about 13 queries however many sets it has. No page view writes the login session unless it has something to remove. An action sent in place costs one trip to the server. Every figure on every page is unchanged.

## Stage C. Fewer queries

1. **Session page.** One rake total for all of a session's sets in one query (a new function in `ledger/queries.py`). Set timers and "is the clock running" for all sets from one read of the play periods (`games/clock.py`; `seconds_by_set` exists, it gains the running sets). The session's sets, the current results and the payments are each read once and passed on (`web/views.py`, `settlement/queries.py`).
2. **Set page and poll.** One read of play intervals gives the totals and who is running; one read of play periods gives the timer and whether it runs (`games/clock.py`). Active members are read once (`web/views.py`).
3. **No needless session write.** `groups.http.take_form` writes the login session only when it took a draft out.

Files: `ledger/queries.py`, `games/clock.py`, `settlement/queries.py`, `web/views.py`, `groups/http.py`, tests beside each.

## Stage D. One-trip actions

1. **Spike, thrown away.** Prove the three points listed in the study on the vendored Turbo, in a scratch copy. If either of the first two fails, stop and record it; stage D ends.
2. **Server.** A middleware, placed after the session, login and message middleware. For a POST that carries `X-Answer-In-Place: 1` and whose view answered with a redirect to the same-origin path named by the form's page, it renders that page as a GET in the same request and returns it with status 200, `X-In-Place-Location` and `Cache-Control: no-store`. Anything else passes through untouched. If rendering fails, the redirect is returned.
3. **Browser.** `turbo-setup.js` adds the header to forms it sends in place, and turns such an answer into a visit with the HTML it carries. A redirect answer is handled as today, so an older page talking to a newer server, or the reverse, keeps working.
4. **Switch.** A setting, `ANSWER_IN_PLACE` (default on, off by a Vercel variable without a release), in the manner of `NUMPAD` and `SERVICE_WORKER`.

Files: a new `config/inplace.py`, `config/settings.py`, `config/pwa.py` (the flag), `templates/base.html` (the flag), `static/js/turbo-setup.js`, tests in `web/tests/test_inplace.py`, `web/tests/browser/inplace.mjs`.

## Scope and exclusions

No model, migration, service or form changes. No caching and no stored totals. Views keep answering with redirects. The no-JavaScript path is untouched. Polling, the service worker and the motion system are untouched. Push and deployment require an instruction per stage.

## Acceptance criteria

- AC1. Query counts, asserted in tests: Session page with one set at most 14 and the same count with three sets; set page at most 12; Your groups makes no write on a plain view.
- AC2. Each changed page renders the same HTML before and after stage C for the fixtures of `seed.py`, `seed_end_set.py` and `seed_night.py` (compared byte for byte after removing CSRF and request tokens), as host and as player.
- AC3. A refused form still returns its typed values once (`take_form`), and the prefetch tests still pass.
- AC4. With the header, every in-place form (buy-in, cash-out, counts, set transitions, player actions, reversals, overrides, finalize, mark paid and undo) is answered in one request with the updated page, and the write happened once. Without the header the answer is the redirect it is today.
- AC5. In the browser an in-place action makes one request where it made two; scroll, typed values in other fields, open details, the sheet, toasts, the change marks and the poll's version behave as before. `inplace.mjs`, `flow.mjs`, `count_flow.mjs`, `numpad.mjs` and `night.mjs` pass.
- AC6. A refusal from the service (a rule error) shows where it does today. A failure while rendering the page falls back to the redirect. A double tap writes once.
- AC7. `ANSWER_IN_PLACE=False` restores two trips with no other change.
- AC8. All Django tests pass on SQLite and PostgreSQL. On the phone the readout shows the Session page's query count down and an action's wait near a link's.

## Ordered implementation board

- [x] **C, tests first.** Query-count tests and the before/after HTML comparison, failing on the counts. Then the three changes, one commit each: `perf(web): read a session's sets once`, `perf(games): one read per clock`, `fix(groups): write the login session only when a draft is taken`.
- [x] **C rendezvous.** Both suites, the browser checks that read these pages (`night.mjs`, `home.mjs`, `flow.mjs`). Record counts before and after. Sync the wiki. Stop for the instruction to release, then read the phone's numbers.
- [ ] **D spike.** Report what it showed. Stop if it fails.
- [ ] **D, tests first.** Middleware tests (one request, one write, messages shown, fallback, header absent), then the browser check for one request per action. Then the middleware, the header and the visit, and the switch. Commit `perf(web): answer an in-place action with its page`.
- [ ] **D rendezvous.** Both suites and the five browser scripts. Sync DESIGN.md (nothing visual changes; one line), the wiki (architecture, deployment for the switch) and TODO. Stop for the instruction to release.

## Stage C: verification record (2026-10-06)

Branch `perf/fewer-queries`: `16d07eb` (login session write), `010b829` (sets and clocks read once).

| Page | Queries before | After |
|---|---|---|
| Session, one set, closed | 23 | 14 |
| Session, one set, open | 18 | 12 |
| Session, three sets, open | 32 | 12 |
| Set in play, and a poll that redraws | 15 | 13 |
| Your groups | 14 reads and a write of the login session | 14 reads |
| Group settings | up to 12 | up to 9 |

- Django suite: 691 pass on SQLite (10 PostgreSQL-only skipped) and on PostgreSQL 17. Five new query-count tests failed first. New direct tests: `clock.timers` and `clock.player_clocks` against the single-set functions, `queries.rake_total` against the summaries, including a reversed buy-in.
- AC2: 240 pages (every session, set, poll and log of the `seed.py`, `seed_end_set.py`, `seed_night.py` and `seed_home.py` fixtures, as host and as player) rendered before and after. With CSRF tokens, request ids and the text of running timers masked, all 240 are identical.
- Browser: `night.mjs` 53, `home.mjs` 60, `flow.mjs` 52, `count_flow.mjs` 89, `inplace.mjs` 38, all pass.

Rulings:

1. **The set page stops at 13, not the 12 of AC1.** The thirteenth is the list of members a host can add, which the host menu shows. If wrong: nothing; the test asserts 13.
2. **Two commits, not three.** The session page and the clocks change the same view, so they are one commit.
3. **Two recap tests patched `clock.set_seconds`,** which the recap no longer calls. They now patch the one read that replaced it and assert the same outcomes.
4. **A new session with no money still makes up to 8 small "does any record exist" queries** for the host's archive and delete panel (`night_has_records`). Left as it is: it stops at the first hit, so a session with money pays one.

## For the human to do

- After C is live: open a session with two or more sets with `?perf=1` and send the line; the count in brackets should be about 13.
- After D is live: record a rebuy and mark a transfer paid with `?perf=1`; "wait" should be near 200 where it was near 400. Play one whole set as you did on 2026-10-06 and say if anything behaves differently.

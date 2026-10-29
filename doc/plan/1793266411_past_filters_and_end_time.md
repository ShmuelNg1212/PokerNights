# Plan: filters on past sessions, and a correction of a set's end time

Study: [1793266411_past_filters_and_end_time.md](../study/1793266411_past_filters_and_end_time.md).

Two independent features. Each is one Conventional Commit on one branch, `feat/past-filters-and-end-time`, from `main`.

## OPEN QUESTIONS

Approved with the defaults on 2026-10-29.

1. **Which filters?** **"All", "Not settled" and "I played"**, as chips above the list. Also possible: "Table" (only shown when the group has two or more tables), or "Player" (pick any member; one more query).
2. **Who may correct the end time?** **Hosts only**, the same as "End play".
3. **When?** **Only while the set is counting up** (after "End play", before finalize). For a finalized set, the host reopens it first. The alternative is to also allow it on a finalized set, which rewrites its results as a new revision in one step.
4. **Earlier only?** **Yes.** The new end must be after the last start (or resume) and before the recorded end. A later end time is out of scope.
5. **Reason required?** **Optional.** The audit log keeps the old and the new time either way.

## Task 1: filters on past sessions — `tests: alongside`

- [x] `past_years(me, nights, only=None)` selects rows before the grouping: `"unsettled"` keeps `settle.status != "settled"`; `"mine"` keeps `my_net is not None`. Any other value means all.
- [x] The group view reads `?past=` on the Sessions tab and passes it on. An unknown value is ignored.
- [x] The template shows a chip row above the past list: All · Not settled (N) · I played. Each chip is a link with `aria-current` on the active one. 48 px targets. DESIGN.md tokens.
- [x] With a filter active, every year that has a row is open.
- [x] Empty result: one line, "No sessions match.", and a link back to All.
- [x] Tests: each filter selects the right rows; an unknown value shows all; the query count does not change with a filter.
- [x] Design pass: screenshot review of the chip row at 320, 390 and 1280 px. The `/impeccable` skill was not run.

**Done when:** on the live group page, "Not settled" shows only the sessions with open transfers, and the count on the chip matches the heading.

## Task 2: correct a set's end time — `tests: first`

- [x] Service `games.services.correct_end_time(session_id, actor, ended_at, reason="", *, request_id)`:
  - host only; set must be in `RECONCILIATION`;
  - `last_period.started_at < ended_at < last_period.ended_at`, else `RuleError` with a plain message;
  - in `transaction.atomic()`, with the session locked by `select_for_update()`;
  - sets the last `PlayPeriod.ended_at`, clamps each `PlayInterval.ended_at > ended_at` of the set to `ended_at` (and `started_at` to `ended_at` where it started later), sets `GameSession.ended_at`;
  - replaying the same `request_id` changes nothing;
  - `audit.record("session.end_time", …)` with the old and new times in the summary; `touch(session)`.
- [x] Tests first: shortens the set timer and each player's time; an earlier cash-out is unchanged; a late joiner becomes zero; a resumed set changes only its last period; refused when running, finalized, before the last start, at or after the old end, or by a non-host; replay is a no-op; audit row written; finalize after the correction writes the corrected `play_seconds`.
- [x] View and form on the counting page: a small "Wrong end time?" link for hosts opens a form with a time input (date shown, Asia/Manila; date input only when the set crosses midnight). On success, return to the counting page with a toast "End time set to 10:42 PM".
- [x] Design pass: the link is secondary and does not compete with the count-up actions.

**Done when:** on the live site, a host ends a set, sets the end 30 minutes earlier, finalizes, and the player page "per hour" uses the shorter time.

## Completion

- [x] SQLite and PostgreSQL suites pass.
- [x] Rendezvous: `code-review`, a security check by hand (host check, input parsing; the `security-review` skill was not run), a browser probe of each task's first user step.
- [x] Sync docs: `features.md`, the roadmap rows, TODO.md phone checks.

## Rendezvous record (2026-10-29)

Frozen after this section.

- SQLite suite: 1503 tests pass. PostgreSQL suite: passes (run on the final code).
- Tests first for Task 2: 18 tests in `games/tests/test_end_time.py`, one in `ledger/tests/test_play_seconds.py` (finalize stores the corrected time).
- Task 1 tests: 6 in `web/tests/test_sessions_tab.py`, including an equal query count with and without a filter.
- Browser probe `web/tests/browser/past_filters.mjs`: 39/39 on a fresh database. First run found the `datetime-local` field at 21 px; fixed with the input styles; second run passed.
- `code-review` (medium): 10 findings. Fixed: typed values lost on a live redraw (`data-keep`); an unchanged form trimmed the seconds past the recorded minute; `strptime` refused input with seconds; the lower-bound message named a refused minute; timer trim moved to `clock.trim`; `clock_time` moved to `clock.py`.
- Not fixed, by decision: money rows after the new end are not checked (the host knows when play ended; money does not depend on the timer; recorded as a footgun). A request id made on every poll (cheap). The heading count next to the "Not settled" chip (a contrast check covers it). The filter loop runs three times over the rows (small).
- Security, checked by hand: the view resolves the set through `session_for` (membership, 404 on a miss); the service calls `require_host` (a player gets 403, tested); the form posts with CSRF; input is parsed with `fromisoformat` and refused when it has a time zone.
- Design: chips reuse `.pills` and `--tap`; the end-time control sits under "More host controls" and does not compete with the count-up actions. Captures in `/private/tmp/pn-past-filters-review/`.

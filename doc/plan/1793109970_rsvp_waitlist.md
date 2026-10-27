# Plan: RSVP with seat limits and a waitlist

Study: [1793109872_rsvp_waitlist.md](../study/1793109872_rsvp_waitlist.md), with its design addendum. Mode: mixed. Branch: `feat/rsvp-waitlist`, from `main` (nothing is unreleased).

## Goal

A host announces a session. Players answer In or Out from their phones. The session confirms players up to its seat limit, and puts the rest on a waitlist in order. When a seat opens, the first in line gets it and a notice. When the host adds players to set 1, the confirmed players are already ticked.

## OPEN QUESTIONS

All five answered on 2026-10-27: each REC is accepted.

1. **Notices.** `Notice` is unique per user and set. REC: add a nullable `night_id`, two kinds `announced` and `seated`, and make the unique rule apply to set notices only (conditional constraint). An RSVP notice is unique per user, session and kind. Alternative: push only, no notice row.
2. **When does RSVP close?** REC: when set 1 goes in play. While set 1 is Draft or Open, answers still count. After that, the host adds players to the set as today.
3. **Removed member.** REC: removing a member from the group turns their RSVP to Out, and the waitlist moves up.
4. **Your groups home.** REC: a group card names the action "Are you in? Fri 8:00 PM" when the viewer has not answered an announced session. Alternative: Sessions tab only.
5. **Spec change.** This is new product scope. After approval, `spec.md` moves RSVP from "Later" into section 1, and an ADR records the rules. REC wording: "A host announces a session with an optional start time and a seat limit (the table's seats by default). Players answer In or Out. Players past the limit wait in line; when a seat opens, the first in line gets it and is told. A host can answer for any player, seat a waiting player over the limit, or mark a player out."

## Tasks

### Technical

- [x] **T1. Model.** `GameNight` gets `announced_at`, `start_time`, `seat_limit` (all nullable). New `games.Rsvp` (night, member, status, queued_at, answered_by, updated_at, request_id) as in the study. Unique (night, member); status check; `request_id` unique; index (night, status, queued_at).
  - Done when: the migration applies on SQLite and PostgreSQL, and tests show the database refuses a second row per member and an unknown status.
- [x] **T2. Services.** In `games/services.py` (or a new `games/rsvp.py` called from it): `announce`, `answer`, `set_seat_limit`, `seat_from_waitlist`. Each locks the night with `lock_night`, calls `audit.record()` with set 1's id, and calls `_bump_sets`.
  - Acceptance: host-only checks in the service; a player answers only for themselves; refused when not announced, closed, archived or past the window (Q2); In fills a seat or joins the line; Out from a seat promotes the first in line; Out then In joins the end of the line; a repeated `request_id` returns the same row; the limit stays 2 to 12 and not under the confirmed count; raising it promotes in order; **Seat now** sets the limit to the confirmed count.
  - Done when: tests cover each rule in `games/tests/test_rsvp.py`.
- [x] **T3. Concurrency.** Two players take the last seat at once.
  - Done when: a PostgreSQL test in `web/tests/test_concurrency.py` shows one confirmed and one waitlisted.
- [x] **T4. Notices.** Per Q1: model change, migration, `notify.tell` takes `night_id` and a kind. Announce tells every active member with a login, except the host who announced. Promotion tells the promoted player. `mark_seen` clears RSVP notices when the player opens the session page.
  - Done when: tests show one notice per user and kind, push after commit, and set notices unchanged.
- [x] **T5. Removal.** Per Q3: `guard_member_removal` or the removal service turns an RSVP Out and promotes.
  - Done when: a test removes a confirmed member and the first in line is confirmed.
- [x] **T6. Queries.** A read function returns, per announced session: confirmed, waitlisted (with place), out, not answered, the counts, and the viewer's own state. Constant query count for the Sessions tab.
  - Done when: `web/tests/test_query_counts.py` covers the tab with 3 announced sessions and 30 members.
- [x] **T7. Views and URLs.** `night_announce`, `night_rsvp` (self), `night_rsvp_for` (host, member id), `night_seats`, `night_seat_now`. POST only; membership resolution; 404 on a miss; refusals as a message on the page.
  - Done when: view tests cover host, player, player acting for another (refused), other group (404), closed session.
- [x] **T8. Drafts made visible.** Players see an announced draft on the Sessions tab and its session page only. The set page and money pages stay hidden while set 1 is Draft.
  - Done when: tests show a player gets the session page of an announced draft, and a 404 on its set page and on an unannounced draft.
- [x] **T9. Set 1 pre-tick.** `add_players` for set 1 of an announced session ticks confirmed members not yet in the set, lists the waitlist unticked with places, then the roster.
  - Done when: a test reads the form's initial values; a later set has no pre-tick.

### Design (brief: study addendum)

- [x] **D1. Announce card** on the draft session page, host only: start time, seats on the numpad, **Announce to the group**, hint line.
  - Done when: it works without JavaScript, and a refused value keeps what the host typed.
- [x] **D2. "Coming up" cards** on the Sessions tab, with the four viewer states and their actions. Title is the link. Update in place after the server accepts.
  - Done when: each state renders with words; 48 px targets; no sideways scroll at 320 px with a 60-character table name.
- [x] **D3. "Who's coming"** on the session page: Coming, Waitlist (numbered), Can't make it and Not answered disclosures, host row actions, **Seats** with its refusal message, "Moved up" badge.
- [x] **D4. Add-players groups**: Coming (ticked), Waitlist, roster.
- [x] **D5. Group card action** on Your groups (only if Q4 is yes).
- [x] **D6. Browser check** `web/tests/browser/rsvp.mjs` at 320, 390 and 1280 px, as host and player, and without JavaScript: targets, contrast of the Brass waitlist line, overflow, in-place update.

### Rendezvous

- [x] **R1.** SQLite and PostgreSQL suites pass. Record the counts here.
- [x] **R2.** `code-review`, `verification-before-completion`, `security-review` (user data and permissions change).
- [x] **R3.** `/impeccable critique` and `audit`, then `polish`; `break-ui` on the Coming up card and Who's coming.

### Sync docs

- [ ] **S1.** `spec.md` (per Q5), an ADR, `GLOSSARY.md` terms from the study, `features.md`, `architecture.md` (RSVP belongs to the session), DESIGN.md addendum, TODO.md phone checks.

## Deviations from the plan

- **T2.** The writes are in `games/services.py` (`announce_night`, `answer_rsvp`, `set_seat_limit`, `seat_from_waitlist`, `lock_rsvp_nights`, `rsvp_member_removed`). `games/rsvp.py` only reads. AGENTS.md rule 2 asked for this; the code review found the first version outside `services.py`.
- **T2.** `announce_night`, `set_seat_limit` and `seat_from_waitlist` carry no `request_id`. Each is safe to repeat by its state: a second announce, the same limit, or Seat now on a seated player returns what is there.
- **T2.** Set 1's `seat_count` grows to the seat limit. It never shrinks. Without this, add-players refused the confirmed players after **Seat now**.
- **T5.** Removal locks the sessions first (`groups.services.REMOVE_LOCKS`), then the member. Adding players takes the locks in that order too.
- **T6.** The query-count test is in `web/tests/test_rsvp_pages.py`, not `test_query_counts.py`.
- **T7.** One view, `night_rsvp`, takes an optional `member`. There is no separate `night_rsvp_for`.
- **D2.** "Coming up" shows while answers count: set 1 Draft or Open. While set 1 is Open, the session is also on "Now playing", to reach the set.
- **D3.** The "Moved up" badge is not built. The moved-up player gets a notice; the list shows them under Coming.
- **D4.** Add-players keeps one list. The confirmed come first with "Said they're coming", then the waitlist with its place, then the roster. It ticks no more than the free seats.
- **Model.** `Rsvp` rows CASCADE with their session and roster entry. With PROTECT, deleting a session and claiming a roster entry failed (code review).

## Rendezvous record (2026-10-27)

- **R1.** SQLite: 1405 tests pass (15 skipped: PostgreSQL only). PostgreSQL: 1405 tests pass. The add-and-remove race test fails with the lock fix switched off, and passes with it.
- **R2.** `code-review` (high): 10 findings, all fixed in `0603956`. `security-review`: no finding. A malformed member id is a 404 (`27283e6`).
- **R3.** `/impeccable critique` ran in this session, not in two subagents (AGENTS.md allows subagents only in execute). The detector found advisories only: the browser's default black, from scanning partials without the stylesheet. The review fixed a long name below its chip (`e5b9921`), and the start time, the seat count and the empty Now playing text said twice (`9a5f3d2`). Browser check `rsvp.mjs`: 28 of 28 at 320, 390 and 1280 px, as host and player, and without JavaScript. The Brass waitlist line measures 10:1.
- **Open, not in this feature.** On add-players, a long name beside two badges wraps to five lines at 390 px. The row layout is older than RSVP.

## Completion criterion

A host announces a session; two phones answer; the third answer past the limit waits in line; one confirmed player drops out and the waiting player is told they are in; set 1's add-players form starts with the confirmed players ticked. All tests pass on SQLite and PostgreSQL.

## Release safety

The migrations only add nullable fields, a new table and a relaxed notice constraint. With no session announced, every screen behaves as today.

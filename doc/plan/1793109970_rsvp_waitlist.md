# Plan: RSVP with seat limits and a waitlist

Study: [1793109872_rsvp_waitlist.md](../study/1793109872_rsvp_waitlist.md), with its design addendum. Mode: mixed. Branch: `feat/rsvp-waitlist`, from `main` (nothing is unreleased).

## Goal

A host announces a session. Players answer In or Out from their phones. The session confirms players up to its seat limit, and puts the rest on a waitlist in order. When a seat opens, the first in line gets it and a notice. When the host adds players to set 1, the confirmed players are already ticked.

## OPEN QUESTIONS

1. **Notices.** `Notice` is unique per user and set. REC: add a nullable `night_id`, two kinds `announced` and `seated`, and make the unique rule apply to set notices only (conditional constraint). An RSVP notice is unique per user, session and kind. Alternative: push only, no notice row.
2. **When does RSVP close?** REC: when set 1 goes in play. While set 1 is Draft or Open, answers still count. After that, the host adds players to the set as today.
3. **Removed member.** REC: removing a member from the group turns their RSVP to Out, and the waitlist moves up.
4. **Your groups home.** REC: a group card names the action "Are you in? Fri 8:00 PM" when the viewer has not answered an announced session. Alternative: Sessions tab only.
5. **Spec change.** This is new product scope. After approval, `spec.md` moves RSVP from "Later" into section 1, and an ADR records the rules. REC wording: "A host announces a session with an optional start time and a seat limit (the table's seats by default). Players answer In or Out. Players past the limit wait in line; when a seat opens, the first in line gets it and is told. A host can answer for any player, seat a waiting player over the limit, or mark a player out."

## Tasks

### Technical

- [ ] **T1. Model.** `GameNight` gets `announced_at`, `start_time`, `seat_limit` (all nullable). New `games.Rsvp` (night, member, status, queued_at, answered_by, updated_at, request_id) as in the study. Unique (night, member); status check; `request_id` unique; index (night, status, queued_at).
  - Done when: the migration applies on SQLite and PostgreSQL, and tests show the database refuses a second row per member and an unknown status.
- [ ] **T2. Services.** In `games/services.py` (or a new `games/rsvp.py` called from it): `announce`, `answer`, `set_seat_limit`, `seat_from_waitlist`. Each locks the night with `lock_night`, calls `audit.record()` with set 1's id, and calls `_bump_sets`.
  - Acceptance: host-only checks in the service; a player answers only for themselves; refused when not announced, closed, archived or past the window (Q2); In fills a seat or joins the line; Out from a seat promotes the first in line; Out then In joins the end of the line; a repeated `request_id` returns the same row; the limit stays 2 to 12 and not under the confirmed count; raising it promotes in order; **Seat now** sets the limit to the confirmed count.
  - Done when: tests cover each rule in `games/tests/test_rsvp.py`.
- [ ] **T3. Concurrency.** Two players take the last seat at once.
  - Done when: a PostgreSQL test in `web/tests/test_concurrency.py` shows one confirmed and one waitlisted.
- [ ] **T4. Notices.** Per Q1: model change, migration, `notify.tell` takes `night_id` and a kind. Announce tells every active member with a login, except the host who announced. Promotion tells the promoted player. `mark_seen` clears RSVP notices when the player opens the session page.
  - Done when: tests show one notice per user and kind, push after commit, and set notices unchanged.
- [ ] **T5. Removal.** Per Q3: `guard_member_removal` or the removal service turns an RSVP Out and promotes.
  - Done when: a test removes a confirmed member and the first in line is confirmed.
- [ ] **T6. Queries.** A read function returns, per announced session: confirmed, waitlisted (with place), out, not answered, the counts, and the viewer's own state. Constant query count for the Sessions tab.
  - Done when: `web/tests/test_query_counts.py` covers the tab with 3 announced sessions and 30 members.
- [ ] **T7. Views and URLs.** `night_announce`, `night_rsvp` (self), `night_rsvp_for` (host, member id), `night_seats`, `night_seat_now`. POST only; membership resolution; 404 on a miss; refusals as a message on the page.
  - Done when: view tests cover host, player, player acting for another (refused), other group (404), closed session.
- [ ] **T8. Drafts made visible.** Players see an announced draft on the Sessions tab and its session page only. The set page and money pages stay hidden while set 1 is Draft.
  - Done when: tests show a player gets the session page of an announced draft, and a 404 on its set page and on an unannounced draft.
- [ ] **T9. Set 1 pre-tick.** `add_players` for set 1 of an announced session ticks confirmed members not yet in the set, lists the waitlist unticked with places, then the roster.
  - Done when: a test reads the form's initial values; a later set has no pre-tick.

### Design (brief: study addendum)

- [ ] **D1. Announce card** on the draft session page, host only: start time, seats on the numpad, **Announce to the group**, hint line.
  - Done when: it works without JavaScript, and a refused value keeps what the host typed.
- [ ] **D2. "Coming up" cards** on the Sessions tab, with the four viewer states and their actions. Title is the link. Update in place after the server accepts.
  - Done when: each state renders with words; 48 px targets; no sideways scroll at 320 px with a 60-character table name.
- [ ] **D3. "Who's coming"** on the session page: Coming, Waitlist (numbered), Can't make it and Not answered disclosures, host row actions, **Seats** with its refusal message, "Moved up" badge.
- [ ] **D4. Add-players groups**: Coming (ticked), Waitlist, roster.
- [ ] **D5. Group card action** on Your groups (only if Q4 is yes).
- [ ] **D6. Browser check** `web/tests/browser/rsvp.mjs` at 320, 390 and 1280 px, as host and player, and without JavaScript: targets, contrast of the Brass waitlist line, overflow, in-place update.

### Rendezvous

- [ ] **R1.** SQLite and PostgreSQL suites pass. Record the counts here.
- [ ] **R2.** `code-review`, `verification-before-completion`, `security-review` (user data and permissions change).
- [ ] **R3.** `/impeccable critique` and `audit`, then `polish`; `break-ui` on the Coming up card and Who's coming.

### Sync docs

- [ ] **S1.** `spec.md` (per Q5), an ADR, `GLOSSARY.md` terms from the study, `features.md`, `architecture.md` (RSVP belongs to the session), DESIGN.md addendum, TODO.md phone checks.

## Completion criterion

A host announces a session; two phones answer; the third answer past the limit waits in line; one confirmed player drops out and the waiting player is told they are in; set 1's add-players form starts with the confirmed players ticked. All tests pass on SQLite and PostgreSQL.

## Release safety

The migrations only add nullable fields, a new table and a relaxed notice constraint. With no session announced, every screen behaves as today.

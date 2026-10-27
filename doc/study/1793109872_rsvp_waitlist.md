# Study: RSVP with seat limits and a waitlist

Date: 2026-10-27. Mode: mixed. Spec item: "RSVP with seat limits and a waitlist (typically 9 to 10 seats)" in [spec.md](../wiki/spec.md), section "Later".

## Problem

The group agrees each game in a chat. The host counts replies by hand. When the table is full, late replies wait, and the host remembers the order. When someone drops out, the host tells the next person. The app knows the roster, the tables and their seats, but it has no record of who is coming.

## What exists

- A host creates a session (`GameNight`) with set 1 as a Draft (`GameSession.state == "setup"`). `games.services.create_session`.
- A session has `game_date` and no start time.
- Players do not see a Draft. The Sessions tab shows drafts last, for hosts only.
- `Table.seat_count` is 2 to 12. A set copies it to `GameSession.seat_count`. `add_participant` refuses a join past it, under the session lock.
- `notify.Notice` is one row per user and **set** (`notice_once_per_set` on `user, session_id`). `notify.tell` skips a user told before about the same set. Push goes out after the commit.
- `audit.record` takes a `session_id` (a set id). Night-level writes, such as `archive_night`, pass the last set's id.
- Night-level writes lock the night with `lock_night` and bump all its sets' `version` with `_bump_sets`.

## Decisions from the human (2026-10-27)

1. **Announce.** A host creates the session as today, then taps **Announce**. Players then see it on the Sessions tab, get a notice, and answer In or Out. A Draft that is not announced stays hidden from players.
2. **Promotion.** When a confirmed player drops out, the first player on the waitlist gets the seat at once. A notice tells them they are in. Nobody has to act.
3. **Seat limit.** It starts at the table's seat count. A host can raise or lower it for that session.
4. **Lower limit.** The limit cannot go below the confirmed count. The host first moves someone out or to the waitlist.
5. **Set 1.** When the host adds players to set 1, the list starts with every confirmed player ticked. The host unticks no-shows and adds walk-ins. Waitlisted players are not ticked.
6. **Start time.** Optional, in Asia/Manila. The invite shows it. No reminders.
7. **Host powers.** A host can answer In or Out for any roster player, with or without a login. A host can seat a waitlisted player over the limit; this raises the limit by one. A host can move a confirmed player to Out; the waitlist then moves up.

## Domain model

New words, for `GLOSSARY.md` (it does not exist yet; `domain-modeling` creates it):

- **Announce**: a host makes a session visible to players for RSVP.
- **RSVP**: one member's answer for one session: In or Out.
- **Seat limit**: how many players a session confirms. Not the same as a set's seat count.
- **Confirmed**: an RSVP of In that has a seat.
- **Waitlisted**: an RSVP of In that has no seat yet. It has a place in line.

RSVP belongs to a session (`GameNight`), not to a set. Rule 10 of AGENTS.md puts money, counts and timers on a set; an RSVP is none of these. It is a fact about the gathering.

Proposed model, in the `games` app (it owns `GameNight`; dependencies stay `groups → games`):

```
GameNight
  + announced_at      DateTimeField, null      # null = not announced
  + start_time        TimeField, null          # Asia/Manila wall time
  + seat_limit        PositiveSmallIntegerField, null   # set at announce from table.seat_count

Rsvp
  night        FK GameNight (PROTECT)
  member       FK Member (PROTECT)
  status       "confirmed" | "waitlisted" | "out"
  queued_at    DateTimeField               # line order; reset on each new In
  answered_by  FK User                     # the member, or the host who answered for them
  updated_at   DateTimeField
  request_id   UUID, unique                # rule 3; the last write's id
  unique (night, member)
  check status in the three values
```

Each answer changes one row in place. The audit log keeps the history. An RSVP is not money, so rule 4 (append-only) does not apply.

The order of the waitlist is `queued_at`, then `id`. A player who goes Out and then In again joins the end of the line.

### Rules (all in one service, under `lock_night`)

- `answer(night, actor, member, going, request_id)`:
  - Refuses if the session is not announced, is closed or archived, or if set 1 has left Draft and Open. (After play starts, the host adds players to the set as today.)
  - A player answers only for themselves. A host answers for any active member.
  - In: confirmed if confirmed count < seat limit, else waitlisted. A repeated In changes nothing.
  - Out from confirmed: the first waitlisted becomes confirmed and is told.
- `set_seat_limit(night, actor, n)`: host only; 2 ≤ n ≤ 12, n ≥ confirmed count. Raising it confirms waitlisted players in order, and tells each one.
- `seat_from_waitlist(night, actor, member)`: host only; confirms that member and sets the limit to confirmed count.
- `announce(night, actor, start_time)`: host only; once. Sets `seat_limit` from the table and tells every active member with a login.

Each write calls `audit.record` with the night's set-1 id and bumps the night's sets (`_bump_sets`). That satisfies rule 6 without a new version field.

### Set 1 hand-off

The host's add-players form for set 1 pre-ticks confirmed members not yet in the set. It is a view default; nothing is written until the host sends the form. Later sets do not pre-tick.

### Notices

`Notice` is unique per user and set. RSVP needs more than one notice per user and session (announced, then moved up). Options:

- **A. Add `night_id` and a kind per RSVP event, with a conditional unique constraint.** The unseen-notice logic stays per set for set notices. **Recommended.**
- B. Push only, no Notice row. Players without push would see nothing.

Notice kinds to add: `announced` ("Ace table · Fri 8:00 PM. Are you in?"), `seated` ("You're in. A seat opened at …"). The waitlisted player gets no notice when they join the line; the screen tells them their place.

## Screens (for the design shape pass)

- **Host, Draft session page**: an Announce card: optional start time, seat limit (default the table's), button **Announce**.
- **Sessions tab, player**: an announced session shows its date, time, table, "6 of 9 seats", and the viewer's state with one action: **I'm in** / **Can't make it**. A waitlisted viewer sees "Waitlist · 2nd in line".
- **Session page, everyone**: who is coming (confirmed), the waitlist in order, and who is out. Host controls on each row.
- **Set 1 add-players**: confirmed players ticked.

## Risks

- **Notices schema change.** A constraint change on `notify_notice`. It must migrate on PostgreSQL in the Vercel build. Test on the local PostgreSQL suite.
- **Concurrency.** Two players taking the last seat. The night row lock serializes them; a test must prove it on PostgreSQL.
- **Drafts become visible.** Every query that hides drafts from players must let announced drafts through, but only on the Sessions tab and the session page, never set money pages.
- **Removal of a member.** `guard_member_removal` must decide what to do with their RSVPs. Proposal: a removed member's RSVP goes Out, with promotion.

## Not in scope

Reminders, recurring games, offers with a time limit, a deadline to answer, guests outside the roster, "Maybe".

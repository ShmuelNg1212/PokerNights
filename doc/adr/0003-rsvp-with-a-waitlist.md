# 0003: RSVP with a seat limit and a waitlist

Date: 2026-10-27. Status: accepted. Plan: [RSVP with a waitlist](../plan/1793109970_rsvp_waitlist.md).

## Context

The group agreed each game in a chat. The host counted the replies, remembered who asked late, and told the next person when a seat opened. The app knew the roster and the tables, but not who was coming.

## Decision

- A host **announces** a draft session. Players then see it and answer In or Out. A draft that is not announced stays hidden from players.
- The session has a **seat limit**. It starts at the table's seats; a host changes it from 2 to 12, never below the confirmed count.
- An In takes a seat while one is free. Else it joins the **waitlist**, in the order of the answers. An Out and a new In go to the end of the line.
- When a confirmed player goes Out, or a host marks them out, or they leave the group, the first in line takes the seat at once and gets a notice.
- A host answers for any roster player, with or without a login. **Seat now** seats a waiting player and raises the limit by one.
- Answers count while set 1 is Draft or Open. After play starts, the host adds players to the set as before.
- Set 1's Add players starts with the confirmed players ticked, no more than its free seats. Set 1's seats grow to the seat limit.

## Reasons

- An RSVP belongs to the gathering, not to a round of play: it is on `GameNight`, beside settle-up and the unit.
- Moving up at once needs no scheduled job, and the app has none. An offer with a time limit would need one.
- The host stays in charge at the table: the ticks are a starting point, not seats.

## Consequences

- An RSVP is not a money record. Each answer changes its row; the audit log keeps the history. The rows go with their session or roster entry when either is deleted.
- `Notice` now also holds session notices (`night_id`, kinds `announced` and `seated`). The one-per-set rule applies to set notices only.
- Removing a member locks their sessions before the member row, in the order that adding players uses.
- Reminders, a deadline, "Maybe" and guests outside the roster are not built.

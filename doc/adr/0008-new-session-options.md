# 0008: New session can apply a chip preset and announce

Date: 2026-10-30. Status: accepted. Plan: [session setup menu](../plan/1793347607_session_setup_menu.md). Extends [ADR 0003](0003-rsvp-with-a-waitlist.md) and [ADR 0005](0005-group-chip-presets.md).

## Context

After a host creates a session, the next steps are to announce it and to set the chip values. The human asked for the app to go to those steps after creation, and for the option to do them on the New session page.

## Decision

- After New session, the app goes to the session page. The session page holds the Announce and Chip values cards.
- New session offers two options for each session: a chip preset and "Announce to the group". Both are off by default. There is no group default.
- A new session starts without chip values unless the host selects a preset. The session keeps a copy, as ADR 0005 says.
- The list shows the presets of the chosen unit. The server refuses a preset of the other unit, an archived preset and a preset of another group.
- Announcing from New session uses the table's seats and an optional start time. The host can change the seats on the "Who's coming" card.
- Creating the session, copying the values and announcing run in one transaction. A refusal creates nothing and tells nobody.
- A New session request carries a request ID that is unique in the group. A repeated request changes nothing and tells nobody again.
- A stakes preset does not select a chip preset.

## Consequences

A host who plays at once selects "Open set 1" after creation: one more tap than before. Before set 1 opens, "Announce to the group" is the primary action on the session page until the session is announced. `GameNight.create_request_id` is empty on older sessions.

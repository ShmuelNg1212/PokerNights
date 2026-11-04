# 0012: A host draws seats from a draft

Date: 2026-11-04. Status: accepted. Plan: [draw seats from a draft](../plan/1793514402_draw_from_draft.md). Revises [ADR 0009](0009-start-a-game-fast.md) on "A seat draw still needs an open set" and on the extra choice in its Consequences.

## Context

Since ADR 0009, a host adds players to a draft and taps Start the set. The set goes from draft to running in one step. A seat draw needed an open set, and a running set cannot go back to open. So on a first set, the draw was only available after More host controls, then "Let players join first". That button is closed by default, and its label is about something else. The human approved this change on 2026-11-01.

## Decision

- A host can draw seats from a draft that has 2 or more seated players. The optional Seat draw step shows on the draft. Start the set stays the one main button.
- The Draw action opens the set, then draws, in one transaction. This follows the way that Start the set opens and starts. The audit log has `session.open` and `seats.drawn`. The set's version rises by two.
- Seated players with a login hear that the set is ready to join, as when a set opens. The host who drew does not.
- The step on a draft says "Players see the set when you draw." The host knows this before the tap.
- A refused draw changes nothing: the set stays a draft and nobody is told. A repeated request returns the first draw. It does not open the set or tell anyone again.
- A draft holds no draw. An open set can hold a draw and go back to draft after its players are removed. That draw is out of date: Back to draft makes it not current, and the log keeps it. The page also shows no draw on a draft, for drafts that went back before this change.
- "Let players join first" stays. It is the way to let players join by themselves.

## Consequences

The set's states and `TRANSITIONS` are unchanged. `games.services.draw_seats` calls `transition(..., "open")` when it meets a draft, after its replay, switch and player-count checks. A draw on a running set is still refused, with "Seats are drawn before the set starts." Back to draft is refused once a player is seated, so a host cannot undo a draft draw with that button. Draw again and cancel stay available.

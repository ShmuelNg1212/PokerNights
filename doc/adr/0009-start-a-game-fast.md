# 0009: A host reaches a running game in fewer steps

Date: 2026-10-31. Status: accepted. Plan: [UI revamp](../plan/1793431937_ui_revamp.md), slice B. Revises [ADR 0008](0008-new-session-options.md) on where New session leads and on the session page's primary action.

## Context

A study walked a new host and a repeat game through the app. A new group went to Group settings to make a table, then back to New session. A host whose players have no login still had to open the set and then start it. The human chose to remove these steps.

## Decision

- **First table.** A group with no table names it on New session, with its seats (9 by default). One request makes the table and the session in one transaction. A refused session leaves no table. A repeated request changes nothing. If a table of that name appeared meanwhile, the session uses it.
- **Start from Draft.** Start the set works from a draft set. In one transaction, the set opens and starts. The audit log has both steps, seated players are told as when a set opens, and opening buy-ins are recorded as from an open set. A repeated request changes nothing.
- **Open stays.** "Let players join first" opens a draft without starting it, for a game where players join by themselves or a seat draw comes first. A seat draw still needs an open set.
- **Where New session leads.** To the set, unless the session was announced. An announced session goes to the session page, because Who's coming is there.
- **The session page's primary action.** The set's button. A player who has not answered an announced session has their answer as the primary action instead. Announce and Chip values are quiet lines until they hold something.
- **Where New session starts.** The chosen preset, else the group's latest session that is not archived: its table, location, game and stakes. Rake starts Off, as before. When these are known, the game and stakes read as one line.
- **Home-screen suggestion.** A person with no session in any of their groups is not asked after signing up or logging in. They are asked when they first reach a session or a set in that browser tab. A person with a session is asked after login, as before.

## Consequences

A seat draw needs one more choice than a plain start: the host opens "More host controls" and selects "Let players join first". The set's states are unchanged, and each records the same facts. `games.services.transition` runs `open` first when `start` meets a draft, so the set's version rises by two. Set 2 and later begin open, as before.

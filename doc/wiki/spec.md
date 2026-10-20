# Poker Home Game App (Cash Games): Project Spec

Updated 2026-10-12 to match the app as built. The earlier text asked for chip counts with a chip-to-cash rate and listed five open decisions; both are replaced below. The history of each change is in `doc/study/` and `doc/plan/`.

## Overview

A mobile-friendly app for running **home cash games**. The main job is replacing the napkin-and-calculator routine: track buy-ins and cash-outs, verify the books balance, and work out who pays whom at the end of the night. The app **tracks who owes what only**. It does not process payments.

## Scope

**In scope:**
- Cash games only (no tournaments, no blind timer)
- Tracking money, not moving it
- Private groups of regular players. A person can be in several groups.

**Out of scope for now:**
- In-app payments or anything requiring payment licensing
- Tournament features (blind timer, table balancing, eliminations)
- Public discovery or matchmaking of games

## Words

- A **session** is one gathering: a date, a table and a location.
- A **set** is one round of play inside a session. A session has one or more sets. Money records, counts, the timer and results belong to a set. Settle-up belongs to the session.
- The **unit** of a session is pesos or chips. A pesos game counts in centavos. A chips game counts whole chips and has no peso value: nothing converts chips to pesos.

## Build order

1. **Session with buy-ins and rebuys**
2. **Cash-outs with balance check**
3. **Settle-up calculator**
4. **Player roster and session history**
5. **Leaderboard and stats**

Each step should be usable on its own before moving to the next. Steps 1 to 3 and 5 are built. Step 4 is built except the banker role.

## Feature details

### 1. Sessions, sets, buy-ins and rebuys
- Create a session: date, table, location, stakes (e.g. 1/2), game type (Hold'em, PLO, etc.), min, max and usual buy-in, unit, and an optional rake rule.
- A group can have several sessions open at the same time, for example at two tables. The group's Sessions tab shows each one, with the viewer's own table first.
- Add players to a set from the roster, or type new names. Players can join late.
- Log each buy-in and rebuy per player with a timestamp and amount. Every player has a running total. Starting a set can record the usual buy-in for everyone at the table.
- The host records any buy-in. A player with a login records their own rebuy from their phone; the host can reverse it. One rebuy sent from two phones is recorded once.
- Each set has its own timer.
- **Rake (optional):** off, a flat amount or a percentage, taken from every buy-in and rebuy. It is chosen before a set accepts money and is locked after that. The group keeps a running total of rake collected, with pesos and chips separate.
- **Seat draw (optional):** before a set starts the host can draw the dealer and the seats. Every phone shows the same draw.
- On a phone, numbers are typed with the app's own number keys.

### 2. Cash-outs and balance check
- A cash-out is typed as an amount in the session's unit. There is no chip count and no chip-to-cash rate.
- A player who leaves during play is cashed out by the host. Players leave at different times.
- At the end of a set the host ends play and counts up: one final count per player still at the table. A player with a login can send their own count; the host confirms it or types another, and only a confirmed count is cashed out.
- **Balance check:** remaining stacks plus cash-outs plus collected rake must equal total bought in. If not, show the discrepancy amount and its direction (short or over) so the table can find the error. Finalizing is blocked until the books balance, or the host overrides with a note and assigns the difference to one named player or as an equal share.
- Finalizing a set asks for confirmation once.
- A host can reopen a finalized set, or a closed session, with a reason that everyone sees. Earlier results are kept and marked as replaced. A session with a transfer marked paid is not reopened until the mark is removed.
- Money records are never edited or removed. A correction is a reversal or a new record with a reason.

### 3. Settle-up calculator
- Compute each player's net result over all sets of the session (cash-outs minus buy-ins; rake counts as part of the loss and is not charged again).
- Produce the **minimum number of transfers** to settle all debts (who pays whom, how much).
- Show each player their own net result and what they owe or are owed, clearly.
- Mark each transfer as paid. Unpaid transfers stay visible, and each session reads Settled, Partly settled or Unsettled.
- When closing a session, the host can carry earlier unpaid transfers between two of its players into the new settle-up. They are netted with the night's results into one list.
- Any member can share a closed session's results to the group chat as one picture and as text. The app sends nothing itself.

### 4. Roster and history
- Saved player roster for fast session setup. A roster player needs no login.
- Hosts add several names at once, remove a player after seeing what they still owe or are owed, bring a removed player back with their history, and keep a contact note that only hosts see. A player at the table of an unfinished set cannot be removed. Anyone with a login changes their own name in the group, or in all their groups at once from their profile; a group where the name is taken is skipped.
- Session history list with buy-ins, cash-outs and results per session, and a recap of each closed session.
- Hosts rename a group. Every member sees the new name.
- Hosts archive and restore sessions and groups. An archived session is left out of the stats and the totals. Deleting is allowed only where no money was ever recorded.
- Optional banker role: one player designated to handle cash for that night. Not built yet.

### 5. Leaderboard and stats
- Per player: total profit or loss, sessions played, average result per session, win rate, return on buy-ins, result per hour, rebuys and rake paid.
- A page per player with a running profit chart, best and worst nights, and their sessions.
- Leaderboard ordered by profit, average, return, per hour or sessions, over all time, this year, the last three months or one month. A player needs a few sessions to hold a place.
- Stats count closed sessions only. Pesos and chips are never mixed.
- A profile per person, opened from their chip at the top right, shows their record across all their groups except archived ones, for all time or this year. It adds pesos across their groups. Chips are shown per group and never added across groups ([ADR 0001](../adr/0001-chips-never-add-across-groups.md)).
- Later: seasons.

### 6. Accounts and access
- Players have logins. A host runs the game; players follow it live on their own phones.
- The way in is an invite link from a host. A new person signs up from it and is in the group at once.
- A host gives a roster player their own login with a claim link. The player keeps their history.
- A person who forgot their password asks a host for a reset link. It works once and lasts 24 hours. The app sends no email or message.
- Sign up asks for a username and one password. Two of the four password rules tick while the person types; the server checks all four on sending. An invited Sign up names the group, who sent the link and how many play.
- A logged-in person changes their password on their profile, giving the current one. Their other logins end, and live reset links stop working. Five wrong current passwords in 15 minutes stop further tries for a while.
- The app can be added to a phone's home screen and suggests it after a login.

## Later (not built)

- RSVP with seat limits and a waitlist (typically 9 to 10 seats), recurring games, reminders
- Payments recorded before a session closes (a player who leaves early and is paid at the table)
- Dealer tips
- Notes per session (house rules, disputes)
- Export results as CSV
- Joining two records of the same person

## Data model

The built model is described in [doc/wiki/architecture.md](doc/wiki/architecture.md). In the code a session is `GameNight` and a set is `GameSession`.

Store all money as **integers in the session's unit** (centavos or whole chips), never floats.

## Money logic requirements

- Balance check and settle-up are the most important correctness pieces. Unit tests cover: perfectly balanced sets, small discrepancies, players who cash out in several steps, players who rebuy several times, a winner paid by multiple losers, rake, carried transfers, and rounding when amounts do not divide evenly.
- Settle-up must always sum to zero across all players.

## Decisions made

These were open when the project started.

- **Platform:** a responsive web app that can be added to the home screen. No native app.
- **Backend:** shared. Every player sees the session on their own phone, updated within seconds.
- **Accounts:** players have logins, joined through an invite link. A roster player without a login can still play; the host records for them.
- **Currency:** Philippine pesos, shown as ₱1,600 or ₱1,600.50, or chips with no peso value. Dates use Asia/Manila.
- **Audience:** private groups. Sign-up on the public address needs an invite link.

## Conventions

- Keep the UI fast and usable one-handed at a poker table, in low light.
- Prefer simple, boring tech. Avoid anything that requires payment processing.
- Commit small, with clear messages. Run tests before each commit.

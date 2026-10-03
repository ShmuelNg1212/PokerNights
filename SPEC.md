# Poker Home Game App (Cash Games): Project Spec

## Starter prompt for Claude Code

> Read SPEC.md in full. Before writing any code, propose a tech stack and project structure based on the "Open decisions" section, and ask me about anything blocking. Then build the MVP in the order listed under "Build order", one step at a time, with tests for the money logic (balance check and settle-up). Commit after each step.

## Overview

A mobile-friendly app for running **home cash games**. The main job is replacing the napkin-and-calculator routine: track buy-ins and cash-outs, verify the books balance, and work out who pays whom at the end of the night. The app **tracks who owes what only**. It does not process payments.

## Scope

**In scope (MVP):**
- Cash games only (no tournaments, no blind timer)
- Tracking money, not moving it
- Single group of regular players to start

**Out of scope for now:**
- In-app payments or anything requiring payment licensing
- Tournament features (blind timer, table balancing, eliminations)
- Public discovery or matchmaking of games

## Build order

1. **Session with buy-ins and rebuys**
2. **Cash-outs with balance check**
3. **Settle-up calculator**
4. **Player roster and session history**
5. **Leaderboard and stats**

Each step should be usable on its own before moving to the next.

## Feature details

### 1. Sessions, buy-ins and rebuys
- Create a session: date, location, stakes (e.g. 1/2), game type (Hold'em, PLO, etc.), min and max buy-in, host.
- Add players to the session from the roster.
- Log each buy-in and rebuy per player with a timestamp and amount. Every player has a running total.
- Players can join late.

### 2. Cash-outs and balance check
- Record a player's final chip count when they leave. Players leave at different times.
- Convert chips to cash using the session's chip values (support a simple single chip-to-cash rate first, denominations later).
- **Balance check:** total cashed out must equal total bought in. If not, show the discrepancy amount and which direction it is off (chips missing or extra) so the table can find the error. Block "finalize session" until balanced, or allow an explicit override with a note.

### 3. Settle-up calculator
- Compute each player's net result (cash-out minus total buy-ins).
- Produce the **minimum number of transfers** to settle all debts (who pays whom, how much).
- Show each player their own net result and what they owe or are owed, clearly.
- Mark each transfer as paid. Unpaid transfers stay visible.

### 4. Roster and history
- Saved player roster for fast session setup.
- Session history list with buy-ins, cash-outs and results per session.
- Optional banker role: one player designated to handle cash for that night.

### 5. Leaderboard and stats
- Per player: total profit/loss, sessions played, average result per session, win rate.
- Leaderboard filterable by month, season or all-time.
- Later: bankroll graph over time.

## Later (not MVP)

- RSVP with seat limits and a waitlist (typically 9 to 10 seats), recurring games, reminders
- IOUs and credit carried across sessions
- Optional rake / house fee and dealer tips
- Session timer for hourly-rate stats
- Notes per session (house rules, disputes)
- Export results as CSV or a shareable image for the group chat

## Suggested data model (starting point, adjust as needed)

- **Player:** id, name, optional contact info
- **Session:** id, date, location, stakes, game_type, min_buyin, max_buyin, host_id, banker_id, chip_rate, status (open / balanced / settled)
- **SessionPlayer:** id, session_id, player_id, joined_at, left_at
- **Transaction:** id, session_player_id, type (buyin / rebuy / cashout), amount, chips, created_at
- **Settlement:** id, session_id, from_player_id, to_player_id, amount, paid (bool), paid_at

Store all money as **integer minor units** (e.g. centavos or cents), never floats.

## Money logic requirements

- Balance check and settle-up are the most important correctness pieces. Write unit tests covering: perfectly balanced sessions, small discrepancies, players who cash out in several steps, players who rebuy several times, a winner paid by multiple losers, and rounding when amounts do not divide evenly.
- Settle-up must always sum to zero across all players.

## Open decisions (ask me before assuming)

- **Platform:** mobile app (React Native / Flutter), responsive web app / PWA, or native iOS and Android? A PWA is probably the fastest start since the table will use phones.
- **Backend:** local-only storage for one device, or shared sessions that every player can see on their own phone? This is the biggest architectural choice.
- **Accounts:** do players need logins, or does one host run everything?
- **Currency:** which currency and denominations should the defaults use?
- **Audience:** just my own group, or something to release publicly?

## Conventions

- Keep the UI fast and usable one-handed at a poker table, in low light.
- Prefer simple, boring tech. Avoid anything that requires payment processing.
- Commit small, with clear messages. Run tests before each commit.

# Features

What the app does today (Stage 1). Items that are planned but not built are listed at the end.

## Accounts and groups

- Sign up, log in, log out.
- Create a group. The creator is a host.
- A host creates an invite link (valid 7 days, 20 uses, revocable). A signed-in person who opens it becomes a player.
- A host adds a player to the roster by name, without a login. The host acts for that player.
- A host renames or removes a member, and makes a member with a login a host. A group always keeps one host.
- A person outside the group gets "not found" for everything in it.

## Tables and presets

- A table has a name and 2 to 12 seats.
- A preset saves stakes: blinds, game type, minimum and maximum buy-in, the usual buy-in and its chips.
- Editing a preset changes no existing game.

## A game night

1. **Create.** The host picks a table, date, location, game type and stakes. The game starts as a draft that only hosts see.
2. **Open.** Players join from their phones. The host adds roster players. A full table refuses the next join. A second tap on "Join" adds nothing.
3. **Buy-ins and rebuys.** The host records each one with an amount between the minimum and the maximum. Each row keeps its amount, chips and time. Each player has a running total.
4. **Live view.** Each member sees the player count, buy-in count, total pesos bought in and chips in play. A change by someone else appears within about 5 seconds.
5. **Cash-outs.** The host records the chips a player hands in. A player can cash out in several steps and can leave early.
6. **Balance check.** After play ends, the screen compares chips cashed out with chips issued. A difference is shown in chips and pesos, with its direction and likely causes.
7. **Corrections.** A wrong buy-in or cash-out is reversed with a reason. The reversed row stays in the log.
8. **Override.** If the error cannot be found, the host records a note and who absorbs the difference: one named player or all players equally.
9. **Finalize.** Results are frozen. Each player sees profit or loss. The app lists who pays whom with the minimum number of transfers.
10. **Paid marks.** The host marks each transfer paid, and can undo it. The game shows unsettled, partly settled or settled.
11. **Game log.** Each member can read the players, settings, each buy-in, reversal and cash-out, overrides, results, transfers, payment records, and who did what and when.

A game without accepted buy-ins can be canceled with a reason. A canceled game does not count.

## Limits today

- The app records who owes what. It does not move money.
- The transfer list assumes that no money changed hands before finalization. A payment during the game cannot be recorded yet.
- A finalized game cannot be reopened. Check the chip counts before finalizing.
- No banker mode, no seating, no seasons, no leaderboard, no statistics across games.
- No password reset by email.
- The app runs on one machine. It is not deployed.

See the [roadmap](../roadmap/README.md).

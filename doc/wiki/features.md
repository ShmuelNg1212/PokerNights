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
- A preset saves stakes: blinds, game type, minimum and maximum buy-in, the usual buy-in, and the unit.
- Editing a preset changes no existing game.

## Units

- Each game counts in **pesos** (the default) or in **chips**. The host selects the unit on the preset or when creating the game.
- In a pesos game, each figure is a peso amount: buy-ins, cash-outs, results and transfers.
- In a chips game, each figure is a chip count, shown as "1,600 chips". A chips game has no peso value. No ₱ appears on its screens, and its transfers are in chips.
- The app does not convert between chips and pesos.
- The unit of a game cannot change after the first accepted buy-in.

## Sessions and sets

- A **session** is one gathering at one table on one date. It holds one or more **sets**, played one after another.
- Each set has its own buy-ins, cash-outs, balance check, results and timer. A new set starts with fresh buy-ins.
- After play of a set has ended, the host taps **Start next set**. The new set has the same table and settings and the players who were still at the table. The host can add or remove players before starting it.
- Who pays whom is worked out **once per session**: the host taps **Close session and settle up** when every set is finalized or canceled. The list nets each player's results over all sets.
- A closed session cannot get another set.

## Timers

- Each set has its own timer. It starts when the host starts the set and stops when the host ends play. If the set is resumed, the timer continues; the time spent counting is not added.
- Each player's playing time in a set is the part of that timer during which they were at the table. A late joiner starts later; a player who leaves stops earlier.
- All times come from the server. A reload or another tab shows the same figure.
- Playing time is stored with each frozen result. Sets played before this feature show "not recorded".

## End of a set

1. **End play.** The set's timer and every player's time stop at one moment.
2. **Confirm final counts.** The host types what each player has left, for as many players as are counted, then confirms. Each "Confirm count" button and "Confirm all counts" confirm every typed count at once. 0 is a valid count. An empty field is skipped and stays "Awaiting count"; it is never treated as zero. If one value is refused, nothing is saved and the typed values stay in their fields.
3. **Statuses.** Each player is "Awaiting count", "Ready to cash out" or "Cashed out".
4. **Cash out counted players (N).** The host reviews the counted players, each amount and the total, then confirms once. All of them are cashed out, or none. Players still to count stay pending; the host runs the action again later.
5. **Stale review.** If a count changed or a player was cashed out elsewhere after the review opened, nothing is recorded and a fresh review is shown.
6. **Finalize the set.** Needs a final cash-out for every player and balanced books (or an override). This freezes the set's results. It lists no transfers.

The individual cash-out still exists: tap the player name to open Details during play (for early departures), or expand "Details" while counting. Without JavaScript, expand the player row’s Details.

## A game night (one set)

1. **Create.** The host picks a table, date, location, game type, unit and stakes. The game starts as a draft that only hosts see.
2. **Open.** Players join from their phones. The host adds roster players. A full table refuses the next join. A second tap on "Join" adds nothing.
   - **Add players.** A host can add several players in one action: tick them in a searchable list, check the count against the free seats, and confirm once ("Add 4 players"). Everyone selected is added, or nobody is. Players at the table cannot be ticked. If someone else changed the roster first, nothing is added and the selection is kept for review. Adding players records no buy-in and no payment.
3. **Buy-ins and rebuys.** The host records each one with an amount between the minimum and the maximum. Each record keeps its amount and time. Each player has a running total. On the active set, tap the row’s `+` and confirm to record the default amount. The sheet also offers minimum, default, twice default (capped at maximum), and maximum amounts.
4. **Live view.** Each member sees the player count, buy-in count, the total bought in and the amount still in play. A change by someone else appears within about 5 seconds.
5. **Cash-outs.** The host types the amount a player leaves with, in the game's unit. A player can cash out in several steps and can leave early.
6. **Balance check.** After play ends, the screen compares the total cashed out with the total bought in. A difference is shown as an amount, with its direction and likely causes.
7. **Corrections.** A wrong buy-in or cash-out is reversed with a reason. The reversed row stays in the log.
8. **Override.** If the error cannot be found, the host records a note and who absorbs the difference: one named player or all players equally.
9. **Finalize the set.** Its results are frozen. Each player sees profit or loss for the set.
10. **Close the session.** The app lists who pays whom with the minimum number of transfers. The host marks each transfer paid, and can undo it. The session shows unsettled, partly settled or settled.
11. **Game log.** Each member can read the players, settings, each buy-in, reversal and cash-out, overrides, results, transfers, payment records, and who did what and when.

A game without accepted buy-ins can be canceled with a reason. A canceled game does not count.

## Limits today

- The app records who owes what. It does not move money.
- The transfer list assumes that no money changed hands before finalization. A payment during the game cannot be recorded yet.
- A finalized set and a closed session cannot be reopened. Check the cash-outs before finalizing.
- No breaks: "Left" is the way to stop a player's time. The end time of a set cannot be edited.
- The session page does not refresh by itself; the set page does.
- No banker mode, no seating, no seasons, no leaderboard, no statistics across games.
- No password reset by email.
- The app runs on one machine. It is not deployed.

See the [roadmap](../roadmap/README.md).

## Active set design (slice 1)

- The Rack uses an indigo table field, warm dark ground, Archivo figures and player tokens with initials. Shared forms and other screens use the same base styles; their composition is not yet redesigned.
- The first phone viewport shows still in play, clock and blinds. Total bought in and cashed out remain separate labels. From 900 px, the field and host controls sit beside the player list.
- Tap a player's name for cash-out, playing time, money records and corrections. Tap `+` for buy-in or rebuy. The next host action sits in an opaque phone dock. More host controls includes settings, cancellation and adding one player.
- Without JavaScript, each row has expandable forms for the same actions.
- A refused sheet submission reopens with typed amounts or reasons and the server's error. Pending buttons say “Sending…”. A changed server figure gets a temporary brass highlight; an unchanged refresh has none. Figures never count up.
- Live updates keep open sheets and their focused field intact. Count-up uses one inline form and preserves typed drafts during polling.
- Native dialogs support keyboard focus, Escape and focus return. Reduced motion disables movement. Chip colour comes from join order and repeats after ten; initials remain visible.

## End-of-set design (slice 2)

- Count-up uses slate felt and shows ready plus finally cashed-out players out of all players with buy-ins. Earlier partial cash-outs do not complete a player. Total bought in and recorded cash-outs have separate labels.
- Every eligible host count field stays inline. A confirmed count is written above the draft field. Count confirmation and recording cash-outs remain separate actions. Players see statuses and confirmed counts without host inputs.
- The host dock links to the batch review when counts are ready, offers finalization only when the books balance, and exposes the next-step explanation. Resume play and cancellation remain under More host controls.
- Batch review shows the confirmed amount to record, this batch's total, the amount already cashed out and the prospective total after confirmation. It makes no payment and does not finalize.
- The books-balance double rule appears only when the existing accounting gate passes, including disclosed overrides. It animates once per set per browser. Reduced motion leaves it static.
- Final set results use frozen snapshots, with Final tags, signed amounts, directional icons and time played. The viewer's result is prominent. Who pays whom stays on the session page.
- Count-up, review and finalized pages use two columns from 900 px. On phones, counts stay in one column; the balance check follows the count list. Long names wrap. JavaScript-free forms remain usable.


The [parent plan](../plan/1791046015_visual_redesign.md) records remaining slices; the [slice 2 plan](../plan/1791050738_redesign_slice_2.md) records end-of-set verification.

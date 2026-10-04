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
- Each set has its own buy-ins, cash-outs, balance check, results and timer. A new set starts money-free. Before play starts, the host can record fresh opening buy-ins with the default start option.
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
The live stack counter adds remaining counts, accepted cash-outs and collected rake, then compares the sum with gross buy-ins. The host preview updates while typing; a valid draft replaces a saved count. A blank field uses its saved count, or stays uncounted if none exists. Zero is valid. Missing players and invalid entries prevent a complete match. Final-cashed-out players contribute only through cash-outs, so their saved counts are not added twice. Overrides stay outside this raw stack check. Unsaved totals are labelled Preview; confirmation and cash-out remain separate. Players and JavaScript-free views see confirmed totals only.

3. **Statuses.** Each player is "Awaiting count", "Ready to cash out" or "Cashed out".
4. **Cash out counted players (N).** The host reviews the counted players, each amount and the total, then confirms once. All of them are cashed out, or none. Players still to count stay pending; the host runs the action again later.
5. **Stale review.** If a count changed or a player was cashed out elsewhere after the review opened, nothing is recorded and a fresh review is shown.
6. **Finalize the set.** Needs a final cash-out for every player and balanced books (or an override). This freezes the set's results. It lists no transfers.

The individual cash-out still exists: tap the row's Cash out button during play (for early departures), or expand "Details" while counting. Without JavaScript, expand the player row’s Cash out form.

## A game night (one set)

1. **Create.** The host picks a table, date, location, game type, unit and stakes. The game starts as a draft that only hosts see.
2. **Open.** Players join from their phones. The host adds roster players. A full table refuses the next join. A second tap on "Join" adds nothing.
   - **Add players.** A host can add several players in one action: tick them in a searchable list, check the count against the free seats, and confirm once ("Add 4 players"). Everyone selected is added, or nobody is. Players at the table cannot be ticked. If someone else changed the roster first, nothing is added and the selection is kept for review. Adding players records no buy-in and no payment. Add players stays available during play even when every roster member is seated. The same page offers Add new player: enter a name to save a no-login roster identity and join them to the current set in one action. The new player’s timer starts when they join; record their buy-in separately. Duplicate names direct the host to roster selection, or back to the set if that player is already seated, and a full or ended set adds nobody.
3. **Start play and opening buy-ins.** Start the set includes a checked option to add the set’s usual buy-in for each player at the table without an accepted buy-in. Existing buy-ins are kept, even at a different amount. Uncheck the option to start without automatic entries. Records and timers commit together; repeated confirmation creates nothing twice. Each new set uses its own current settings. Resume and late joining add no automatic buy-in. A reversed-only player qualifies again before first start; uncheck when that is intentional.
4. **Buy-ins and rebuys.** The host records each one with an amount between the minimum and the maximum. Each record keeps its amount and time. Each player has a running total. On the active set, tap the row’s Buy-in or Rebuy button and confirm to record the default amount. The sheet also offers minimum, default, twice default (capped at maximum), and maximum amounts.
5. **Live view.** Each member sees the player count, buy-in count, the total bought in and the amount still in play. A change by someone else appears within about 5 seconds.
6. **Cash-outs.** The host types the amount a player leaves with, in the game's unit. A player can cash out in several steps and can leave early.
7. **Balance check.** After play ends, the screen compares cash-outs plus collected rake with gross buy-ins. A difference is shown as an amount, with its direction and likely causes.
8. **Corrections.** A wrong buy-in or cash-out is reversed with a reason. The reversed row stays in the log.
9. **Override.** If the error cannot be found, the host records a note and who absorbs the difference: one named player or all players equally.
10. **Finalize the set.** Its results are frozen. Each player sees profit or loss for the set.
11. **Close the session.** The app lists who pays whom with the minimum number of transfers. The host marks each transfer paid, and can undo it. The session shows unsettled, partly settled or settled.
12. **Set log.** Each member can read the players, settings, each buy-in, reversal and cash-out, overrides, results, and who did what and when. Transfers and payment records are on the linked session page.

A game without accepted buy-ins can be canceled with a reason. A canceled game does not count.

## Rake

New session offers Off (default), Flat amount, and Percentage of buy-in before the first buy-ins. On an empty draft or open set, Choose rake before buy-ins opens the same settings. Only the chosen value applies; unused value fields do not block a save. Percentage accepts 0.01%–99.99%, with at most two decimals. It rounds down separately per buy-in to a centavo or whole chip. Flat rake uses the set's unit. The amount entered for a buy-in is gross: ₱1,000 at 5% gives ₱950 in play and ₱50 collected rake. The fee must leave a positive playable amount.

Every buy-in and rebuy uses the rule, including default opening buy-ins and manually recorded late-player buy-ins. Rake stays locked while accepted buy-ins or cash-outs exist. Reversing all accepted money allows reconfiguration. Ordinary stakes edits keep the rule; next sets inherit it. A permitted unit change resets it to Off. Presets do not configure rake.

The set shows gross bought in, collected rake and available to play. Counts/cash-outs plus rake must match gross buy-ins; rake does not replace a missing player's cash-out. Final results include the fee as a loss. Settle-up excludes this already-collected fee, so it is never charged twice and the rake account receives no transfer.

Group settings shows the group's lifetime collected rake across all sessions and sets, including games in progress. Peso and chip totals stay separate. Expand the session/set breakdown to see where each total came from. Reversing a buy-in excludes its fee; payment marks and Undo do not change rake totals. Historical records start at zero rake.

## Limits today

- The app records who owes what. It does not move money.
- The transfer list excludes rake already collected at buy-in. It assumes no earlier player payments. A player payment during the game cannot be recorded yet.
- A finalized set and a closed session cannot be reopened. Check the cash-outs before finalizing.
- No breaks: "Left" is the way to stop a player's time. The end time of a set cannot be edited.
- The session page does not refresh by itself; the set page does.
- No banker mode, no seating and no seasons. Stats have no minimum-session threshold, average result or ROI yet.
- No password reset by email. A superuser sets a new password in `/admin/`.
- On the public address, an account can be created only from a usable invite link; a superuser adds the first host of a group.

See the [roadmap](../roadmap/README.md).

## Active set design (slice 1)

- The Rack uses an indigo table field, warm dark ground, Archivo figures and player tokens with initials. Home, group, accounts, forms and log use the completed Rack compositions.
- The first phone viewport shows still in play, clock and blinds. Total bought in and cashed out are plain labelled rows; there is no split bar. The indigo field appears only while the set is in play; draft and open sets use the neutral lead panel. From 900 px, the field and host controls sit beside the player list.
- Each host row has written Buy-in or Rebuy and Cash out buttons at every width. Tap a player's name for playing time, money records and corrections. The next host action sits in an opaque phone dock. More host controls includes settings, cancellation and adding one player.
- Without JavaScript, each row has expandable forms for the same actions.
- A refused sheet submission reopens with typed amounts or reasons and the server's error. Pending buttons say “Sending…”. A changed server figure gets a temporary brass highlight; an unchanged refresh has none. Figures never count up.
- Live updates keep open sheets and their focused field intact. Count-up uses one inline form and preserves typed drafts during polling.
- Native dialogs support keyboard focus, Escape and focus return. Reduced motion disables movement. Chip colour comes from join order and repeats after ten; initials remain visible.

## End-of-set design (slice 2)

- Count-up uses the neutral lead panel and shows ready plus finally cashed-out players out of all players with buy-ins. Earlier partial cash-outs do not complete a player. Total bought in and recorded cash-outs have separate labels.
- Every eligible host count field stays inline. A confirmed count is written above the draft field. Count confirmation and recording cash-outs remain separate actions. Players see statuses and confirmed counts without host inputs.
- The host dock links to the batch review when counts are ready, offers finalization only when the books balance, and exposes the next-step explanation. Resume play and cancellation remain under More host controls.
- Batch review shows the confirmed amount to record, this batch's total, the amount already cashed out and the prospective total after confirmation. It makes no payment and does not finalize.
- The books-balance double rule appears only when the existing accounting gate passes, including disclosed overrides. It animates once per set per browser. Reduced motion leaves it static.
- Final set results use frozen snapshots, with Final tags, signed amounts, directional icons and time played. The viewer's result is prominent. Who pays whom stays on the session page.
- Count-up, review and finalized pages use two columns from 900 px. On phones, counts stay in one column; the balance check sits above the count list. Waiting for counts is a neutral notice. When every player is cashed out and the books still differ, the panel leads with the exact signed amount and the next step. Long names wrap. JavaScript-free forms remain usable.


## Session and settle-up design (slice 3)

- Open sessions lead with the current set action and show Results so far over finalized sets. Host close controls explain unfinished sets. Closed sessions lead with Still to pay and settled/partly settled/unsettled status.
- Still to pay sums unpaid transfers. The progress bar measures paid amounts against all transfer amounts; the paid transfer count is labelled separately. A fully paid session says Settled in words instead of ₱0. With no transfers, the page says Nobody owes anything and shows no bar. Paying or undoing a transfer does not change frozen poker results.
- Each transfer is a card with payer, payee, tokens, amount and Paid / Not paid. Only hosts see Mark paid and Undo. Payment records retain undone rows and name the recorder. Session results use signed figures, directional icons and a Final tag only after closing.
- Initial tokens use session standings' first-appearance order, keyed by member. They may have different colours from an individual set. Full names stay visible.
- The closing recap opens automatically once per session, signed-in viewer and browser. View session recap reopens it manually. Close, backdrop tap and Escape dismiss it; Tab stays in the modal, and focus returns to the trigger. Reduced motion is static. Storage refusal skips automatic opening; manual access remains. Without JavaScript, the recap is inline and native payment/close/next-set forms still work.
- Recap Recorded play time sums known finalized-set durations, says Not recorded if none are known, and marks a partial sum. It excludes canceled sets. Total bought in across finalized sets sums frozen buy-in snapshots, so money bought in again in another set is counted again. Top session result names all tied winners; break-even sessions say Everyone broke even. Your session result is omitted for a non-playing viewer.
- The page is one column on phones and 400 px / flexible columns from 900 px. Long settlement amounts use a smaller fixed type size to preserve the whole numeric value on one line. This page still requires reload to see another client's payment changes.

The [parent plan](../plan/1791046015_visual_redesign.md) records remaining slice 4; [slice 2](../plan/1791050738_redesign_slice_2.md) and [slice 3](../plan/1791053204_redesign_slice_3.md) record verification.


## Remaining screen design (slice 4)

- Home shows group navigation and roles, then group creation. Empty home explains how to create or join a group.
- Group shows current sessions first, with New session above the list for hosts. Past sessions follow. Tables, presets, roster and invitations form a management rail from 900 px and follow sessions on phones.
- Roster names stay alphabetic. Initial tokens use member ID and the existing palette; colour is not a cross-view identity guarantee. Host tools use native disclosures.
- Failed group creation, table creation, roster add and rename keep editable values, show a local error and open the failed disclosure. Success uses the existing redirect. Passwords stay blank on refused account submissions.
- Account, invitation, session, preset, settings and picker pages share a narrow form frame. The picker still supports search and native all-or-nothing submission.
- The set log groups complete records by category, with exact amounts, actors, times and reasons. Reversed and voided rows stay visible. Frozen results show signed values and Final labels. Native section links aid navigation.
- Canceled sets show their reason, retained roster and log link, with no final result or money action.


## Your groups home

- The first page lists each group with its players, one status band and one next action for the viewer: **Open the table** for a set in play, **Open set N** for a draft, open or counting set, **Go to the session** when every set is finished, and **New session** or **Add a table** for a host in a quiet group. A player in a quiet group gets no button.
- A set in play shows players at the table and the timer on the blue felt band. Money still in play is not shown here; the page does not refresh by itself.
- **To settle** lists the viewer's unpaid transfers from closed sessions ("You owe Miguel ₱425", "Jerome owes you ₱1,375"), three at most, each linking to its session. Nobody sees another member's debts here.
- **Your record** shows profit or loss, sessions and wins per unit, by the same rules as Stats. **Last session** shows the viewer's result in the latest closed session, or "You did not play".
- Groups with a set in play come first, then groups with an open session, then by name. Drafts stay hidden from players.
- Create a group is a closed section under the groups. A person with no group gets a first-group screen.

## Group page, stats and branding (UI evolution)

- The group page has tabs on the one group address: **Sessions** (default), **Stats** and **Group settings** (`?view=stats`, `?view=settings`). An unknown `view` shows Sessions.
- Sessions lists current and past sessions. With none in progress, a neutral card gives one next action for the viewer: New session, Add a table (host without tables), or a note that a host starts it.
- Group settings holds players, invite links, tables, presets and the group rake account. Each management action returns to its own section. Players read the same lists without host forms.
- Stats appears once the group has a closed session. It ranks players by profit or loss, with sessions played and win rate, for all time or one month, and for pesos or chips separately.
  - Only closed sessions count, using the current frozen results of their finalized sets. Canceled sets and open sessions are excluded.
  - A player's sets are added per session first. Several sets in one session count as one session.
  - Profit or loss is the result after rake. It is not the settle-up balance.
  - Win rate is profitable sessions divided by sessions played, rounded down. A break-even session is played, not won.
  - The month is the session's date. Players who left the group keep their history. There is no minimum number of sessions.
- Words: a **Session** is the whole gathering and its settle-up; a **Set** is one round of buy-ins, counting and results. Screens say Set settings, Set log, Join this set and Poker variant. "Pesos game" and "chips game" still name the unit.
- Branding: `static/branding/` has `logo-mark.svg` (a notched chip with a crescent), `logo-horizontal.svg`, `app-icon.svg` and `logo-mono.svg` for cream backgrounds. The header shows the mark beside the name; the mark is the favicon.

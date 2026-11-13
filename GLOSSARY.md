# Glossary

Words of the product, as screens and docs use them. The code names are in brackets. Decisions are in [doc/adr/](doc/adr/).

- **Session** (`GameNight`): one gathering at one table on one date. It holds sets. Settle-up, payments and the unit belong to it.
- **Set** (`GameSession`): one round of play in a session. Money records, counts, the timer and results belong to it.
- **Set states**: Draft, Joining, In play, Counting up, Finalized and Canceled. Screens and messages use these words (`GameSession.state_word`). The stored names stay.
- **Joining** (`GameSession.State.OPEN`): a set that players can join before play starts. The host's action is "Let players join". Do not say "Open" for this state.
- **In progress** (`GameNight.Status.OPEN`): a session that is not closed. Do not say "open" or "not closed" for this state. On the session's own badge, one with no set started yet says **Not started**.
- **Go to**: the word for moving to a place: Go to the table, Go to set 1, Go to the session. "Open" stays only as a verb for a link, an app or a disclosure.
- **Chip values** (`GameNight.chip_values`): the session's optional colour-to-value assignments. Each value uses its session unit. Every set shares them. They lock after the first chip-based count is submitted.
- **Chip preset** (`ChipPreset`): a group's saved chip values with a name and a unit. A host fills a session's chip values from one; the session keeps a copy.
- **Chip breakdown**: the denomination, quantity and subtotal saved with a chip-based count. It explains the amount. It does not replace host confirmation or cash-out.
- **Announce**: a host makes a draft session visible to players, so they can answer.
- **RSVP** (`Rsvp`): one member's answer for one announced session: In or Out.
- **Seat limit** (`GameNight.seat_limit`): how many players an announced session confirms. Not a set's seat count, which grows to it.
- **Confirmed**: an In that has a seat. Screens say "Coming" and "You're in".
- **Waitlist**: the Ins without a seat, in the order of their answers. Screens say "Waitlist · 2nd in line".
- **Rake fund** (`GroupRakeAccount`, `Transfer.to_rake_fund`): the group's collected rake as a party in settle-up. It only receives. Used when the group's rake rule is "At settle-up, into the rake fund" (ADR 0007); otherwise settle-up returns each player's own fee.
- **Debt**: an unpaid transfer viewed across closed sessions. Debts between two players are netted within one group and one unit.
- **Clearance**: a record of the net amount settled between two players. It closes the linked debts across sessions, including when they cancel to zero.
- **Counted session**: a closed session that is not archived. Stats and the recap's marks read only counted sessions, in one unit (`settlement.queries.counted_results`).
- **Winning run**: 3 or more counted sessions in a row that a player finished ahead, among the sessions that player played. A break-even session ends it. The recap says it; it never says a losing run ([ADR 0014](doc/adr/0014-marks-of-a-night.md)).
- **Personal best**: a positive session result higher than each earlier one of that player, from the third counted session.
- **Mark** (`settlement.stats.Mark`): a fact in the recap's Highlights about a player's history: a winning run, a personal best, a first win or a round number of sessions. Read, never stored.

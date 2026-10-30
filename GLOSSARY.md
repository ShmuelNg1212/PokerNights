# Glossary

Words of the product, as screens and docs use them. The code names are in brackets. Decisions are in [doc/adr/](doc/adr/).

- **Session** (`GameNight`): one gathering at one table on one date. It holds sets. Settle-up, payments and the unit belong to it.
- **Set** (`GameSession`): one round of play in a session. Money records, counts, the timer and results belong to it.
- **Chip values** (`GameNight.chip_values`): the session's optional colour-to-value assignments. Each value uses its session unit. Every set shares them. They lock after the first chip-based count is submitted.
- **Chip preset** (`ChipPreset`): a group's saved chip values with a name and a unit. A host fills a session's chip values from one; the session keeps a copy.
- **Chip breakdown**: the denomination, quantity and subtotal saved with a chip-based count. It explains the amount. It does not replace host confirmation or cash-out.
- **Announce**: a host makes a draft session visible to players, so they can answer.
- **RSVP** (`Rsvp`): one member's answer for one announced session: In or Out.
- **Seat limit** (`GameNight.seat_limit`): how many players an announced session confirms. Not a set's seat count, which grows to it.
- **Confirmed**: an In that has a seat. Screens say "Coming" and "You're in".
- **Waitlist**: the Ins without a seat, in the order of their answers. Screens say "Waitlist · 2nd in line".
- **Rake fund** (`GroupRakeAccount`, `Transfer.to_rake_fund`): the group's collected rake as a party in settle-up. It only receives. Used when the group's rake rule is "At settle-up, into the rake fund" (ADR 0007); otherwise settle-up returns each player's own fee.

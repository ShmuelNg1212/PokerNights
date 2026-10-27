# Glossary

Words of the product, as screens and docs use them. The code names are in brackets. Decisions are in [doc/adr/](doc/adr/).

- **Session** (`GameNight`): one gathering at one table on one date. It holds sets. Settle-up, payments and the unit belong to it.
- **Set** (`GameSession`): one round of play in a session. Money records, counts, the timer and results belong to it.
- **Announce**: a host makes a draft session visible to players, so they can answer.
- **RSVP** (`Rsvp`): one member's answer for one announced session: In or Out.
- **Seat limit** (`GameNight.seat_limit`): how many players an announced session confirms. Not a set's seat count, which grows to it.
- **Confirmed**: an In that has a seat. Screens say "Coming" and "You're in".
- **Waitlist**: the Ins without a seat, in the order of their answers. Screens say "Waitlist · 2nd in line".

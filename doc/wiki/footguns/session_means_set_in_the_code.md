# In the code, `GameSession` is a set

- **Trigger:** Reading or writing code after sessions with several sets were added (2026-10-04).
- **Observed behavior:** The product has two levels: a **session** (one gathering) that holds **sets** (rounds of play). The model that was first called `GameSession` is the set. The session is the newer model `GameNight`. Fields named `session` on buy-ins, cash-outs, participants and results point to a set. The URL `/s/<id>/` is a set; `/n/<id>/` is a session.
- **Impact:** A change meant for the whole session can be written against one set, or the reverse. Settle-up, transfers, payments and the unit belong to `GameNight`. Money records, timers, counts and results belong to `GameSession`.
- **Evidence:** The rename was considered and not done: it would touch every app and each migration for no change in behavior (study addendum A3).
- **Remedy:** Read `GameSession` as "set" and `GameNight` as "session". Use the screen words in user-facing text only.

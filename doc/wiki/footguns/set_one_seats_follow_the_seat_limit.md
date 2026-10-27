# Set 1's seats follow the RSVP seat limit

- **Trigger:** Changing the seat limit of an announced session, or **Seat now** (2026-10-27).
- **Observed behavior:** `_fit_set_one()` in `games/services.py` raises set 1's `seat_count` to the seat limit. It never lowers it. A later set copies set 1's seats, as before.
- **Impact:** A set can have more seats than its table. Lowering the session's seats leaves set 1 as it was.
- **Evidence:** Without it, Add players ticked more confirmed players than set 1 could seat, and the send was refused (code review, 2026-10-27). `test_set_one_grows_with_the_seat_limit`.
- **Remedy:** Read a set's seats from `GameSession.seat_count`, never from the table, once the set exists.

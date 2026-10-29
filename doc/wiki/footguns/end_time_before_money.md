# A corrected end time can come before money rows

- **Trigger:** A host moves a set's end of play earlier (2026-10-29, "Wrong end time?").
- **Observed behavior:** `games.services.correct_end_time` checks only the last start and the recorded end. A buy-in or a cash-out recorded during play after the new end stays as it is. The set then shows money recorded after play ended.
- **Impact:** A check that assumes "every in-play buy-in is before `GameSession.ended_at`" is wrong. Money and results do not depend on the timer, so totals and settle-up are not affected. Only playing time changes.
- **Evidence:** Code review of 2026-10-29, recorded in the [plan](../../plan/1793266411_past_filters_and_end_time.md).
- **Remedy:** None by design: the host knows when play ended. Do not use `ended_at` to order money rows; use their own `created_at`.

# An announced draft is seen by players

- **Trigger:** Changing who can see a session whose sets are all drafts (2026-10-27, RSVP).
- **Observed behavior:** `games.access.night_for` lets a player open the session page once a host has announced it, although set 1 is still a draft. `session_for` still returns 404 for the set page. The session page hides Results and Sets from players until play starts.
- **Impact:** A check that assumes "players never see a draft session" is wrong. Anything added to the session page shows to players of an announced draft unless it is gated on `me.is_host` or `before_play`.
- **Evidence:** `web/tests/test_rsvp_pages.py`, `test_a_player_sees_an_announced_draft_but_not_its_set`.
- **Remedy:** Gate host-only and money parts of the session page explicitly. Keep set and money pages behind `session_for`.

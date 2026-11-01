# Plan: draw seats from a draft

Mode: technical. Size: one `feat:` commit, plus one `docs:` commit for the checks. No study: the facts are below.

Status: the human approved this change on 2026-11-01. Build it. Do not stop for approval.

## OPEN QUESTIONS

None.

## Problem

A seat draw needs an open set. Since [ADR 0009](../adr/0009-start-a-game-fast.md), a host adds players to a draft and taps Start the set. The set goes from draft to running, and the draw is not available for that set. The service refuses a draw on a running set, and a running set cannot go back to open.

The only way to the draw on a first set is More host controls, then "Let players join first". That button is closed by default, and its label is about something else. Set 2 and later begin open, so they do not have this problem.

## Decision

A host can draw from a draft that has 2 or more seated players. The Draw button opens the set and draws in one transaction. This follows the way that Start the set opens and starts.

"Let players join first" stays. It is still the way to let players join by themselves.

## Behaviour

- The optional **Seat draw** step shows on a draft to a host when 2 or more players are seated. Start the set stays the one main button.
- A tap on **Draw** does these steps in one transaction: open the set, then draw. The audit log has both steps. `GameSession.version` rises by two.
- Seated players get the "set N is ready to join" notice, as when a set opens. The host who drew does not get it.
- Players can then see the set. Their phones play the draw as they do for a draw on an open set.
- After this, the set is open. All later steps do what they do now: choose a seat, Draw again, Start the set.
- A refused draw changes nothing. The set stays a draft, and nobody gets a notice.
- A repeated request changes nothing. It returns the first draw, and it does not open or notify again.
- Players never see the Draw button. A draft stays a 404 for a player.
- `SEAT_DRAW=False` hides the step and refuses the draw. The set stays a draft.

## Where the code is

| Change | File |
|---|---|
| Open a draft before the draw | `draw_seats` in `games/services.py`. The state check is `if session.state != State.OPEN`. |
| Offer the draw on a draft | `web/views.py`, the block that starts `if settings.SEAT_DRAW and session.state in ("open", "running")` |
| Step text | `templates/web/_session_live.html`, the `data-step="seats"` step |
| Button note | `templates/web/_host_controls.html`, under "Let players join first" |

`games.services.transition` shows the pattern to follow:

```python
if session.state == State.SETUP:
    session = transition(session_id, actor, "open")
```

Rules for the service change:

- Keep the `request_id` replay check first, so that a replay does not open the set again.
- Keep the `SEAT_DRAW` check before the open.
- `draw_seats` is `@transaction.atomic`, so a refusal for too few players rolls back the open and its notice. Prove this with a test.

Rules for the view change:

- `can_draw_seats` is true on a draft under the same conditions as on an open set: not archived, a host, 2 or more seated.
- `seating` stays `None` on a draft. An open set can hold a draw and then go back to draft after its players are removed. That old draw must not show on the draft.

The form in `_session_live.html` already shows when `can_draw_seats` is true and `seating` is empty. Its `request_id` field is already there.

## Do not build these

- No change to the set's states or `TRANSITIONS`.
- No seat draw after a set starts.
- No change to Start the set.
- No new model or migration.

## Tasks

### 1. Draw from a draft

`tests: first`. Put the view tests in `web/tests/test_seat_draw.py`. Put the service tests in `games/tests/test_start_from_draft.py`, or in a new file beside it.

- [ ] Make a feature branch `feat/draw-from-draft`. Stack it on `feat/ui-revamp-f-motion` if Slice F is not released. Otherwise, start from `main`.
- [ ] Write these tests and see them fail:
  - A draw on a draft with 2 players opens the set and makes one current draw.
  - The audit log has `session.open` and `seats.drawn`.
  - The version rises by two.
  - Seated players get one notice, and the host gets none.
  - A replay with the same `request_id` makes no second draw, audit row or notice.
  - A draw on a draft with 1 player is refused. The set stays a draft, with no audit row and no notice.
  - `SEAT_DRAW=False` refuses, and the set stays a draft.
  - A player who posts a draw on a draft gets a 404, and the set stays a draft.
  - A draw on a running set is still refused.
  - A draw on an archived session is refused as it is now.
  - The draft page offers Draw to a host with 2 players, and not with 1.
  - The draft page does not show an earlier draw.
- [ ] Change `draw_seats` and update its docstring.
- [ ] Change the view.
- [ ] Change the refusal text in `draw_seats` to "Seats are drawn before the set starts." Search the tests for the old text first.
- [ ] Add this to the step line on a draft: "Players see the set when you draw." The host must know this before the tap. Keep the current line on an open set.
- [ ] Remove "You can draw seats then." from the note under "Let players join first".

Done when: all these tests pass, and the full SQLite and PostgreSQL suites pass.

### 2. Browser check

`tests: alongside`. Extend `web/tests/browser/seat_draw.mjs` and `web/tests/browser/seed_seat_draw.py` with a draft set.

- [ ] On a phone-width page, sign in as the host on a draft with 2 or more players. See the Seat draw step. Tap Draw.
- [ ] See the stage open at once on the host's page, and see the set's badge change to Joining.
- [ ] Sign in as a seated player. See that the draft is a 404 before the draw. See the set and the draw after it.
- [ ] As the host, choose a seat and tap Start the set. See the seats on the running set.
- [ ] Add a draft with 2 players to a host flow and tap Start the set without a draw. See that this flow does not change.

Done when: the script passes, and the existing `seat_draw` checks still pass. The first check must fail on the code before task 1.

### 3. Docs

`tests: alongside`. Commit these with task 1, except the checks record.

- [ ] Add `doc/adr/0011-draw-seats-from-a-draft.md`. It revises ADR 0009 on "A seat draw still needs an open set" and on the extra choice in its Consequences. Do not edit ADR 0009.
- [ ] Update the Seat draw rule in `doc/wiki/spec.md`. This plan is the approval for that change.
- [ ] Update "Where" and add a line on the draft in the Seat draw section of `doc/wiki/features.md`.
- [ ] Add the phone checks below to `TODO.md`. Keep the file at 40 lines or fewer.
- [ ] Run `graphify update .`.

Done when: no wiki page says that a draw needs an open set.

## Phone checks for TODO.md

- [ ] Add two players to a new set. Seat draw shows without opening a menu, and the step says that players see the set when you draw.
- [ ] Tap Draw. The draw plays, the set says Joining, and a player's phone gets the notice and shows the same draw.
- [ ] Add two players and tap Start the set. The set starts as before.

## Notes for the builder

- At the time of writing, Slice F has uncommitted changes in this working tree, including `web/views.py`. Start after Slice F is committed. Slice F task F5 also changes the checklist in `_session_live.html`, so check for conflicts there.
- **Back to draft** is refused once a player is seated. So a host cannot undo a draw on a draft with that button. Draw again and cancel stay available. This is expected.
- Use `.venv/bin/python manage.py test` with `DEBUG=True` when `SECRET_KEY` is unset.

## Rendezvous

Record the checks here. Then leave a verified branch. Merge only on "ship".

- [ ] Tests:
- [ ] Review skills:
- [ ] Browser probe:

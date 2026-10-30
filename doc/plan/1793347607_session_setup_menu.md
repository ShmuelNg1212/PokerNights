# Session setup menu: plan

Date: 2026-10-30. Mode: mixed. Status: approved 2026-10-30; in execution.

Study: [session setup menu](../study/1793347607_session_setup_menu.md). Branch: `feat/session-setup-menu`.

Skills: `tdd` for T1 to T3. `/impeccable` for T4, with DESIGN.md's tokens. `code-review`, `/impeccable critique` and `break-ui` at rendezvous.

## OPEN QUESTIONS

None. The human approved each recommendation on 2026-10-30:

1. The two options live on New session only. They are chosen for each session and are off by default.
2. Automatic announce is a tick box, and a start time that shows when the box is ticked. Seats come from the table. The host can change seats on the "Who's coming" card.
3. Before set 1 opens, "Announce to the group" is primary and "Open set 1" is neutral until the session is announced. After that, "Open set 1" is primary.
4. A new session starts without chip values unless the host selects a chip preset on New session. ADR 0008 and the spec edit in T5 record this.

## Decisions that follow

- The chip preset list starts at "Set later". A stakes preset does not change it.
- The session keeps a copy of the preset's values, as ADR 0005 requires.
- A refused option creates nothing. The form keeps what the host typed and shows the reason.
- The home and group cards do not change. They still lead to the set page.

## Tasks

### T1: Go to the session page after creation

`tests: alongside`

- [x] `session_new` redirects to `night`.
- [x] Update `games/tests/test_sessions.py`, `games/tests/test_form_layout.py` and the browser scripts that continue after creation.

Acceptance: A host who selects Create session lands on the session page. The page shows the Announce card and the Chip values card.

Complete when: the suite passes and a signed-in browser probe lands on the session page.

### T2: Record a session creation once

`tests: first`

- [ ] Add nullable `GameNight.create_request_id` with a unique constraint on group and request ID. The migration adds a nullable field only.
- [ ] `create_session` returns the first set of the existing session when the request ID repeats.
- [ ] The form carries a `request_id` and `data-once`. A refused form keeps its ID.

Acceptance: Two posts with one request ID make one session. Two different request IDs make two sessions.

Complete when: the tests pass on SQLite and PostgreSQL, including a concurrent PostgreSQL test.

### T3: Apply the options in one transaction

`tests: first`

- [ ] `create_session` takes `chip_preset_id`, `announce` and `start_time`.
- [ ] A chip preset applies through `set_chip_values`, with the preset's name in the audit record.
- [ ] The announcement applies through `announce_night`, after the chip values.
- [ ] Refuse an archived preset, a preset of another group and a preset of the other unit. Each refusal creates no session and sends no notice.

Acceptance: Each option works alone and with the other. The replay from T2 sends no second notice.

Complete when: the service tests cover each case above, with a check that a refusal leaves no `GameNight` and no `Notice`.

### T4: Add the options to New session and fix the page hierarchy

`tests: alongside`

- [ ] `SessionForm` gets `announce`, `start_time` and `chip_preset`. Without active chip presets, the chip field does not show.
- [ ] Add one form group above Create session. The hint names how many players get a notice.
- [ ] `static/js/setup.js` lists only the presets of the chosen unit and resets a choice that no longer fits. Remove options, because iOS ignores hidden options.
- [ ] Without JavaScript, all presets show with their unit, and the server refuses a mismatch.
- [ ] Apply the answer to open question 3 on the session page.

Acceptance: The controls have 48 px targets and fit at 320, 390 and 1280 px. A change of unit, by hand or by stakes preset, updates the list. A player does not see the session until a host announces it.

Complete when: a browser probe creates a session with both options, a player account sees it and gets the notice, and a second probe confirms that a session without the options stays hidden.

### T5: Record the decision

`tests: alongside`

- [ ] Add ADR 0008. It extends ADR 0005.
- [ ] Update the Chip presets and RSVP lines of `doc/wiki/spec.md`.

Acceptance: The ADR and spec state the new rule, and nothing states the old one as current.

Complete when: a search for the old sentence finds it only in ADR 0005, with a pointer to ADR 0008.

## Completion

All tasks are ticked. Both test suites pass. The rendezvous checks are recorded here. `doc/wiki/features.md` and TODO.md's phone checks match the code.

## Rendezvous checks

Not run yet.

# Several new names at once on Add players: plan

Status: approved 2026-10-14 ("approved"): one form; refuse and offer; mark the arrivals. Built and released. Date: 2026-10-14, Asia/Manila. Study: [Several new names at once](../study/1791948615_new_names_at_once.md).

## Outcome

On Add players a host ticks regulars and types newcomers, one per line, and adds everyone with one button: "Add 5 players". Each new name becomes a roster player without a login and joins the set in the same action, or nobody is added and every problem is named. Back on the set, the players who just arrived rise into place with the brass mark.

Works on a draft, an open and a running set. Records no buy-in, as today. No migration. Built with the design (impeccable) and motion skills.

## What you will see

1. **Add players:** the roster list, then a "New names" box (one name per line). Under the box, each name with "New" or its problem.
2. **A name that is already a roster player:** "Ana is on the roster. Tick Ana instead"; one tap ticks her in the list and removes the line.
3. **The bar at the bottom:** "2 ticked · 3 new" and "Add 5 players". If that is more than the free seats, it says so before you send.
4. **A refusal:** the page comes back with your ticks and your typed names kept, and one message naming every problem.
5. **The set page:** the new rows rise into place one after another and carry the brass mark for three seconds.

## Decisions for the human

| # | Question | Recommended |
| --- | --- | --- |
| 1 | One form and one button for ticks and new names (study, option A), or keep the two forms and let the new-player form take several names (option B)? | A |
| 2 | A typed name that matches a roster player: refuse and offer "Tick … instead", or join that roster player automatically? | Refuse and offer. Two people can share a name, and joining the wrong one mixes their histories. |
| 3 | Mark the arrivals on the set page? | Yes |

## Implementation

Branch `feat/new-names-at-once` from `main`. Mode: Operate. Read impeccable's craft floor before the first edit.

1. **Service** `games.services.add_players(session_id, actor, member_ids, names, request_id)`: under the set's lock and the group's lock, check the typed names with the Group settings rules plus "already at the table", count ticks plus names against free seats, create the roster players, seat everyone through the existing path, one `ParticipantBatch`. All or nobody; the same `request_id` returns the first call's players. `add_new_player` and `add_participants` stay for their other callers.
2. **The name checks** in `groups.services` are shared, not copied: the part of `add_roster_players` that finds problems becomes a function both use, and its words stay the same.
3. **View** `participants_add`: one POST reads `member_id` and `names`. On refusal the ticks and the box are kept. On success the session remembers the new participants for one page view.
4. **Template** `add_players.html`: one form; the box after the list; the sticky bar counts both. The page's data for the preview (roster names, who is at the table, removed names) rides on the form as data attributes.
5. **Script** `static/js/pick.js`: the preview, "Tick … instead", the joint count and the button's words. The page works without it.
6. **Set page:** rows of the remembered participants carry `data-arrived`; a few lines in `flow.js` give them the rise and the brass mark, first keyframe first.
7. **`ROSTER_TOOLS=False`:** the box takes one name, as Group settings does with the switch off. No new switch.

## Checks

- **Django tests:** the service (mixed add, each clash named, several clashes in one message, seats counted across both, all or nothing, retry with the same `request_id`, removed names, the switch off, each set state); the view (refusal keeps ticks and names; success marks the arrivals once); the template (one form, one main button).
- **Browser check** `new_names.mjs` on a fresh database: the preview at 390 and 1280px, "Tick … instead", the joint count, a refusal, a mixed add, the arrival on the first frame and after, reduced motion, a 12-seat table filling up, no sideways scroll.
- **Existing checks:** `late_player.mjs`, `session_setup.mjs`, `roster.mjs`; `late_player.mjs` and `session_setup.mjs` post to this page and will need their selectors updated.
- One batched visual inspection at 390 and 1280px, one batch of fixes, one confirming round.
- SQLite and PostgreSQL suites.

## Acceptance

1. Ticking two regulars and typing three new names adds five players in one send; the three are on the roster without logins.
2. Any clash adds nobody, names every problem, and keeps what was ticked and typed.
3. A name already on the roster is offered as a tick before sending.
4. On the set page the five rows arrive with the mark; under reduced motion they carry the mark without moving.
5. Without JavaScript the same send works and the same refusals come back.

## Fail-safe

The writes reuse tested services inside one transaction, so a failure adds nobody. `ROSTER_TOOLS=False` takes the box back to one name without a release. The way back is a revert of the commit.

## Not covered

- Buy-ins for the new players: recorded on the set page as today.
- Contact notes for new names: added later in Group settings, as for Group settings' own several-names box.
- "Or add one player" under More host controls stays a single roster pick.

## Release

Kept local until you say to push.

## Progress

2026-10-14: built on `feat/new-names-at-once`, as planned.

- **Service.** `add_players` in `games/services.py`; the name checks became `groups.services.new_name_problems` and `create_roster_players`, which Group settings' `add_roster_players` now calls too, with its words unchanged. "Already at the table" is named apart from the rest of the roster. The seat message says "1 player", not "1 players".
- **Page.** One form; the roster, then "New players" with the "New names" box. A refusal that comes back after the set moved on or filled up keeps the ticks and the typed names and draws the form disabled.
- **Script.** `pick.js` previews each name, offers "Tick … instead", counts ticks and names against the seats, and holds the button while a name has a problem.
- **Set page.** The arrivals carry the brass mark and rise into place. **Found in the inspection:** on a phone the arrivals were scrolled into view behind the dock and its message. The page now scrolls them above the dock once the dock has measured itself, never past the first of them.
- **Browser checks updated:** `late_player.mjs`, `rake.mjs` and `rake_controls.mjs` type into the box; `late_player.mjs` reloads the page after turning scripts off, because the picker's script holds the button until something is chosen; `session_setup.mjs` looks for the new title.

Verification:

- 1,114 tests pass on SQLite (15 skipped) and on PostgreSQL 17, the race tests included (1,101 before). New: `games/tests/test_new_names.py` (12: a mixed send, every problem named at once, seats across both, a bad tick taking the names back, the retry, each set state, the switch off, a player refused, the arrivals marked once, the page's preview data, a refused tick keeping the names). The page tests in `test_new_player.py` were rewritten for one form.
- `new_names.mjs`: 18 of 18 at 390px, at 1280px and at 390px under reduced motion.
- `rake_controls.mjs` 25 passes, `session_setup.mjs` 21 of 21, `roster.mjs` 44 passes. `late_player.mjs` 19 passes and the same 2 failures as on `main`.
- Inspection: one batched round at 390 and 1280px (the preview with every problem, "Tick … instead", the arrival), one fix (the scroll above the dock), one confirming round. Captures in the study's assets folder.

Acceptance: 1 to 5 are met in headless Chrome; 5 by `late_player.mjs` with scripts off and by the Django tests.

Not verified: a real phone (the keyboard over the box, the scroll on arrival), a screen reader reading the preview and the bar, the in-app numpad (not used by this text box).

Documentation synced: DESIGN.md, PRODUCT.md, wiki (features, journal), roadmap, the browser checks' README, TODO.

2026-10-14, release: merged as `f51f4ac` and pushed on the human's word "release" (previous production commit `899a93e`). About four minutes after the push, one fetch of `/static/js/pick.js` returned the new script (it holds "Tick … instead"), and one fetch of the log-in page showed it under a new release tag. Not verified: the pages themselves on the live site, which need a login, and a real phone.

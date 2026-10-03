# Study: add several players to a game at once

- **Date:** 2026-10-03 23:34 (Asia/Manila), Unix timestamp `1791041698`
- **Request:** Let the host select several players and add them to a table's game in one action, next to the existing single-player flow.
- **Workflow:** `agentic-workflow`, Phase 1 of a new cycle. No code changes before approval of the plan.

Labels: **FACT** = verified today. **REC** = recommendation. **ASSUMED** = needs confirmation.

## 1. Intended outcome

A host opens "Add players" on a game, ticks several group members, sees how many are selected and how many seats are free, and confirms once. Each selected player joins the game, or none does.

Terms: the request says "poker table". In this app a table is reusable and has no players. Players join a **game** (session) at a table. This study uses "game".

## 2. Current state (FACT)

Repository: branch `main`, clean. No `doc/canonical/`. Both earlier plans have status `done`. `AGENTS.md` design rules apply.

| Item | Today |
|---|---|
| Single add | `games.services.add_participant(session_id, actor, member_id)`. A player joins for themselves, or a host adds one roster member |
| Screen | In the players card of the game page: a dropdown "Add from the roster" and an "Add" button (`templates/web/_players.html`). Players see "Join this game" |
| Who can add | A host of the group. A player can add only themselves |
| When | Host: game state `setup`, `open` or `running`. Player self-join: `open` or `running` |
| Who is eligible | An active member of the game's group, with or without a login |
| Capacity | `seat_count` of the game. Players with status `joined` count. The check runs under the session row lock |
| Duplicates | Unique `(session, member)`. Adding a member who is at the table returns the same row |
| Players who left or withdrew | A host can add them again. The existing row returns to `joined` |
| Record | One `Participant` row, one `AuditEvent` ("Added Ana"), and `GameSession.version + 1` for the live view |
| Live view | The game page polls each 4 seconds and replaces the live region when the version changes |

### Couplings checked

| Could adding a player also… | Finding |
|---|---|
| Create a buy-in or a cash-out | No. Only `ledger.services` writes those, and nothing calls it from the add path |
| Issue chips | No. Chips as a separate count no longer exist |
| Record a payment | No |
| Start a per-player timer | No. The app has no timers |
| Draw or assign a seat | No. Seat numbers are not built (roadmap Stage 4). Joining uses one unit of capacity; it gives no seat number |

No coupling exists. The new action must not add one.

### Guests

Players without a login exist as roster members (`Member` without a user). A host adds them on the group page, one name at a time. They are eligible for a game like any member, so they appear in the new list without extra work.

## 3. Options

### Where the picker lives

| Option | Pros | Cons |
|---|---|---|
| **A. Its own page**, linked from the players card | The live view's polling cannot wipe the ticks. Room for search and a review list on a phone. Works without JavaScript | One more page |
| B. A panel inside the live region | No navigation | Each poll re-renders the region. Ticks and the search text would be lost unless the live script learns to protect them |

**REC: A.**

### Search that keeps the selection

| Option | Pros | Cons |
|---|---|---|
| **A. Filter in the browser**: a small script hides rows that do not match. The checkboxes stay in the form | Ticks cannot be lost. No request per keystroke. A group roster is small | Needs JavaScript for search only. Without it the full list still works |
| B. Search on the server | No script | Each search reloads the page; the selection must travel in the URL |

**REC: A.**

### Retry of a successful request

| Option | Pros | Cons |
|---|---|---|
| **A. A `request_id` stored with a unique constraint** in a small `ParticipantBatch` row | A retry is recognized and shows the same success. Follows design rule 3 | One new table |
| B. No stored id | Nothing new | A retry finds each player "already at the table" and reports a conflict for an action that succeeded |

**REC: A.**

### Players already at the table in a submitted selection

| Option | Behavior |
|---|---|
| **A. Refuse the whole request** | Nobody is added. The page names the players that are now at the table and keeps the rest ticked for review |
| B. Skip them and add the rest | Not all-or-nothing. The host may not notice the change |

**REC: A**, as the request states.

## 4. Recommended design

### Screen

- The players card keeps the dropdown. It gains a button **"Add players"** for hosts in `setup`, `open` and `running`.
- The page **"Add players"** (`/s/<id>/players/add/`) shows:
  - "3 of 9 seats are free."
  - A search field with a label. Typing hides rows that do not match.
  - One row per active group member: a checkbox with the name as its label. Tags: "No login", "Left earlier".
  - Members at the table: listed, checkbox disabled, tag "At the table".
  - A review block: "Selected: Ana, Ben, Carlo, Dani" with the count, announced to screen readers.
  - If the selection is larger than the free seats: "Only 3 seats are free. Remove 1 player." The button is disabled.
  - The button text follows the count: "Add 4 players". Without JavaScript it reads "Add selected players".
- After success: back to the game page with "Added 4 players: Ana, Ben, Carlo, Dani."
- Native checkboxes and labels give keyboard use. Rows are full-width with 48 px height, as the stylesheet defines.

### Service

`games.services.add_participants(session_id, actor, member_ids, request_id)`, one transaction:

1. The actor must be a host.
2. Lock the session row.
3. If a `ParticipantBatch` with this `request_id` exists for the session, return its players. Nothing else happens.
4. The state must be `setup`, `open` or `running`.
5. The selection must not be empty. Repeated ids count once.
6. Each id must be an active member of the game's group.
7. No selected member can have status `joined` in this game.
8. The count must fit the free seats.
9. Create or reactivate each participant in list order, with the next `join_order` values.
10. Write one `ParticipantBatch`, one audit event per player (the same text as the single add), and one version increment.

Steps 5 to 8 raise an error that names the players and the numbers. Any error, and any failure in steps 9 and 10, rolls back the whole transaction.

The function writes `Participant`, `ParticipantBatch` and `AuditEvent` rows only. It calls nothing in `ledger` or `settlement`.

### Conflict

Another host changes the roster while the picker is open. On submit, the server refuses and the page shows again with:

- the reason, for example "Ben is already at the table. Nothing was added.";
- Ben's row now disabled with "At the table";
- the other ticks kept;
- the new seat count.

### Connected users

One version increment makes each open game page show the new roster at its next poll, within about 5 seconds. The picker page does not poll; the server check on submit covers a stale picker.

## 5. Guests: a separate scope decision

The request asks to assess typing several guest names in the same flow.

| Option | Detail |
|---|---|
| **A. Not in this change** | Roster players without logins already appear in the list. New names are added on the group page first |
| B. A "New players" box on the picker, one name per line | Each name becomes a roster member and joins the game in the same transaction. It needs name-clash rules inside the all-or-nothing check, and it creates group members from a game screen |

**REC: A now, B as a follow-up if wanted.** B is a second feature with its own rules. It uses the existing roster model; it needs no new guest-account system.

## 6. External inputs

None. No new dependency. One new small JavaScript file.

## 7. Risks

| Risk | Mitigation |
|---|---|
| Two hosts submit at once | The session lock. A threaded test on PostgreSQL |
| A partial group after a failure | One transaction. A test that forces a failure in the middle |
| The selection is lost by search | Rows are hidden, not removed. A browser check |
| The single flow changes by accident | Its tests stay unchanged and must pass |

## 8. Open questions

1. **Q1.** Guests: option A (not in this change) or B?
2. **Q2.** May a host re-add players who left or withdrew through this picker, as the single flow allows? (REC: yes, tagged "Left earlier".)

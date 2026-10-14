# Several new names at once on Add players: study

Date: 2026-10-14, Asia/Manila.

## Request

The human said: "lets add the feature where adding several new names at once during a set. make sure to use design and motion skills to refine this feature's implementation."

This is the roadmap's follow-up "New names in the player picker": type several new names, one per line, on Add players; each becomes a roster player without a login and joins the set in the same all-or-nothing action. The roadmap says it needs name-clash rules and its own plan, and that it uses the existing roster model, not guest accounts.

## What exists

Read from the code; the page was captured at 390px on 2026-10-13 (`doc/study/1791872138_session_setup_polish_assets/after-add-players-390.png`).

1. **Add players** (`games.views.participants_add`, `templates/games/add_players.html`) has two forms since 2026-10-13: the roster list with ticks and the page's main button, then "Add a new player" with one name field and its own button. Each form is its own request.
2. **One new name** goes through `games.services.add_new_player`: it creates the roster player (`groups.services.add_roster_player`) and seats them through `add_participants`, in one transaction, with one `request_id`. Clashes are refused with a recovery: a removed name says to bring them back in Group settings; a name already in the group says to choose them from the roster, or that they are already at the table.
3. **Several roster players** go through `add_participants`: all or nobody, re-checked under the set's lock, seats counted, the same `request_id` returning the first call's players.
4. **Several new names in Group settings** already exist (`groups.services.add_roster_players`, 2026-10-09): one name per line, up to 30, every problem named at once (already in the group, typed twice, removed, too long), all or nobody. `static/js/roster.js` counts the names as they are typed. `ROSTER_TOOLS=False` turns it back into one name at a time.
5. **Where a set can take players:** draft, open and in play (`HOST_ADD_STATES`). A set has at most 12 seats, so the seats left, not the 30-name limit, decide how many names fit.
6. **Arrival on the set page:** after adding, the host is sent back to the set with a message ("Added 3 players: …"). The new rows appear with no mark. When rows arrive by a live update instead, `flow.js` already lets them rise into place 40ms apart. Group settings marks rows a host just added with the brass mark and the same rise (`roster.js`, `data-arrived`).

## What is missing

- Several new people at once: today a host types one name, sends, comes back, types the next. Three newcomers are three round trips through two pages each.
- One action for a mixed table: regulars ticked from the roster plus newcomers typed in. Today these are two separate sends, and the seat count of one does not know about the other.
- A mark on the set page for who just arrived.

## Clashes, and the rule for each

| Typed name | Today, one name | Proposed for several |
| --- | --- | --- |
| Already a roster player, not at the table | Refused: "Choose that player from the roster instead." | Refused and named. The page's preview says it before sending and offers to tick that player in the list. Auto-ticking was considered and rejected: two different people can share a name, and joining the wrong one moves a newcomer's results into a regular's history, which only the site administrator can untangle. |
| Already at the table | Refused: "They are already at the table." | Refused and named. |
| A removed player | Refused: bring them back in Group settings. | Refused and named, with the same recovery. |
| Typed twice | — | Refused and named. |
| Longer than 60 characters | Refused. | Refused and named. |
| Blank lines, extra spaces | — | Ignored, as in Group settings. |
| More people than free seats | Refused. | Refused with both counts: ticks plus names against seats. |

Every problem is named in one message, and nothing is added until there is none, as in Group settings.

## Design (impeccable, Operate mode)

The Rack is the visual authority. The page's job is a host at the table adding the people who just sat down, with one hand, between hands.

- **One form, one button.** The roster ticks and a "New names" box in one form, so the sticky bar counts both and its button names the total: "Add 5 players". This removes the page's second button (the 2026-10-13 polish made it an ordinary button; it would go).
- **The box.** A text area, one name per line, the same words and limits as Group settings, starting two lines tall and growing with what is typed (`field-sizing: content` where the browser has it; a fixed height elsewhere).
- **The preview.** Under the box, each typed name as a line with a written state: "New" in the muted voice, or the problem in the refusal colour with its recovery. A name that is a roster player gets "Tick Ana instead", which ticks her in the list above and removes the line. The preview is a convenience; the server checks everything again.
- **Seats.** The existing capacity line and warning count ticks and names together.
- **Without JavaScript** the box still works: the server reads the lines and refuses or adds.

## Motion (motion skill)

One authored moment, as the craft floor asks: the arrival on the set page.

- **Arrival.** The rows of the players just added rise 12px into place 40ms apart and carry the brass "just changed" mark for three seconds, the same values as `flow.js` and `roster.js`. The first keyframe is written before Motion starts (footgun `motion_starts_a_frame_late.md`). It runs once: the mark comes from the session and is gone on the next poll.
- **The preview.** A new line fades in (the `fade` preset, 180ms); nothing moves sideways while the host types. A removed line just goes.
- **"Tick Ana instead".** The row in the list gets the same brass mark, and the list scrolls to it if it is out of sight; no other movement.
- **Reduced motion:** the marks stay, the movement goes.

## Options

| Option | For | Against |
| --- | --- | --- |
| A. One form: ticks and new names together, one button | One send for a mixed table; one seat count; the page has one main action | The page changes shape again a day after the polish |
| B. Keep two forms; the new-player form takes several names | Smallest change | A mixed table is still two sends, and each send's seat count ignores the other |
| C. Names typed on the set page itself | No page change | The set page fits one phone screen on purpose; a text area there breaks that |

Recommended: A.

## Risk

Every write goes through services that exist and are tested: roster creation and seating, all or nothing, one `request_id`. The new part is one service that does both in one transaction, and the page around it. No migration.

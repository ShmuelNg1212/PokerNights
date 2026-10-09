# Roster management: plan

Status: approved 2026-10-09 ("approved."); all eight decisions as recommended. Date: 2026-10-09, Asia/Manila. Study: [Roster management](../study/1791525548_roster_management.md).

## Outcome

A host keeps the group's player list in order from Group settings → Players: removing someone is asked first and can be undone with their history intact, several names go in at once, and each row says how often the player comes. Anyone with a login fixes their own name.

Mode: Operate. Visual authority: the built Rack in DESIGN.md (confirmation pages, archived lists, form fields). No new colour, font, asset or motion. No migration.

## Behaviour

### 1. The Players list

Each row keeps the token, the name and the Host and No login badges, and gains one muted line under the name:

> 12 sessions · last played Oct 1

or "No sessions yet". A session counts as it does in Stats: closed, not archived, with a counted result, once per session, across pesos and chips games. Every member sees this line.

### 2. Change your own name

Your own row gets a closed disclosure **Change your name**, for a host and for a player:

- Field **Name**, with your current name in it.
- Help: "This is your name in {group}. You still log in as **{username}**."
- Button **Save**. Success: "Your name is now {name}."

The name rule is today's: 1 to 60 characters, and no other active player in the group has it (capitals ignored). A refused name stays in the field beside its error.

### 3. Manage another player (hosts)

"Manage {name}" keeps Make host or Make player and the reset link. Two things change:

- Rename becomes one form with **Name** and **Contact (optional)** and one **Save** button. Contact is free text up to 120 characters, for example a phone number. Only hosts see it.
- **Remove from group** opens a confirmation page and no longer removes on the first tap.

### 4. Removing a player

The confirmation page uses the 560px form page:

- Back link to Group settings → Players.
- Heading **Remove {name} from the group?**
- What happens:
  - "{name}'s results stay in past sessions and in Stats."
  - "{name} can't be added to a set."
  - With a login: "{name} can no longer open this group. Their account and their other groups are not touched."
  - "You can bring {name} back from Removed players."
- If {name} has unpaid transfers, a panel **Still to pay** lists each one ("Ben pays Ana ₱500 · Oct 1, Main table") and says "These stay on their session pages. Removing {name} does not settle them."
- Danger button **Remove {name}** and a quiet **Keep {name}**.

When removal is not allowed the page says why and shows only the back link:

| Case | Message |
|---|---|
| At the table of a set that is not finished | "{name} is at the table in {table} set {n}. Take them off that set or finish it first." with a link to the set |
| The only host | "A group needs at least one host. Make someone else a host first." |

After removing: back in Players with "{name} was removed. Bring them back from Removed players."

### 5. Removed players

At the end of the Players panel, for hosts, a closed disclosure **Removed players (N)** under a Line rule. Each row has the token, the name, the No login badge where it applies, the same activity line and a **Bring back** button.

Bringing back makes the member active again as a player, with every past result still theirs. Success: "{name} is back in the group." A member with a login can open the group again at once. A former host comes back as a player.

If another active player now has that name, the member comes back under the next free name and the message says so: "{name} is back as {name} (2), because another {name} is in the group. Rename either one."

### 6. Adding several players

"Add a player without a login" becomes **Add players without a login**:

- One box **Names**, one name per line. One name still works.
- Help: "One name per line, up to 30. They join the roster without a login."
- Button **Add to roster**. Success: "Added 4 players." or "Player added."

Everyone is added, or nobody is. Blank lines are skipped. The box keeps what was typed when anything is refused, and the error names every problem at once:

| Problem | Message |
|---|---|
| A name an active player has | "Already in this group: Ben, Dani." |
| A name typed twice | "Typed twice: Ana." |
| A name a removed player has | "Removed from this group: Carlo. Bring them back from Removed players, or use a different name." |
| A name over 60 characters | "Too long (60 characters at most): {the first 20 characters}…" |
| More than 30 names | "Add 30 players at most at a time." |

The removed-name rule also applies to the new-name field on a set's Add players page, which says: "Carlo was removed from this group. Bring them back in Group settings, then add them here."

### 7. Switch

`ROSTER_TOOLS=False` in Vercel turns the new tools off without a release: the Players section shows as it does today (one-name add, no own name, no contact, no activity line, no Removed list) and the new services refuse. The removal confirmation page and its checks stay on, because they are the safe path and need no JavaScript. Default on.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise. The reasons are in the study.

1. **A player at the table of an unfinished set cannot be removed.** The alternative is a warning that still allows it.
2. **A player with unpaid transfers can be removed**, after the page shows the transfers. The alternative is to refuse until they are paid.
3. **A removed player's name cannot be added again as a new player.** The host brings the player back, or uses a different name for a different person. This changes one current behaviour: today the same name can be re-added and the history splits.
4. **A restored player whose name is now taken comes back as "{name} (2)".** The alternative is to refuse until the host renames someone.
5. **Anyone with a login can change their own name in the group.** The audit log records each change with the old name. The alternative is hosts only.
6. **Only hosts see the contact note.**
7. **Bringing back a former host makes them a player.** A host makes them a host again if wanted.
8. **The wording** in sections 1 to 6. Change any of it.

## Implementation

Tests are written first for each step. The app direction holds: `groups` imports neither `games` nor `settlement`.

1. **`groups/services.py`.**
   - `REMOVE_GUARDS = []`: `guard(member)` raises `RuleError`. Same idea as `ARCHIVE_GUARDS`.
   - `removal_refusal(actor, member_id) -> str | None`: the reason removal is not allowed, for the confirmation page. Read-only.
   - `remove_member`: after the group lock, lock the member row with `select_for_update()`, run the guards, then mark removed. A repeat on a removed member changes nothing and writes no audit event.
   - `restore_member(actor, member_id) -> (member, old_name)`: host only, group lock, the member must be removed and in the actor's group; role becomes player; `_free_name` settles a clash before the status changes; `audit.record("member.restored")`. A repeat on an active member changes nothing.
   - `rename_self(actor, name)`: the actor's own row, group lock, the name rule, `audit.record("member.renamed")`.
   - `edit_member(actor, member_id, name, contact)`: replaces `rename_member`. Host only. Writes only the fields that changed and one audit event that says which ("Renamed Ben to Benjie", "Changed Ben's contact note"). The contact text is not copied into the audit summary.
   - `add_roster_players(actor, names) -> list[Member]`: host only, group lock, clean every name, collect every problem in section 6 into one `RuleError`, then create all rows and one audit event per member.
   - `add_roster_player` gains the removed-name refusal and stays the single-name entry that `games.add_new_player` calls.
   - With `ROSTER_TOOLS` off: `restore_member`, `rename_self`, a contact change and more than one name are refused with "This is turned off."
2. **`games/services.py` and `games/apps.py`.**
   - `guard_member_removal(member)`: refuses when the member has a `Participant` with status joined in a set whose state is in `UNFINISHED_STATES`. Registered in `ready()` beside the archive guard.
   - `add_participant`, `add_participants` and the return-to-set path read their member rows with `select_for_update()`. Lock order is set, then group, then member on every path; removal takes group, then member and never a set. This closes the race in the study.
   - `add_new_player` gives the removed-name refusal its own recovery sentence (section 6).
3. **`settlement/queries.py`.** `roster_activity(member_ids) -> {member_id: (sessions, last_date)}` over `counted_results()`, one query for the whole roster, units together.
4. **Views and addresses.**
   - `web/views.py`: `member_remove` moves here from `groups`, because the page needs `settlement.queries.unpaid_transfers`. GET shows the confirmation or the refusal; POST removes. Same address and name (`g/<group>/members/<member>/remove/`). Both resolve through `member_for`; a non-host gets the existing 403.
   - `groups/views.py` and `urls.py`: `member_restore` (POST), `member_rename_self` (POST `g/<group>/me/name/`), `member_edit` replaces `member_rename` at the same address, and `member_add` reads the Names box.
   - `group_settings_context` adds the activity for every row, the removed members for a host, the own-name form, and the name-and-contact form per member. The tab's query count stays fixed as the roster grows.
5. **Forms (`groups/forms.py`).** `MemberForm` (name, optional contact) and `NamesForm` (a textarea). `NameForm` stays for the own name and group names.
6. **Templates.** `web/_group_settings.html` (sections 1, 2, 3, 5, 6, with today's markup kept under the switch) and a new `web/member_remove.html` in the confirmation-page pattern, reusing the unpaid-transfer panel of the session archive page. CSS only if the activity line or the textarea needs a rule that the existing classes do not give.
7. **Setting.** `ROSTER_TOOLS = env.bool("ROSTER_TOOLS", default=True)`.
8. **Tests.**
   - `groups/tests/test_roster.py`: restore keeps the same member row and its results; restore of a login member, of a former host, of a clashing name, of a member of another group (refused), by a player (refused), repeated; removal of the last host, repeated removal; own rename by a host and by a player, a clash, a blank; edit of name only, contact only, both, neither; several names added, each problem in section 6 alone and together, all-or-nothing, 30 and 31 names; the removed-name refusal, replacing today's re-add assertion; each audit event carries the group; the switch off.
   - `games/tests`: the removal guard for each unfinished state and for joined, withdrawn and left; a finished or canceled set does not block; the removed-name message on the set's Add players page.
   - `settlement/tests/test_stats.py`: `roster_activity` agrees with `group_stats` on which sessions count, counts a two-unit player once per session, ignores archived and unclosed sessions, and runs in one query.
   - `web/tests`: the confirmation page for a clean player, with unpaid transfers, when seated and for the only host; POST removes and GET never does; a player gets 403 and another group's host 404; the Removed list and the contact field appear for hosts only; the own-name disclosure appears on your own row only; refused forms keep their typing and open their disclosure; the settings tab's query count does not grow with members or removed members; the switch off renders today's section.
   - PostgreSQL only: removal and seating of the same member at once (never both), two restores at once, two hosts adding the same names at once (one wins, no duplicate).
   - Browser check `roster.mjs` with a seed, at 320, 390 and 1280px: add three names in one go, a refused batch keeps its text, change your own name, save a contact note, open the removal page with unpaid transfers, remove, bring back; 48px targets, contrast, visible focus, no horizontal overflow, every action working without JavaScript.
9. **Verify.** SQLite and PostgreSQL suites. `roster.mjs`, then `archive.mjs` and `late_player.mjs`, which share the confirmation pattern and the add service. Captures inspected. A design critique of the Players section against DESIGN.md, with every P1 fixed before release.
10. **Sync docs.** Wiki features and architecture (the guard, the lock order, the new services), deployment (the switch), DESIGN.md addendum, PRODUCT.md addendum, roadmap Stage 2, TODO. SPEC.md is the human's.

Work is done on branch `feat/roster-management` with Conventional Commits, in this order: restore and safe remove, own name, details, several names. Each is usable on its own and the tests pass after each. Nothing is pushed without an instruction.

## Acceptance criteria

- AC1. Removing a player takes a confirmation page that states what happens and lists their unpaid transfers. Opening the page removes nobody.
- AC2. A player at the table of an unfinished set cannot be removed, in the page or by a direct request, and cannot be seated and removed at the same moment (PostgreSQL).
- AC3. A host brings a removed player back, with or without a login, and their past results and Stats are the same member's as before.
- AC4. A name that belongs to a removed player is not created as a second player, in Group settings or at the table.
- AC5. A host and a player each change their own name. No two active players in a group share a name, however the names were set.
- AC6. A host saves and reads a contact note. A player never sees one.
- AC7. Each roster row shows sessions played and the last date, and the count matches Stats for all time.
- AC8. A host adds up to 30 names in one action. One bad name adds nobody and the typed text is kept.
- AC9. Every new write is refused for a non-host where it is a host action, returns 404 across groups, and leaves an audit event.
- AC10. `ROSTER_TOOLS=False` restores today's Players section without a release.
- AC11. No migration. Existing tests pass on SQLite and PostgreSQL after the one listed change to the re-add test.

## Out of scope

- Claim links and merging two member rows.
- Several new names on a set's Add players page.
- A player leaving a group by themselves.
- Search, sort or filters on the roster.
- Showing when or by whom a player was removed (the audit log has it).
- The rest of Stage 2: history list, banker, payments before finalization, reopening.

## Rollback

Set `ROSTER_TOOLS=False` in Vercel for an immediate stop of the new tools. To remove the code, revert the feature commits; there is no migration to reverse. Names changed, notes saved and players restored or removed stay as they are.

## Progress and blockers

2026-10-09: Study and plan complete. The human chose the scope (all four parts) the same day. Waiting for the human's approval of this plan. No code written.

2026-10-09: The human approved with "approved."; all eight decisions as recommended. The human added: "make sure to refine the UI elements along the way as well. use the necessary skills and plugins for UI design and dynamic animations."

Change from the plan: the Outcome said "No new colour, font, asset or motion". With the human's addition, the Players section is refined within DESIGN.md's tokens, and motion is added with the app's existing Motion setup and its reduced-motion rule. No new colour, font or asset. What was refined and animated is recorded below when built.

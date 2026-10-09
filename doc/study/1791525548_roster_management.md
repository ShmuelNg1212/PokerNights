# Roster management: study

Date: 2026-10-09, Asia/Manila.

## Request

The human asked to start the study and plan for roster management, the first item of roadmap Stage 2 ([roadmap](../roadmap/README.md)) and `SPEC.md` step 4 ("Saved player roster for fast session setup"). The Stage 1 plan left it as "Roster management pages beyond add and rename" ([plan](../plan/1791037623_poker_home_game_architecture.md)).

Asked which gaps to cover, the human chose all four offered on 2026-10-09:

1. Safe remove and restore.
2. Player details (the contact note, sessions played, last played).
3. Change your own name.
4. Add several names at once in Group settings.

## What exists today

Group settings → Players (`templates/web/_group_settings.html`, `groups/services.py`):

- Lists the active members alphabetically, with Host and No login badges.
- A host adds one player by name without a login (`add_roster_player`), renames another member (`rename_member`), makes a member with a login a host or a player (`set_role`), creates or cancels a password reset link, and removes a member (`remove_member`).
- A set's Add players page adds roster players in bulk and one new name at the table (`games.services.add_participants`, `add_new_player`).
- Results, transfers and payments point at `Member` with `on_delete=PROTECT`. A member row is never deleted; "removed" is `Member.status`.
- Stats keeps a removed player's history (`settlement/tests/test_stats.py`). Your groups drops the group for a removed person (`web/tests/test_home.py`).

## Gaps found in the code

**Remove**

- One tap, no confirmation. The button sits in the same block as Rename and Make host.
- No check at all. A host can remove a player who is seated in a running set, or who still owes or is owed money. The set and the transfers keep the row, but the player can no longer be added back to a set, and a player with a login gets a 404 on the group while a transfer with their name is unpaid.
- One-way. No screen lists removed members and no service restores one. A removed person with a login can come back only with an invite link (`accept_invite` reactivates the row). A removed player without a login cannot come back at all.
- Adding the same name again creates a second `Member`, so that person's history is split in two in Stats. Nothing merges members. `groups/tests/test_roster.py` asserts this re-add works today.
- The race: `add_participants` and `add_participant` read the member's status without locking the member row, and `remove_member` locks only the group. A removal and a seating at the same moment can both succeed.

**Names**

- "Manage" is hidden on your own row (`m.pk != me.pk`). A host cannot rename themself from the screen, and a player cannot change their name at all. A member's name starts as their username.
- A name is per group (`Member.display_name`). The username used to log in is separate and is not changed by a rename.
- Every screen reads the name from the member row, so a rename also changes how past results read. The audit event keeps the old name.

**Details**

- `Member.contact` (120 characters) exists and the add service accepts it, but the add form has no field for it and no screen shows or edits it.
- A roster row says nothing about the player: not how many sessions they played or when they last came.
- `settlement.queries.counted_results()` already defines which results count for statistics: current results of finalized sets in closed, unarchived sessions.

**Adding**

- One name per submit in Group settings.

## Constraints

1. **App direction** (AGENTS.md rule 11): `groups` cannot import `games` or `settlement`. A check that needs seats must be registered into `groups` by `games`, as `ARCHIVE_GUARDS` is. A page that shows unpaid transfers must be built in `web`.
2. **Only services write, each write is audited** (rules 2 and 6). Group writes lock the group row. They do not touch a `GameSession`, so there is no version to increment; a set page on another phone shows a new name at its next update, as with today's rename.
3. **`request_id`** (rule 3). Group writes carry none today (invites, add, rename). Each new write here is safe to repeat without one: a second remove or restore changes nothing, and a second add of the same names is refused by the name rule.
4. **Money records are append-only** (rule 4). Removing a member touches no money record. A member with records is never deleted.
5. **Missing locks pass on SQLite** ([footgun](../wiki/footguns/sqlite_hides_missing_locks.md)). The remove-against-seating race needs a PostgreSQL test.
6. **Partial unique constraints are not deferrable** ([footgun](../wiki/footguns/partial_unique_constraints_are_not_deferrable.md)). `member_active_name_unique` covers active rows only. A restore that would clash must be settled in the service, under the group lock, before the row turns active.
7. **A form per row loses typing** ([footgun](../wiki/footguns/one_form_per_row_loses_typing.md)). Each "Manage" block is its own form. They are opened and saved one at a time, so one form per member stays; name and contact share that one form and one Save.
8. **No preview deployments.** The human tests on the live site. The change needs a switch that turns it off without a release, and the safety parts must not depend on JavaScript.
9. **Design.** DESIGN.md already defines the pieces: confirmation pages on the 560px form page with a panel of unpaid transfers, and closed "Archived … (N)" disclosures for hosts. No new colour, font, asset or motion is needed.

## Options

**Removing a player who is at the table of an unfinished set**

- **A. Refuse, and say which set (recommended).** The host takes the player off the set or finishes it first. Nothing odd can follow.
- **B. Warn and allow.** The set finishes with a removed player in it. Bringing a "Left" player back into that set is then refused, which a host would meet mid-game.

**Removing a player with unpaid transfers**

- **A. Show them on the confirmation page and allow (recommended).** The transfers stay on their session pages and in "Still to pay". A group must be able to drop a player who will not pay.
- **B. Refuse until every transfer is paid.** Leaves a host unable to remove someone who has gone.

**A restored name that another active player now uses**

- **A. Restore under the next free name, "Ben (2)", and say so (recommended).** This is what `accept_invite` already does for a returning member. The host renames either one after.
- **B. Refuse until the host renames the active player.** Clearer, but the host must leave, rename, and come back.

**Adding a name that a removed player has**

- **A. Refuse and point to Removed players (recommended).** A silent second row splits a person's history for good, because nothing merges members. A different person with the same name gets a different name ("Ben S").
- **B. Keep today's behaviour.** Nothing stops the split.

Option A also reaches the set's Add players page, which calls the same service: a host at the table is told to bring the player back in Group settings first.

**Who can change a name**

- **A. A host renames anyone; anyone with a login renames themself (recommended).** The name rule and the audit event apply to both.
- **B. Hosts only, including their own row.** Smaller, but every player depends on a host for a typo.

**Who sees the contact note**

- **A. Hosts only (recommended).** It is a note a host typed about someone, often a phone number.
- **B. Every member.**

**What "sessions played" counts on a roster row**

- **A. The Stats rule, across both units (recommended):** closed, unarchived sessions with a counted result, each once, with the date of the latest. The roster and Stats then never disagree.
- **B. Any set the player joined.** Includes canceled and unfinished sets, and would not match Stats.

**Where several names are typed**

- **A. One box, one name per line, replacing the single-name field in Group settings (recommended).** One name still works. Everyone is added, or nobody is.
- **B. A second form beside the first.** Two ways to do one thing.

**Recording when a member was removed**

- **A. No new column (recommended).** The audit log has the event. The Removed list sorts by name and shows the same activity line as the roster. No migration.
- **B. Add `removed_at`.** One migration for one muted date.

## What stays outside this cycle

- Claim links: joining a player without a login to a real account (roadmap Stage 5), and merging two member rows.
- Typing several new names on a set's Add players page so they also join the set (roadmap follow-up). This cycle's box is in Group settings.
- A player leaving a group by themselves.
- Search, sort or filters on the roster.
- Deleting a member row.
- The rest of Stage 2: the history list, a banker, payments before finalization, reopening a finalized set.

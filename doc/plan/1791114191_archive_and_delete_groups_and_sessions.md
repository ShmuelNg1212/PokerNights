# Archive and delete groups and sessions: plan

Status: approved 2026-10-04 ("im fine with the defaults. proceed"). Date: 2026-10-04, Asia/Manila. Study: [Archive and delete groups and sessions](../study/1791114128_archive_and_delete_groups_and_sessions.md).

## Outcome

A host can clear away a session or a group that should no longer be on the lists.

- **Archive** hides it and takes it out of the totals. It can be restored.
- **Delete** removes it for good. It is offered only when no money was ever recorded in it.

Money records are never removed. A session or group with any buy-in, cash-out or payment can be archived and cannot be deleted.

## Decisions for the human

Each has a recommended answer. Approving the plan accepts the recommendations unless you say otherwise.

1. **Delete only when there is no money.** Recommended. A session with any recorded buy-in (even a reversed one) can only be archived. The alternative, deleting money records, breaks the append-only rule and lets a host erase a debt.
2. **What archiving a session does to the totals.** Recommended: an archived session is out of the books. It leaves the stats, each player's record, "To settle" on the home page and the group rake total, and comes back when restored. This is what lets you clear a test session that has invented buy-ins. The alternative keeps archived sessions in the totals and only hides them from the list.
3. **Archiving a session with unpaid transfers.** Recommended: allowed, after a confirmation that lists who still owes whom. The alternative refuses until every transfer is marked paid.
4. **When archiving is refused.** Recommended: while any set of the session is a draft, open, in play or counting up. Finish or cancel it first. A group cannot be archived or deleted while one of its sessions is in that condition.
5. **Who.** Recommended: any host of the group, as for every other host action. There is no owner role.
6. **What an archived group looks like.** Recommended: it disappears from Your groups for every member. Its pages return "not found" and its invite links stop working. Hosts get an "Archived groups" list at the bottom of Your groups with a Restore button. Memberships and all records are kept.
7. **What an archived session looks like.** Recommended: it leaves the group's Sessions list and the home page. Hosts get an "Archived sessions" list at the bottom of the Sessions tab. Its pages stay readable to group members who have the link, marked "Archived", with no action other than a host's Restore.
8. **Delete confirmation.** Recommended: a separate page that names what will be removed and asks the host to type the group name (for a group) before the button works. A session delete asks for one confirmation without typing.
9. **Single sets.** Recommended: not in this cycle. A set without money can already be canceled.

## Behaviour

### Session

| Condition of the session | Archive | Delete |
|---|---|---|
| A set is a draft, open, in play or counting up | No | No |
| No money row in any set (all sets canceled, or never used) | Yes | Yes |
| Has money, not closed (sets finalized) | Yes | No |
| Closed, transfers all paid or none | Yes | No |
| Closed, transfers unpaid | Yes, after the confirmation in decision 3 | No |

- **Archive session** and **Delete session** sit in a "Manage this session" disclosure at the bottom of the session page, for hosts. Each explains in one sentence why it is or is not available.
- **Archived**: the session page shows an "Archived on … by …" notice and, for a host, **Restore session**. Every other action is absent, and every write service refuses.
- **Restore** puts the session back exactly as it was, open or closed, with its transfers and payments.
- **Delete** removes the session, its sets, players, timers and settings. The audit events stay. The host lands on the group page with a confirmation message.

### Group

- **Archive group** and **Delete group** sit in a "Manage this group" section at the bottom of Group settings.
- **Archive** is refused while a session has a set in play or counting up. Otherwise the group leaves Your groups for everyone.
- **Restore** from the host's "Archived groups" list on Your groups.
- **Delete** is offered only when no session of the group has a money row. It removes the group, its members' memberships (not their accounts), tables, presets, invites and empty sessions.
- A host who deletes or archives their only group lands on Your groups, which shows the create-group form as it does for a newcomer.

### Everywhere

- Dates of archiving use Asia/Manila. Wording uses Session and Set as on the rest of the app.
- All actions are native forms that work without JavaScript. Buttons are 48 px; Delete uses the danger style.

## Implementation

Two slices, each committed after the full suite passes.

### Slice 1: sessions

1. **Model and migration (`games`).** `GameNight.archived_at` (nullable datetime) and `archived_by` (nullable, `PROTECT`). Replace the index `night_group_status_date` with one that serves "active sessions of a group".
2. **Services (`games/services.py`).**
   - `night_has_money(night)`: any buy-in, count, cash-out, override or finalization under its sets, or a plan or payment on the session. Uses reverse relations; no import from `ledger` or `settlement`.
   - `archive_night(night_id, actor, confirm_unpaid=False)`, `restore_night(night_id, actor)`, `delete_night(night_id, actor)`. Each: `require_host`, `lock_night`, rule checks from the table above, write, `audit.record`, bump the version of every set (archive, restore). A repeat of archive or restore is a no-op.
   - `delete_night` deletes sets, then the session, inside the transaction. It records the audit event with the table name, date and set count in `data`, since the target row will be gone.
   - `lock_night` and `lock_session` refuse with a `RuleError` when the session is archived. `restore_night` uses its own lock. This one change closes every existing write service to archived sessions.
3. **Queries.** Exclude archived sessions in `web.views.visible_nights`, `web.home.home_cards`, `settlement.queries.counted_results`, `unpaid_transfers`, `session_nets` where it feeds the home card, and `ledger.queries.group_rake`. One shared filter where the app direction allows.
4. **Views and URLs (`games`).** `POST n/<id>/archive/`, `POST n/<id>/restore/`, `GET/POST n/<id>/delete/` (GET is the confirmation page). The unpaid-transfer confirmation is a GET page that lists the transfers and posts with `confirm_unpaid`.
5. **Templates.** `night.html`: the notice, the manage disclosure, and no actions when archived. `_group_sessions.html`: the host's "Archived sessions" disclosure. `session.html` and partials: the archived notice and no host dock. A confirmation template.
6. **Tests first.**
   - Services: each row of the table; non-host refused; other group's session is 404; repeat is a no-op; every existing write service refuses on an archived session (one parametrised test over buy-in, cash-out, count, transition, next set, close, mark paid).
   - Queries: stats, records, months, "To settle", rake total and both lists exclude an archived session and include it again after restore, in pesos and chips.
   - Delete: the rows are gone, audit events remain, and a session with a reversed buy-in is refused.
   - Database: a direct `night.delete()` with money raises `ProtectedError` on both engines.
   - Concurrency (PostgreSQL): archive racing a buy-in; one waits for the lock and then sees the other's result.
   - Live page: the state endpoint of an archived or deleted set gives the page a reload, not an error.

### Slice 2: groups

1. **Model and migration (`groups`).** `GameGroup.archived_at`, `archived_by`.
2. **Access (`groups/access.py`).** `member_for` returns 404 for an archived group. A separate lookup serves restore and delete for hosts.
3. **Services.** `groups.services.archive_group` and `restore_group` (lock the group, check via a hook that no session is live, audit). `games.services.delete_group`, because it must remove sets, sessions, tables and presets before the group (study, constraints 3 and 5); it also removes the rake account when it has no entries, the invites and the memberships.
4. **Other effects.** `accept_invite` and `usable_invite` refuse for an archived group. `home_cards` skips archived groups and returns the host's archived ones separately.
5. **Views, URLs and templates.** `POST g/<id>/archive/`, `POST g/<id>/restore/`, `GET/POST g/<id>/delete/` with the typed-name confirmation. `_group_settings.html`: the manage section. `home.html`: the "Archived groups" disclosure.
6. **Tests first.** Service rules; 404 on every group, session and set URL of an archived group for a host and a player; invite refused; home lists; restore; delete with and without money; delete leaves user accounts and the audit log; concurrency on PostgreSQL for archive racing a new session.

### Both slices

- **Verify.** SQLite and PostgreSQL suites. Migration applied forward on a copy of a database with data, and checked for drift. A browser check script at 320, 390 and 1280 px for the new sections, the confirmation pages, both archived lists, no-JavaScript submission, long names and focus. Query counts on the home and group pages stay within the budget recorded in the home plan.
- **Sync docs.** Wiki features and architecture, PRODUCT.md, DESIGN.md addendum for the new sections, the browser README, TODO.md, the roadmap's decision list. SPEC.md is not edited; a "Waiting for the human" item notes that it does not mention archive or delete.

## Acceptance criteria

- AC1. A host can archive and restore a session; after archive it is absent from the Sessions list, the home page, stats, records, "To settle" and the rake total; after restore all of these match their values before.
- AC2. A host can delete a session that has no money row, and cannot delete one that has, through the screen or by posting to the URL.
- AC3. No write of any kind succeeds on an archived session other than restore.
- AC4. A host can archive and restore a group; while archived, no member can open any of its pages and its invite links refuse.
- AC5. A host can delete a group with no money row after typing its name; user accounts and audit events remain.
- AC6. A player cannot archive, restore or delete anything, and sees no control for it.
- AC7. No money row is deleted or changed by any of these actions; the database refuses a delete that would do so.
- AC8. Each action writes an audit event with the actor.
- AC9. Existing tests pass on SQLite and PostgreSQL.

## Out of scope

- Archiving or deleting a single set.
- Deleting money records, or a "purge" of an archived group.
- Reopening a closed session (roadmap, Stage 2).
- An owner role, or transferring a group.
- Screens for archiving tables and presets.
- Deleting a user account.

## Rollback

Revert the feature commits and migrate `games` and `groups` back one step each; the columns are nullable and hold no money data. Rows already deleted through the feature cannot be brought back, by design.

## Progress and blockers

2026-10-04: Study and plan complete. The human approved with “im fine with the defaults. proceed”; all nine decisions stand as recommended.

2026-10-04 execution on `feat/archive-delete`, two feature commits, each after the full SQLite suite.

1. `9881967` sessions: migration `games.0012_night_archive`, services, the write gate in `lock_night` and `lock_session`, query filters, views, pages.
2. Groups: migration `groups.0004_group_archive`, `member_for` 404, services, `delete_group`, views, pages.

Changes from the plan:

1. **The session views and URLs are in `settlement`, not `games`.** The archive confirmation lists unpaid transfers, which `games` may not import.
2. **The money check is a registry** (`games.NIGHT_RECORD_CHECKS`, filled by `ledger` and `settlement`), not reverse relations. It follows the existing `SESSION_MONEY_CHECKS`.
3. **Every action has a GET confirmation page and a POST.** The plan gave archive a direct POST with an extra page only for unpaid transfers; one page for all cases is simpler and always states the consequences. `confirm_unpaid` is therefore not a service argument: the confirmation is a screen, not a rule.
4. **The index `night_group_status_date` is unchanged.** The tables are small and no query needed it.
5. **The typed group name is checked in the service**, so a direct POST cannot skip it.
6. **`create_invite` now locks the group**, found by a test: an invite could be created for an archived group.
7. **`session_nets` needed no filter**; its callers pass only sessions that are already filtered.
8. **Archived pages hide host controls by rendering with a player-role copy of the membership** (`games.access.read_only`), instead of a condition on each control.

2026-10-04 verification:

- 569 tests pass on SQLite (ten PostgreSQL-only skips) and all 569 on local PostgreSQL 17, started for the run and stopped after. The four new race tests ran five more times on PostgreSQL without a failure.
- 46 new tests: service rules, every existing write service refused on an archived session, totals before/during/after, database `ProtectedError`, pages, 403 and 404, invites, group delete.
- `makemigrations --check` reports no drift. Both migrations applied forward on the local development database with seeded data.
- `archive.mjs`: 85 of 85 on a fresh temporary database; captures inspected at 320 and 390px.
- The home page stays at 11 queries (`web/tests/test_home.py`); the archived-groups lookup is in the view, outside that count, and adds one.

Not verified: a physical phone, a screen reader, migration on a copy of production data, and the live-page case from the plan as a browser check (the 404 of the state endpoint after delete is covered by a Django test; `live.js` already reloads on 404).

Known gap: a write on a finished set in a group that is being archived at the same moment can land, because set writes do not lock the group row. It breaks no money rule and is visible after restore. Recorded in the wiki.

AC1 to AC9 are met.

Documentation synced: wiki features and architecture, PRODUCT.md, DESIGN.md, roadmap decisions, browser README, TODO.

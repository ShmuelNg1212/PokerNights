# Archive and delete groups and sessions: study

Date: 2026-10-04, Asia/Manila.

## Request

The human asked: can hosts have the option to delete or archive groups, or sessions within groups?

"Session" here is the gathering (`GameNight`), which holds one or more sets (`GameSession`). See the footgun [session means set in the code](../wiki/footguns/session_means_set_in_the_code.md).

## What exists today

- **A set can be canceled**, only while it has no accepted buy-in (`games.services.transition`, action `cancel`). A canceled set stays in the database and on the session page.
- **A session can be closed.** Closing writes the settle-up plan. A closed session stays in the group's list forever.
- **Tables and presets have `archived_at`.** Queries filter on `archived_at__isnull=True`. There is no screen that sets it. This is the pattern to copy.
- **A member can be removed** (`status = removed`); the row stays.
- **Nothing can be deleted** and no group or session can be hidden. A test session, a session created by mistake, or a group that stopped playing stays on every list.
- SPEC.md and the roadmap say nothing about deleting or archiving. The roadmap lists "reopen a closed session" for Stage 2; that is a different feature.

## Constraints

1. **Money records are append-only** (AGENTS.md rule 4). A buy-in, cash-out, count, override, finalization, result, rake entry, settle-up plan, transfer or payment is never removed. A reversed buy-in is still a money record.
2. **The database enforces this.** Every money table points at its set, session, group or member with `on_delete=PROTECT` (`ledger/models.py`, `settlement/models.py`). Deleting a set or session that has any money row fails in PostgreSQL and SQLite.
3. **Other `PROTECT` links shape the delete order.** `GameSession.night`, `GameNight.table`, `GameSession.table` and `GroupRakeAccount.group` are `PROTECT`. Django's `PROTECT` refuses even when the protected row would also be removed by a cascade, so a delete must go set → session → table → rake account → group, in a service.
4. **The audit log survives.** `AuditEvent` keeps `group_id` and `session_id` as plain integers, "so the log survives any later cleanup". A delete leaves its own event and all earlier ones.
5. **App direction** is `groups → games → ledger → settlement → web`. `groups` cannot import `games`. A group delete has to remove sessions and tables, so its service belongs in `games` (which may import `groups`). Money checks use reverse relations (`session.buy_ins`), as `games.services.has_money` already does.
6. **Writes go through services, lock first, audit and bump the version** (rules 2 and 6). Session-level writes lock the `GameNight` row (`lock_night`), as `close_night` does. `groups.services._lock_group` locks a group row.
7. **Request ids** (rule 3). Lifecycle actions that are safe to repeat (`close_night`, most `transition` actions) carry no `request_id` today: a repeat is a no-op. Archive, restore and delete are the same kind.
8. **Access** (rule 5). Every view resolves through `groups.access.member_for`, which needs an active membership. Archived objects need one more condition, in that one place and in `lock_night` / `lock_session`, so no write can reach an archived session.
9. **Totals are queries** (rule 7). Hiding a session from totals means filtering these queries: `settlement.queries.counted_results` (stats, records, months), `unpaid_transfers` (home "To settle"), `session_nets`, `ledger.queries.group_rake`, `web.views.visible_nights`, `web.home.home_cards`.
10. **Live pages.** A set page polls its version. Archiving or deleting under an open page must lead it to a clean state: `live.js` already reloads on 404.

## What "delete" can honestly mean

Because of constraints 1 and 2, there are two different operations:

- **Delete**: the rows are gone. Possible only when no money row exists under the session or group. This covers a session made by mistake and a group that never played.
- **Archive**: the rows stay, and the session or group leaves the lists. Possible for anything that is not in play. It can be undone.

A third option, deleting money rows too, would break rule 4 and the database protections, and would let a host erase a debt that another player is owed. It is rejected.

## The question that decides the design

Does an archived session still count in the totals?

- **Out of the books (recommended).** An archived session is excluded from stats, player records, "To settle" and the group rake total, and restoring it puts everything back. This is what makes archive useful for the likely case: a test session with invented buy-ins cannot be deleted, so archiving is the only way to stop it polluting the stats.
- **Hidden only.** The session leaves the list but its results still count. Simpler, and nobody can make a real loss vanish from the stats. But a test session then distorts the stats for good.

The risk of the first choice is that a host archives a real session with unpaid transfers and the debt disappears from the payer's home page. The plan answers this with a confirmation that names the unpaid amounts, an audit event, a visible "Archived sessions" list for hosts, and restore.

## Other findings

- **Who.** There is one host role and a group can have several hosts. No "owner" exists. `GameGroup.created_by` is recorded.
- **Sets.** A set with no money can already be canceled; a set with money must be finished. Archiving one set inside a session would leave a session whose sets do not add up. Out of scope.
- **Archived group and invites.** `accept_invite` must refuse for an archived group.
- **Archived group and the home page.** `home_cards` lists every active membership. A player in an archived group should see nothing; a host needs a way back to restore it.
- **SQLite hides missing locks** ([footgun](../wiki/footguns/sqlite_hides_missing_locks.md)). The race "archive a session while a buy-in is being recorded" must be tested on PostgreSQL.

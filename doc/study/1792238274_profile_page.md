# Profile page: study

Date: 2026-10-17. Mode: mixed (technical, then design).

## Request

The human wants a profile page. A tap on the account token at the top right opens it. The page has profile settings: change name and change password. The page also shows personal stats that collect the person's results from all the groups that they joined.

## Decisions from the human (2026-10-17)

| Question | Answer |
|---|---|
| What does "change name" change? | One name for all groups. One field renames the person in every group that they are in. A group where another member already has that name is skipped, and the page names that group. The login username does not change. |
| How do stats combine units across groups? | Pesos from all groups add up to one total. Chips are shown per group and are never added across groups, because a chip has a different value in each group. |
| Which groups count? | All groups except archived groups. Groups where the person was removed count, because that history is theirs. |
| How much do the stats show? | A summary and a breakdown: headline figures, a running-profit chart, and one row per group that links to the person's player page in that group. Periods: All time and This year. |

## What exists now

### Names

- `User` is a plain `AbstractUser` ([accounts/models.py](../../accounts/models.py)). The username is the login name. The account token shows its first letter.
- Each group has its own name for the person: `Member.display_name`. It is unique among active members of a group, case-insensitive (`member_active_name_unique`).
- `groups.services.rename_self(actor, name)` renames one membership. It locks the group, checks `_name_taken`, writes, and records `member.renamed`. It is gated by `settings.ROSTER_TOOLS`. The group settings page calls it from `groups/views.py` `rename_self`.
- A rename is idempotent by state: a second identical request finds the name already set and writes nothing. It has no `request_id`, and the new service can do the same.
- A removed member keeps `user`. Only `status` changes. History from a removed membership is therefore found through `Member.user`.

### Passwords

- Sign-up, login, and a host-issued reset link exist (`accounts/views.py`, `accounts/services.py`). A person cannot change their password while logged in.
- `accounts/forms.py` has `NewPasswordForm` (a `SetPasswordForm` with plain words). Django's `PasswordChangeForm` adds the current-password check.
- `revoke_reset_links(user)` cancels live reset links. The caller records the audit event.
- No login throttle exists. A current-password field is a second place to guess a password. It must not be easier to guess there than at login.

### Stats

- `settlement.stats.fetch(group, unit)` reads all counted results of one group in one unit. It folds a player's sets into one `SessionResult` per session. `PlayerRecord` does all the arithmetic in integers.
- `counted_results()` excludes archived sessions. It does not exclude archived groups. The profile query must add that filter.
- `queries.member_records(member_ids)` already gives `{member: {unit: PlayerStats}}` across groups for Your groups. It has only net, sessions, and wins.
- `web/stats.py` `player_context` builds the per-group player page: lead figure, running chart (`web/charts.py` `running_chart(record, unit)`), tiles, highlights, sessions.
- A unit belongs to a session, not to a group. One group can have pesos sessions and chips sessions.
- `SessionResult` has `member_id` and `table`, but not the group. The profile needs the group for the breakdown and to name the group of the best and worst nights.

### Header

- `templates/_account.html` is a native `<details>` panel: chip, "Logged in as", username, Log out. DESIGN.md "The header (2026-10-17)" fixes its look and motion. `header.mjs` has 103 browser checks for it.

## Domain model

- **Profile** is a view of one `User` across their memberships. It owns no table. It stores nothing.
- **Your name** on the profile is a request to set `Member.display_name` on every active membership in an unarchived group. It is not a new field on `User`. Groups keep their own names, so a host can still rename a person in one group, and the names can differ again.
- **Personal stats** are queries over `PlayerResult` where `member.user` is the person, the group is not archived, and the session is counted. Rule 7 (totals are queries) holds. Nothing is snapshotted.
- **Unit rule.** Pesos add across groups. Chips never add across groups. This is stricter than the spec's "Pesos and chips are never mixed". Add it to spec.md section 5 after approval.

## Technical findings

1. **Dependencies.** The page view goes in `web` (it reads `groups` and `settlement`). The name service goes in `groups`. The password service goes in `accounts`. All of them point one way.
2. **Name service.** `rename_everywhere(user, name)` takes the active memberships in unarchived groups, locks each group in id order (this prevents deadlocks), applies `_rename` in each, and returns the groups that it renamed and the groups that it skipped. It runs in one `transaction.atomic()`. Each rename records its own `member.renamed` event, as now. `ROSTER_TOOLS=False` refuses it, as it refuses `rename_self`.
3. **Current name.** When all memberships have the same name, the field shows it. When they differ, the field is empty and the page lists each group with its name.
4. **Password service.** `change_password(user, current, new)` checks the current password and runs the validators through `PasswordChangeForm`. It sets the password, revokes live reset links, and records `account.password_changed` with no group. The view calls `update_session_auth_hash`, so this phone stays logged in. Django's session hash then logs out the person's other sessions. This is the expected effect of a password change.
5. **Guessing.** A wrong current password must cost what a wrong login costs. Today neither has a limit. Option: count wrong current-password attempts per user in the session and refuse after five for fifteen minutes. This is an OPEN QUESTION for the plan.
6. **Stats query.** Add `fetch_for_user(user, unit)` beside `fetch`. It filters `member__user=user` and `group__archived_at__isnull=True`. It returns `SessionResult` rows that carry `group_id` and the group name. `PlayerRecord` works unchanged on the merged list, because it reads only `results`. Two queries are enough for the page in each unit.
7. **Chart.** `running_chart(record, unit)` takes a `PlayerRecord`. The pesos chart can reuse it unchanged.
8. **Same-night sessions in two groups.** The list is sorted by `(date, night_id)`. Night ids are global, so the order is stable.

## Design shape brief

Visitor mode: **Operate**. The established world (DESIGN.md) holds. This page adds no new colour, font, or asset.

1. **Job and audience.** A player or a host, often between games, not at the table. They want to know "how am I doing overall" and want to fix their name or password. Short glances, one hand.
2. **Outcome and proof.** The main figure is the pesos profit or loss across all groups, with its sign and icon. The breakdown proves where it comes from: one row per group. Settings are secondary and sit below the stats.
3. **Direction.** Reuse the player page's grammar: lead panel with the big figure, running chart, a small set of tiles, then group rows in the board-row style (token or group name, muted sessions line, signed figure). Chips groups follow as a separate section, "Chips games", one row per group, each with its own figure and the word "chips". No combined chips figure.
4. **Order on the page.** Header: way back to Your groups. Then the person's token, name, and username. Then the period pills (All time, This year). Then the pesos lead, chart, tiles (Sessions, Win rate, Average, Best night, Worst night), pesos groups, chips groups. Then **Settings**: Your name, Password. Then Log out stays in the account panel only.
5. **Entry.** The account panel gets a **Profile** row above Log out: a neutral 48 px full-width link with a `user` icon. The set (Lucide paths in `table_tags.ICONS`) has none yet; add Lucide's `user`. The token itself still opens the panel. The page is one tap from the panel.
6. **Forms.** Use the shared field box and the "Account and supporting forms" rules. Each form is a native disclosure that shows its current value in the summary ("Your name: Ana"). An error keeps the form open with local error text. Success shows a message only after the server accepts it. The name result names the groups that were skipped and why.
7. **States.**
   - No closed session in any group: one empty-state panel, "Your stats appear after your first closed session." Settings still show.
   - Pesos history but no chips history: no chips section. The reverse: no pesos lead, and the chips section moves up.
   - One group only: the breakdown still shows its one row, because the row is the link to the group's player page.
   - Fewer than three pesos sessions: no chart, the same line as the player page.
   - This year with no sessions: the empty text names the period.
   - Long group names end in an ellipsis on one line. Big amounts use tabular figures and do not wrap.
8. **Motion.** Period change uses the existing stats motion (`data-stats`, pill marker, figures shift in). The chart reveal is as on the player page. Disclosures use the existing motion. Reduced motion: none.
9. **Layout.** Single column on phones. From 900 px, the tiles go to four columns, as on the player page. 48 px targets.

## Risks

- `header.mjs` checks the panel's contents. The new row changes the panel height and needs new checks.
- The name change writes to many groups at once. A host may be surprised to see a new name. The audit log records each rename.
- A password change logs out the person's other phones. The success message must say so.

## Not in scope

- Changing the login username.
- An avatar picture.
- Seasons, or any period beyond All time and This year.
- A session list across groups. Each group's player page keeps that.

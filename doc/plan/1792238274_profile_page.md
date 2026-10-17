# Profile page: plan

Study: [doc/study/1792238274_profile_page.md](../study/1792238274_profile_page.md). Mode: mixed.

Goal: a tap on the account token opens a panel with a **Profile** link. The profile page shows the person's stats across all their groups and lets them change their name in all groups and their password.

## OPEN QUESTIONS

Answered by the human on 2026-10-17 ("approve" = the recommended answers).

1. **Password guessing.** Approved: limit wrong current-password attempts to 5 per 15 minutes for each user. After that, the form refuses and says when to try again.
2. **Spec change.** Approved: spec.md section 5 gets "A person's profile adds pesos across their groups. Chips are shown per group and never added across groups." An ADR records it.
3. **Design brief.** Approved as written in the study.

## Tasks

Branch: `feat/profile-page` from `main`. One Conventional Commit per task. Run the SQLite tests before each commit.

### 1. Personal stats query (`settlement`)

- [x] Add `group_id: int | None = None` and `group: str = ""` to `SessionResult` with defaults, so `fetch` stays unchanged.
- [x] Add `stats.fetch_for_user(user, unit)`: counted results where `member__user=user` and `group__archived_at__isnull=True`, folded per session as `fetch` does, with group id and name.
- [x] Add `stats.units_for_user(user)`: the units in which the person has counted results.
- [x] Tests (`tdd`): two groups in pesos add up; chips rows keep their group; an archived group is left out; a removed membership counts; an archived session is left out; another user's rows never appear; query count is fixed.

Acceptance: a person in two pesos groups with nets +500 and −200 gets one record with net +300 and two groups. Completion: tests pass; commit `feat: read a person's results across groups`.

### 2. Rename in all groups (`groups`)

- [x] Add `services.rename_everywhere(user, name) -> (renamed, skipped)`. One `transaction.atomic()`. Lock each group of the user's active memberships in unarchived groups, in id order. Apply `_rename`. A taken name puts that group in `skipped` and writes nothing there. `ROSTER_TOOLS=False` raises `RuleError`.
- [x] Each rename records `member.renamed` (existing `_rename`).
- [x] (Moved to task 4, done there, because it redirects to the profile URL.) Add view `rename_everywhere` (POST, `NameForm`) at `me/name/`. It redirects to the profile with a message: "Your name is now Ana." plus "Not changed in Friday Club: another Ana is in that group." when groups were skipped. A refused form is kept with `keep_form` for one redirect.
- [x] Tests (service; the view tests are in task 4): all groups renamed; one skipped; same name writes nothing and records nothing; removed and archived memberships untouched; a blank name is refused; a signed-out POST goes to login.

Acceptance: a name taken in one group renames the others and names the skipped group. Completion: tests pass; commit `feat: change your name in all your groups`.

### 3. Change password (`accounts`)

- [x] Add `ChangePasswordForm` in `accounts/forms.py`: `NewPasswordForm` plus a current-password field. The service checks the current password, so each wrong one is counted.
- [x] Add `services.change_password(user, current, new)`: set the password, `revoke_reset_links(user)`, `audit.record("account.password_changed", actor=user, ...)` with no group and no password text.
- [x] (Moved to task 4, done there, because it redirects to the profile URL.) Add view at `account/password/` (POST). On success: `update_session_auth_hash`, redirect to the profile, message "Password changed. Other phones and browsers are logged out." On failure: keep only the errors for one redirect, with **no password values**. `keep_form` saves every field's data, so do not pass this form to it; save the errors alone.
- [x] The attempt limit (5 wrong current passwords per 15 minutes per user), with tests. Each refusal is a `password.change_refused` audit event, and the count reads them. Reason: no shared cache exists, and on Vercel a memory count resets for each instance.
- [x] Tests (service and form; the view tests are in task 4): right current password changes it and keeps this session logged in; wrong current password is refused and the password is unchanged; a weak new password is refused; reset links are revoked; the audit event has no secret; the redirect page has no password value.

Acceptance: after a change, the old password fails at login and the new one works. Completion: tests pass; commit `feat: change your password from your profile`.

### 4. Profile page (`web`)

- [x] Add `web/profile.py` `profile_context(request, user)`: period from `?period=` (All time, This year only), pesos `PlayerRecord` over `fetch_for_user`, the running chart, tiles (Sessions, Win rate, Average, Best night, Worst night with group names), pesos group rows, chips group rows (each its own `PlayerRecord`), the current name or the list of differing names.
- [x] Add view `profile` at `me/` and `templates/web/profile.html`, following the shape brief: token, name, username; period pills; pesos lead, chart, tiles, group rows; chips section; Settings with two native disclosures (Your name, Password).
- [x] Each group row links to the person's player page in that group (`player` URL with their member id there and the same period).
- [x] Empty states as in the study: no closed session; no pesos; fewer than three sessions; empty period.
- [x] Tests: the page needs login; it shows only the requester's data; pesos sum across groups; chips are never summed; the archived group is absent; links point to the right member ids; empty states; fixed query count.

Acceptance: the page loads in a fixed number of queries and shows the figures in the examples above. Completion: tests pass; commit `feat: add the profile page with stats across your groups`.

### 5. Entry from the account panel (design)

- [x] Add Lucide `user` to `ICONS`.
- [x] Add a neutral full-width **Profile** link (48 px, icon) above Log out in `templates/_account.html`. Mark it current on the profile page.
- [x] `/impeccable` build pass on `profile.html` inside DESIGN.md tokens and motion presets; `mobile-native` check.
- [x] Extend `web/tests/browser/header.mjs` for the new row; add `web/tests/browser/profile.mjs` (seed: `seed_profile.py`) at 320, 390 and 1280 px: no overflow, 48 px targets, contrast, period change keeps scroll, reduced motion, no JavaScript.

Acceptance: Profile is one tap after the token, and the header checks still pass. Completion: browser checks pass; commit `feat: open your profile from the account panel`.

## Rendezvous checks

Recorded 2026-10-17. The plan is frozen after this section.

- [x] SQLite suite: 1291 tests pass (15 skipped, PostgreSQL-only). PostgreSQL suite: 1287 tests pass before the polish commit; the polish changed only the profile page and its tests.
- [x] `code-review` (medium): 10 findings. Fixed 7 in `fix: harden the profile's name and password changes`: a group archived during a rename; a password change sent twice (now idempotent by state, so no `request_id`); the lockout wait rounds up; the name rule from the service; the message with no group; a stale current mark on the permanent panel; a redundant field order. Not changed: three queries instead of one (the count is fixed); the private `_errors` use (the same as `take_form`); a small period duplication.
- [x] `verification-before-completion`: every claim above comes from a test or browser run in this session.
- [x] `security-review`: no findings at confidence 8 or more. Checked: another user's data, login and CSRF, the sent-twice path as a password oracle, sessions after a change, passwords in the session and the audit log, XSS in group and display names.
- [x] `/impeccable critique` (dual assessment): 29/40. Detector: clean; overlay findings were sampling errors or the body texture that the branch did not touch. Polish in `fix: polish the profile after the design critique`: a Name and password link to the settings; chevrons and straight separators on group rows; "Even" for zero; a two-line group name with its full title; best and worst nights without this year's year. Not changed: the order (stats first, approved); "Touch the chart" (shared player-page copy).
- [x] `break-ui` cases covered by the browser seed: a 56-character group name, a group in two units, a zero result, a group left. Not covered: amounts above ₱1,000,000 on this page.
- [x] Browser: `profile.mjs` 62/62 and `header.mjs` 106/106 at 320, 390 and 1280 px.

## Sync docs

- [ ] spec.md section 4 and 5 (after OPEN QUESTION 2), features.md, architecture.md (Stats: `fetch_for_user`), DESIGN.md addendum for the profile and the panel row, ADR for the unit rule, TODO.md phone checks.

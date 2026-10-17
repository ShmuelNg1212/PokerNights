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
- [ ] (Moved to task 4, because it redirects to the profile URL.) Add view `rename_everywhere` (POST, `NameForm`) at `me/name/`. It redirects to the profile with a message: "Your name is now Ana." plus "Not changed in Friday Club: another Ana is in that group." when groups were skipped. A refused form is kept with `keep_form` for one redirect.
- [x] Tests (service; the view tests are in task 4): all groups renamed; one skipped; same name writes nothing and records nothing; removed and archived memberships untouched; a blank name is refused; a signed-out POST goes to login.

Acceptance: a name taken in one group renames the others and names the skipped group. Completion: tests pass; commit `feat: change your name in all your groups`.

### 3. Change password (`accounts`)

- [ ] Add `ChangePasswordForm(PlainWords, PasswordChangeForm)` in `accounts/forms.py`.
- [ ] Add `services.change_password(user, new_password)`: set the password, `revoke_reset_links(user)`, `audit.record("account.password_changed", actor=user, ...)` with no group and no password text.
- [ ] Add view at `account/password/` (POST). On success: `update_session_auth_hash`, redirect to the profile, message "Password changed. Other phones and browsers are logged out." On failure: keep only the errors for one redirect, with **no password values**. `keep_form` saves every field's data, so do not pass this form to it; save the errors alone.
- [ ] The attempt limit (5 wrong current passwords per 15 minutes per user), with tests.
- [ ] Tests: right current password changes it and keeps this session logged in; wrong current password is refused and the password is unchanged; a weak new password is refused; reset links are revoked; the audit event has no secret; the redirect page has no password value.

Acceptance: after a change, the old password fails at login and the new one works. Completion: tests pass; commit `feat: change your password from your profile`.

### 4. Profile page (`web`)

- [ ] Add `web/profile.py` `profile_context(request, user)`: period from `?period=` (All time, This year only), pesos `PlayerRecord` over `fetch_for_user`, the running chart, tiles (Sessions, Win rate, Average, Best night, Worst night with group names), pesos group rows, chips group rows (each its own `PlayerRecord`), the current name or the list of differing names.
- [ ] Add view `profile` at `me/` and `templates/web/profile.html`, following the shape brief: token, name, username; period pills; pesos lead, chart, tiles, group rows; chips section; Settings with two native disclosures (Your name, Password).
- [ ] Each group row links to the person's player page in that group (`player` URL with their member id there and the same period).
- [ ] Empty states as in the study: no closed session; no pesos; fewer than three sessions; empty period.
- [ ] Tests: the page needs login; it shows only the requester's data; pesos sum across groups; chips are never summed; the archived group is absent; links point to the right member ids; empty states; fixed query count.

Acceptance: the page loads in a fixed number of queries and shows the figures in the examples above. Completion: tests pass; commit `feat: add the profile page with stats across your groups`.

### 5. Entry from the account panel (design)

- [ ] Add Lucide `user` to `ICONS`.
- [ ] Add a neutral full-width **Profile** link (48 px, icon) above Log out in `templates/_account.html`. Mark it current on the profile page.
- [ ] `/impeccable` build pass on `profile.html` inside DESIGN.md tokens and motion presets; `mobile-native` check.
- [ ] Extend `web/tests/browser/header.mjs` for the new row; add `web/tests/browser/profile.mjs` at 320, 390 and 1280 px: no overflow, 48 px targets, contrast, period change keeps scroll, reduced motion, no JavaScript.

Acceptance: Profile is one tap after the token, and the header checks still pass. Completion: browser checks pass; commit `feat: open your profile from the account panel`.

## Rendezvous checks

- [ ] SQLite and PostgreSQL suites pass.
- [ ] `code-review`, `verification-before-completion`.
- [ ] `security-review` (password and user data change): no password in session drafts, logs or audit; no data from another user; CSRF on both POSTs.
- [ ] `/impeccable critique` and `audit`, then `polish`; `break-ui` with long group names, 12 groups, huge amounts, one session.
- [ ] Record the results here.

## Sync docs

- [ ] spec.md section 4 and 5 (after OPEN QUESTION 2), features.md, architecture.md (Stats: `fetch_for_user`), DESIGN.md addendum for the profile and the panel row, ADR for the unit rule, TODO.md phone checks.

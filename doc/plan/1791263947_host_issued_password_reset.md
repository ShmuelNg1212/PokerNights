# Host-issued password reset: plan

Status: approved 2026-10-06 ("approved."); all six decisions as recommended. Date: 2026-10-06, Asia/Manila. Study: [Host-issued password reset](../study/1791263946_host_issued_password_reset.md).

## Outcome

A player who forgot their password asks a host of their group. The host creates a reset link in Group settings and sends it to them. The player opens it, chooses a new password and is logged in. Nobody needs the site administrator.

Mode: Operate. Visual authority: the built Rack in DESIGN.md and its Entry pages addendum. No new colour, font or asset. One migration (`accounts.0002`, a new table; nothing existing changes).

## Behaviour

### 1. The host creates the link

Group settings → Players → "Manage {name}" gains **Create password reset link** for a member who has a login. It is not offered for a roster player without a login, or for yourself.

After the tap, the Players section shows once:

> **Reset link for Maria.** Send it to Maria only. Whoever opens it can set the password. It works once and expires Oct 7, 21:40.

with the link in a read-only field, as an invite link is shown today. The link is never shown again; only its hash is stored.

While a link is live, the member's "Manage" block says "Reset link active until Oct 7, 21:40" with **Cancel link**. Creating another link cancels the earlier one. Any host of a group the player is in sees and can cancel a live link.

A host is refused, with the reason, for:

| Member | Message |
|---|---|
| A site administrator | "A site administrator's password is set in the admin." |
| Someone who hosts another group | "{name} hosts another group. The site administrator resets their password." |
| A roster player without a login | "{name} has no login." |
| Yourself | "This is for another player." |

### 2. The player uses the link

The link opens a page in the entry frame, signed out or not:

- Heading **Set a new password**, and the line "Your username is **maria**." (People forget that too.)
- Password with the Show button, and Repeat password, with the same rules, help and wording as Sign up.
- Button **Save and log in** ("Saving…" while it is sent).

On success the password is changed, the link is used up, the person is logged in on this device and lands on Your groups with "Password changed. You're logged in." Every other device logged in to that account is signed out.

A link that is unknown, used, cancelled or expired shows **This reset link doesn't work**, one reason ("…has already been used", "…has expired", "…is not valid") with "Ask a host of your group for a new one", and a quiet Log in line. Status 404.

Opening the link changes nothing; only saving a password uses it. A chat app that fetches the address for a preview cannot spend it, and the page title does not name the account.

### 3. The words that said "no reset"

- Sign up, under Password: the line "There is no password reset yet." goes. It becomes "Forgot it later? A host of your group can send you a reset link."
- Refused login: "Forgot your password? Ask a host of your group for a reset link."

### 4. Switch

`RESET_LINKS=False` in Vercel turns the feature off without a release: the button is hidden, creating is refused, and every reset link says it is not valid. The login line then falls back to today's wording. Default on.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **Who a host can issue a link for.** Recommended: any member of their group with a login, except a site administrator and anyone who hosts another group. The reason is in the study: a link lets its holder become the account, and without this limit a stranger could create a group, invite a host of another group, and take that group over.
2. **What remains after that limit.** A host can still open the link themselves and log in as one of their own players, and would then see any other group that player is in, as a player. The audit log records who issued the link and when it was used, and the player finds their password changed. Recommended: accept this for private groups of friends.
3. **The link lasts 24 hours** and works once. Invites last 7 days; this one is a key to an account.
4. **Saving the new password logs the person in.** Recommended. The alternative is one more Log in screen.
5. **A host who is the only host of their group and forgets their password** still needs you, in `/admin/`. A second host in the group avoids that. Recommended: accept, and say so in the wiki.
6. **The wording** in sections 1 to 3. Change any of it.

## Implementation

1. **Model (`accounts/models.py`, migration `0002`).** `PasswordResetLink`: `user`, `token_hash` (unique, SHA-256), `expires_at`, `used_at`, `revoked_at`, `created_by`, `group_id` (a plain number for the audit log, as `AuditEvent` keeps it), `created_at`. Registered read-only in the admin.
2. **`accounts/services.py` (new; the only writer).**
   - `issue_reset_link(user, *, created_by, group_id) -> (link, token)`: in one transaction, lock the user row, cancel the user's live links, create the new one with a 32-byte random token. The token is returned once.
   - `usable_reset_link(token, *, lock=False)`: the link or a `ResetLinkError` with the reason.
   - `redeem_reset_link(token, password) -> user`: lock the link row, check it again, set the password, stamp `used_at`, `audit.record("password.reset", …)`.
   - `revoke_reset_links(user, *, actor, group_id)`.
3. **`groups/services.py`.** `create_password_reset(actor, member_id)` and `cancel_password_reset(actor, member_id)`: `require_host`, lock the group, resolve the active member in the actor's group, apply the refusals in section 1, call the `accounts` service, `audit.record("password_reset.issued" / ".cancelled", group_id=…, target=member)`. `accounts` never imports `groups`.
4. **Views and addresses.**
   - `groups`: `POST g/<group>/members/<member>/reset-link/` and `…/reset-link/cancel/`, resolved through `member_for` (a miss is 404). The new address is put in the session for one display, as `new_invite_url` is.
   - `accounts`: `accounts/reset/<token>/`, exempt from the login requirement, `never_cache`, `Referrer-Policy: no-referrer`. GET shows the form or the refusal; POST redeems, calls `login()` and redirects home.
5. **Form (`accounts/forms.py`).** A subclass of Django's `SetPasswordForm` with the app's wording. The code-to-words map and the "first refused field gets the cursor" rule move from `SignupForm` into a small mixin both use. Validators are unchanged.
6. **Templates.** `accounts/reset.html` (entry frame, both states); `web/_group_settings.html` (the action, the live-link line, the once-only notice); `registration/login.html` and `accounts/signup.html` (the wording).
7. **`web/views.py`.** The settings tab reads the live links for the group's members in one query and takes the once-only notice from the session.
8. **Setting.** `RESET_LINKS = env.bool("RESET_LINKS", default=True)`.
9. **Tests first.**
   - `accounts/tests/test_reset_links.py`: issue returns a token whose hash is stored and whose plain form is not; a second issue cancels the first; redeem changes the password, stamps the link and writes the audit event; a used, cancelled, expired or unknown token is refused with its reason and changes nothing; a GET never uses the link; a refused password (each rule) keeps the link usable and shows the app's words; success logs in and lands on Your groups; another client's session for that account is signed out; the page sends `no-store` and `no-referrer` and its title has no username; the switch off refuses everything.
   - `groups/tests/test_password_reset.py`: a host can issue for a player and for a co-host; a player cannot (403); a host of another group gets 404; each refusal in the section 1 table; a removed member; an archived group; cancel; both audit events carry the group.
   - `web/tests`: the action appears only for hosts and only on members with a login; the notice shows once and not on reload; the live-link line; the settings tab's query count does not grow with the number of members.
   - `accounts/tests/test_entry.py` and `entry.mjs`: the two changed lines.
   - PostgreSQL only: two redemptions of one link at once (exactly one wins, one password is set); two issues at once (exactly one live link remains).
   - Browser check `reset.mjs` with a seed: host creates the link at 390 px, opens it in a second signed-out browser, a refused password, then success and Your groups; the used link then refuses; 48 px targets, contrast, focus placement, 320, 390 and 1280 px.
10. **Verify.** SQLite and PostgreSQL suites. `reset.mjs`, then `entry.mjs`, which shares the pages. Captures inspected.
11. **Sync docs.** Wiki features, architecture (the `accounts` service, the new table) and deployment ("Who can get in", the switch), PRODUCT.md addendum, DESIGN.md addendum, roadmap stage 5, TODO. SPEC.md is the human's; a line is left in TODO if it should mention this.

## Acceptance criteria

- AC1. A host creates a link for a player in their group, and the player sets a new password with it and is logged in, without the site administrator.
- AC2. A link works once, stops after 24 hours, and stops when cancelled or replaced. Opening it without saving never uses it.
- AC3. Only a host of a group the player is in can create or cancel a link. No link can be created for a site administrator, for a host of another group, or for a member without a login.
- AC4. The database holds no usable token: only hashes.
- AC5. Two simultaneous uses of one link set exactly one password (PostgreSQL).
- AC6. After a reset, other devices logged in to that account are signed out.
- AC7. Issuing, cancelling and using a link each leave an audit event naming who and when.
- AC8. Sign up and Log in no longer say there is no reset.
- AC9. `RESET_LINKS=False` removes the feature without a release.
- AC10. Password rules accept and refuse exactly what Sign up does. Existing tests pass on SQLite and PostgreSQL after the listed wording updates.

## Out of scope

- A "change my password" screen while logged in.
- Reset by email, SMS or any channel the app would send on.
- Showing a player that a link was issued for them, or a history of resets on screen (the audit log has it).
- Claim links for roster players without a login.
- Limiting how many links a host may create per day.

## Rollback

Set `RESET_LINKS=False` in Vercel for an immediate stop. To remove the code, revert the feature commits; the new table can stay empty and unused, so no migration needs reversing. Passwords changed through a link stay changed.

## Progress and blockers

2026-10-06: Study and plan complete. Waiting for the human's approval. No code written.

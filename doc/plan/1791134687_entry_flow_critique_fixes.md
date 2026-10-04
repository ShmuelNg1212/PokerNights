# Entry flow fixes from the critique: plan

Status: approved 2026-10-05 ("approved"); all six decisions as recommended. Date: 2026-10-05, Asia/Manila. Study: [Entry flow fixes from the critique](../study/1791134589_entry_flow_critique_fixes.md).

## Outcome

A player who opens an invite link for the first time creates an account and is in the group, in two screens instead of four, knowing what name their friends will see and that the password cannot be reset yet. Errors speak in the app's plain voice.

Mode: Operate. Visual authority: the built Rack in DESIGN.md and its Entry pages addendum. No new colour, font or asset. No migration.

## Behaviour

### 1. Invite link, signed out → Sign up first

| Visitor opens `/join/<token>/` | Today | After |
|---|---|---|
| Signed out, usable invite | Log in ("Log in to join") | **Sign up**, with "You're invited to {group}" and "Already have an account? Log in" |
| Signed out, invalid, expired, used-up or revoked invite | Log in, and the error only after logging in | The "invite not valid" page at once, with a Log in button |
| Signed in | Join group page | Unchanged |

Log in reached from that Sign up link keeps the invite and still says "You're invited to {group}".

### 2. Joining happens at sign-up

- An account created from a usable invite joins that group at once and lands on the group page with the message "Welcome to {group}. You're in."
- If the invite stopped being usable in the seconds between (used up, revoked), the account is still created and the visitor lands on the invite page, which explains it.
- A person who already had an account keeps the "Join {group}" confirmation with "Not now".
- The Join page says "You will see this group's sessions and can join their games." instead of "sets".

### 3. Lost passwords: say what is true

- Sign up, under Password: "At least 8 characters, not a common password, not only digits, and not like your username." and, on its own line, "**There is no password reset yet.** Save it in your phone's password manager."
- Log in, under a refused login: "Forgot your password? There is no reset yet. Tell your host, who can ask the site administrator to set a new one."
- No reset is built in this cycle.

### 4. Names and words

- Username help: "Your friends see this name. Letters and numbers, no spaces."
- Messages, by Django's error code; the rules themselves are unchanged:

| Case | New wording |
|---|---|
| Wrong login | "That username and password don't match. Check capital letters." |
| Username taken | "That name is taken. Try another." |
| Username has a space or other refused character | "Use letters and numbers, with no spaces." |
| Password too short | "Too short. Use at least 8 characters." |
| Password too common | "That password is too common. Pick a less usual one." |
| Password only digits | "Use more than digits." |
| Password like the username | "Too close to your username. Pick something different." |
| Passwords differ | "The two passwords don't match." |

- After a refusal the keyboard focus goes to the first refused field; after a refused login, to Password.
- Busy buttons say "Logging in…" and "Creating account…" instead of "Sending…".
- A refused sign-up still returns empty password fields. Writing a password back into the page is a security cost and is not done.

### 5. Polish from the measured review

- Show button: one state, not two. It keeps its changing text and label ("Show password" / "Hide password") and drops the pressed state.
- A refused sign-up announces once ("Check the highlighted fields.") instead of up to three alerts; each field stays marked invalid and tied to its message.
- A refused login marks both fields invalid and ties them to the notice.
- Skip link at 48 px.
- "Sign-up needs an invite" gets the tab title "Invite needed"; the invite error notice gets the alert role.
- Help text on the entry pages rises from 13.6 px to 14.4 px.
- The primary button sits 16 px below the last field; from 900 px the column starts lower on the page.
- Sign up shows the one-line description and gains a short second sentence on both pages: "It records the game. It never moves money."

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **Lost-password wording.** A host cannot reset a password today; only you, as site administrator, can in `/admin/`. I recommend the honest wording above. If you would rather build a host-issued reset link now, say so; it is a larger cycle with a migration.
2. **Automatic joining** for accounts created from an invite, with no "Not now". Recommended.
3. **Invalid invite links shown while signed out.** Recommended: yes, show "This invite link is not valid" straight away instead of asking the visitor to log in first. It reveals nothing the sign-up page does not already reveal.
4. **"It never moves money."** Recommended as a second sentence under the description. It is the product's own statement (PRODUCT.md).
5. **Refused sign-up still clears the passwords.** Recommended: accept, for the security reason above.
6. **Autofocus on Username stays** on a fresh page. A screen reader then starts in the field; removing it would cost every sighted user a tap. Recommended: keep.

## Implementation

1. **`accounts/signup.py`.** A third registry, `AFTER_SIGNUP`, and `after_signup(request, user, next_path) -> str | None`: the first hook that returns a URL decides where the new user goes.
2. **`groups`.**
   - `access.join_from_invite(request, user, next_path)`: for a usable invite path, call `services.accept_invite(user, token)`, add the welcome message and return the group URL. On `RuleError`, return `None`, so the visitor goes to the invite page. Registered in `GroupsConfig.ready()`.
   - `views.accept_invite`: exempt from the login requirement. Signed out with a usable invite → redirect to sign-up with `next`. Signed out with a bad invite → the existing error page (status 404). A signed-out POST → log in.
3. **`accounts`.**
   - `views.signup`: after `login()`, ask `after_signup`; otherwise redirect as today.
   - `views.Login`: a form subclass with the new `invalid_login` message; mark fields invalid and move autofocus to Password on refusal.
   - `forms.SignupForm`: help texts; `error_messages` for `unique` and `invalid`; a code-to-wording map applied where the password validators report, and for `password_mismatch`; autofocus on the first refused field.
4. **Templates.** `login.html`, `signup.html`, `signup_closed.html`, `invite_accept.html`, `partials/entry_head.html`, `partials/entry_field.html`: the copy, the single alert, the lost-password lines, `data-busy` labels, the title and the alert role.
5. **JavaScript.** `password.js`: drop `aria-pressed`. `forms.js`: use a button's `data-busy` text when present, else "Sending…".
6. **CSS.** Skip link size; entry help size; button spacing; desktop top offset; the lost-password line.
7. **Tests first.**
   - Flow: signed-out invite link → sign-up; bad link → error page with 404; POST while signed out; sign-up from an invite creates the membership, uses the invite once and lands on the group with the welcome; an invite used up between page load and submit creates the account and lands on the invite page; an existing account still gets the confirmation; sign-up without an invite (setting off) is unchanged; `next` to another site is ignored.
   - Words: each message in the table by its trigger; the login message does not differ between a wrong username and a wrong password; the rules still refuse and accept the same passwords as before.
   - Markup: one alert on a refused sign-up; `aria-invalid` and `aria-describedby` on refused fields; autofocus placement; no `aria-pressed`; titles.
   - Update `test_signup_gate.py`, `test_invites.py`, `test_entry.py` for the new flow.
   - Concurrency (PostgreSQL): two sign-ups racing for the last use of an invite: both accounts exist, exactly one is a member, `use_count` equals `max_uses`.
   - Browser check `entry.mjs`, updated: the two-screen flow from link to group as a new account; the existing-account path; contrast and 48 px for the new lines and the skip link; focus placement after refusals; busy labels; sign-up at 390 × 844 with the Create account button visible without scrolling when empty, or the measured overflow recorded if it is not.
8. **Verify.** SQLite and PostgreSQL suites. `entry.mjs`, then `dock.mjs`, `archive.mjs`, `settled.mjs` and `session_form.mjs`, which log in through these pages. Captures inspected at 320, 390 and 1280 px.
9. **Review.** Re-run `/impeccable critique` on the same target and record the new score beside 24 of 40.
10. **Sync docs.** DESIGN.md addendum, PRODUCT.md (the invite flow), wiki features and deployment ("Who can get in"), browser README, TODO.

## Acceptance criteria

- AC1. A signed-out visitor with a usable invite reaches the group in two screens: Sign up, then the group page.
- AC2. No account is ever added to a group by an invite that is not usable at that moment, and an invite is never used more times than its limit.
- AC3. A person who already has an account is still asked before joining.
- AC4. Sign up says that friends see the username and that there is no password reset; the login error says what to do about a forgotten password.
- AC5. Every message in the table appears for its case; the login message is the same for a wrong username and a wrong password.
- AC6. Password and username rules accept and refuse exactly what they did before.
- AC7. The measured items in section 5 hold in the browser check.
- AC8. Existing tests pass on SQLite and PostgreSQL after the listed updates.
- AC9. The repeated critique scores above 24 of 40, with no P1 left among these five.

## Out of scope

- A password reset or change screen.
- A separate "Your name" field at sign-up.
- Removing "Repeat password".
- Email, phone numbers or any contact channel.
- The group page a new player lands on, beyond the welcome message.

## Rollback

Revert the feature commits. No migration. Memberships created by automatic joining stay; they are ordinary memberships.

## Progress and blockers

2026-10-05: Study and plan complete. The human approved with “approved”; all six decisions as recommended.

2026-10-05 execution on `feat/entry-flow`. The implementation was written first and the tests directly after; six existing tests that pinned the old flow and wording were updated as the plan listed.

2026-10-05 repeat critique (plan step 9), two isolated assessments that were not shown the first one: **25 of 40**, against 24. Snapshot: `.impeccable/critique/2026-10-04T17-44-36Z__templates-registration-login-html.md`.

- Of the five original issues, four no longer appear as P1: the newcomer's landing, the redundant Join step, the username help, and the stock errors.
- **Lost passwords is still P1.** The honest wording did not change the fact that recovery is a dead end. It needs a real reset.
- **The invite fix created a new P1:** a signed-out existing member who opens an invite was steered to "Create your account", with the Log in link last on the page.
- New P2s: Log in offered "Sign up" where sign-up would refuse; the invalid-invite page repeated itself and led with "Log in"; the hierarchy still serves the brand and Sign up no longer fits one phone screen.

One fix batch after the critique, not re-scored:

1. Invited Sign up shows "Already have an account? Log in" with the invite sentence, before the first field.
2. Log in offers Sign up only when sign-up would open; otherwise "Ask a host of your group for an invite link."
3. Invalid invite: heading "This invite link doesn't work", one notice, and Log in as a quiet line.
4. One welcome sentence for both ways of joining.
5. The description wraps to three lines; the desktop offset applies only in tall windows, after the measurement showed the button 4px below an 844px window at 1280px.

Changes from the plan:

- Tests were not written strictly first; see above.
- The alert role was removed from individual field errors on the entry pages only; other forms keep it.
- The Join page message became "Welcome to {group}. You're in." to match.

2026-10-05 verification:

- 612 tests pass on SQLite (ten PostgreSQL-only skips) and all 612 on local PostgreSQL 17, started for each run and stopped after. Seventeen new tests. The invite race test (two sign-ups for the last use) passed six times on PostgreSQL.
- `entry.mjs`: 91 of 91 on a fresh temporary database. `dock.mjs` 145, `archive.mjs` 85, `settled.mjs` 24 and `session_form.mjs` 69 pass through the changed login page.
- Captures inspected at 320 and 390px.

Acceptance:

- AC1 to AC8 are met.
- **AC9 is half met.** The score rose above 24, but a P1 remains among the five (lost passwords), as decision 1 accepted when the reset was left out.
- AC7 note: an invited Sign up is 848px tall at 390px wide (four pixels over an 844px screen) with the button ending at 800px; a refused Sign up needs a scroll to reach the button.

Not verified: a physical phone, a screen reader, a chat app's in-app browser, and sign-up with the invite gate on in a browser (covered by Django tests only).

Documentation synced: DESIGN.md, PRODUCT.md, wiki features and deployment, browser README, TODO.

# Entry flow fixes from the critique: study

Date: 2026-10-05, Asia/Manila. Source: the Impeccable critique of the login and sign-up pages, saved as `.impeccable/critique/2026-10-04T17-19-58Z__templates-registration-login-html.md` (score 24 of 40; two independent assessments).

## Request

The human asked to start the workflow for all five priority issues of the critique at once. Their answers after the critique: invite flow first; all five issues in one cycle; the username stays one field and its help text explains that friends see it.

## The five issues and what the code does today

### 1. An invited newcomer lands on Log in (P1)

- `LoginRequiredMiddleware` protects every view. `groups.views.accept_invite` is not exempt, so a signed-out visitor to `/join/<token>/` is redirected to `/accounts/login/?next=/join/<token>/`.
- The login page says "You're invited to X. Log in to join." The route to an account is the muted link "No account? Sign up".
- On production, sign-up is possible only from a usable invite (`SIGNUP_REQUIRES_INVITE`). So the most common first visit starts on a form the visitor cannot use.

### 2. A forgotten password cannot be recovered and nothing says so (P1)

- `accounts/urls.py` has sign-up, log in and log out only. There is no reset or change view.
- **A host cannot reset a player's password.** The only way today is a superuser in Django's `/admin/`. The critique's suggested line "Ask your host" would send people to someone who cannot help, unless the host is also the site administrator.
- A real reset is on the roadmap (Stage 5) and needs a delivery channel the app does not have (no email, no phone number is required).

### 3. "Username" hides that friends see it, and its rules (P1)

- `groups.services.accept_invite` and `create_group` copy the username into `Member.display_name`. It then appears in player lists, results and "who pays whom".
- The help text is "The name you log in with." Django's username validator refuses spaces and answers "Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters."
- The `UserAttributeSimilarityValidator` refuses a password close to the username; the form does not say so.

### 4. Stock error wording; a refused sign-up wipes both passwords (P2)

- Messages come from Django: the login error, "A user with that username already exists.", the password validator messages and the mismatch message. Each has a stable error code (`invalid_login`, `unique`, `password_too_short`, `password_too_common`, `password_entirely_numeric`, `password_too_similar`, `password_mismatch`), so wording can change without touching the rules.
- After a refusal, Django's `autofocus` is on Username, which is the one field that kept its value.
- Password fields come back empty because Django never writes a password into the page. Writing it back would put the password in the HTML of the response; that is a real security cost and is rejected.
- Every submit button shows "Sending…" while busy (`static/js/forms.js`).

### 5. The Join screen is a redundant step after sign-up (P2)

- `accounts.views.signup` redirects to `next`, the invite page, which asks "Join group / Not now". The visitor has already been told twice that they are invited. "Not now" leaves a new account with no group.
- The page says the person "can join their sets", a word a newcomer has not met.

## Smaller findings to take in the same cycle

From the measured assessment and the design review:

- The Show button changes both `aria-label` and `aria-pressed`, so it would read "Hide password, pressed".
- A refused sign-up renders up to three `role="alert"` regions at once.
- The login error sets no `aria-invalid` and is not tied to the fields.
- The skip link is 39 px high when focused, under the 48 px rule.
- The "needs an invite" page is titled "Sign up" in the tab; the invite error notice has no alert role.
- The help text is 13.6 px, the smallest text on the page, and carries the rules.
- The wordmark (32 px) outranks the task heading (22 px); the button sits 12 px under the last field, the same gap as between fields; at 1280 px the column hugs the top.
- Nothing on the first page a newcomer sees says the app does not handle money. After fix 1 that first page is Sign up, which today omits the one-line description.

## Constraints

1. **App direction.** `accounts` must not import `groups`. Sign-up already asks `groups` two things through registries in `accounts/signup.py` (`CHECKS`, `INVITERS`). Joining after sign-up needs a third of the same kind.
2. **Writes.** Joining a group is `groups.services.accept_invite`: it locks the invite and the group, increments `use_count`, writes an audit event and is safe to repeat. The view must call that service, not write.
3. **Two transactions.** Creating the account and joining the group are separate. If the invite stops being usable in between (used up by someone else, revoked), the account exists without a group. The fallback must be the existing invite page, which then explains the problem.
4. **Security.**
   - Making the invite page reachable while signed out reveals whether a token is valid. The sign-up gate already reveals that (403 or the form). Tokens are 32 random bytes.
   - The login error must keep one message that does not say which field was wrong.
   - `next` stays validated by `safe_next`.
   - Password rules do not change; only the words shown.
5. **Honest copy** (PRODUCT.md: plain words, no invented claims). The lost-password line must say what is true: there is no reset yet, and only the site administrator can set a new password.
6. **Sign-up must stay usable on a 390 × 844 phone.** More text above the form pushes the button down. The earlier criterion "the empty form fits without scrolling" may no longer hold with the description, the invite sentence and the password warning; the button must at least be reachable without hunting.
7. **Tests that pin today's flow.** `accounts/tests/test_signup_gate.py` asserts that signing up does not use the invite and that the visitor then posts to the invite page. `groups/tests/test_invites.py`, `accounts/tests/test_entry.py` and `web/tests/browser/entry.mjs` walk link → log in → sign up → join → group. These change with the flow.
8. **Other browser scripts** log in through `form.form-section [type=submit]`, `[name=username]` and `[name=password]`. Those must keep working.

## Options

**Lost password.**
- A. Warn now, build reset later (recommended; the human's scope is the critique's fixes).
- B. Build a host-issued reset link in this cycle. Larger: a new token model, a migration, a host screen and a set-password page. It is the real fix and deserves its own study.

**Joining after sign-up.**
- A. Join automatically when the account was created from that invite (recommended). Existing accounts keep the confirmation.
- B. Keep the confirmation and only reword it.

**Refused sign-up wiping passwords.**
- A. Accept it, and reduce how often it happens by stating the rules up front and focusing the refused field (recommended).
- B. Drop "Repeat password". Rejected earlier by the human's own decision while there is no reset.
- C. Write the password back into the page. Rejected, constraint 4.

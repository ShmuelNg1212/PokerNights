# Front door, second pass: plan

Status: approved 2026-10-17 ("approve the plan"); the three open questions as recommended. Date: 2026-10-17, Asia/Manila. Study: [Front door, second pass](../study/1792250537_front_door_second_pass.md).

Mode: design, with a small technical part. Visual authority: the built Rack and the 2026-10-09 front-door frame. No new colour, font, asset, token or motion world. No migration.

## OPEN QUESTIONS

Approving accepts each recommendation.

1. **Profile change-password form.** It also has a repeat field. Recommended: leave it in this cycle. A person who is logged in and changes a password is in a different situation. Say if you want one field there too.
2. **Invite count.** Recommended: count active members of the group, with or without a login, and say "players". A group of 1 reads "1 player".
3. **Inviter's name.** Recommended: the inviter's name in that group (`display_name`), not the username.

## Outcome

A newcomer reads who invited them, how many play, and what the app does, before the form. A returning player sees the form and a way to recover a password, and nothing else. The password rules answer while the person types. Sign-up has one password field.

## What you will see

**Log in**
- The chip and "PokerNights". No description.
- Heading, the two fields, Log in.
- Under the button, always: "Forgot your password? Ask a host of your group for a reset link." With `RESET_LINKS=False` the line uses today's no-reset words.
- After a failed login the notice shows; the forgot line is not shown twice.

**Sign up, not invited**
- Heading "Create your account".
- Directly under it, one line: "Keeps the books for your home poker game. It never moves money." (shortened from today's two sentences; see task 4).
- Username, Password, Create account. No "Repeat password". No description at the foot.

**Sign up, invited**
- Heading "Join {group}".
- Under it: "{Inviter} invited you · 8 players". If the inviter is no longer in the group: "8 players".
- Then the description line, then "Already have an account? Log in".
- The form as above.

**Password rules, on Sign up and Set a new password**
- Under the password field, two lines with a mark each: "At least 8 characters" and "Not only digits". Each one ticks when the typed password meets it, and unticks when it stops.
- Under them, plain: "We also check it is not a common password or like your username when you send."
- Before typing, both lines are neutral, not red. Nothing turns red before the person sends.
- The marks are icon and words, never colour alone. A screen reader hears the change through a polite live region, at most once per rule change.
- Without JavaScript, the lines are a plain list of the four rules, as today.

**Set a new password**
- One password field with the ticks. The rest is unchanged.

## Tasks

- [ ] **1. Branch.** Create `feat/front-door-2` from `main`.
  - Done when: the branch exists and the suite passes on it.
- [ ] **2. Tests first.** In `accounts/tests/test_entry.py` and the groups invite tests:
  - Log in has no description, and has the forgot line before any failure, once after a failure.
  - Sign up has the description directly after the heading, and no `door-foot`.
  - Sign up and reset render one password field. `password1` / `new_password1` keep their names and `autocomplete="new-password"`.
  - A valid invite shows the inviter's display name and the active-member count. Inviter gone: count only. Revoked, expired or used-up invite: no line.
  - A sign-up with one password creates the account; all four server rules still refuse.
  - Done when: these tests exist and fail for the right reason.
- [ ] **3. Server.**
  - `accounts/signup.py`: `invited_to` returns a small value with `group`, `inviter` (or None) and `players` (or None). The claim hook returns the group only.
  - `groups/apps.py` invite hook: fill `inviter` from `Invite.created_by`'s active membership in the group, and `players` from active members. One query each.
  - `accounts/forms.py`: `SignupForm` and `NewPasswordForm` drop the second password field. Keep `PlainWords`; remove the mismatch wording only if no form uses it.
  - Done when: task 2's server tests pass.
- [ ] **4. Templates and copy.**
  - `partials/entry_head.html`: remove the `line` use on Log in.
  - `registration/login.html`: the forgot line moves out of the error block to under the form.
  - `accounts/signup.html`: invite line, description under the heading, foot removed.
  - `accounts/reset.html`: one field.
  - `partials/entry_field.html`: a `rules` variant that renders the two rule lines and the note.
  - Copy for the description on Sign up: "Keeps the books for your home poker game. It never moves money." The link-preview sentence stays as it is.
  - Done when: all template tests pass.
- [ ] **5. JavaScript.** Add the rule ticks to `static/js/door.js` (no new module). Listen to `input` on the password field; update `data-met` on each rule line. Clean up on leaving the page, as `door.js` already does.
  - Done when: the browser check in task 7 passes; the page works with JavaScript off.
- [ ] **6. CSS.** In the entry section of `app.css`: the rule lines and their two states, with existing tokens only. The ticked state uses the existing positive colour and an icon. A tick change is a 120ms opacity and scale on the icon only; reduced motion turns it off.
  - Done when: the detector reports no new finding; text contrast is 4.5:1 or more.
- [ ] **7. Browser checks.** Update `entry.mjs` and `reset.mjs`; add cases to `door.mjs`. At 320 × 568, 390 × 844 and 1280 × 800:
  - no overflow; every control at least 48 px;
  - the empty invited Sign up shows its whole button without a scroll at 390 × 844;
  - typing "1234567" ticks nothing, "12345678" ticks length only, "abcd1234" ticks both; deleting unticks;
  - JavaScript off: the plain rule list shows and sign-up works.
  - Done when: these checks pass on a fresh seed.
- [ ] **8. Regression.** Both suites (SQLite and PostgreSQL). `entry.mjs`, `reset.mjs`, `claim.mjs`, `door.mjs`, `motion.mjs`.
  - Done when: all pass, or a failure is shown to fail on `main` too and is recorded.
- [ ] **9. Review.** `/impeccable critique` of Log in and Sign up, scored beside 29 of 40, then `audit` and `polish`; one fix batch. `security-review`, because the sign-up form changes.
  - Done when: the critique scores above 29 and the security review has no open finding.
- [ ] **10. Sync docs.** `doc/wiki/features.md`; `spec.md` section 6 behaviour; a DESIGN.md addendum for the rule lines; PRODUCT.md (remove the stale "no password reset yet" from the entry-flow addendum and record this change); the surface brief addendum; TODO.md phone checks; remove the front-door item from Next.
  - Done when: no page describes the old form.

## Acceptance criteria

- AC1. Log in shows no description and always shows the forgot line.
- AC2. Sign up shows the description directly under the heading and nothing under the button but the alternate link.
- AC3. A valid invite shows "{Inviter} invited you · N players"; with no inviter in the group, "N players"; an unusable invite shows neither.
- AC4. Sign up and Set a new password have one password field, and a password manager sees `autocomplete="new-password"` on it.
- AC5. Two rules tick live; the server still refuses all four; nothing turns red before sending.
- AC6. With JavaScript off, reduced motion or `DOOR_MOTION=False`, every screen is complete and every form works.
- AC7. Both suites and the listed browser checks pass.
- AC8. The repeat critique scores above 29 of 40.

## Out of scope

- The first step for a new player on the group page.
- The profile change-password form (open question 1).
- Claim-link wording.
- A server endpoint that checks a password before sending.
- The keyboard-covers-the-chip finding. It stays on the phone checklist.

## Rollback

Revert the feature commits. No migration and no stored data changes. Accounts made with one password field are ordinary accounts.

## Cannot be verified from here

A physical iPhone, a real password manager's save prompt on the one-field form, and a screen reader's announcement of the ticks. These go on the phone checklist.

## Progress and blockers

2026-10-17: Study and plan written after three questions to the human, all answered as recommended. Waiting for approval.

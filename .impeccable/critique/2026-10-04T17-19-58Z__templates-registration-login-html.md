---
target: the login and signup pages
total_score: 24
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 3
target_identity: "file:/Users/shm/PokerNights/templates/registration/login.html"
target_fingerprint: "sha256:18dbbacf7e2e44d46405eff807a453f8775792142208d771a0b49bda5585ad26"
target_path: /Users/shm/PokerNights/templates/registration/login.html
timestamp: 2026-10-04T17-19-58Z
slug: templates-registration-login-html
---
Method: dual-agent (A: a6c88c452e19446ae · B: ab96de73c30bfbefe)

# Critique: login and sign-up pages

Targets: templates/registration/login.html, templates/accounts/signup.html, templates/accounts/signup_closed.html, templates/groups/invite_accept.html. Score 24/40 (Acceptable).

## Design health score

| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of system status | 3 | Busy label on every button is "Sending…", not "Logging in…" |
| 2 | Match system / real world | 2 | "Username" is really the name friends see; errors are in Django's voice |
| 3 | User control and freedom | 2 | No password recovery; a refused sign-up wipes both passwords |
| 4 | Consistency and standards | 3 | Show button changes both its label and aria-pressed, which conflict |
| 5 | Error prevention | 2 | Username rules and the "too similar to username" rule are not stated |
| 6 | Recognition rather than recall | 3 | The newcomer must work out that "Log in" is not for them |
| 7 | Flexibility and efficiency | 3 | Password managers supported; the Join screen costs a step |
| 8 | Aesthetic and minimalist design | 3 | The wordmark outranks the task heading |
| 9 | Error recovery | 2 | Stock wording, no next step |
| 10 | Help and documentation | 1 | No "forgot password", no "what happens next" |
| | Total | 24/40 | Acceptable |

## Design specificity verdict

Half specific. The identity (mark, warm dark ground, bone button, the one-line promise) is this product's. The flow and wording are a generic account form and ignore that every production sign-up arrives by invite.

Detector: CLI scan exit 0 with 7 advisory `design-system-color` findings, all false positives (the `{% static %}` stylesheet link could not be resolved, so templates were read unstyled; the colour rules did not run against the real CSS). In-page detector injected on 8 page/width combinations: "No anti-patterns found" on all. Headless; no overlay shown to a human.

Measured: no overflow at 320/390/1280; all controls in main at least 48px; inputs 16px; lowest text contrast 7.33:1; focus ring 3px brass at 10.91:1; login page 8 requests, about 163 KB uncompressed on the dev server; works without JavaScript.

## What's working

1. The lockup and one-line promise tell a stranger what the app is in one glance.
2. Form mechanics: labels, autocomplete, errors tied to fields, 48px targets, no overflow with a 60-character group name at 320px.
3. The Show/Hide button: text not icon, reveals both sign-up fields, absent without JavaScript, reverts on submit.

## Priority issues

1. [P1] An invited newcomer lands on "Log in"; sign-up is a quiet link under the button (templates/registration/login.html:9, :18). Fix: with a usable invite, send signed-out visitors to Sign up first with "Already have an account? Log in" as the alternate. Command: /impeccable onboard.
2. [P1] A forgotten password cannot be recovered and nothing says so (no reset route in accounts/urls.py). Fix: state it under Password and add "Forgot it? Ask your host." under the login error; build reset (roadmap Stage 5). Command: /impeccable harden.
3. [P1] "Username" hides that it is the display name friends see (groups/services.py:219) and its character rules; spaces are refused with a sentence about "@/./+/-/_ characters". Fix: help text "Your friends see this name. Letters and numbers, no spaces."; longer term ask for "Your name" separately. Command: /impeccable clarify.
4. [P2] Errors are stock Django and a refused sign-up wipes both passwords. Fix: "That username and password don't match. Check capital letters."; "That name is taken. Try another."; focus the first empty or refused field. Command: /impeccable clarify.
5. [P2] The Join screen is a redundant step after sign-up (accounts/views.py redirect to templates/groups/invite_accept.html); "sets" is unexplained. Fix: join automatically when the account was created from that invite; keep the confirmation for existing accounts. Command: /impeccable onboard.

## Persona red flags

- Jordan (first-timer): "Log in" with no account; real name with a space is refused; never told the app does not handle money.
- Sam (screen reader, keyboard): Show button would read "Hide password, pressed"; up to three alert regions at once on a refused sign-up; autofocus skips the heading and invite sentence; skip link is 39px high and not the first Tab stop. Read from markup; no screen reader was run.
- Casey (one-handed, interrupted): refused sign-up clears both passwords; an expired invite leads to a page offering only "Log in".
- Invited player in Manila, phone, late at night: gets "Log in" first; 13.6px muted help text carries the rules in a dim room.

## Minor observations

- Wordmark 32px outranks the 22px task heading; lockup takes the top third before the first field.
- Button sits 12px below the last field, the same gap as between fields.
- At 1280px the column hugs the top.
- Login error sets no aria-invalid on either field.
- signup_closed.html is titled "Sign up" in the tab.
- The invite error notice lacks role="alert".
- logo-mark.svg is fetched twice (image and favicon).

## Questions to consider

1. If every production account starts from an invite, why is "Log in" the front door for an invite link?
2. Does a player need a password, or could a host-issued personal link replace sign-up?
3. Should the first thing a new player types be "Your name"?

Not covered: real iPhone rendering, an actual screen reader, the group page after joining, production compression and caching.

---
target: "front door: log in, sign up, set a new password (second pass)"
total_score: 33
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 1
target_identity: "file:/Users/shm/PokerNights/templates/registration/login.html"
target_fingerprint: "sha256:e1b5ef6fbbf41cc34865d20ecb806f939aecd9e22b9879e4a3b4d2fe0c3579f2"
target_path: /Users/shm/PokerNights/templates/registration/login.html
timestamp: 2026-10-17T16-12-06Z
slug: templates-registration-login-html
---
Method: dual-agent (A: design review · B: detector and browser evidence)

Target: the front door after the second pass (feat/front-door-2): Log in, Sign up (plain and invited), Set a new password. Previous score: 29 of 40.

## Design health score

| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of system status | 3 | Rules tick live with a polite announcement; keyboard may cover ticks and chip (phone check) |
| 2 | Match with the real world | 4 | "hana invited you · 9 players"; one "we" voice slip in the server note |
| 3 | User control and freedom | 3 | A refused sign-up empties the password |
| 4 | Consistency and standards | 3 | Rule list indented 18px by `.hint ul` |
| 5 | Error prevention | 3 | Two rules judged while typing; username hint states a rule the server does not enforce |
| 6 | Recognition rather than recall | 4 | Forgot line on Log in before any failure |
| 7 | Flexibility and efficiency | 4 | One field, Show, new-password autocomplete, next/go keys |
| 8 | Aesthetic and minimalist design | 3 | Five lines of muted text under the password field |
| 9 | Error recovery | 3 | The field error sits under the help, about 80px from the field |
| 10 | Help and documentation | 3 | Inviter and count named; no line says the account joins the group at once |
| **Total** | | **33/40** | Good |

## Design specificity verdict

Grounded in the head: "Join {group} / {inviter} invited you · N players", "It never moves money." and the chip. From Username down it is a stock form; the ring-to-check checklist is a common pattern.

Deterministic scan: exit 0; six `design-system-color` advisories, all false positives (templates scanned without the stylesheet). Live injection: one `bounce-easing` on Log in, the accepted arrival spring; Sign up and invited Sign up clean. Measurements: no overflow at 320/390/1280; all controls 48px; contrast 7.58 or more on every new line; invited Create account visible at 390x844 (ends 672px).

## What is working

1. The invited head carries social proof from real data, named only while the inviter is active.
2. The ticks change shape and colour, announce only changes, count code points as Django does, and respect reduced motion.
3. Log in is lean: heading, two fields, button, forgot line.

## Priority issues

- [P1] A refusal puts the error far from the field, under the rules and notes; after green ticks a "too common" refusal contradicts the checklist. Fix: render the error directly under the field. `/impeccable harden`
- [P2] `.hint ul { padding-left: 18px }` beats `.door-rules { padding: 0 }`; the rules are indented. Fix: raise specificity. `/impeccable polish`
- [P2] Five lines of muted text under the password field. Fix: fold the server rules into the list; move the reset note. `/impeccable distill`
- [P2] The invited head is four centred lines of near-equal weight; at 320x568 the button needs a scroll. `/impeccable layout`
- [P3] The username hint "Letters and numbers, no spaces" is wrong: Django also accepts _ . @ + - and one character. `/impeccable clarify`

## Persona red flags

- Jordan: green ticks, then "too common"; "9 players" does not say if Jordan counts; nothing says the account joins the group at once.
- Sam: the password field's description reads all help on every focus; the error is read last; the alert present at load may not be announced.
- Casey: at 320x568 the invited button is below the fold; with the keyboard up the ticks sit at the cut line (phone check).

## Minor observations

- Refused Log in: brass focus over red border reads as two alarms (unchanged).
- Dead reset-link page has an empty lower sheet (unchanged).
- Orphan "spaces." in the username hint.

## Questions

1. Does a half-green checklist help, or teach a newcomer to trust a signal the server then overrules?
2. The invite proves a host vouched for the person. Must the first night start with inventing a password?

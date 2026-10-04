---
target: the login and signup pages
total_score: 25
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 2
target_identity: "file:/Users/shm/PokerNights/templates/registration/login.html"
target_fingerprint: "sha256:b3a17733be80e961d9763b7ef136c53107adce07bcb38a90b42fb4f91f002c92"
target_path: /Users/shm/PokerNights/templates/registration/login.html
timestamp: 2026-10-04T17-44-36Z
slug: templates-registration-login-html
---
Method: dual-agent (A: abca7b8c13c9faf32 · B: a911014721b2e1644)

# Critique: login and sign-up pages (after the entry flow fixes)

Assessed before the final fix batch of this cycle. Score 25/40.

| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of system status | 3 | "Create account" does not say it also joins the group; arrival is a toast |
| 2 | Match system / real world | 3 | "host" and "site administrator" assume inside knowledge |
| 3 | User control and freedom | 2 | No self-service password recovery |
| 4 | Consistency and standards | 3 | Sign-up joins at once, log-in needs a second tap; two success sentences |
| 5 | Error prevention | 2 | Returning members were routed to a sign-up form; a taken name is found only on submit |
| 6 | Recognition rather than recall | 3 | The password must be remembered for good |
| 7 | Flexibility and efficiency | 2 | A returning host pays for the full lockup every time |
| 8 | Aesthetic and minimalist design | 3 | Lockup takes about 250px; password help runs to four lines |
| 9 | Error recovery | 3 | Plain field errors with focus moved; both passwords still wiped |
| 10 | Help and documentation | 1 | No help or contact; recovery is a two-person chain |
| | Total | 25/40 | Acceptable |

Design specificity: half specific. Voice and material are the product's; composition is a standard auth page. The invitation is a caption, not the subject.

Detector: CLI exit 0, 7 advisory design-system-color findings, all false positives (unresolved {% static %} stylesheet). In-page detector on 8 page/width combinations: no anti-patterns.

Measured: no horizontal overflow; all controls in main 48px; lowest text contrast 7.33:1; focus ring 3px at 10.91:1; one alert on refused login and on refused sign-up; focus lands on Password after a refused login and on the first refused field after a refused sign-up; busy label "Logging in…". Shortfalls: sign-up scrolls at every width (881–960 against 844); invited sign-up at 1280 put the button 4px below the fold; the refused sign-up puts the button below the fold; skip link moves no focus; Repeat password has no description.

Priority issues as assessed:
1. [P1] A returning member who opens an invite while signed out is sent to a sign-up form; the way to Log in was the last element on the page. FIXED after this assessment: "Already have an account? Log in" now sits with the invite sentence, before the first field.
2. [P1] Account recovery is a dead end and hidden until a login fails. OPEN: needs a real reset.
3. [P2] The hierarchy serves the brand, not the task or the invitation; sign-up no longer fits one phone screen. PARTLY: tagline widened to three lines, desktop offset limited to tall windows.
4. [P2] "No account? Sign up" on Log in led to a wall where sign-up needs an invite. FIXED after this assessment.
5. [P2] The invalid-invite page repeated itself and offered "Log in" as its main action. FIXED after this assessment.
6. [P3] Password help and error text pile up. OPEN.

Not re-scored after the fix batch.

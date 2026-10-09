---
target: "front door: log in and sign up"
total_score: 29
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 3
target_identity: "file:/Users/shm/PokerNights/templates/registration/login.html"
target_fingerprint: "sha256:2ffb669012698ec3dd830853a9984ba04cb14c57205f9886df0103a909b05051"
target_path: /Users/shm/PokerNights/templates/registration/login.html
timestamp: 2026-10-09T11-18-45Z
slug: templates-registration-login-html
---
Method: dual-agent (A: a2527e90457df0e89 · B: a235c4b66b1ad663c)

Target: the front door after the revamp of 2026-10-09 (Log in, Sign up and the shared frame). Earlier scores for this target: 24, then 25 of 40.

## Design health score

| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of system status | 3 | The button says "Logging in…" and the ring spins, but the chip may be off screen with the keyboard up |
| 2 | Match with the real world | 4 | "Your friends see this name", "Ask a host of your group" |
| 3 | User control and freedom | 3 | A key or tap ends the arrival; a refused sign-up clears both passwords |
| 4 | Consistency and standards | 3 | Log in leads with the description; Sign up carries it as a footer |
| 5 | Error prevention | 2 | Four password rules, checked only after sending |
| 6 | Recognition rather than recall | 3 | Forgot-password help appears only after a failure |
| 7 | Flexibility and efficiency | 3 | "Repeat password" is redundant beside Show |
| 8 | Aesthetic and minimalist design | 3 | The description on Log in and the empty lower sheet |
| 9 | Error recovery | 3 | Exact field errors and focus; the summary line adds little |
| 10 | Help and documentation | 2 | No inviter named on the invite |
| **Total** | | **29/40** | Good |

## Design specificity verdict

Half grounded. The chip-and-crescent mark, "Join {group}" and "It never moves money." belong to this product. Without the mark the sheet is a competent dark sign-in card. The specificity lives in the chip and its reactions; the sheet carries none of the group's world (no host, no players).

Deterministic scan: 12 findings. Nine `design-system-color` advisories are false positives (templates scanned without the stylesheet). `layout-transition` is the vendored Turbo progress bar. `bounce-easing` is the documented `arrive` spring on the chip. `gpt-thin-border-wide-shadow` is a true match on the desktop card only: a 1px rule edge with a 48px soft shadow. No overlay: no browser automation tool was exposed.

## What is working

1. "Join {group}" with "Create your account to get in." answers why the visitor is here.
2. Refusals: no arrival, focus on the refused field, one shake, words that say what to do.
3. The mark is drawn in the page and moved in parts, with no raster and no casino cliché.

## Priority issues

- **[P1] The description is placed for the wrong audience.** Returning hosts read it on every Log in; newcomers on Sign up get it under the button. Fix: one line under the Sign up heading; drop or shorten it on Log in. Needs the human: it reverses approved decision 3 and removes copy. `/impeccable clarify`
- **[P1] The invite gives no social proof.** "Join Kamuning Card Club" names the group, not who invited or how many play. Fix: "Invited by Hana · 8 players". A new cycle: it shows data the page does not have today. `/impeccable onboard`
- **[P1] The chip's reactions may be hidden by a phone keyboard.** Computed, not observed. Fix: check on a phone; if confirmed, move the answer to the focused field or the button. `/impeccable animate`
- **[P2] Sign-up friction.** Repeat password beside Show, cleared passwords after a refusal, rules judged only by the server. `/impeccable harden`
- **[P2] Empty lower sheet** on Log in and on dead-link pages. `/impeccable layout`

## Persona red flags

- First-timer on a small phone: unknown brand, no inviter, explanation below the fold at 320px.
- Returning host, one hand: the hero pushes the form to mid-screen; no forgot-password line before a failure.
- Keyboard and screen reader: an alert present at page load is not reliably announced; the title does not change on an error.

## Minor observations

- No `enterkeyhint` on the fields (fixed in the batch after this critique).
- The brass focus ring over a red invalid border reads as two alarms.
- The password hint mixes rules with advice about the future.

## Questions

1. If the chip's reactions were deleted, would a phone user notice?
2. Why does a product built on "a host vouches for you" open with a password form and not the host's name?

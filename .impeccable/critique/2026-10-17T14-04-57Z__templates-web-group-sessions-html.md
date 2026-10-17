---
target: the group Sessions tab
total_score: 32
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 0
target_identity: "file:/Users/shm/PokerNights/templates/web/_group_sessions.html"
target_fingerprint: "sha256:07cfbfe670bb9e25f940b6b407dcf15233fa117209a500fe92b1f86197baa8c0"
target_path: /Users/shm/PokerNights/templates/web/_group_sessions.html
timestamp: 2026-10-17T14-04-57Z
slug: templates-web-group-sessions-html
closed: true
---
⚠️ DEGRADED: single-context (AGENTS.md allows subagents only during execute; Assessment A was done before Assessment B ran)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|---|---|---|
| 1 | Visibility of System Status | 3 | Live clock, set state, "You're playing"; settle state in words |
| 2 | Match System / Real World | 4 | Table, set, "8 at the table", "You pay Carlo ₱200" |
| 3 | User Control and Freedom | 3 | Plain links; year folds away |
| 4 | Consistency and Standards | 3 | Two bone actions when seated at two tables |
| 5 | Error Prevention | 3 | Drafts hidden from players; nothing destructive |
| 6 | Recognition Rather Than Recall | 4 | Your table marked and first; your debt on the row |
| 7 | Flexibility and Efficiency | 3 | One tap to the table |
| 8 | Aesthetic and Minimalist Design | 3 | Dense past rows with two debt lines on a phone |
| 9 | Error Recovery | 3 | "Now playing" over "No session in progress" |
| 10 | Help and Documentation | 3 | Empty states explain the prerequisite |
| **Total** | | **32/40** | Good |

## Design Specificity Verdict
LLM: product-specific (felt card, seat chips, clock, "You're playing"; ledger in the room's words).
Deterministic: CLI 3 advisories, all false positives (partials without the stylesheet). In-page 11 per view, none in new code: 10 chip edge-band samples, 1 possible k6 chip contrast 3.8:1 (existing palette), body texture (existing).

## Priority Issues
- [P2] Two bone actions when seated at two tables. Fix: bone only on the first card that is yours. /impeccable polish
- [P2] The card link's spoken name is the whole card. Fix: aria-labelledby title, state and "You're" line. /impeccable harden
- [P2] "Now playing" over "No session in progress". Fix: "Nobody is playing". /impeccable clarify

## Persona Red Flags
Riley (host): two equal bone buttons. Sam (screen reader): long link names. Ben (player): none.

## Minor Observations
Long table name plus large still-to-pay wraps on a phone. k6 chip initials 3.8:1 (existing). Status words repeat the coloured debt.

## Questions to Consider
Should a next-week draft sit under "Now playing"? Does a seated host need the pot on the card?

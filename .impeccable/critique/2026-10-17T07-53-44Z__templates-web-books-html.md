---
target: end-of-set screens when the books do not balance
total_score: 24
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 2
target_identity: "file:/Users/shm/PokerNights/templates/web/_books.html"
target_fingerprint: "sha256:9c4a50e6ba972d5a7e473453f18167fdc9f6a563f003d58065e51185288f8b78"
target_path: /Users/shm/PokerNights/templates/web/_books.html
timestamp: 2026-10-17T07-53-44Z
slug: templates-web-books-html
---
# When the books do not balance: critique (2026-10-17)

DEGRADED: single-context (no sub-agents requested). Rendered: sets 9 (₱100 missing), 10 (override), 2 (count-up in progress) at 390 and 1280, host and player.

| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of status | 3 | Coral in the books, amber ⚠ in the host bar for the same fact |
| 2 | Match real world | 3 | "Off by −₱100" says the direction twice; rake mentioned with no rake |
| 3 | User control | 3 | Reverse, override, remove override exist |
| 4 | Consistency | 2 | Two severities; override drawn as the green balanced state; override summary has no chevron |
| 5 | Error prevention | 2 | Nothing points at the likely culprit |
| 6 | Recognition vs recall | 2 | Host compares each player's sheet from memory |
| 7 | Flexibility/efficiency | 2 | "See the ₱100 difference" links to #balance, already in view: a dead tap |
| 8 | Minimalist design | 2 | Players see ₱100 three times; 6+ line panel |
| 9 | Error recovery | 2 | Generic list of causes |
| 10 | Help | 3 | Inline guidance present |
| Total | | 24/40 | Fair |

Detector: 3 advisory "black text" findings on partials, false positives (the stylesheet isn't loaded when partials are scanned on their own).

## Priority issues
- [P1] Host bar's main button is a dead tap (_host_controls.html:56 → #balance already in view). Fix: scroll so the books sit under the header and pulse the panel once; later, jump to the first suspect row.
- [P1] Player rows sit at y=678 under the fixed host bar (665) at 390×844: the screen hides where to look. Fix: shorten the panel; give each cashed-out row "₱1,000 in · ₱900 out · −₱100"; mark in brass any row whose cash-out differs from its confirmed count.
- [P2] One fact, three statements, two severities (books panel, Confirmed counts, host bar). Fix: once everyone is cashed out the books panel is the one statement; drop "0 still to count."
- [P2] Players are told to reverse records they cannot touch. Fix: "The host is checking the records." plus their own in/out line.
- [P2] An override is drawn as success (green double rule). Fix: neutral with a brass rule; green only for books that truly balance.

## Motion
The gap arrives with `shift` once; when fixed, the panel leaves with `leave` and the existing balanced reveal plays; the button gets a pulse. No shake, no counting digits, nothing on the running total.

## Minor
_balance.html unused; "0 still to count." noise; rake wording branch; green on a losing cash-out; desktop repeats the gap under Host controls.

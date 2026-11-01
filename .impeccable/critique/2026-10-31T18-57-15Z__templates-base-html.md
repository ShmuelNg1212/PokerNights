---
target: PokerNights signed-in app, baseline before Slice E
total_score: 26
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 2
target_identity: "file:/Users/shm/PokerNights/templates/base.html"
target_fingerprint: "sha256:91eb0221004771dfe8fa8cca6f18abf9bab1a25f6b8c8483d895f470c7252ba7"
target_path: /Users/shm/PokerNights/templates/base.html
timestamp: 2026-10-31T18-57-15Z
slug: templates-base-html
---
Method: dual-agent (A and B isolated). Detector ran by URL through a GET-only proxy, because engine 0.1.15 has no --cdp.
Baseline before Slice E of doc/plan/1793431937_ui_revamp.md. Captures: /private/tmp/pn-surfaces-baseline.

Heuristics: 1 Status 3; 2 Real world 3; 3 Control 3; 4 Consistency 2; 5 Error prevention 3; 6 Recognition 2; 7 Efficiency 3; 8 Minimalist 2; 9 Recovery 3; 10 Help 2. Total 26/40.
Scale for later runs: 4 excellent with no material exception; 3 good with exceptions on secondary paths; 2 the exception appears on main paths.
Design specificity: authored at the table; category-default on settings, forms and empty states.
Priority issues:
- P1 On a phone, cash-out cannot be found without already knowing it. The only instruction sits at the page foot, past the dock.
- P1 The recount main button does not advance the repair. The repair instruction is folded, and the difference is restated four ways.
- P2 State and disclosure vocabulary differ (Final/Finalized, Session open/In progress, five disclosure forms, Host badge neutral and green).
- P2 Too many frames and undersides, head too tall and repetitive. Title gap 9 px, tabs end 204 px, 20 frames on Sessions, 8 undersides on a set in play.
- P2 "Now playing" holds Canceled and Draft. Money text under 13 px. Thin empty states; the Stats tab disappears when empty.
Detector: 175 findings. A judged 171 false (chip gradients, pill markers, unstyled fragments); 2 literal but misattributed stripes; 1 accurate flat hierarchy on /n/1/; 1 stripes on /s/3/.

# Critique: templates/web/profile.html (2026-10-17)

Method: dual-agent (A: design review · B: detector and browser evidence). Score 29/40.

Priority issues and outcome:
- [P1] Settings far below the stats: added a "Name and password" link under the name (order kept, approved by the human).
- [P2] Group rows did not look tappable; separator curled: chevron on linked rows, straight separators.
- [P2] Zero read as a loss: "Even".
- [P2] Long group name cut: two lines, full name in title.
- [P3] Tile dates broke mid-date: no year for this year. "Touch the chart" left as shared copy.

Detector: CLI clean (3 advisory false positives from unstyled templates). Overlay: chip and pill contrast were sampling errors; body halo and stripes are the app's ground, not this branch.

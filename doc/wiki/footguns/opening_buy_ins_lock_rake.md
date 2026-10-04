# Default opening buy-ins lock the rake rule

- **Trigger:** Start the game records the checked usual opening buy-ins while rake is Off.
- **Observed behavior:** Rake controls are disabled after accepted money exists. Opening buy-ins count as money; the lock is not a broken enable switch.
- **Impact:** A host cannot enable or change rake for that set while its accepted money remains.
- **Evidence:** `games/tests/test_rake_controls.py` verifies configuration before start, exact opening fees, disabled controls and ordinary stakes edits. `web/tests/browser/rake_controls.mjs` verifies native initial and later-set setup.
- **Remedy:** Choose Off, Flat amount, or Percentage of buy-in in New session. For a later empty set, use Choose rake before buy-ins before Start the game. The written lock reason explains recorded and default opening buy-ins. Do not rewrite existing fees or charge historical buy-ins.

A separate fixed defect let an unused percentage of zero or malformed text block Flat/Off. Shared form parsing now validates only the chosen value and normalizes unused fee parameters to zero.

# A chip draft can hide the confirmation check

Date: 2026-10-28, Asia/Manila.

**Trigger.** A count row has a hidden chip-draft field between its amount field and its confirmation check.

**Observed behavior.** An adjacent-sibling CSS selector no longer finds the check. The count saves and the check's drawing animation runs, but the check stays transparent.

**Remedy.** In `static/css/app.css`, match the check as a later sibling of `input[data-count-input]`. Show it only when the amount field is empty and has a saved count. This keeps unsaved edits unmarked. Reduced motion shows the accepted check without movement.

**Evidence.** `chip_batch.mjs` checks chip and typed confirmations, unsaved drafts, edits and reduced motion. Before the fix, the two confirmed-check checks fail. After the fix, all 21 browser checks pass. The 1,478-test suite passes with 17 PostgreSQL-only skips. An independent motion review approved the change.

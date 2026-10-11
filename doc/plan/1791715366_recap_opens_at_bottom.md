# The session recap opens at its top: plan

Status: awaiting approval. Date: 2026-10-11, Asia/Manila. Study: [The session recap opens at its bottom](../study/1791715365_recap_opens_at_bottom.md).

## Outcome

The session recap opens showing its first line, whether it opens by itself or from "View session recap". "Share results" stays where it is, as the last line.

No migration, no new words, no visual change.

## Implementation

Branch `fix/recap-opens-at-top` from `main`.

1. **Reproduce.** Run `night.mjs` and see "recap reopens at its top" fail; add a check that the recap opened by itself is also at its top.
2. **`templates/web/night.html`:** the recap's source says it is for reading (`data-sheet-reads`).
3. **`static/js/sheets.js`:** for such a sheet `open()` puts the focus on the sheet's Close button instead of the first button in the content. The same rule in `swap()`, so coming back from the share sheet would behave alike if that path is ever added.
4. **Measure the share sheet** on the longest fixture; if its first button is below the first screen, it gets the same start. Reported either way.
5. **Tests.** `night.mjs` (the failing check passes, the new one passes, nothing else changes), `share.mjs`, `night_live.mjs`. Django suite on SQLite; PostgreSQL before release.
6. **Documents.** Wiki features (one line under the recap), TODO.md.

## Acceptance

1. A closed session's recap, opened either way, shows its heading and first section, not "Share results".
2. Focus is on Close; Escape and Tab work as before.
3. `night.mjs` has no failure left from this cause.

## Release

Kept local until you say to push.

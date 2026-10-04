# A form per row, and a live refresh, both lose unsaved typing

- **Trigger:** A list where each row has its own form and field, on a page that people fill in for several rows before saving. Or any typed field inside the live region of the set page.
- **Observed behavior:** A submit sends one row. The page reloads and the other typed fields are empty. Separately, `live.js` replaces the whole live region on an update, which also empties typed fields.
- **Impact:** A host typed final counts for several players, tapped one "Confirm count", and lost the rest (reported 2026-10-04). Saved data was not affected.
- **Evidence:** A headless-browser reproduction failed 7 of 11 checks on the old code and passes on the fix. The first tests confirmed one row at a time and did not see it.
- **Remedy:** When rows are filled together, put their fields in one form (the `form` attribute lets fields sit anywhere) and save them in one transaction. Give each typed field in the live region a `data-keep` key. Test a page the way a person uses it: several fields first, then one tap.

## 2026-10-04 addendum: counter and refused defaults

A live redraw originally emitted `live:updated` before restoring drafts. A derived counter could therefore read blank fields. Also, a refused submission renders drafts as input defaults; comparing value against defaultValue alone drops those drafts on a later poll.

The live script now restores fields and disclosures before emitting the event. It retains every nonblank eligible count input, including refused defaults. The synthetic two-host browser check verifies that an invalid refused draft remains unavailable after another host confirms a count and polling redraws the page. Saved amounts remain server records; retained drafts remain local previews.

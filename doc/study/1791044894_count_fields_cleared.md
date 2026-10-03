# Study: typed counts are lost when one count is confirmed

- **Date:** 2026-10-04 00:28 (Asia/Manila), Unix timestamp `1791044894`
- **Report:** "there is a bug where if i click confirm count all the fields empty."
- **Workflow:** `agentic-workflow`, Phase 1 of a short cycle. No code changes before approval of the plan.

Labels: **FACT** = verified in the code today. **REC** = recommendation.

## 1. What happens

While counting up, each player row has a "Final count" field and its own "Confirm count" button. A host who types several counts and then taps one button keeps one count. The other fields come back empty.

## 2. Causes (FACT)

**Cause 1, the reported one.** In `templates/web/_players.html` each row is a separate form. A tap on "Confirm count" sends only that row's field. The server saves it and reloads the page. Nothing saved the other fields, so they are empty after the reload.

**Cause 2, the same loss by another path.** `static/js/live.js` replaces the live region when the set changes. It waits while a field has focus, and applies the update when focus leaves the field. An update replaces the whole region, so each typed and unsaved value in it is lost. This happens when another host, or an earlier confirmation, changes the set while the host is typing: moving from one field to the next clears what was typed.

The same two causes affect any typed and unsaved field on the set page, for example a buy-in amount or a reversal reason. The count fields make it visible, because a host types several before saving.

No data is damaged. Saved counts are correct. Only unsaved typing is lost.

Why the tests missed it: the tests and the browser check confirmed one count at a time.

## 3. Options

| Option | Pros | Cons |
|---|---|---|
| **A. One submit confirms every filled count** | Matches how a host works: type all, confirm once. Also faster | A new service that confirms several counts in one transaction |
| B. Keep one form per row and warn about unsaved fields | Small | The host still loses the work, with a warning |
| C. Save each field as it is typed | No button | A half-typed number would be saved as a count. Counts must be explicit |

**REC: A, plus a fix for cause 2.**

## 4. Recommended design

- All count fields of the set belong to one form. Each "Confirm count" button, and a new "Confirm all counts" button under the list, sends every filled field.
- A new service confirms them in one transaction. An empty field is skipped and stays "not counted"; it is never read as zero. A field that holds the player's current count is skipped too, so no needless new version is made.
- If any field is invalid, nothing is saved, the message names the player, and the page shows again with each typed value still in its field.
- The live refresh keeps typed, unsaved values: before it replaces the region it reads each field that has a stable key, and puts the values back afterwards.
- A repeated submission is a no-op, through the form's `request_id`, as elsewhere.
- No model changes. No migration.

## 5. Risks

| Risk | Mitigation |
|---|---|
| A host expects one button to save one row | Every button saves all filled fields, so nothing typed is lost either way. The message says how many counts were confirmed |
| Restored values after a refresh hide a change made by another host | The restored value is the host's own unsaved typing. Status badges and the "Counted" line next to it still show the saved state |

## 6. Open questions

None that block. The plan states the behavior for review.

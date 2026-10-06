# Copy link button: plan

Status: approved 2026-10-06 ("approved. can the button be within the field instead."), with the button inside the field. Date: 2026-10-06, Asia/Manila. Study: [Copy link button](../study/1791265489_copy_link_button.md).

## Outcome

A host who has just created an invite link or a password reset link copies it with one tap and is told that it worked.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new colour, font or asset. No migration; nothing on the server changes.

## Behaviour

- Under the read-only field of a new **invite link** and a new **password reset link**, a full-width button **Copy link**.
- A tap copies the whole address. When the browser confirms, the button reads **Copied** with a check for two seconds, then returns to "Copy link". A screen reader hears "Link copied."
- If the browser refuses, nothing claims success: the address in the field is selected and a line under the button says "Could not copy. The link is selected: copy it from the menu."
- The field stays, and still selects its text when tapped.
- Without JavaScript the button is hidden and the page is as it is today.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **Words:** "Copy link", "Copied", and the refusal line above.
2. **Place and size:** under the field, full width, 48 px high. The alternative is a small button beside the field, which leaves less of the address visible on a phone.
3. **No share sheet** in this cycle (sending the link straight to a chat app). Say so if you want it next.

## Implementation

1. **`static/js/copy.js`** (new, registered with `page.js`, loaded from `base.html`). For each `[data-copy]` button: show it; on a tap, write the value of the field named by `data-copy` with `navigator.clipboard.writeText`; on success set the label and the status line and restore them after two seconds; on refusal, or where the clipboard does not exist, select the field and show the refusal line. The stop function clears the timer and the listeners.
2. **`templates/web/_group_settings.html`.** Each of the two notices gets an id on its field, the hidden button with `data-copy`, and an empty polite status line.
3. **CSS.** Spacing between the field and the button only, if the existing stack does not already give it.
4. **Tests first.**
   - `web/tests`: each notice carries a hidden button that names its own field, and `base.html` loads the script; nothing is rendered when no link was just created.
   - Browser check `copy.mjs` on a fresh database: with clipboard permission granted, a tap on each button puts exactly the shown address on the clipboard, the label reads "Copied" and returns; with the clipboard refused, no "Copied", the field is selected and the refusal line shows; leaving the screen and coming back does not double the listeners; without JavaScript the button is not visible; 48 px target, contrast, and no overflow at 320, 390 and 1280 px.
5. **Verify.** SQLite and PostgreSQL suites; `copy.mjs`, then `reset.mjs`, which uses the same notice. Captures inspected.
6. **Sync docs.** Wiki features, DESIGN.md addendum, browser README, TODO. The same commit records the password reset release, which the human pushed on 2026-10-06.

## Acceptance criteria

- AC1. One tap on Copy link puts the complete invite or reset address on the clipboard.
- AC2. "Copied" appears only after the browser confirms the copy.
- AC3. When the copy is refused, the host is told and the address is selected in the field.
- AC4. Without JavaScript, or if the script fails, the page works as it does today.
- AC5. The button is a 48 px target and the result is announced to a screen reader.
- AC6. No model, service, address or migration changes. Existing tests pass on SQLite and PostgreSQL.

## Out of scope

- The share sheet.
- Showing a link a second time, or copying a link from the list of active invites (only hashes are stored).
- A copy button anywhere else.

## Rollback

Revert the feature commit. No data change.

## Progress and blockers

2026-10-06: Study and plan complete. Waiting for the human's approval. No code written.

2026-10-06: The human approved and asked for the button inside the field instead of under it.

2026-10-06 execution on `feat/copy-link`.

Changes from the plan:

- **The button is inside the field's right edge**, as the password Show button is, at the human's request (decision 2). It reads **Copy**, then **Copied**, with the accessible name "Copy link". The address is cut with an ellipsis before the button. There is no check mark: the word changes and turns green.
- The refusal line appears under the field.
- The tests and the code were written together, not tests first.

2026-10-06 verification:

- 748 tests pass on SQLite (twelve PostgreSQL-only skips) and all 748 on local PostgreSQL 17, started for the run and stopped after. Four new tests in `web/tests/test_copy_link.py`.
- `copy.mjs`: 33 of 33 on a fresh temporary database, for the invite link and the reset link: the exact address reaches the clipboard, "Copied" follows the browser's confirmation, a refused or missing clipboard selects the address and says so, one copy per tap after the page scripts restart, hidden without JavaScript, 48 px, contrast, and 320, 390 and 1280 px. `reset.mjs`: 43 of 43 afterwards.
- Captures inspected at 390px: Copied on the invite link and the refusal on the reset link.

Acceptance: AC1 to AC6 are met.

Not verified: a physical phone. The clipboard was tested in desktop Chrome only; Safari on an iPhone and the installed app decide for themselves whether to allow a copy.

Documentation synced: wiki features, DESIGN.md, browser README, TODO.

2026-10-06 correction: the first full run after the merge had one failure, `web.tests.test_inplace.ScriptsLoadOnceTests`, which lists the scripts in `base.html` in order and did not know `copy.js`. The feature commit and the merge were made before that result was read. The test's list was updated in the next commit; the 748 figures above are from the runs after that fix, on both engines.

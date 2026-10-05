# Actions update in place (stage 3): plan

Status: approved 2026-10-05 ("ok lets focus on turbo for now. approved."); decisions as recommended. Date: 2026-10-05, Asia/Manila. Study: [Actions update in place](../study/1791178826_actions_in_place.md). Programme: [app-like experience](1791172782_app_like_experience.md).

## Outcome

On the set page and the session page, a buy-in, rebuy, cash-out, count, set transition or paid mark updates the screen without a reload. The host stays where they were on the page, text typed elsewhere stays, and open sections stay open. Everything still works as a native form without JavaScript.

No migration. No change to any service, rule or message.

## Approach

Turbo 8.0.23 as one vendored file, with **navigation switched off by default**. It is switched on only for the forms listed below. Links are untouched in this stage; that is stage 4.

### In scope: forms that return to the page they were sent from

- **Set page:** buy-in and rebuy, cash-out, confirm and clear counts, the set transitions (open, start, end, resume, back to draft, cancel), add one player, withdraw, mark left, reversals and overrides, finalize.
- **Session page:** mark paid, undo.

### Out of scope in this stage (they keep reloading)

- Forms that lead to another page: close session, next set, cash out counted players, New session, group settings, archive and delete, log in, sign up, log out.
- Forms that re-render with errors and status 200. They need their status changed first; that belongs with stage 4.

## What must be true, and how each is proven

Each line is a test written before the code. The first five come from the trial's findings.

1. **Typed values survive.** Text typed in another field (a count, a cancel reason, a reversal reason) is still there after an in-place update. Uses the existing `data-keep` marks.
2. **Open sections survive.** A disclosure with `data-key` that was open stays open.
3. **A fresh form after every update.** After a rebuy from a sheet, opening the sheet again carries a new `request_id`, and a second rebuy is recorded as a second buy-in. This is the hazard the trial found.
4. **A refused amount keeps the sheet open** with the error beside the field and the typed amount intact, as today.
5. **No page from a cache.** Turbo's page cache and previews are off; going back never shows an older ledger.
6. **Success only after the server answers.** The button shows its busy state until then; nothing on the page changes before.
7. **One tap, one record.** A double tap sends once; a repeated `request_id` records once.
8. **A failed send says so.** With no connection or a server error, the page shows a failure message, changes nothing and leaves the form ready to send again. It never looks like success.
9. **The 4-second poll keeps working** alongside, and the two never fight: no duplicate refresh that discards typing, no stale version.
10. **Keyboard focus** returns where it does today: to the control that opened the sheet, or stays on the pressed button.
11. **Screen readers** hear the success message once.
12. **Without JavaScript** every form behaves exactly as before.
13. **The library is not re-downloaded on each release.** It is served from an address that carries its own version, cached for a year.

## Implementation

1. **Vendor the file** at `static/js/vendor/turbo-8.0.23.js` with its licence. Exempt `js/vendor/` from the per-release tag so the address is stable (constraint 5). Loaded from `base.html` after `app.js`.
2. **`static/js/turbo-setup.js`** (small): switch navigation off by default; switch the page cache off; preserve `data-keep` values, `data-key` disclosures and `data-focus-key` focus across a morph; show the failure message for a failed send; announce nothing twice.
3. **Templates.** Mark the in-scope forms. Mark the sheet container and the offline notice so a refresh leaves them alone. Two meta tags for morph refresh and scroll preservation on the set and session pages only.
4. **`sheets.js`.** After an in-place update: close on success with a fresh form left in the page; stay open with the error on refusal. The existing "reopen after a refused full reload" path stays for the no-JavaScript and failure cases.
5. **`live.js`, `forms.js`, `toasts.js`, `changes.js`, `counts.js`, `dock.js`, `clock.js`.** Each already reacts to `live:updated`; an in-place update raises the same event, so they need no new logic. Toasts are created for messages that arrive in an update.
6. **Tests first.**
   - Django: the in-scope forms carry the mark and the out-of-scope ones do not; the meta tags are on the two pages only; the vendored file is served unversioned.
   - Browser check `inplace.mjs`, one check per line of the list above, at 390 px, for: rebuy, cash-out, count confirm with a typed count in another row, end play, resume, mark paid, undo, a refused amount, a double tap, a send with the server stopped, and two hosts acting on one set.
   - The probe from the study, kept as a script, with its before and after numbers recorded.
   - Every existing browser script must pass: `dock`, `archive`, `settled`, `entry`, `session_form`, `install`.
7. **Verify.** SQLite and PostgreSQL suites, including the concurrency tests; all browser checks.
8. **Release** to production, check the live site, and give the human a short phone checklist.
9. **Sync docs.** AGENTS.md is the human's file for the stack rule, so the dependency is recorded in the wiki's external-dependencies page, DESIGN.md (no visual change; behaviour note), wiki features and architecture, browser README, TODO and the programme plan. The spike branches are deleted.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **Turbo, not our own module.** Recommended, for the reasons in the study: it is also the mechanism for stage 4. The alternative is the 2.4 KB module from the trial, limited to these two pages, with stage 4 decided separately.
2. **Forms only in this stage; links wait for stage 4.** Recommended. It keeps this release small and keeps every page's scripts running exactly as they do now.
3. **Scope: the set page and the session page.** Recommended. These are the actions a host repeats during a game. Group settings and the forms that change page stay as they are for now.
4. **The stack rule.** AGENTS.md says no front-end framework without a recorded requirement. This plan is that record: one vendored file, pinned version, no build step. If you want AGENTS.md itself to mention it, that edit is yours to make or to ask for.
5. **Size.** 46 KB compressed, downloaded once and then cached for a year. Recommended to accept.

## What I cannot verify

- How it feels on your phone. The checklist after release: record a rebuy from the bottom of a long player list and check you stay there; type a count, confirm a different one and check the first is still typed; mark a transfer paid; turn on Airplane Mode and try a rebuy.
- Items 5 and 13 on a real iPhone's back gesture and cache.

## Acceptance criteria

- AC1. For each in-scope action the page does not reload and the scroll position stays within a few pixels.
- AC2. Lines 1 to 13 above each pass their test.
- AC3. The probe's requests for a rebuy fall from 16 to 3 or fewer locally.
- AC4. All existing tests pass on SQLite and PostgreSQL; all existing browser checks pass; every flow works with JavaScript off.
- AC5. Before-and-after numbers are recorded in this plan.

## Out of scope

Links and screen changes (stage 4); forms that lead to another page; forms that re-render with status 200; any visual or motion change (stage 6); replacing the 4-second poll.

## Rollback

Remove the script tag from `base.html` and release: every form goes back to a native reload, because the marks do nothing without the library. Then revert the commits.

## Progress and blockers

2026-10-05: Study with a two-spike trial, and plan. The human approved with “ok lets focus on turbo for now. approved.”

2026-10-05 execution on `feat/actions-in-place`. The behaviours were explored in the browser check as they were built; the check and the Django tests were completed alongside, not strictly first.

Verified against Turbo's source and by test, where the study had only cited documentation:

- `Turbo.session.drive = false` switches navigation off, and `data-turbo="true"` on a form switches it on for that form.
- **Found by test:** Turbo also requires the *pressed button* to be inside a marked element. The count-up buttons submit `#counts-form` from outside it, so the first run reloaded the page. They are marked too.
- `turbo:before-morph-element` and `turbo:before-morph-attribute` can be cancelled; that is how typed values and open disclosures are kept.
- `data-turbo-permanent` keeps the sheet container and the offline notice through a morph.
- `turbo:before-fetch-response` can be cancelled; that is how an answer that is not a same-page update falls back to an ordinary load.

Changes from the plan:

1. **Typed values are kept unless the field belonged to the form just sent.** A confirmed count must come back empty, while a count poll must keep it; the rule distinguishes the two.
2. **An error after an in-place update floats as a toast.** Not in the plan: with the scroll position kept, a message at the top of the page would be out of sight.
3. **A refusal in a sheet takes the page's fresh `request_id`** as well as keeping the sheet open.
4. **Scroll is judged by the tapped control staying under the finger,** not by the raw scroll number. When a row grows by a line above the control, the browser keeps the control in place and the number changes by that line.
5. **The vendored file is named with its version** and exempt from the per-release tag, as planned; the licence is beside it.

Measured with `probe_rebuy.mjs`, a rebuy from a sheet on a running set, local server:

| | Before | After |
|---|---|---|
| Page reloaded | yes | no |
| Requests | 16 (2 documents) | 3 (the POST, the refreshed page, the logo image) |
| Typed text elsewhere kept | no | yes |
| Open section kept | no | yes |
| Refused amount keeps the sheet open | yes | yes |

2026-10-05 verification:

- 632 tests pass on SQLite (ten PostgreSQL-only skips) and all 632 on local PostgreSQL 17, started for the run and stopped after. Six new tests in `web/tests/test_inplace.py`.
- `inplace.mjs`: 37 of 37 on a fresh temporary database, one check per line of the plan's list.
- With Turbo loaded on every page: `dock.mjs` 145, `archive.mjs` 85, `settled.mjs` 24, `entry.mjs` 91, `session_form.mjs` 69 and `install.mjs` 33 all pass.

Acceptance: AC1 to AC5 are met, with these limits.

- Line 8 (a failed send) is tested for a server that cannot be reached. The 5xx branch is written but **not exercised by a test**; no view can be made to fail on demand.
- Line 10: focus returns to the sheet's opener (tested). After mark paid or a set transition the pressed button no longer exists, and focus is not placed anywhere in particular; before this stage a reload put it at the top of the page.
- Line 11: one message in the status region is tested; no screen reader was run.

Not verified: a real phone; an iPhone's back gesture with the page cache off; the installed (full-screen) app.

Documentation synced: wiki external dependencies (the recorded library exception), features and architecture, DESIGN.md, browser README, TODO. The spike branches `spike/own` and `spike/turbo` are deleted.

2026-10-05 release: pushed `main` at `1ad5d20` (previous production commit `31028b1`). Checked on the live site: the library is served from `/static/js/vendor/turbo-8.0.23.js` with a one-year immutable cache, compressed to about 50 KB, and its checksum matches the vendored file; `turbo-setup.js` carries the release tag; Turbo is loaded with navigation off; the login form still loads a page the ordinary way; no script error on the login page. Signed-in behaviour on production is not checked by the agent (no account); the human's phone checklist is in TODO.md.

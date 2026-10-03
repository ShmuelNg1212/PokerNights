# Plan: visual redesign slice 2

- Date: 2026-10-04, Asia/Manila. Shell timestamp: `1791050738`.
- Status: `done`.
- Study: [slice 2 revalidation](../study/1791050655_redesign_slice_2.md).
- Parent: [visual redesign, task 8](1791046015_visual_redesign.md).
- Sources: `SPEC.md`, `AGENTS.md`, `PRODUCT.md`, `DESIGN.md`, current wiki and the original visual study.
- Baseline: clean `main` after slice 1; 375 SQLite tests pass. No slice 2 implementation yet.
- Approval record: human approved on 2026-10-04 with “continue.” The proposed player-progress wording is accepted.

## OPEN QUESTIONS

Accepted decision: **“N of M players ready or cashed out”**, with separate status counts and cash-out totals. This replaces the original “Counted amount of bought-in amount” because earlier partial cash-outs make that ratio ambiguous. The human accepted this recommendation by approving the plan.

## Goal and scope

Make the host's end-of-set flow as clear and usable as the active Rack table: count players, review and record cash-outs, check the books, then view frozen final results.

Recompose the reconciliation set page, batch cash-out review and finalized set page. Keep inline count inputs, one shared count form, corrections, exceptions, resume play, override controls and session navigation. Use slate felt, token rows, aligned amounts and a books-balance double rule. Keep canceled sets working through their existing composition.

Only templates, CSS, small existing JavaScript modules, read-only presentation helpers and verification files change. No models, services, routes, permissions, posted field names, accounting or money formatting changes. No session/settle-up redesign, new feature, asset, dependency, light theme or sound. SPEC.md stays unchanged.

## Acceptance criteria

1. At 390 × 844, count-up shows the state, player progress and labelled bought-in/recorded cash-out totals in the first screen. Every eligible host count field stays visible in the document. At 1,280 px use a quiet overview beside the count list. Test 320 px, long names and large amounts for no horizontal page overflow. No page-height limit hides count fields.
2. Progress includes only money players: ready plus finally cashed out, out of all money players. Separate status labels distinguish awaiting, ready and cashed out. Partial cash-outs alone do not count as completion. No-money state has no misleading percentage or finalization action.
3. Each existing submit confirms all typed counts. Zero is valid; empty fields are skipped. One refused value saves nothing and retains every draft. Confirmed values and input drafts remain visually distinct. Host fields are labelled; players get read-only counts and statuses.
4. A second client can change records while the host types. Polling preserves focus and drafts. Unchanged polls animate nothing. Stale-connection status remains visible. Count-up contains no net result figure.
5. Review shows names, exact confirmed amounts, batch total and prospective cumulative cash-outs. Exact count IDs and request ID remain posted. Changed/cleared counts or intervening final cash-outs reject the entire stale review and show fresh values. Batch confirmation neither finalizes the set nor marks payment.
6. Finalization is offered only when the existing `balance.ok` is true. Pending cash-outs remain ordinary progress. Completed discrepancies and override disclosures retain existing explanations. The double rule animates at most once per set per browser, only for `balance.ok`; reloads/repeated polls keep a static message. Reduced motion removes movement.
7. Finalized rows use snapshot results, signed amounts, direction icons and Final tags, with buy-ins, cumulative cash-outs, overrides and recorded time. The viewer's result is prominent when present. The session link retains existing meaning. There are no set-level transfers or payment controls.
8. Both pesos and chips states work; chips show no peso symbol. Keyboard focus stays visible, controls have 48 px targets, and the host dock covers no field or last action. Text contrast meets 4.5:1 and large figures/control edges 3:1. Counts, review, corrections and finalize work without JavaScript.
9. All existing tests pass on SQLite and PostgreSQL. Add focused presentation tests and extend browser checks for this slice without changing accounting assertions. Slice 1 active-table flows remain valid. No migrations or runtime external requests. Overall redesign additions remain under 40 KB CSS and 8 KB JavaScript; reuse or simplify existing code to retain the budget.

## Dependencies, branch and rollback

Use current local Archivo, inline icons and Rack tokens. Use synthetic fixtures in a temporary database for Chrome verification, with PostgreSQL 17 for the second test suite. Revalidate server state before captures; restart after template edits when using `--noreload`. Keep the user's dev database intact.

Create `feat/visual-redesign-slice-2` from current `main` in a separate worktree. Test before each commit. Merge locally at rendezvous after verification. No push or deploy. No database migration; rollback is a revert of the merge commit.

## Tasks

- [x] **1. Build the slice.** Recompose count-up, batch review and final results with shared presentation helpers. Keep a single count form and existing fallback controls. The phone dock links to batch review while ready players exist, offers finalize when balance permits, otherwise explains the next step; count confirmation stays at the count form. Add the bounded balance treatment without exceeding the existing JavaScript budget.
  - Commit: `feat(web): recompose count-up and finalized sets`.
  - Done when: criteria 1–8 work on host/player views and both units; active and canceled sets have no regression.
- [x] **2. Verify and finish.** Add focused markup tests and browser fixtures for zero/empty/rejected multi-count submissions, partial and final cash-outs, stale reviews, balanced/discrepant/overridden books and frozen results. Run SQLite and PostgreSQL suites, migration check, no-JavaScript flow, two-client polling, reduced motion, keyboard, contrast and asset-size checks. Capture phone and desktop together, run the Impeccable detector once and a fresh finish reviewer. Apply one fix batch and one confirmation round. Record evidence and any unavailable checks here.
  - Commit: `test(web): verify count-up and final results` (include related finish fixes if required).
  - Done when: all acceptance criteria have recorded evidence, required checks pass and the bounded finish review is resolved.
- [x] **3. Rendezvous and sync docs.** Merge to main, verify the merged result, have the Impeccable documenter record the built patterns, and update DESIGN.md, relevant `.impeccable` surface records, wiki features/architecture, parent task 8 and TODO. Add a footgun only if evidence warrants it. Restart the dev server and check `/healthz`.
  - Commit: `docs: sync redesigned end-of-set flow`.
  - Done when: main contains the verified slice, docs match the built result, the server answers and the plan is marked done. Slices 3–4 remain pending.

## Progress and blockers

- Phase 1: source review complete. Study committed as `a6ce949`; baseline SQLite suite passes (375 tests).
- No blockers. Approved Phase 2 is complete.
- Initial implementation: 384 tests pass on SQLite (14.379 s) and PostgreSQL (20.723 s); no migrations. Active-table regressions: 20 action checks and 13 accessibility checks pass. Added JavaScript: 7,912 bytes; stylesheet: 24,518 bytes.
- First capture batch: long-name explanation overflow needs a fix. Native reversal succeeded, but the browser check selected an earlier partial cash-out; update it to select the final cash-out. Full-page captures and JSON are in `/private/tmp/pn-slice2-review/`. Fresh finish review in progress.

## Verification evidence

- Build commit: `464d9d1`. Final fix batch passes all 384 tests on SQLite (13.794 s) and PostgreSQL 17 (19.738 s). The only existing test edit changes a moved time-label assertion; accounting assertions remain unchanged. Migration check: no changes.
- Existing active-table action and accessibility scripts: 20 and 13 checks pass. New end-set browser script: all 47 checks pass on the confirmation fixture. It covers both units, 390/1280 layouts, long names and large totals at 320, read-only player counts, viewer final result, visible dock guidance, keyboard/48px targets, draft preservation under polling, zero/empty/invalid multi-counts, exact stale-review rejection, native batch/finalize/correction flows, once-only balance and reduced motion. No browser runtime errors were observed.
- Slate contrast: secondary text 9.38:1, bone 11.71:1, positive 8.68:1 and negative 6.32:1. Existing text/control/token contrast checks remain passing. Amounts are accepted server values, with no interpolation.
- Assets: stylesheet below 26 KB; overall added JavaScript 7,912 bytes; existing 103,912-byte font. No new package, build step, external runtime request or migration.
- Detector ran once: zero anti-patterns. Its 49 advisory notes concern contextual type sizes and standalone Django templates lacking the application's CSS; they are not visible failure evidence. No second scan.
- Fresh finish review returned three material fixes: long-name containment, visible dock recovery guidance, and drawn review navigation icon. One fix batch and one confirmation round resolved all three. Verdict: `ship` for the scored fixes, not a new whole-surface audit.
- Captures in `/private/tmp/pn-slice2-confirm-review/` use synthetic data in a separate database. Nothing was added to the development database. Full-page capture includes the fixed dock at its viewport position. Confirmation compares overflow with the requested device width, because mobile `innerWidth` can grow with overflow.
- Not checked: a physical phone, a screen reader or production deployment. Canceled-set behavior is covered by the existing suite; no new canceled-screen browser flow was run.

| Criterion | Result |
|---|---|
| 1–2: hierarchy, responsive layout and truthful progress | Met: phone/desktop captures and presentation tests; partial cash-out and no-money cases |
| 3–4: counts, role view, drafts and polling | Met: existing service tests plus two-client/invalid/zero/empty browser flows; stale recovery regression passes |
| 5: exact review and atomic rejection | Met: review IDs/presentation tests, stale review browser refusal, existing accounting/concurrency suite |
| 6: balance gates and bounded motion | Met: pending/discrepancy/override tests and captures, once-only/reduced-motion browser checks |
| 7: frozen final results | Met: snapshot presentation test, host/player final captures and native chips finalization |
| 8: unit, keyboard, contrast and native flow | Met: both units, 48px/focus/clearance/contrast and JavaScript-disabled flows |
| 9: regression and budgets | Met: 384 tests on each engine, 20+13 old and 47 new browser checks, migration/asset checks |

## Rendezvous complete

- Local merge to main: `1004ffa`. Implementation `464d9d1`, verification/fixes `e77c65a`, living docs `1588680`. No push or deploy.
- Main verification: all 384 tests pass on SQLite (14.850 s) and PostgreSQL (21.504 s); no migrations. Served stylesheet matches the merged file.
- Required documenter refreshed DESIGN.md, the sidecar and two end-of-set surface briefs from finished code. Wiki, roadmap, parent plan and TODO are synchronized. SPEC.md and accounting services are unchanged.
- Normal development server restarted at `http://127.0.0.1:8000`; `/healthz` returns `ok`. Synthetic verification data remain only in temporary databases. The temporary browser server and verification PostgreSQL process are stopped after the run.
- Preserved pre-existing documentation drift: the slice 1 surface contract keeps its original 76px/27px targets, while DESIGN.md and the built active phone use 64px/22px. Slice 2 inherits the built system and does not reopen that older contract.
- Slices 3–4 remain pending. Next: session page and settle-up, with its own study, plan and approval.

User check: end a set, type several counts including 0, confirm once, review and record cash-outs, then finalize when the books balance. Check the Final result and the session navigation.

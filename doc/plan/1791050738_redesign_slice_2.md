# Plan: visual redesign slice 2

- Date: 2026-10-04, Asia/Manila. Shell timestamp: `1791050738`.
- Status: `awaiting-approval`.
- Study: [slice 2 revalidation](../study/1791050655_redesign_slice_2.md).
- Parent: [visual redesign, task 8](1791046015_visual_redesign.md).
- Sources: `SPEC.md`, `AGENTS.md`, `PRODUCT.md`, `DESIGN.md`, current wiki and the original visual study.
- Baseline: clean `main` after slice 1; 375 SQLite tests pass. No slice 2 implementation yet.
- Approval record: pending. Record the human answer before implementation.

## OPEN QUESTIONS

Approve the proposed progress wording: **“N of M players ready or cashed out”**, with separate status counts and cash-out totals. This replaces the original “Counted amount of bought-in amount” because earlier partial cash-outs make that ratio ambiguous. Approval of this plan accepts this recommendation unless the human specifies a change.

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

- [ ] **1. Build the slice.** Recompose count-up, batch review and final results with shared presentation helpers. Keep a single count form and existing fallback controls. The phone dock links to batch review while ready players exist, offers finalize when balance permits, otherwise explains the next step; count confirmation stays at the count form. Add the bounded balance treatment without exceeding the existing JavaScript budget.
  - Commit: `feat(web): recompose count-up and finalized sets`.
  - Done when: criteria 1–8 work on host/player views and both units; active and canceled sets have no regression.
- [ ] **2. Verify and finish.** Add focused markup tests and browser fixtures for zero/empty/rejected multi-count submissions, partial and final cash-outs, stale reviews, balanced/discrepant/overridden books and frozen results. Run SQLite and PostgreSQL suites, migration check, no-JavaScript flow, two-client polling, reduced motion, keyboard, contrast and asset-size checks. Capture phone and desktop together, run the Impeccable detector once and a fresh finish reviewer. Apply one fix batch and one confirmation round. Record evidence and any unavailable checks here.
  - Commit: `test(web): verify count-up and final results` (include related finish fixes if required).
  - Done when: all acceptance criteria have recorded evidence, required checks pass and the bounded finish review is resolved.
- [ ] **3. Rendezvous and sync docs.** Merge to main, verify the merged result, have the Impeccable documenter record the built patterns, and update DESIGN.md, relevant `.impeccable` surface records, wiki features/architecture, parent task 8 and TODO. Add a footgun only if evidence warrants it. Restart the dev server and check `/healthz`.
  - Commit: `docs: sync redesigned end-of-set flow`.
  - Done when: main contains the verified slice, docs match the built result, the server answers and the plan is marked done. Slices 3–4 remain pending.

## Progress and blockers

- Phase 1: source review complete. Study committed as `a6ce949`; baseline SQLite suite passes (375 tests).
- No implementation blocker. Human approval of this completed plan is the next workflow step.

# Plan: redesign slice 3

- Date: 2026-10-04 (Asia/Manila), Unix timestamp `1791053204`.
- Status: **in-progress**.
- Study: [slice 3 revalidation](../study/1791053103_redesign_slice_3.md), committed as `4ca6763`.
- Parent: [visual redesign, task 9](1791046015_visual_redesign.md).
- Sources: SPEC.md, AGENTS.md, PRODUCT.md, DESIGN.md, wiki and the original redesign study. No doc/canonical directory is present.
- Baseline: clean main before this cycle; slices 1–2 complete; 384 SQLite tests pass in 13.553 s.
- Approval: human approved this completed plan on 2026-10-04 with “proceed.” Phase 2 is authorized.

## Goal and scope

Recompose the session page and settle-up in the established Rack system. A host can close a finished session, record a transfer as paid and undo a mistake. A player can distinguish their poker result from what they must pay or receive. Keep the set list and payment history accessible. Add the approved closing recap with the precise definitions below.

This is an Operate surface. Extend the approved Rack composition directly; no new visual-world or concept-selection round is needed. The plan approval confirms the proposed hierarchy and recap refinements.

Exclusions: slice 4, new payment types, partial payments, banker, reporting/confirmation tiers, session polling, reopening, accounting changes, migrations, new routes, new packages, chip conversion, push and deployment. Preserve existing service authorization, forms, field names, CSRF, request IDs and money formatting. Do not edit SPEC.md or repair unrelated design-document drift.

## Composition contract

**First viewport:** compact session heading and metadata, then the immediate task. On a closed session, a slate field displays Still to pay at the existing large amount scale, labelled progress, status and the viewer's result/pay-or-receive instructions. The first transfer follows promptly. On an open session, lead with the current set action and the viewer's Results so far; explain that settle-up follows closing. No unpaid-zero or Settled claim appears on an open session.

**Reading order:** task summary; Who pays whom on closed sessions; Session results / Results so far; Sets; Payment records. Host close/start controls stay beside the relevant session/set task and retain the current gates. Before any finalized set, use an explicit empty-results message. On phones use one column and 48 px actions. At 900 px and above, use the built two-column proportions (400 px summary/action column, flexible rows, 28 px gap within 1180 px). Preserve sensible document and keyboard order.

**Rows:** transfer rows show payer and payee tokens plus full names, direction, amount and Paid / Not paid text. Paid includes its recorded time and “marked by the host” meaning. Host Mark paid and Undo remain native POST actions. Result rows use signed figures and existing directional icons; only closed-session aggregate results carry Final. Open results say “Over finalized sets; session still open.” Sets show number, state and known time. Payment records remain chronological, include recorder and undone status, and never hide a reversed record.

**Identity:** derive session token order from first appearance in session standings. Key it by member, not per-set participant. Names and disambiguated initials remain visible. This does not promise identical colours between a set and the session.

**Signature interaction:** a closing recap automatically opens once, with a short line stagger within 600 ms. Money appears at its accepted value. Reduced motion removes movement. Payment success appears after server acceptance through existing feedback; no optimistic progress or animated amount counting.

## Approved-plan definitions (proposed)

1. Still to pay is the integer sum of transfers with no active payment. Total to pay is the sum of all transfer amounts. Progress is paid amount / total amount, with a separately labelled paid-transfer count. For no transfers, display Nobody owes anything and zero remaining, with no division by zero. Payment changes cannot change frozen results.
2. Recap Recorded play time sums known finalized-set timer durations only. None known means Not recorded; missing durations make the displayed sum explicitly partial. Canceled and unfinished sets do not contribute.
3. Recap Total bought in across finalized sets sums current Finalization.total_buy_in snapshots. Label the scope explicitly; repeated money across sets is still counted as each set's recorded buy-in, never as transfers.
4. Top session result uses the highest positive aggregate standing and names all ties. All-zero standings say Everyone broke even. Your session result appears only for a viewer with a standing; a non-playing host gets no invented zero.
5. Automatic recap consumption is per closed session, signed-in viewer and browser. Persist the consumed key before opening. Keep a manual View session recap control. Storage failure skips auto-open and preserves manual access. No-JavaScript users can read an inline recap and use every native form.
6. A Close button, backdrop tap or Escape closes in one action. Tab follows native modal focus navigation. Focus returns to the manual trigger. This intentionally refines original M14's “any key closes” for keyboard access. Manual reopening is allowed; once-only refers to automatic opening.

## Acceptance criteria

| ID | Observable result |
|---|---|
| AC1 | Open and closed sessions follow the hierarchy above; both host and player views retain permitted navigation and actions. Draft sets do not leak to players. |
| AC2 | Unequal transfer amounts produce amount-based progress. Mark paid reduces Still to pay by exactly that transfer; Undo restores it. Repeat submissions do not double-record. Zero-transfer sessions show the explicit empty state. |
| AC3 | Results aggregate frozen finalized sets only. They remain unchanged after payment/undo; open results are provisional for the session and closed results are Final. |
| AC4 | Recap totals follow definitions 2–4, including canceled sets, missing time, several sets, tied winners, break-even players and a non-playing viewer. |
| AC5 | First closed visit auto-opens once; reload, payment redirect and undo redirect do not. Another session/viewer has its own key. Manual access works, including storage failure. |
| AC6 | Recap dismisses and restores focus correctly. Tab works. Reduced motion is static. No amount is interpolated and no recurring page-load choreography is added. |
| AC7 | Native close, next-set, paid and undo flows work without JavaScript. Current service gates reject premature closing and unauthorized writes. Reversed records remain visible. |
| AC8 | Pesos and chips keep their formats with no conversion. Long names and large amounts fit 320, 390 and 1280 px. Compare overflow against requested viewport width, not mobile innerWidth. Text contrast is at least 4.5:1; controls have visible focus and 48 px targets. |
| AC9 | Added JavaScript across the whole redesign stays below 8,000 bytes, CSS below 40 KB and font below 150 KB using the parent plan's measurement method. No runtime external assets or new dependency. Existing sheets, drafts, polling and end-set flows still work. |
| AC10 | Required tests, bounded browser review, fresh finish handoff, local merge and documentation sync are complete before marking done. |

## Dependencies and execution strategy

No external input is needed. Use local Django, PostgreSQL 17, Chrome and the existing CDP scripts. Recheck availability at execution. Use an isolated branch/worktree `feat/visual-redesign-slice-3` based on main and temporary synthetic databases; do not add verification data to the dev database.

The JavaScript budget has only 88 bytes free. Generalize/reuse dialog mechanics and reduce duplication before adding recap orchestration. Preserve behavior rather than remove existing features to meet the budget. If this cannot fit, report the measured gap and obtain a plan amendment before increasing the ceiling. This is a known implementation risk, not approval of a higher budget.

Rollback: revert slice 3's implementation commits to the working slice 2 session page and assets. No schema or accounting migration needs reversal.

## Task board

- [x] **1. Build the session composition and recap.** Add read-only presentation totals/context in the appropriate query/view layer; recompose night.html and scoped CSS; implement shared dialog/recap enhancement within budget. Read Impeccable craft-floor immediately before UI edits. Preserve native forms and service contracts.
  - Commit: `feat(web): recompose the session page and settle-up`.
  - Done when: all page states and definitions are implemented, focused presentation tests pass and measured assets meet AC9.
- [x] **2. Verify flows and resolve the bounded finish review.** Add meaningful tests for unequal-transfer sums, frozen-result separation, recap snapshots/time/ties and role visibility. Extend synthetic browser fixtures and checks for real paid/undo/close/next-set flows, once-only recap, keyboard, storage refusal, reduced motion and no-JavaScript behavior. Run all Django tests on SQLite and PostgreSQL and check for unintended migrations. Run the existing active-table and end-set browser regressions, especially shared sheets/drafts/polling.
  - Commit: `test(web): verify session settle-up and recap` (include directly related fixes).
  - Done when: AC1–AC9 have evidence and the required finish disposition is resolved.
- [ ] **3. Rendezvous and sync docs.** Have the required Impeccable documenter compare the finished build with the incumbent system. Update the session surface brief and built-pattern documentation within its write boundary. Update affected wiki pages/index, parent task 9 and TODO. Merge locally to main, verify the merged result, restart the development server and check health and served assets. Mark this plan done only after required work completes.
  - Commit: `docs: sync redesigned session settle-up`.
  - Done when: main contains the verified slice, docs describe actual behavior, the server works and slice 4 remains pending.

## Browser and review protocol

Use one batched full-page capture round for open/blocked/ready-to-close, unpaid/partly-paid/settled/no-transfer sessions, host/player views and recap. Include phone and desktop; add 320 px stress cases for names and amounts. Validate every capture before handoff. Test extra behavioral states without repeated visual-polish rounds.

Run the detector once on changed targets. Spawn the required fresh Impeccable finish reviewer without inherited conversation history, supplying this contract, captures, changed files, craft-floor and findings. Batch material fixes and confirm at most once; do not reopen a self-review loop. Follow the skill's recapture/rebuild rules if evidence is invalid or fidelity fails. An unresolved second verdict requires a concrete user decision. Spawn the documenter after the final correction. No implementation or review agents start while this plan awaits approval.

Existing browser harness regressions are 20 active-table action checks, 13 accessibility checks and 47 end-set checks. Use fresh fixtures for scripts that mutate state. Two clients on the session page confirm the current reload-based behavior; this slice does not add automatic refresh.

## Progress and blockers

- Phase 1 study committed. Baseline SQLite: 384 tests pass; system check reports no issues.
- No missing input blocks planning. Asset-budget risk is recorded above.
- Phase 2 approved with “proceed.” Execution is on feat/visual-redesign-slice-3.

- Initial build: 390 tests pass on SQLite (13.009 s) and PostgreSQL (20.267 s); no migrations. Added JavaScript 7,771 bytes (new sheets/changes/toasts plus existing forms/live growth); CSS 28,227 bytes. Active-table browser regressions pass. Fresh finish review identifies large-amount wrapping for the verification fix batch.


## Verification evidence

- Build `4374197`: read-only transfer totals and recap context, session composition and shared dialog enhancement. Existing money services, routes and schema are unchanged.
- Final fix batch: all 390 tests pass on SQLite (13.121 s) and PostgreSQL 17 (19.984 s). No migrations. New tests cover uneven transfer progress, repeat paid, undo/history, frozen results, two-set snapshot totals, unknown/partial time, canceled-set exclusion, ties, chips break-even and non-playing host. Existing role/draft visibility and accounting tests remain passing. Existing assertion edits follow moved markup and drawn/text direction; financial assertions remain intact.
- Session browser script: 53/53 checks pass on fresh synthetic fixtures. Phone390/desktop1280 and 320 stress cases; host/player views; recap once per viewer/session, manual reopening, storage refusal, Tab/Escape/focus return, reduced motion, paid/repeat paid/undo, reload-based second client, no-JS payment/undo/close/next-set and 48px targets. No runtime exceptions were observed. Native next-set fixture was corrected after the first harness targeted a setup-only session where that action is rightly blocked.
- Existing browser regressions: 20 active-table, 13 accessibility and 47 end-set checks pass. Shared sheets preserve drafts and focused inputs under polling; native fallbacks and stale recovery still work. Slate text contrast ratios remain 9.38:1 secondary, 11.71:1 bone, 8.68:1 positive and 6.32:1 negative.
- Detector ran once: one advisory black-text finding on a standalone unrendered Django template; rendered application uses palette CSS. Fresh finish reviewer returned one material fix: large Still to pay digits/cents split across lines. One session-scoped formatted-length size fix and one confirmation round resolved it. Verdict: ship for that scored fix, not a second whole-surface audit.
- All 35 confirmation captures were opened and validated. Evidence: `/private/tmp/pn-slice3-confirm-review/`, including desktop recaps and inline no-JS recap/history. Reviewer records: `/private/tmp/pn-slice3-finish-review.md` and `/private/tmp/pn-slice3-finish-verdict.md`. No further polishing or detector round.
- Assets: CSS 28,431 bytes; cumulative added JavaScript 7,771 bytes (sheets 5,204 + changes 1,578 + toasts 802 + forms growth 81 + live growth 106); font 103,912 bytes. All budgets pass. No package, external runtime request or build step added.
- Not checked: physical devices, screen-reader playback or production deployment. Multi-set and unknown/partial recap time are covered by Django tests rather than new visual fixtures.

| Criteria | Evidence |
|---|---|
| AC1–AC3 | Host/player and open/closed captures; native service/permission suite; uneven transfer/payment and frozen-result tests |
| AC4 | Snapshot/time/cancellation/tie/break-even tests; host/player and tie recap captures |
| AC5–AC7 | 53 session browser checks including once-only, storage refusal, modal focus, motion and native actions |
| AC8–AC9 | Width/48px/focus checks, confirmed exact large amount, old contrast/regression checks and measured assets |
| AC10 | Verification complete; documentation and local rendezvous remain in task 3 |

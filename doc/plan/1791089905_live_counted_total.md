# Live counted total

Status: **done**. Date: 2026-10-04.

Source: [study](../study/1791089661_live_counted_total.md), committed as `fe89e53`. Main implementation baseline: `6ccad9a`. Canonical sources: AGENTS.md, SPEC.md, PRODUCT.md, DESIGN.md and current wiki. Baseline: 410 SQLite tests pass, with three PostgreSQL-only skips.

## OPEN QUESTIONS

No blocking technical question. Approval confirms the proposed local-preview behavior, preservation of partial cash-outs, and an allowance of up to 4,000 new JS bytes with a cumulative added-JS ceiling of 12,000 bytes. The completed redesign's 8,000-byte ceiling has only 87 bytes left; this feature cannot fit that ceiling. Human approved “proceed” on 2026-10-04. Execution, rendezvous and documentation sync are authorized.

## Goal and acceptance criteria

Help the host check all remaining stacks against total buy-ins before cashing out.

- **AC1:** During count-up, a compact counter updates immediately on input, paste and clearing fields. Show remaining counts, earlier accepted cash-outs, their accounted total, and the difference from accepted buy-ins in the game's native unit. The counter stays visible while typing on a phone; desktop placement follows the existing two-column layout.
- **AC2:** Each money-bearing player without an accepted final cash-out contributes their valid nonblank draft, or their saved confirmed count when the field is blank. If neither exists, report the player as uncounted. Zero is valid. A draft replaces a saved count; it never adds to it. Final-cashed-out players contribute only through accepted cash-outs. Partial cash-outs contribute once alongside the remaining stack.
- **AC3:** Show how many players remain to count. Claim a complete match only when all required players are counted, there is no stray cash-out without buy-ins, every draft is valid and the raw difference is zero. Otherwise show missing/extra amount with incomplete coverage, or an explicit invalid-input state. An empty money ledger must not claim a completed match.
- **AC4:** Unsaved totals are clearly labelled as a preview. They do not record counts, create cash-outs, enable finalization or replace the existing server balance check. Keep confirmation, review and partial cash-out flows. Overrides remain outside this physical amount comparison; explain this when an override exists.
- **AC5:** Reversed buy-ins/cash-outs and voided counts do not contribute. Polling recomputes from current server records after restoring local drafts. Saved changes from another host appear through the existing polling mechanism. Failed submissions, focus deferral and page restoration retain correct previews. A saved baseline works without JS; other users do not receive a host's unsaved drafts.
- **AC6:** Python and browser totals use exact integers, including PHP centavos and large chips totals. No float arithmetic, chip conversion, new data model, money write or migration. Existing amount formatting, membership gates and host permissions remain intact.
- **AC7:** Focused query/view/browser checks and full SQLite/PostgreSQL suites pass. Rack layout, keyboard access, reduced motion, 48px actions and dock clearance remain usable. New JS is at most 4,000 bytes; cumulative added JS is at most 12,000 bytes; CSS remains below 40,000 bytes. No new dependency or asset.

## Implementation scope

1. Add a small derived count-total read model in `ledger/queries.py`, using the existing accepted summary. Return exact raw totals, count coverage and ledger eligibility. Keep Balance unchanged. Pass the read model through the existing session context.
2. Extend the count-up templates with a server-rendered confirmed baseline and stable data attributes for unit, accepted buy-ins/cash-outs, saved counts and eligible participants. Use one shared counter partial. Put the host's live preview in the existing dock, with scoped clearance, and expose the saved baseline in the count-up overview for read-only/no-JS use. Label overview totals as confirmed so they cannot be confused with unsaved previews.
3. Add a small vanilla `counts.js` module, loaded on the session page so transitions into count-up also initialize it. Use BigInt for amount arithmetic and exact formatting. Support ordinary documented native amount syntax: grouped integer chips and peso values with up to two decimal places, including normal unit labels. Invalid, out-of-range or unsupported draft syntax makes the preview unavailable and identifies the affected entry; backend validation remains authoritative. Do not silently use old amounts for invalid drafts.
4. Recompute on initial render, relevant input/change, pageshow and live updates. Dispatch `live:updated` after values and open details have been restored, or provide an equivalent explicit post-restoration event. Preserve current sheet, timer, change notification and checkbox behavior. Do not add polling or requests.
5. Use established Rack styles without a new visual direction. Apply Impeccable guidance as a bounded extension during execution. Verify required renders and use the applicable finish-review/documentation roles if required by that skill. Do not run a new design exploration.

## Task board and commits

- [x] Record human approval, recheck current main, then create `feat/live-counted-total` in an isolated worktree. Link the active plan from TODO during execution.
- [x] **`feat(web): add a live counted total`**: implement the query, templates, integer preview and post-restoration integration. Completion: AC1–AC6 demonstrated with focused automated checks and real browser flows on synthetic data.
- [x] Verify AC7: full SQLite and PostgreSQL suites, relevant existing count-up/live/dock regressions, scoped screenshots and required finish review. Resolve material findings within this feature.
- [x] **`docs: document live counted total`**: sync the affected wiki, built design/surface notes, TODO and plan evidence. Completion: docs explain confirmed totals versus preview, missing counts, partial cash-outs and override boundary.
- [x] Rendezvous: merge verified work into local main, check the running app and mark the plan done. No push or deployment.

## Verification

- Query tests: saved counts, missing versus zero, money-free participants, partial and final cash-outs, reversals, voided counts, stray records and overrides. Assert exact totals and completeness, including the invariant that recording a final cash-out moves its count into cash-outs without changing the accounted total.
- View tests: data reaches only authorized members, host inputs and preview labels are correct, confirmed baseline remains useful without JS, and validation errors retain drafts. No new write endpoint or permission bypass.
- Browser: enter balanced counts, short/excess counts, blank and zero, invalid text, replacements for saved counts, PHP cents and large chips values. Confirm counts and review/cash out through native flows. Verify a partial cash-out plus remaining counts matches the original buy-ins and a final cash-out does not double count.
- Polling/browser: preserve drafts and opening opt-out across redraws, apply another host's saved count, defer updates while typing, recompute after restoration, and retain normal timer/sheet behavior. Run relevant existing end-set and session regressions because the live event order is shared.
- Check phone and desktop overflow, dock clearance, focus order, preview visibility and reduced motion. Use temporary databases only. Report physical-device verification as unavailable.
- Run SQLite before each commit and PostgreSQL before merge. Check migration drift and exact script/CSS sizes. Broaden tests only for unresolved failures or changed shared behavior.

## Boundaries, rollback and documentation

No denomination inventory, per-chip tapping interface, physical chip-to-peso conversion, automatic cash-out, new cash-out gate, payment changes, new timer or historical backfill. Human-owned SPEC.md is unchanged. No external service or credential is needed.

Rollback by reverting this feature and its documentation; there is no schema or data migration. Do not mutate development game records for verification.

Sync wiki features/architecture and journal/index where affected. Update DESIGN.md and the existing end-set surface brief only for the built counter and dock behavior. Keep historical studies unchanged. Update PRODUCT.md only if the capability description needs this distinction. Record any confirmed polling/parser footgun with evidence.

## Progress

2026-10-04: study complete; plan prepared for approval. No external blocker. Implementation has not started.

## Execution evidence

2026-10-04: AC1–AC6 implemented and verified. Added 13 query/view tests. Full suites: 423 tests pass on SQLite (14.879 s; three PostgreSQL-only skips) and PostgreSQL 17 (22.565 s; all 423). Migration drift check reports no changes. The original test failure was a test-only assumption about CashOutBatch's return type; corrected before the passing full runs.

All 35 dedicated counter browser checks pass after the final polling fix. Exact centavos, large chips, native units, saved fallback, draft replacement, blank/zero, incomplete match, invalid/out-of-range syntax, partial cash-outs, native confirmation/review/cash-out, no-JS baseline, player privacy, overrides and no-money behavior are covered. Two hosts verify that deferred snapshots calculate after draft restoration, changed saved counts appear when a draft clears, and refused defaults survive another later poll. Page restoration and 320px invalid preview checks pass. Evidence: `/private/tmp/pn-counter-confirm/counts.json`; initial 32-check captures/review: `/private/tmp/pn-counter-review`.

The required finish reviewer opened all three captures (390/1280 pesos, 390 chips), returned ship with five contract sections, and requested no material fixes. One detector run found advisory-only standalone-template black and existing type-ramp findings; rendered counter inherits Rack. The documenter recorded the built extension in DESIGN.md and the existing end-set surface addendum; token values, frontmatter and sidecar stay unchanged.

The live redraw now emits its event after fields/details are restored. Nonblank count drafts are retained even when they equal defaultValue, because a refused native POST renders unsaved text as defaults. This fixes a verified polling edge case. No money write, gate, endpoint or migration is added. Unsupported browser draft syntax (for example scientific notation) is unavailable in the preview; existing backend parsing remains authoritative.

Budgets: counts.js 3,467 bytes plus 60 bytes in live.js = 3,527 new JS bytes; cumulative added JS 11,440 bytes, within approved 12,000. CSS 32,942 bytes; font unchanged at 103,912 bytes. No new asset/dependency/motion. Physical-phone verification is unavailable.

All 152 incumbent regression checks pass: Rack 20, accessibility/live updates 13, end-set/native cash-out 47, session/settlement/recap 53, default opening buy-ins 16 and opening opt-out redraw 3. Together with the 35 counter checks, 187 browser checks pass. A browser-port overlap interrupted the first session harness; its sequential rerun completed all 53 checks. Existing fixtures were only synthetic temporary data. Feature commit: `1bc7bc5`.

## Rendezvous

Completed 2026-10-04. Feature `1bc7bc5` and synced docs `b074c8e` merged into local main. Main's full 423-test SQLite suite passes (15.729 s; three PostgreSQL-only races skipped here, all passed on PostgreSQL above). The existing development server remains at http://127.0.0.1:8000; `/healthz` returns 200 and its served counts.js/CSS exactly match main. No migration or development game mutation was needed. Temporary verification server and PostgreSQL are stopped. No push or deployment.

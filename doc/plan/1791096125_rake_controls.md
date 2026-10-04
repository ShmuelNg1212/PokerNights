# Usable rake choices before buy-ins

Status: **done**. Date: 2026-10-04.

Source: [study](../study/1791096071_rake_controls.md), commit `16d367a`. Implementation baseline: main `7011a71`. Sources of truth: AGENTS.md, SPEC.md (read-only), PRODUCT.md, DESIGN.md, current wiki and the approved set-rake plan. Baseline: 465 SQLite tests pass with ten PostgreSQL-only skips.

## OPEN QUESTIONS

No blocking design input remains. The exact reported trigger is unconfirmed: an optional question asks whether buy-ins already existed. This plan fixes both confirmed control defects and retains the approved lock while accepted money exists. It does not authorize charging historical buy-ins or changing a running set's rule after money is accepted.

## Goal and acceptance criteria

The host can choose **Off**, **Flat amount**, or **Percentage of buy-in** before the first buy-ins, and only the selected value can prevent a valid save.

- **AC1 — Early choice:** New session offers a native radio group with those three choices, default Off. Flat amount is expressed in the session's unit; percentage applies to each gross buy-in. The initial settings version stores the choice before default opening buy-ins can run. Subsequent empty sets expose a clear Change rake settings link before Start game and keep inherited rules.
- **AC2 — Active value only:** Flat requires a positive native amount and ignores unused percentage text, including zero or malformed text. Percentage requires 0.01%–99.99%, at most two decimal places, and ignores unused flat text. Off ignores both values. Unused parameters normalize to zero. No float or chip conversion is introduced. Errors appear beside the selected field and preserve the chosen mode and entered values.
- **AC3 — Native usability:** New session and Change settings share the rake section and parsing rules. Use labeled text inputs with decimal input hints and clear help that only the chosen value applies. Both value inputs can remain visible; inactive native number constraints cannot block submission. No JavaScript is required. Existing Rack layout, 48px targets and keyboard access remain usable on phone and desktop.
- **AC4 — Accounting guard:** Existing money locks the rule and values. Explain that accepted buy-ins, including default opening buy-ins, fix the rake rule. Ordinary stake edits preserve it. Permitted unit changes still reset the rule to Off. Prior fees, totals, finalizations and settlement remain unchanged.
- **AC5 — Atomic creation:** The service validates stakes and rake before accepting session creation and writes the chosen rule in its initial settings version. Invalid rake leaves no partial night, set, settings, audit or money rows. Services remain the only write boundary and retain existing host, membership, transaction and action-identity guarantees. Presets remain stakes-only.
- **AC6 — Verification:** Regression tests reproduce both current failures and pass after the fix. Native browser flows prove initial creation, subsequent-set setup, switches between modes, invalid active input, stale inactive input and the accepted-money lock in both units. Required SQLite and PostgreSQL checks pass before local rendezvous.

## Scope and implementation

Use one shared rake form component for SessionForm and SettingsForm. Parse only the selected input through the existing integer/native-money and basis-point rules. Avoid the current globally validated DecimalField for an inactive percentage. Keep the service as the authoritative validator. Templates render the shared radio group and value fields separately from their generic stakes fields, with field-specific errors and explanatory text.

Extend `create_session` to pass validated rake to the first SettingsVersion. Absent rake retains Off for existing callers. Add a discoverable pre-start settings action and improve locked-rule help. Keep next-set copying, the unit reset and all ledger hooks unchanged. No migration, new write endpoint, new dependency, fee calculator or accounting algorithm change is expected.

## Ordered task board

- [x] Record explicit approval in this plan, recheck main and create `fix/rake-controls` in an isolated worktree. Link TODO to the active plan. Reproduce the two failures as maintained regression tests.
- [x] **`fix(games): make rake choices usable before buy-ins`**: implement shared active-only parsing, initial service configuration, native rake section, pre-start discovery and lock explanation. Apply Impeccable as a bounded extension of Rack for the form changes; follow its applicable finish-review and documenter requirements. Completion: AC1–AC5 pass automated and browser verification; saved money and accounting behavior remain unchanged.
- [x] **`docs: document rake setup controls`**: sync affected PRODUCT/DESIGN narrative and surface notes as needed, wiki feature/setup guidance, the confirmed default-opening lock footgun, TODO and plan evidence. Preserve SPEC and historical studies. Completion: documentation matches the verified forms and lifecycle.
- [x] Rendezvous: run required checks, finish review, merge into local main, and confirm the existing development server serves the updated forms. Mark done only after merge and doc sync. No push or deployment.

## Verification

Add tests at the actual form/view/service boundaries: creation form exposes the choice; flat with unused percentage zero or malformed text succeeds; Off ignores both fields; percentage ignores stale flat text; active values reject missing, invalid, excessive precision and out-of-range input. Cover pesos and whole chips. Verify selected mode, normalized parameters and retained errors.

Create sessions with each mode, then start default opening buy-ins and assert exact stored rule, fee and playable amounts. Verify a flat amount that consumes a buy-in still refuses the start atomically under existing ledger validation. Check invalid session creation rolls back, outsiders cannot configure, hosts can configure empty inherited sets, accepted money locks all rake fields, and unchanged-rule stake edits preserve fees. Keep unit-reset and replay regressions passing.

Use synthetic browser fixtures rather than modifying the user's games. Check JavaScript-enabled and disabled native submission, keyboard/radio labels and field errors at phone and desktop widths. Inspect initial setup, later-set pre-start link, all mode switches with stale values, and the locked state after default opening buy-ins. Record captures and observable results. Physical-phone testing remains unavailable unless an actual device becomes accessible.

Run the full SQLite suite before each commit and the PostgreSQL suite before merge; record skips explicitly. Run system and migration-drift checks. Keep CSS below 40,000 bytes and cumulative added JavaScript below 12,000 bytes (current 11,474); prefer no new JavaScript. Broaden checks only if a failure or new concern requires them.

## Dependencies, exclusions and rollback

No external input or service is required. Do not add group default rates, preset rake, future-only rate changes after accepted money, retroactive deductions, rake payees or data backfills. The previously approved accounting semantics stay in force.

The branch contains a form/service fix and documentation. Roll back code by reverting those commits; preserve all settings and fee rows created through valid choices. Do not delete records or remove schema. If review finds an accounting change is necessary, stop that part and record a revised plan for approval.

## Progress and blockers

2026-10-04: Study complete. Two desired-behavior probes fail (missing creation choice and inactive percentage validation); the opening-buy-in lock probe passes. Existing 465-test SQLite baseline passes with ten PostgreSQL-only skips. Phase 1 contains documentation only. Implementation awaits approval of this completed plan.

2026-10-04: Human approved this plan with “approved”. Execution uses branch `fix/rake-controls`, worktree `/private/tmp/pn-rake-controls`.

2026-10-04 verification: 472 SQLite tests pass in 15.863s (ten PostgreSQL-only skips); all 472 PostgreSQL tests pass in 25.198s. System and migration-drift checks pass. Native browser: 25/25 checks, JS disabled/enabled, both units, next-set setup, inactive stale values and accepted-money lock. Ten valid 390/1280px captures are in `.impeccable/review/rake-controls/`. CSS is 33,125 bytes; no added JS (cumulative 11,474). Detector reports zero primary findings and 64 advisories from fragment default colors and existing palette analysis. Independent finish reviewer: **ship** for the changed setup controls; report `/private/tmp/pn-rake-controls-finish-review.md`.

2026-10-04: Implementation committed as `fcb2dbf fix(games): make rake choices usable before buy-ins`. Documenter is syncing the bounded Rack extension; local merge follows doc completion.

2026-10-04: Documentation sync complete. PRODUCT/DESIGN prose and two surface addenda describe the native controls; machine frontmatter and design.json are preserved. Wiki feature/architecture/setup/index and the opening-buy-in lock footgun are current. Documentation-commit SQLite: 472 pass in 15.693s, ten PostgreSQL-only skips. Local rendezvous pending.

2026-10-04 rendezvous: merged into local main as `e233ce8 fix: merge usable rake controls`. Main SQLite: 472 pass in 15.873s, ten PostgreSQL-only skips. All 472 PostgreSQL checks passed on the final implementation. Browser 25/25; independent finish review **ship**; required documenter completed the ordinary extension and verified machine frontmatter/sidecar preservation. Existing localhost:8000 server answers health and login; no migration is required. The temporary fixture server and verification PostgreSQL instance are stopped. AC1–AC6 are complete. No push or deployment.

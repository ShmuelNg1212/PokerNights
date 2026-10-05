# Who pays whom: alignment repair plan

Status: in-progress. Date: 2026-10-05, Asia/Manila. Study: [transfer alignment](../study/1791210055_transfer_alignment.md).

## Outcome

Transfer cards make payer, payee, amount, payment state and host action easy to scan. Long names start beside their chips rather than surrounding them. Paid timestamps grow below the state. Mark paid and Undo have predictable positions at every card width.

Mode: Operate. Visual authority: the existing Rack in DESIGN.md and the session surface brief. Sources: SPEC.md, PRODUCT.md, wiki features and the source study. Base: `main` at `ebb4ad7`. Working branch: `ui/transfer-alignment`, with study commit `717e17d`. No implementation has begun.

## Recommended layout

1. **Wide cards:** payer and payee stay side by side around the written direction. Tokens, names and direction align to the first identity line. Below them, amount and state form the left group; the host action occupies a stable right column.
2. **Narrow cards:** payer and payee each get a full-width identity row, joined by a compact arrow and "pays". The amount gets a full-width row. Under it, state is left-aligned and the host action is right-aligned. The timestamp stays within the state block. Use the actual available card width, so the narrow desktop detail column gets the same protection as a phone. Start with a 440px container breakpoint and adjust only if the content-fit measurements require it.
3. **Player and archived views:** the facts use the available width without an empty action column.
4. **Amounts:** retain the whole accepted value and unit. Apply the existing smaller figure roles to unusually long values if needed. No truncation, abbreviation, conversion or internal digit wrapping.
5. Use shared spacing, typography, colors, tokens, radii, focus and 48px action targets. No new motion.

The narrow layout uses more vertical space for short names. This is the tradeoff for full names and a stable transfer path.

## Scope and exclusions

Change only the transfer block in `templates/web/night.html` and its scoped CSS in `static/css/app.css`, plus related browser checks and documentation. An extracted transfer partial is optional if it makes the structure clearer.

Settlement calculation, snapshots, payment services, role gates, CSRF, request IDs, audit records, Turbo form behavior, frozen results and payment records keep their current rules. No dependency, service, model, view or migration change is planned. Other session sections and the general visual system are outside scope. Push and deployment require a new instruction.

## Acceptance criteria

- AC1. Each card preserves the visible reading path: payer → payee → amount → state → action. DOM and keyboard order agree.
- AC2. Long names wrap in useful full-width identity rows on narrow cards. Chips align with the first name line. The direction is unambiguous and never floats halfway down a long name.
- AC3. Paid and Not paid share explicit financial-grid positions. The status block starts at its assigned edge; its timestamp does not vertically center or displace the amount. Host actions stay on the right of the assigned action row, rather than wrapping at an arbitrary flex boundary.
- AC4. No horizontal overflow at 320, 390, 768, 900 or 1280px, including large pesos, large chips, long names and 200% zoom. Figures retain every digit and their unit. Controls are at least 48px high and wide enough to operate.
- AC5. Mark paid and Undo update in place, with correct remaining totals and payment records. Frozen poker results remain unchanged. Player and archived views have the correct action permissions. Native forms work without JavaScript. Reduced motion stays static.
- AC6. Existing Django tests, build-style tests and relevant browser regressions pass. A real iPhone appearance check remains for the human.

## Ordered implementation board

- [x] **Implement and verify — `fix(ui): align session transfer cards`.** Read Impeccable's craft floor before UI edits. Replace wrapping financial flex layout with named grid areas. Add explicit identity hooks and container-aware narrow-card adaptation. Keep existing form routes, fields and Turbo attributes.
- [x] **Add meaningful browser coverage.** Add `transfer_layout.mjs` with fresh synthetic fixtures. Reuse existing night seeds; add a small fixture extension for mixed paid/unpaid and large chips if needed, through the real services. Measure identity alignment, financial grid placement, complete amounts, controls and overflow. Check both host and player/archived views, and payment/Undo transitions.
- [x] **Verify the flow.** Run the Django suite and exact Vercel-style test command. Run the new layout check plus `night.mjs` and `inplace.mjs` on separate fresh temporary databases. Check 200% zoom, JavaScript off, reduced motion, long names and the narrow desktop detail column. PostgreSQL is required before a later release; this layout cycle has no write/locking change.
- [x] **Bounded visual verification.** Use the study captures as the incumbent baseline. Inspect phone and desktop together after the complete build, fix any material defects in one batch, and confirm once. Do not expand into unrelated session redesign. Run the layout detector on the changed markup; explain any advisory findings with rendered evidence.
- [ ] **Rendezvous and docs — `docs: record transfer alignment verification`.** Record actual checks and acceptance results in this plan. Update DESIGN.md's transfer layout, the session surface brief, wiki features, browser README and TODO phone check. Merge the verified branch locally to main. Do not push or deploy.

## Verification and user check

Use fresh temporary SQLite databases. Do not create inspection data in development or production. Stop any server or isolated browser started for this task. A paid timestamp is permitted to increase card height; test stable grid placement rather than equal heights for different content. Test monetary correctness through existing service/acceptance coverage, not new copies of the accounting implementation.

On the iPhone after an authorized release: open a closed session with unpaid transfers, mark one paid, then Undo. Check the payer/payee direction, long names, amount alignment and button positions in Safari and the installed app. Payments must change Still to pay, while Session results remain fixed.

## Rollback and inputs

Revert the scoped markup/CSS and associated documentation commits. No data rollback or migration is needed. No external input blocks implementation. The exact original phone state is unknown; the study independently reproduced layout faults. Container-aware adaptation must be verified against the supported browser experience, with a usable fallback if unavailable.

## Progress

2026-10-05: source and rendered study complete. Mechanical layout scan is empty; rendered measurements identify wrapping and alignment failures. Baseline Django suite passes 677 tests with ten PostgreSQL-only skips. Waiting for human approval of this plan. Application code is unchanged.

2026-10-05: Human approved Phase 2 with “continue.” Execution, rendezvous and doc sync are authorized. Push and deployment remain outside this cycle.

2026-10-05: Implementation and verification complete. The list container retains the planned 440px breakpoint; the 900px viewport produces 416px cards and correctly uses stacked identities. Identity chips/direction align at the first line. Named financial areas keep paid timestamps below the badge and actions at their assigned right edge. Complete transfer figures use 28px normally, content-length roles of 22px/18px narrow and 28px/22px wide. The stacked default remains usable without container queries. Service routes, permission gates and native form fields are unchanged.

Checks: 677 Django tests pass, ten PostgreSQL-only skips; the Vercel-style SQLite test command also passes 677 with ten skips. `transfer_layout.mjs` passes 155/155, `night.mjs` passes 53/53, and `inplace.mjs` passes 38/38. Each suite used a fresh temporary SQLite database and isolated localhost server. The layout detector reports `[]`. No production or development inspection data was added. No PostgreSQL run is required for this UI-only cycle; it remains required before release.

AC1–AC5 pass in Chrome: payer/payee/amount/state/action DOM order, visible keyboard focus, first-line chips, assigned grid rows, complete single-line figures, overflow and 48px targets at 320/390/768/900/1280px; large pesos/chips and long names; host/player/archived views; Mark paid/Undo, remaining totals, reversed payment records and unchanged frozen results; native forms without JavaScript; static cards with reduced motion. Desktop 200% zoom reflow is emulated at 640 CSS pixels and DPR 2 for a 1280px physical window. This is not a native Safari or browser-zoom appearance claim. AC6 automated checks pass; the iPhone appearance check remains on TODO.

Bounded inspection: the first complete phone/desktop capture batch confirmed the intended hierarchy and grouping. Amount/state/action are distinct, with 8px identity joins and 12px/16px financial spacing. Long names get useful rows; the actual 416px desktop card uses the same protection. One confirmation batch corrected test measurement assumptions (text bounds instead of a fixed 40px line-height limit, and desktop zoom reflow instead of CSS body zoom). No broader redesign or further UI polishing was needed. The existing night regression had a stale “Session closed” message assertion; it now checks the actual closed state and generated transfer cards.

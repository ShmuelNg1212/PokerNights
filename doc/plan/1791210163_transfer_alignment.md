# Who pays whom: alignment repair plan

Status: awaiting-approval. Date: 2026-10-05, Asia/Manila. Study: [transfer alignment](../study/1791210055_transfer_alignment.md).

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

- [ ] **Implement and verify — `fix(ui): align session transfer cards`.** Read Impeccable's craft floor before UI edits. Replace wrapping financial flex layout with named grid areas. Add explicit identity hooks and container-aware narrow-card adaptation. Keep existing form routes, fields and Turbo attributes.
- [ ] **Add meaningful browser coverage.** Add `transfer_layout.mjs` with fresh synthetic fixtures. Reuse existing night seeds; add a small fixture extension for mixed paid/unpaid and large chips if needed, through the real services. Measure identity alignment, financial grid placement, complete amounts, controls and overflow. Check both host and player/archived views, and payment/Undo transitions.
- [ ] **Verify the flow.** Run the Django suite and exact Vercel-style test command. Run the new layout check plus `night.mjs` and `inplace.mjs` on separate fresh temporary databases. Check 200% zoom, JavaScript off, reduced motion, long names and the narrow desktop detail column. PostgreSQL is required before a later release; this layout cycle has no write/locking change.
- [ ] **Bounded visual verification.** Use the study captures as the incumbent baseline. Inspect phone and desktop together after the complete build, fix any material defects in one batch, and confirm once. Do not expand into unrelated session redesign. Run the layout detector on the changed markup; explain any advisory findings with rendered evidence.
- [ ] **Rendezvous and docs — `docs: record transfer alignment verification`.** Record actual checks and acceptance results in this plan. Update DESIGN.md's transfer layout, the session surface brief, wiki features, browser README and TODO phone check. Merge the verified branch locally to main. Do not push or deploy.

## Verification and user check

Use fresh temporary SQLite databases. Do not create inspection data in development or production. Stop any server or isolated browser started for this task. A paid timestamp is permitted to increase card height; test stable grid placement rather than equal heights for different content. Test monetary correctness through existing service/acceptance coverage, not new copies of the accounting implementation.

On the iPhone after an authorized release: open a closed session with unpaid transfers, mark one paid, then Undo. Check the payer/payee direction, long names, amount alignment and button positions in Safari and the installed app. Payments must change Still to pay, while Session results remain fixed.

## Rollback and inputs

Revert the scoped markup/CSS and associated documentation commits. No data rollback or migration is needed. No external input blocks implementation. The exact original phone state is unknown; the study independently reproduced layout faults. Container-aware adaptation must be verified against the supported browser experience, with a usable fallback if unavailable.

## Progress

2026-10-05: source and rendered study complete. Mechanical layout scan is empty; rendered measurements identify wrapping and alignment failures. Baseline Django suite passes 677 tests with ten PostgreSQL-only skips. Waiting for human approval of this plan. Application code is unchanged.

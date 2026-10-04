---
version: 1
slug: "templates-web-night-html"
primary_target: "templates/web/night.html"
related_targets: ["static/css/app.css", "static/js/sheets.js", "settlement/queries.py", "web/views.py"]
---

# Session and settle-up — The Rack

Mode: Operate. Scope: approved visual redesign slice 3, extending the incumbent Rack. Human approved `doc/plan/1791053204_redesign_slice_3.md` on 2026-10-04 with “proceed.” That plan is the composition contract; no new visual-world or concept round applies.

## Direction contract

THESIS: Make the current session task immediately clear while keeping poker results distinct from who pays whom.

OWN-WORLD: Preserve warm dark rails, Archivo, initial chips, bone controls and brass focus. Indigo marks the open-session field; the incumbent quiet slate supports closed settlement. No new palette, raster imagery or shared token scale.

STORY: Open the current set, view provisional session results, finalize or cancel unfinished sets, then close. The closed page explains transfers, lets the host mark paid or undo, and keeps frozen results, sets and the full payment record accessible.

FIRST VIEWPORT: Open sessions lead with current-set navigation and the viewer’s result so far when present. Closed sessions lead with Still to pay, amount progress, written status, separately labelled transfer count and viewer result/pay-or-receive instructions when present. The first transfer follows promptly. Open sessions make no Settled or zero-unpaid claim.

FORM: Phone document order is task summary, closed-session Who pays whom, Session results / Results so far, Sets, Payment records and inline recap fallback. From 900px the 1180px container uses 400px overview/actions plus flexible rows with 28px gap. All native actions retain gates, CSRF, request IDs and accepted-server feedback. No session polling is added.

FINISH: The fresh finish review found one material defect: large Still to pay digits wrapped internally. One session-scoped fixed-size adaptation resolved it; the bounded confirmation verdict is ship for that defect only, not a new whole-surface audit. Ordinary display remains 64px; formatted length above 10 uses 32px, above 17 uses 24px, with no internal wrapping or lost precision.

## Built layout and behavior

- Still to pay is total exact integer transfers minus amounts with active paid marks. Progress uses paid amount / total transfer amount, separately from paid-transfer count. No transfers shows Nobody owes anything and no denominator. Payment and undo change accepted payment state without changing frozen aggregate results.
- Transfer rows show payer/payee tokens, full names, written direction, exact amount, Paid / Not paid and native host Mark paid / Undo. Paid includes recorded time and host meaning. Payment records remain chronological, retain recorder, and keep struck undone entries visible.
- Signed aggregate results use frozen finalized sets only. Closed results carry Final. Open results explicitly say Over finalized sets; session still open. No finalized results has an explicit empty message. A non-playing host receives no invented zero.
- Tokens derive order from first appearance in aggregate standings and are keyed by member. Disambiguated initials and full names remain visible; colours are not promised identical to per-set identities.
- Session actions remain in flow; phone composition is one column, with 48px bottom clearance. Names, detail rows and records wrap; transfer identities use 32px chips and flexible columns around “pays.” The primary Still to pay token stays intact. Shared actions have 48px targets and visible brass focus.
- The closing recap sums current finalized buy-in snapshots, labelled Total bought in across finalized sets. Recorded play time sums known finalized-set durations, excludes canceled/unfinished sets, says Not recorded if none are known and labels partial sums. It is deliberately distinct from the existing page label Play time over all sets.
- Top session result names all highest positive ties. All-zero standings say Everyone broke even. Your session result appears only when the viewer has a standing.
- Automatic recap consumption is per closed session, signed-in viewer and browser, via `rack-recap:<night>:<user>`. The key is stored before opening. Reload, paid and undo redirects do not auto-open again; manual View session recap remains. Storage failure skips auto-open and retains manual access. Without JavaScript the recap is inline and native forms remain usable.
- Recap uses the shared native dialog: Close, backdrop or Escape dismisses; Tab retains modal navigation; focus returns to the manual trigger. Four fact lines use 360ms clips and 60ms stagger, ending within 540ms. Reduced motion is static and accepted money never interpolates.

## Evidence and boundaries

Compared PRODUCT.md, incumbent DESIGN.md and sidecar against the approved plan, final night template, appended session CSS, shared sheets module, settlement query and night view. Inspected confirmation PNGs `partly-1280.png`, `large-320.png`, `tied-recap-1280.png` and `no-js-recap.png` in `/private/tmp/pn-slice3-confirm-review/`. Read `night.json`: all 53 browser checks pass, covering layout, intact large amounts, recap identity/storage/focus/reduced motion, payment/undo/frozen-result separation, native forms, host/player gates and runtime errors. Read `/private/tmp/pn-slice3-finish-review.md` and `/private/tmp/pn-slice3-finish-verdict.md`; the latter independently clears the three large-amount recaptures. Coordinator reports 390 tests passing on SQLite and PostgreSQL; the documenter did not rerun them or conduct another polish round.

No accounting services, models, routes, permissions, amount formats or dependencies are changed by documentation. Incumbent machine tokens are unchanged, so `.impeccable/design.json` is preserved. Its pre-existing freshness warning is not a token repair request. PRODUCT.md and prior surface briefs are preserved. Slice 4 remains deferred.

Pre-existing drift, preserved: the slice 1 contract states 76px phone total / 27px phone clock and blinds; incumbent DESIGN.md and finish-reviewed build use 64px / 22px (16px chips blinds). This extension does not repair or reopen that contract.

## 2026-10-04 addendum — per-buy-in rake

The approved `doc/plan/1791093380_set_rake_and_group_pool.md` extends the existing Operate settlement surface. The overview adds Collected rake across sets and, for an affected player, distinguishes the signed after-rake result from their remaining settle-up balance. Who pays whom excludes rake already collected at buy-in; the group account never appears as a transfer party. Existing payment and Undo actions retain their meaning.

The recap adds Rake already collected using the incumbent fact treatment. Top results describe after-rake standings: an all-zero result may say Everyone broke even; a rake-only loss says No positive result after rake. The native inline fallback and shared sheet remain. The supplied equal-loss capture shows two −₱50 results with ₱100 rake and ₱0 still to pay. This extends historical result-copy scope without changing layout, sheet behavior or motion.

This addendum preserves the incumbent Rack and machine-token records. Finish review: **ship** for the approved rake extension, `/private/tmp/pn-rake-finish-review.md`. Shared evidence and preserved historical drift are recorded in the rake addendum of `templates-web-end-set.md`; this is not a new whole-product audit.

## 2026-10-04 addendum — UI evolution

The approved `doc/plan/1791098885_ui_evolution.md` evolves this surface inside the Rack. The overview is neutral in both open and closed sessions. Transfers are cards; a fully paid session says Settled. The closing recap is unchanged.

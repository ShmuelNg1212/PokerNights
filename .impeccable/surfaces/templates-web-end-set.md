---
version: 1
slug: "templates-web-end-set"
primary_target: "templates/web/session.html"
related_targets: ["templates/web/_session_live.html", "templates/web/_count_up.html", "templates/web/_players_count.html", "templates/web/_balance.html", "templates/web/_final_set.html", "templates/web/_results.html", "templates/web/_host_controls.html"]
---

# End of set — The Rack

Mode: Operate. Scope: approved visual redesign slice 2, extending the incumbent Rack. Human approved the slice 2 plan on 2026-10-04 with “continue.” The approved study and code-led plan provide the surface direction; no new direction roll or image-comp round.

## Direction contract

THESIS: Make counting, recording cash-outs and viewing frozen results distinct, legible steps in the same working Rack.

OWN-WORLD: Existing warm dark rails, bone controls, brass focus and initial tokens. Muted Slate felt and Slate Ink labels quiet the stopped-set overview. Preserve active-table patterns.

STORY: Count each remaining stack, confirm all typed drafts through one form, review exact confirmed counts, record cash-outs, then finalize only when the existing books check permits it. Final rows show frozen results; settle-up belongs to the session.

FIRST VIEWPORT: Phone: slate state and player progress, bought-in/recorded cash-out totals, then the count list. All count fields remain in the document. Desktop from 900px: 400px overview and controls beside a flexible count/result list, with 28px gap. No end-set page-height ceiling hides fields.

FORM: Count-up uses inline inputs attached to one shared count form. Every row button confirms all typed values; zero is valid and empty fields are skipped. Confirmed amounts and drafts remain separate. Read-only player views retain names, figures and written states. Final rows use snapshot results, signed amounts, direction icons, a section Final tag, buy-ins, cumulative cash-outs, overrides and recorded time. The viewer's result is prominent when present.

FINISH: Required detector and fresh reviewer completed. First review disposition was fix: long-name containment, visible dock recovery guidance and the review's drawn back arrow were the three material items. One fix batch and bounded confirmation verdict resolved all three with disposition ship. This records that bounded resolution, not a fresh whole-surface audit of every state.

## Built layout and behavior

- Progress counts ready plus finally cashed-out players over players with money. Separate awaiting, ready and cashed-out labels stay visible. Partial cash-outs alone do not complete progress; no-money sets offer no finalization.
- Phone count-up orders overview, counts and balance check. The fixed host dock shows review, eligible finalization or a disabled action with visible explanation. “More host controls” has a 48px target. Bottom clearance is 200px, with 90px/200px scroll margins on count fields; below 360px the button stacks full width beneath its input.
- Long names, explanations and amounts wrap anywhere inside end-set containers; grid columns permit shrinking. Review and final pages use 48px bottom clearance and in-flow actions.
- Balanced books receive a green double rule. Only `balance.ok` adds the eligible count-up marker; localStorage keeps its reveal at most once per set per browser. Unavailable storage, repeated polls/reloads and reduced motion leave the static rule/message. Frozen results use a static rule. Money figures never interpolate.
- Existing details retain corrections, exceptions, resume and override controls. Pending cash-outs are ordinary progress; completed discrepancies retain error explanations. Session navigation keeps its existing meaning.

## Evidence and boundaries

Read PRODUCT.md, incumbent DESIGN.md and sidecar; approved study `doc/study/1791050655_redesign_slice_2.md` and plan `doc/plan/1791050738_redesign_slice_2.md`; the shipping count, balance, host-control, final and result templates, stylesheet, changes module and read-only presentation helpers. Inspected confirmation captures for phone counting, desktop review and phone final, and the confirmation JSON at `/private/tmp/pn-slice2-confirm-review/end-set.json` (47 passing browser checks). Additional phone/desktop, chips, player, discrepancy, override, no-money and long-name captures are in the same directory. Parent execution reports 384 tests passing on both SQLite and PostgreSQL; the documenter did not rerun them or conduct further polish/review.

No models, accounting services, routes, permissions or amount formats change. No new raster asset or external dependency. Canceled sets and deferred session/settle-up compositions retain their existing layout.

Pre-existing drift, preserved: the slice 1 surface contract states 76px phone total / 27px phone clock and blinds; incumbent DESIGN.md and the finish-reviewed build use 64px / 22px (16px chips blinds). This slice does not repair or reopen that earlier contract.

## 2026-10-04 addendum — Live counted total

The approved `doc/plan/1791089905_live_counted_total.md` authorizes a bounded Operate extension of this Rack surface. Its direction retains native exact amounts, the slate overview, warm host dock, existing player rows and ordinary confirmation/review actions. No visual-world replacement or shared-token change was approved.

The built overview adds a “Confirmed counts” baseline after the set facts, separated by the incumbent quiet rule. It shows remaining confirmed stacks plus accepted cash-outs, their accounted total against buy-ins, a written discrepancy or match status and remaining count coverage. The host dock places the same compact equation immediately before its next action; any nonblank draft changes its heading to “Preview · unsaved counts.” Its accounted amount is a supporting 18px tabular figure below a 14px heading. Phone wrapping contains the complete native unit and amount; the extended dock reserves 370px bottom clearance below 900px. Desktop retains the existing 400px overview/control column beside the count list. Count field scroll margins and all existing controls remain unchanged.

Valid drafts replace saved remaining counts; blank fields use saved counts when present and otherwise contribute missing coverage. Zero is valid. Accepted partial cash-outs contribute once alongside remaining stacks; final cash-outs contribute through accepted cash-outs alone. A complete match requires full eligible coverage and valid drafts. Invalid entries receive local field guidance and an unavailable preview; incomplete coverage and an empty ledger never claim completion. Overrides retain an explicit exclusion note. Player and no-JavaScript views use the server baseline. Polling recomputes only after restoring local drafts. This preview records nothing and adds no gate to cash-out review or finalization.

Compared with the incumbent, this is a compact equation and coverage readout inside two existing containers, plus phone dock clearance. Archivo, slate labels, warm rails, quiet rules, exact native amount formatting, focus and 48px actions are inherited. No motion, raster asset, dependency or token is added; `.impeccable/design.json` and DESIGN.md frontmatter are preserved.

Evidence: inspected the shipping shared counter partial, count-up template, host-control placement, `static/js/counts.js` and appended count-total CSS. Inspected all three required synthetic-data captures: `/private/tmp/pn-counter-review/counts-php-390.png`, `counts-php-1280.png` and `counts-chips-390.png`. The supplied `/private/tmp/pn-counter-review/counts.json` contains 32 passing browser checks covering exact centavos/large chips, zero, invalid input, partial coverage, draft restoration, accepted confirmation/cash-out, read-only/no-JavaScript baseline, override exclusion, phone visibility, clearance and overflow. The finish reviewer returned ship with all three captures valid. The documenter inspected this evidence and did not rerun browser or backend checks.

Pre-existing drift remains as recorded above: the slice 1 contract's phone total/clock sizes differ from the finish-reviewed build. The earlier 200px count-up clearance remains the default; 370px is the scoped clearance for the newly extended host dock, not a repair to that earlier surface. No other incumbent design drift was identified within this bounded inspection.

## 2026-10-04 addendum — per-buy-in rake

The approved `doc/plan/1791093380_set_rake_and_group_pool.md` extends count-up, review and frozen results inside the incumbent Operate Rack. Slate overviews add Collected rake and Available to play alongside gross bought in and accepted cash-outs. The confirmed baseline and labelled unsaved preview compare remaining stacks + accepted cash-outs + accepted rake against gross buy-ins; they never estimate an unsaved fee. Existing coverage, zero, invalid-input, override-exclusion and draft-restoration behavior remains. Rake does not make an uncounted player ready to cash out.

Cash-out review shows the batch, previously recorded cash-outs, collected rake, playable amount and gross comparison before confirmation. The balance check includes collected rake once and retains real discrepancy guidance. Frozen results explicitly include already-collected rake, retaining signed after-rake results and exact snapshot facts. Finalization and payment remain distinct tasks. The prior inline-count layout, fixed phone dock clearance and desktop overview/control column are reused.

Finish disposition: **ship**, at the scope of the approved rake extension and the 17 phone/desktop captures in `.impeccable/review/rake/`; review: `/private/tmp/pn-rake-finish-review.md`. The documenter read that full review, the approved plan, source templates/forms and all 36 passing entries in `browser-results.json`, and opened the settings, active and count phone captures plus session and group desktop captures. The review independently inspected all 17 captures. The coordinator reports 465 PostgreSQL tests passing, SQLite passing with ten PostgreSQL-only skips, and supplemental mixed-set and percentage/flat native flows in both units passing. These checks were not rerun by the documenter. Physical-phone testing remains unavailable.

The existing Rack tokens, CSS, assets and motion are reused. CSS remains 32,942 bytes; the coordinator reports cumulative added JavaScript of 11,474 bytes, including 34 additional bytes in counts.js, and unchanged font bytes of 103,912. DESIGN.md frontmatter and `.impeccable/design.json` remain unchanged. The historical active-set type-size mismatch and stale sidecar scope/count-preview narrative are preserved, not repaired. No new scoped design drift was established by the inspected evidence.

## 2026-10-04 addendum — UI evolution

The approved `doc/plan/1791098885_ui_evolution.md` evolves this surface inside the Rack. The overview is the neutral lead panel, not slate. On phones the balance check sits above the count list; a completed mismatch leads with the signed amount. Progress is hidden when no player has a buy-in.

## 2026-10-10 addendum — count-up in one line

The approved `doc/plan/1791630963_count_up_and_settle_up_revamp.md` recomposes count-up: one 65px line per player with the count field on it, the field stating the count's state, player details in a sheet, one mark per player in the overview, and "The books" in place of Set totals and Balance check. Accounting, the counts form, the preview and the verdict are unchanged. DESIGN.md, "Count-up in one line", supersedes the row and order described above. `COUNT_REVAMP=False` returns the earlier screen. Evidence: `count_flow.mjs`, `end_set.mjs`, `dock.mjs`, `player_entries.mjs`, `numpad.mjs` and `inplace.mjs` on fresh seeds; captures at 320, 390 and 1280px reviewed with one fix batch. No separate critique run was made.

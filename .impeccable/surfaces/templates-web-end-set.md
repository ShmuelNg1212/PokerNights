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

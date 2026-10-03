# Study: visual redesign slice 2

- Date: 2026-10-04, Asia/Manila. Shell timestamp: `1791050655`.
- This is a dated revalidation addendum to [the visual redesign study](1791045491_visual_redesign.md). The original study stays unchanged.
- Outcome: extend The Rack to count-up, the batch cash-out review and finalized sets.

## Current state and evidence

Slice 1 is merged on clean `main`. It built the shared palette, Archivo, player tokens, action sheets and active-set layout. `DESIGN.md` records that result. The master plan's task 8 remains unapproved. This review inspected templates and query/service code; it did not run a new visual review.

`templates/web/_session_live.html` still sends reconciliation and finalized sets to `_session_legacy.html`. `_players_count.html` retains the working shared count form, visible fields, status labels, corrections and cash-out exceptions. `_balance.html` already gates finalization on `balance.ok`. `templates/ledger/cash_out_counted.html` retains a separate review and exact count IDs. `_results.html` already has signed result icons and Final tags, but retains the old composition.

`ledger/queries.py` distinguishes awaiting, ready and finally cashed-out money players. `balance.ok` needs final cash-outs for all money players, no stray cash-outs and a zero adjusted difference. Equality of confirmed counts and buy-ins alone is insufficient. `ledger/services.py:cash_out_counted` records each remaining confirmed stack as a new final cash-out. An earlier partial cash-out remains part of the player's cumulative cash-outs. Changed or cleared counts invalidate the review atomically. `confirm_counts` skips empty fields at the view boundary, accepts zero and writes all changed counts or none.

## Options and recommendation

1. Keep “Counted amount of bought-in amount” from the original study. This is compact but conflates remaining stacks, earlier cash-outs and recorded cash-outs. A monetary completion ratio can also exceed its denominator during a discrepancy.
2. Use player progress and distinct monetary totals. Recommended: “N of M players ready or cashed out,” with separate awaiting/ready/cashed-out counts. M includes only players with accepted buy-ins; N is ready plus finally cashed out. Label total bought in and recorded cash-outs separately. The review keeps “Total of this batch” and “After this batch” as explicitly prospective figures.

Use the existing Rack identity without another direction round. Count-up gets muted slate felt, persistent inline count fields and quiet details for exceptions. The host dock links to the batch review while ready players exist; once the books balance, it offers finalization. Keep confirmation of typed counts beside the form so that counting and recording cash-outs remain distinct actions. Show pending cash-outs as normal progress. Show a discrepancy as an error only when the existing balance check says the records are complete.

The books-balance double rule is eligible only when `balance.ok` is true. Animate it at most once per set per browser; always show the static message, including override disclosure. Finalized sets use frozen results, initial tokens, a right-aligned signed amount column, Final tags, time played and the existing session link. They show no transfer or payment controls.

## Constraints, risks and inputs

- Reuse existing local assets and modules. Slice 1 used almost the full 8 KB added-JavaScript budget; the new treatment must stay within the original overall budget, with CSS carrying decoration and reusable code replacing duplication if needed.
- Keep the single counts form, field names, `data-keep`, exact review IDs, request IDs, role checks, routes and accounting services. Read-only presentation helpers may be added. Match token identity by participant primary key when query objects differ.
- Preserve typed zero, several typed counts, rejected values and focus through polling. A fixed action must not cover the last field or conflict with the phone keyboard.
- Final results must use snapshots. Do not label confirmed counts as results or a prospective batch as balanced books.
- Test both units, partial cash-outs, empty/no-money sets, zero counts, overrides and stale reviews. Long names and large amounts must wrap without horizontal page overflow.
- The active-set 1,200 px height criterion is not suitable for eight always-visible count fields. This slice should require first-screen progress and an accessible, unobscured form rather than hide fields to hit that height.
- No new external asset, package or product decision is needed. PostgreSQL and Chrome are local verification dependencies. Browser captures must use synthetic data outside the dev database.

## Open decision

Approve player progress in place of the original monetary “Counted x of y” wording, as part of the slice 2 plan. No implementation has started.

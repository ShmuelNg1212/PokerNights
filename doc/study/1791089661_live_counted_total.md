# Live counted total

Date: 2026-10-04. Request: show a live counter of counted chips so the host can check the stacks before cashing out.

## Outcome and current evidence

The host should see the total change as final counts are entered, compare it with total buy-ins, and identify missing or extra amounts before recording cash-outs.

Main is clean at `6ccad9a`. Sources: AGENTS.md, SPEC.md, PRODUCT.md, DESIGN.md, the ledger/wiki documentation, `ledger/queries.py`, `ledger/money.py`, `web/views.py`, the count-up templates and `static/js/live.js`. Baseline: 410 SQLite tests pass; three PostgreSQL-only tests skip.

The count-up screen shows player progress, total buy-ins and accepted cash-outs. Its existing Balance query checks recorded cash-outs, not counts that are ready but unpaid. It therefore cannot answer the user's question while counting. Counts are confirmed independently from cash-out. A final count is the player's remaining stack; earlier partial cash-outs are already recorded separately.

The count inputs start blank even when a saved count exists. A blank field cannot mean zero. Saved counts are available through PlayerLine; final-cashed-out players have no count input. Reversed money records and voided counts are already excluded by the summary query.

Polling preserves unsaved input through data-keep. However, live:updated currently fires before typed values are restored. A new counter listening to that event would briefly calculate from the wrong fields unless the event order changes.

## Options and recommendation

1. Show only confirmed counts. This gives an authoritative total, but requires submitting each count before seeing the effect.
2. Show an explicit local preview while typing, with confirmed counts as the baseline. This answers the request without adding writes. Recommended.
3. Block cash-outs until the preview matches. This changes partial cash-out behavior and cannot trust unsaved browser values. Do not add this gate.

Recommended equation: **accounted amount = remaining counts + accepted cash-outs**. Compare it with accepted buy-ins. Include remaining counts only for players with buy-ins who have no accepted final cash-out. For each such player, a valid nonblank draft replaces the saved count; a blank draft uses the saved count if present. Otherwise the player is still uncounted. Zero is a valid count. Once a count is cashed out, its amount moves from remaining counts to cash-outs without changing the accounted total.

Show count coverage separately. A partial sum that happens to equal buy-ins must not claim a complete match. An invalid draft must make the preview unavailable rather than silently count as zero or fall back to the old amount. Stray cash-outs without buy-ins must retain an unresolved-ledger warning. Overrides do not enter the physical/raw amount comparison; the current server balance and finalization rules remain authoritative.

## Assumptions, risks and inputs

Interpret “live” as immediate feedback while typing, plus the existing poll for other hosts' confirmed changes. Interpret amounts in the set's native unit: chips in a chips game and pesos in a pesos game. There is no chip denomination inventory or conversion rate in the product.

Use integer arithmetic in Python and BigInt in JavaScript. Accept the documented ordinary amount formats; unsupported or invalid text must not produce a false match. The server remains the final parser and validator. Preserve input, preview accuracy and focus through polling, submission errors and page restoration.

Keep a compact host preview visible while typing on phones, using the existing host dock and appropriate bottom clearance. Reuse Rack typography and colors. Label unsaved totals as a preview; do not present them as recorded money or animate amount acceptance. A server-rendered confirmed baseline remains useful without JavaScript.

The completed redesign used 7,913 of its 8,000 added-JS bytes. This functional addition needs an explicit new allowance: at most 4,000 additional bytes and a cumulative 12,000-byte ceiling. No framework, dependency or asset is needed. Keep CSS under the existing 40,000-byte ceiling.

Verification inputs are available locally: synthetic SQLite/PostgreSQL fixtures and browser automation. No real game records need mutation. Physical-phone testing is unavailable. No blocking external input or technical question remains; the preview semantics and new script allowance need approval through the plan.

# Set rake and group pool

Date: 2026-10-04. Request: optional percentage or flat rake on every buy-in, a per-set rake pool included in balancing, and each group's accumulated rake across all sessions/sets.

## Confirmed outcome

The human confirmed that rake is deducted from the buy-in: ₱1,000 at 5% gives ₱950 in play and ₱50 rake. Rake is its own entity per group, is already collected at each buy-in, and is tracked only. It does not become a recipient in final who-pays-whom transfers.

## Current state and evidence

Main is clean at `0b55fd9`. Sources: AGENTS.md, SPEC.md, PRODUCT.md, DESIGN.md, wiki architecture/features, games settings/lifecycle, ledger models/services/queries, settlement models/services/algorithm, set/session templates and the live counted-total module. Baseline: 444 SQLite tests pass; six PostgreSQL-only races skip.

BuyIn is append-only, carries a settings version and unique set/request ID, and is written under the set lock. The same service handles opening buy-ins, manual first buy-ins and rebuys. Reversal is a separate row. Settings are versioned and next sets copy the preceding settings. There is no rake field, account or ledger entry today.

Current conservation is cash-outs plus overrides = gross buy-ins. Finalization repeats it in Python and a database constraint, freezes PlayerResult, and asserts player nets sum to zero. Session closure feeds those nets to the transfer algorithm. Simply subtracting rake from chips would therefore fail balance/finalization and leave the transfer algorithm with negative total balances.

The live counter uses remaining counts plus accepted cash-outs; active Still in play uses buy-ins minus cash-outs. Both need the rake term. Group pages are composed in web, so web can ask ledger queries for group rake totals without creating a groups-to-ledger dependency. Transfer/Payment endpoints currently name members; confirmed tracking-only rake does not require changing them.

SPEC.md lists optional rake/house fee as future work but states the current no-rake equality and zero-sum player settle-up. This request authorizes a rake extension. Preserve SPEC.md as human-owned and record the changed conservation rule in living docs. Do not hide rake as a balance override or fabricated player win.

## Recommendation and accounting

Give each group a dedicated Rake account identity, separate from Member. Keep all balances derived from immutable per-buy-in rake entries. Do not store a mutable cumulative group counter or fabricate a login/player for the account.

For accepted gross buy-in B, recorded rake R and playable amount P: **B = P + R**. Set end: **accepted cash-outs + active overrides + accepted rake = gross buy-ins**. Live stack check: **remaining counts + earlier cash-outs + accepted rake = gross buy-ins**, before overrides. Still in play subtracts both cash-outs and rake.

Each player has two different facts: their result after rake is cash-outs plus overrides minus gross buy-ins; their remaining settle-up balance adds back their own already-collected rake. Thus player results sum to −set rake, while player settle-up balances sum to zero. Preserve the actual after-rake result for results/history; use the adjusted balance only to calculate transfers. For two ₱1,000 buy-ins at 5%, if each cashes out ₱950, each result is −₱50 and each owes nothing at settle-up. The rake account records ₱100.

Link one immutable rake entry to each new buy-in, including a zero entry where rake is off or rounds to zero. Store the accepted amount, mode/rate and unit. A buy-in reversal excludes its linked rake from all accepted pools; the original rows remain in the log. Retries cannot create another entry. An atomic failure writes neither side. Historical buy-ins receive no invented fee.

Recommended rules for approval: Off by default; percentage uses integer basis points (up to two percentage decimal places), rounded down once per buy-in to a centavo or whole chip; flat amount is per buy-in/rebuy in the native unit. Require rake below the buy-in so some amount remains in play. Configure before money is accepted; allow new settings when all buy-ins have been reversed, without changing old entries. Next sets inherit the last rule and may change it before their first buy-in.

## Options, tradeoffs and risks

Deducted versus added-on rake was resolved by the human. Collected-now versus rake-recipient transfers was resolved in favor of collected-now tracking. The latter preserves transfer-party/payment schemas, but requires an explicit distinction between after-rake results and remaining settle-up balances. Group rake is an accrued collected-fee total, not player winnings, a cash wallet, a payment mark or a withdrawal feature.

Group lifetime totals include every accepted buy-in immediately, including open/running sets, and exclude reversals. A finalized-only total would omit rake already collected during play. Show pesos and chips separately; never add or convert them. Session/set detail should explain where the group total came from. Historical zero-rake data and frozen transfers must remain unchanged.

Risks: duplicate opening/rebuy charges, cumulative-versus-per-entry rounding, stale settings, missing rake in the count preview or override calculation, retrospective fee edits, misleading recap text when everyone loses only rake, and charging paid rake a second time through settlement. Test each directly, plus group isolation and PostgreSQL races.

## Inputs and open questions

Funding and settlement semantics are confirmed. Percentage precision/rounding, rate bounds, configuration lock and next-set inheritance are proposals for plan approval. No external service or credential is needed. Use local SQLite/PostgreSQL and synthetic browser fixtures. Physical-phone verification is unavailable. This reaches settings, ledger, frozen results, settlement projections and several screens; execute it as a small ordered set of coherent commits, not one partially working UI change.

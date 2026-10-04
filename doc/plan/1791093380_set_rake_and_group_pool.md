# Set rake and group pool

Status: **in-progress**. Date: 2026-10-04.

Source: [study](../study/1791093189_set_rake_and_group_pool.md), commit `59d28a7`. Main implementation baseline: `0b55fd9`. Sources: AGENTS.md, SPEC.md, PRODUCT.md, DESIGN.md and current wiki. Baseline: 444 SQLite tests pass; six PostgreSQL-only races skip.

## OPEN QUESTIONS

Funding and settlement are resolved by the human: deduct rake from gross buy-ins; give every group its own rake entity; rake is already collected at each buy-in and is tracked only, without a final transfer to that entity.

Approval also confirms these proposed rules: Off by default; percentage precision of two decimal places; round down separately for each buy-in to the native smallest unit; flat fee per buy-in/rebuy; rake must leave a positive playable amount; lock the rule while accepted money exists; next sets inherit the prior rule. No blocking external input remains. The human approved this plan on 2026-10-04 with “approved”. Implementation is authorized.

## Goal and observable accounting

Collect and track the set's agreed rake exactly once on every accepted buy-in, balance the remaining stacks correctly, and show each group's accumulated rake across all sessions/sets.

For gross buy-in B and rake R, playable amount is B − R. The usual buy-in and existing buy-in limits refer to B. Examples:

| Rule | Gross buy-in | Rake collected | Added to play |
|---|---:|---:|---:|
| 5% | ₱1,000 | ₱50 | ₱950 |
| Flat ₱20 | ₱1,000 | ₱20 | ₱980 |
| 5% | 101 chips | 5 chips | 96 chips |

Percentage is stored in basis points: 5% = 500; rake = gross × basis points // 10,000. Decimal parsing only converts input into an integer rate. No float, cumulative percentage rounding or chip conversion.

At set end: **cash-outs + overrides + rake = gross buy-ins**. Before cash-out: **remaining counts + accepted cash-outs + rake = gross buy-ins**, excluding overrides from the physical stack check. Still in play subtracts cash-outs and rake from gross buy-ins.

Player result after rake = cash-outs + override − gross buy-ins. Player remaining settle-up balance = result after rake + that player's already-collected rake. For two players each buying in ₱1,000 at 5% and cashing out ₱950, each result is −₱50, each owes nothing further, and the group rake total grows by ₱100. Rake does not become a winning player or a payment recipient.

## Acceptance criteria

- **AC1 — Set rule:** Every set supports Off, Percentage or Flat amount. Configure through host set settings before money is accepted. Percentage accepts 0.01%–99.99%; flat amount is positive in the native unit. Off stores zero parameters. Incompatible/unused parameters are normalized or refused consistently. Existing sets start Off. Next sets copy the preceding rule and permit changing it before their first buy-in. Presets remain stakes-only in this scope.
- **AC2 — Configuration protection:** Rule changes run in a locked atomic service with an audited, uniquely constrained request UUID. They create a settings version, never alter prior fees. With accepted buy-ins or cash-outs, changing the rake rule is refused; normal stakes changes can retain the same rule. After all accepted money has been reversed, changing the rule is allowed. Existing unit-change guards remain; any permitted unit change resets rake to Off for explicit reconfiguration rather than interpreting an old flat amount in another unit. Historic entries retain their original units/rates.
- **AC3 — Every buy-in:** Manual first buy-ins, rebuys, default opening buy-ins and late-player buy-ins create one linked immutable rake entry in the same transaction. Store gross, rake and playable facts through the buy-in/entry linkage, including zero rake when Off or rounded to zero. Require 0 ≤ rake < gross. A fee that consumes the buy-in is refused before any money, timer or audit write. Existing gross limits apply. Retries create no extra fee, pool credit, audit or version; failures roll back the whole buy-in/start action.
- **AC4 — Reversal:** Reversing a buy-in excludes its associated rake from accepted player/set/session/group totals. Both original rows remain visible with the reversal reason. A replacement buy-in uses the rule accepted for that new record. No independent rake editing, backdated historical charge or hidden override is permitted. Accepted historical buy-ins without entries count as zero rake.
- **AC5 — Group account:** Every group has exactly one dedicated Rake account, separate from Member, participants, logins and player results. It has no mutable balance counter. Show lifetime accepted accumulated rake on the group page, including current open/running/count-up and finalized sets, across all sessions. Show pesos and chips separately, with zero totals for unused units, and a session/set breakdown that reconciles to each total. Outsiders cannot read it. Payment marks and Undo do not change accumulated rake.
- **AC6 — Live and final balance:** Show gross bought in, rake pool and playable amount distinctly on active/count-up/review/final screens. The live preview adds recorded rake once, after restoring drafts, and never calculates unsaved rake charges. Missing/invalid counts, zero, partial/final cash-outs, reversals and override warnings retain their behavior. Server finalization blocks a real discrepancy, accepts cash-outs plus rake that balance, and overrides cover only the remaining discrepancy. Rake never satisfies missing-player cash-out coverage.
- **AC7 — Frozen results:** Finalization snapshots total rake and each player's contributed rake. Enforce gross conservation in Python and database constraints. Player results after rake plus the rake pool sum to zero; displayed player results alone can sum to a negative rake amount. Old snapshots default to zero rake and keep their exact amounts. Finalized/session result/recap copy distinguishes after-rake result from remaining payments and does not call all players break-even when everyone lost only rake.
- **AC8 — No double collection:** Closing a session computes transfers from each player's result plus their already-collected rake. These balances sum to zero, remain in first-join order, and the existing deterministic minimum-transfer algorithm clears them exactly. No transfer to/from the rake entity, transfer-party schema change or fee-payment mark is introduced. Ordinary player payments/Undo remain unchanged. A session can include both rake-enabled and Off sets.
- **AC9 — Usability and evidence:** Native host settings/buy-in/count/cash-out/finalize/close flows work without JS and display the agreed deduction clearly. Existing Rack layout, 48px actions, keyboard access, unit formatting and reduced motion remain usable. Focused arithmetic/ledger/migration/settlement tests, full SQLite/PostgreSQL and scoped multi-client browser checks pass. No dependency, asset, framework or deployment. CSS stays below 40,000 bytes and cumulative added JS below the existing 12,000-byte limit.

## Implementation boundaries

1. **Groups:** Add a dedicated one-to-one GroupRakeAccount identity with fixed role/name. Create it through group services for new groups and a metadata-only migration for existing groups. It does not import ledger or own cached money. No fake Member or account login.
2. **Games:** Add mode, integer basis points and flat amount to SettingsVersion, with validated combinations. Preserve historical Off defaults and copy rake explicitly on next-set creation. Extend host set settings with native rule fields and a request ID; add nullable historical-compatible settings request tracking with a per-set uniqueness constraint. A retry returns its accepted version before later state/rule refusal. Keep presets and existing stakes semantics stable; services alone write settings.
3. **Ledger:** Add one immutable RakeEntry per new BuyIn, linked uniquely to buy-in and group account, storing integer fee, unit and rule provenance. The linked buy-in's unique request ID is the action identity; the fee cannot be replayed independently. Hook into record_buy_in before acceptance completes, so opening and manual paths cannot diverge. Group and session aggregates query accepted entries and exclude linked buy-in reversals. Do not maintain a separate group counter.
4. **Queries and snapshots:** Add per-player/set rake totals and available-to-play amounts. Update Balance, CountTotal, override discrepancy, cash-out review and finalization. Add total_rake to Finalization and rake_total to PlayerResult (historical zero defaults). Replace Finalization's equality with total_buy_in = total_cash_out + total_rake. Retain net = cash_out − gross buy-ins on PlayerResult. Query session rake from accepted records while live, frozen values in finalized result views.
5. **Settlement:** Keep actual after-rake standings and introduce a separate query/service projection for remaining settlement balances (net + recorded player rake). Use that projection for closure, conservation and transfer-clearance checks. Leave Member endpoints/payment schemas and pure settlement algorithm intact. UI shows why after-rake loss and remaining amount to pay can differ.
6. **Web:** Compose group aggregates in web via ledger queries, respecting one-way dependencies. Extend existing set settings, buy-in help/log, active totals, count-up/dock, batch review, frozen result, session overview/recap and group page. Use established containers and components. Keep the preview's exact BigInt arithmetic; add only the accepted rake term/data to counts.js. Avoid another client fee-calculation subsystem; the accepted record shows the exact gross/rake/playable breakdown.

## Ordered task board and commit boundaries

- [x] Record approval, recheck current main and create isolated branch/worktree `feat/set-rake`. Link TODO to this plan. Approval covers this multi-commit accounting change, its required verification, local merge and docs.
- [x] **`feat(ledger): record per-buy-in rake and group accounts`**: group identity, set rule/version/request tracking, entry model, atomic recording/reversal and compatible migrations. Completion: exact integer fees and accepted pool aggregates verified; default-Off app remains workable at this commit boundary. Do not expose an enabled fee through forms until balance/finalization support is integrated.
- [x] **`feat(settlement): account for collected rake in balances and results`**: rake-aware read models, constraints/snapshots, overrides, separate transfer balances and zero-double-charge closure. Completion: rake-enabled sets finalize and sessions settle with exact conservation; old snapshots/transfers remain unchanged.
- [x] **`feat(web): show rake rules and accumulated pools`**: expose host configuration and all affected facts, group lifetime breakdown and recap distinctions. Completion: native end-to-end percentage/flat/Off flows, live preview, group totals and membership gates meet AC1–AC9. Apply Impeccable as a bounded Operate extension during this UI task; inherit Rack, use batched captures and required finish-review/documenter roles.
- [x] **`docs: document rake accounting and group pools`**: sync PRODUCT/DESIGN as needed, wiki architecture/features/setup/journal, confirmed footguns, relevant surface addenda, TODO and plan evidence. Keep SPEC.md and studies immutable.
- [ ] Rendezvous: merge only after required checks pass; verify main and the running app, apply compatible migrations and record exact evidence. No push or deployment.

## Verification

- Arithmetic: integer basis-point parsing, per-entry floor rounding at centavo/chip boundaries, flat/off, zero rounded rake, minimum positive playable amount, large values and invalid precision/ranges. Assert two small buy-ins use their own rounded fees rather than rounding the combined sum.
- Ledger: manual/rebuy/opening/late paths, same-request replay, duplicate opening-start serialization, partial reversal/replacement, full rollback, host/group gates, configuration racing with a buy-in, simultaneous buy-ins and buy-in/reversal races on PostgreSQL. Assert exact entry/audit/version/settings rows and derived pool totals.
- Configuration/migrations: settings retry after first buy-in, unchanged-rule stakes edit, rejected rate edit while accepted money exists, all-reversed reconfiguration, permitted unit change resetting rule, next-set copy/override. Migrate a consistent SQLite backup with existing sets/results/transfers: original totals and payments stay exact, all historical rates/snapshots are zero, no retroactive fee entries. Check PostgreSQL constraints and migration drift.
- Balance/results: partial/final cash-outs and zero/missing counts, physical live comparison, reversal exclusion, discrepancy/override, group identity isolation, after-rake negative results and complete coverage. Assert total player net + rake = 0 and frozen snapshots do not depend on later settings/query changes.
- Settlement: two equal after-rake losses with zero transfers, unequal winners/losers with exact clearance, several mixed-rate/Off sets, deterministic join-order output and minimum transfers, normal payment/Undo. Assert no rake payee and no second rake deduction.
- Group: multiple sessions/sets, live versus finalized accepted fees, mixed units separately, corrected buy-ins, zero-rake group, canceled sets (no accepted money), pagination/breakdown aggregate consistency and outsider 404. Avoid aggregate join multiplication.
- Browser: synthetic percentage and flat peso/chip games, native settings, opening/rebuy/late entry, visible gross/fee/playable facts, two-host redraw, draft count preservation, rake-aware batch review/finalization, closing a mixed-set session, group lifetime breakdown and result/payment distinction. Check phone/desktop/full/error/Off states and relevant incumbent live/count/settlement regressions. Physical-phone testing remains unavailable.
- Run SQLite before every commit; PostgreSQL before merge. Record exact script/CSS sizes and migration results. Stop broadening checks once relevant tests pass unless another change or unresolved failure requires them.

## Exclusions, rollout and rollback

No dealer tips, per-hand/time rake, caps, percentages of winnings, extra-on-top fee, cash wallet, rake withdrawal, rake recipient transfers, banker or pre-finalization payment features. No group default rate or preset rake controls in this cycle. No historical fee backfill. No change to chip/peso conversion policy.

Use additive defaults and staged constraints so existing development data migrates safely. Rake identity migration creates metadata only. Before exposure, revert the feature/migrations on disposable verification data if needed. Once rake records exist, do not downgrade to an old conservation rule or drop fee/snapshot columns: retain data, disable new rake configuration and use a forward fix. Any data-destructive rollback needs an explicit separate instruction.

## Progress and blockers

2026-10-04: study and completed plan prepared. Deducted funding, group-owned entity and already-collected tracking are confirmed. No external blocker. This was the Phase 1 checkpoint; the human later approved the full scope (recorded below).

2026-10-04: Approved by the human (“approved”). Worktree `/private/tmp/pn-set-rake`, branch `feat/set-rake`. Ledger/configuration step verified: 452 SQLite tests pass (six PostgreSQL-only skips).

2026-10-04: Balance/result/settlement step verified: 456 SQLite tests pass (six PostgreSQL-only skips). Equal after-rake losses create zero transfers; mixed Off/rake sets and payment Undo preserve rake totals.

2026-10-04: UI step verified. All 465 PostgreSQL tests pass, including four new rake races. All 465 SQLite tests pass with ten PostgreSQL-only skips. Main rake browser story: 36/36; supplemental native mixed-set and both-unit flows: 12/12. All 17 captures are in `.impeccable/review/rake/`. Independent finish reviewer: **ship** at the feature/capture scope (`/private/tmp/pn-rake-finish-review.md`); no requested fixes. One batched inspection removed two duplicated labels; final confirmation captures use the corrected templates. Detector: zero primary findings, 15 fragment-only default-black advisories; rendered Rack palette is unchanged. CSS 32,942 bytes, counts.js 3,501 (+34), cumulative added JS 11,474 < 12,000, font 103,912 unchanged.

Migration compatibility checked with a WAL-safe development backup: 58 buy-ins, 4 reversals, 39 cash-outs, 2 cash-out reversals, 9 finalizations, 37 results, 17 transfers and 16 payments retain every original column/value. Every existing group gains its account; historical settings and rake snapshots stay zero and no fee entry is invented. Migration drift check passes. Physical-phone verification remains unavailable.

2026-10-04: Living docs synced: PRODUCT/DESIGN narrative and six surface addenda by the required documenter, wiki architecture/features/setup/journal and rake settlement footgun, browser commands and TODO. DESIGN token frontmatter and sidecar remain unchanged. Local rendezvous follows final checks; no push/deployment.

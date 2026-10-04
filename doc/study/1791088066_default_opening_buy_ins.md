# Default opening buy-ins

Date: 2026-10-04. Request: “before the start of each set, can you add one buy-in per player by default.”

## Outcome

Remove repetitive first-buy-in entry. Proposed interpretation: the host’s Start the game action records the current usual buy-in for every joined player without an accepted buy-in, before starting play. This applies to the first set and each subsequent set. A checked native option lets the host start without automatic entry.

## Current state and evidence

Main is clean at `67ee032`. All 395 SQLite tests pass (13.838 s). AGENTS.md requires study and plan approval before implementation. SPEC.md is human-owned and will remain unchanged. There is no doc/canonical directory.

- `games.services.transition()` handles open → running and starts the set/player clocks. It currently records no buy-in and has no durable start request ID.
- `games.services.start_next_set()` opens a new set, copies settings and joined participants, and copies no money. The host can change its roster before starting play. Existing next-set tests assert these facts.
- `SettingsVersion.default_buy_in` already supplies the usual amount and is constrained between min/max. Each BuyIn records its settings version.
- `ledger.services.record_buy_in()` owns money creation, locks the set, validates joined status/current stakes and writes audit/version updates. BuyIn has a unique `(session, request_id)` constraint. A reversed buy-in is retained but excluded from accepted totals.
- `ledger.apps.LedgerConfig.ready()` already registers lifecycle hooks in games for resume, return and money checks. This permits ledger-owned effects without a games → ledger import.
- `templates/web/_host_controls.html` has the sole Start the game form. It currently has no request_id. `games.views.session_transition()` invokes the lifecycle service.
- `games.clock.start()` starts timers for joined players, independently of their buy-ins. Start next set opens a set; it does not start its timer.

Sources: AGENTS.md, SPEC.md, PRODUCT.md, wiki README/architecture/features; named source and test files above.

## Options and tradeoffs

1. Record on adding a participant or opening a set. Money would exist before the host finishes roster/settings preparation. Withdrawals, cancellations and unit changes would then require reversals. This adds side effects to joining and new-set creation.
2. Record atomically when starting play, before the clock starts. Uses the final roster/settings and one host confirmation. This best fits “before the start” without charging people merely added to a draft.
3. Offer a separate bulk-buy-in action. More control, but leaves an extra required step each set.

Recommend option 2. A checked “Add usual buy-in … for players without a buy-in” option makes the default explicit and permits exceptions. Starting remains one action. Existing accepted buy-ins are not duplicated or topped up. Only joined set participants qualify, not the entire group roster. Late joiners retain manual buy-in entry. Resume never adds a new opening buy-in.

## Implementation direction

Add a start lifecycle hook registered by ledger. Invoke it under the existing set lock and transaction, while the set is open and before creating clock periods. The ledger hook records ordinary append-only BuyIn rows through the existing service. Derive per-player request UUIDs from the host start request and participant ID.

Persist the first start request ID on GameSession with a database uniqueness constraint. Same-request retries return the successful result without recreating money, audit or timer records, including when there were zero eligible players or a buy-in was later reversed. A competing different start request is refused once the set has started. Legacy already-started sets keep a null marker and receive no backfill. New-set creation remains money-free.

## Risks and proposed acceptance decisions

Automatic records affect the books; they must be visible in totals and the log, attributed to the host and reversible with the existing reason flow. Show the formatted usual amount beside the checked option. Settings and roster eligibility are re-read under the lock. A failure must roll back all buy-ins and the start/timers. Concurrent start/manual buy-in writes must serialize on the same set.

A player whose only buy-ins were reversed before starting qualifies again; the host can uncheck automatic entry when that is intentional. A player with any accepted buy-in is skipped even if the amount differs from the usual buy-in. No new setting, payment, conversion, historical backfill or late-join automation is proposed.

External inputs: none. PostgreSQL 17 and native browser verification are needed in execution. Physical-device testing is unavailable.

## Open questions

No blocking implementation question. The trigger, skip rule, per-set opt-out and late-join boundary above are proposals for human approval, not accepted product facts.

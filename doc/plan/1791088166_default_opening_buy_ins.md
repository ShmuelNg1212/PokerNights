# Default opening buy-ins

Status: **awaiting-approval**. Date: 2026-10-04.

Source: [study](../study/1791088066_default_opening_buy_ins.md). Canonical sources: AGENTS.md, SPEC.md, PRODUCT.md and wiki architecture/features. Main was clean at `67ee032`; study commit `d2b6317`. Baseline: 395 SQLite tests pass.

## OPEN QUESTIONS

No blocking technical question. Approval of this plan confirms the proposed behavior: automatic entry on Start the game; skip players with accepted buy-ins; a checked per-start opt-out; late joiners remain manual. No implementation has started.

## Goal and acceptance criteria

Start each set with one usual buy-in per eligible player, without repetitive taps or duplicate money records.

- **AC1:** Start the game shows a native option checked by default, with the set’s formatted usual amount and the explanation that existing buy-ins are kept. Unchecking starts play without automatic buy-ins.
- **AC2:** On confirmation, each joined participant with no unreversed buy-in receives one ordinary BuyIn at the latest settings’ default_buy_in. Players with an accepted buy-in receive no extra record, regardless of amount/count. Left/withdrawn players and unrelated roster members receive none.
- **AC3:** The first and later sets behave alike. Start next set still creates an open set with zero money; roster/settings can be adjusted before starting. Resume and late joining do not trigger opening buy-ins.
- **AC4:** Buy-ins, audit events, version changes, first-start marker and set/player timers commit atomically under the set lock. Any failure leaves all unchanged. Records precede play’s clock start and identify the host, amount/unit and settings version. Totals and log reflect accepted records; reversal remains the correction path.
- **AC5:** A retry with the same start request makes no new buy-in, audit or timer record, even with zero eligible players or after a later reversal. Concurrent different starts and concurrent manual buy-ins serialize, never duplicating an opening record. Host/membership gates remain enforced.
- **AC6:** Pesos and chips retain integer amounts and existing formatting. Existing historical sets receive no backfill. No payment, chip conversion, bankroll or settlement rule changes.
- **AC7:** Focused service/view tests and full SQLite/PostgreSQL suites pass. Native browser start, opt-out and next-set flows show exact expected totals and log records. Current Rack layout and 48px controls remain usable on phone and desktop.

## Scope and implementation

1. `games/models.py` and an additive migration: nullable unique first-start request UUID on GameSession. Existing rows remain null; do not fabricate historical requests. Each new set starts with a null marker.
2. `games/services.py`: extend the start transition with request_id and the default-opening option. Validate host/group, lock the set, detect an already-completed same request before state refusal, then run a registered START_HOOK while open. Persist the request marker and start clocks only after hooks succeed. Other transitions retain their behavior. Direct start service calls use the automatic default, with explicit opt-out for callers needing money-free play.
3. `ledger/services.py` and `ledger/apps.py`: register the hook once. Re-read joined participants and accepted buy-ins under the lock, derive child UUIDs from the start UUID and participant identity, and use record_buy_in for missing opening entries. Add automatic-opening context to the audit data if useful; keep ordinary correction/log behavior. Do not import ledger into games.
4. `games/views.py`: read request_id and native checkbox for start; an unchecked/absent checkbox means opt-out for a posted form. Existing non-start POST behavior stays unchanged.
5. `templates/web/_host_controls.html`: request_id in Start the game form, checked option, formatted usual amount and concise skip explanation. Reuse existing checkbox/field styles and native behavior. No new JS or visual identity. Apply Impeccable guidance only to this small established control extension during execution.

Only service functions write business records. Keep append-only accounting, locks, request constraints, auditing and version updates. Do not duplicate buy-in validation in views.

## Exclusions and dependencies

No buy-in on draft creation, roster addition or next-set creation. No automatic late-join buy-in, global preference, backfill, per-player amount editor or new bulk action. No changes to human-owned SPEC.md. No push/deploy. Local Django, SQLite, PostgreSQL 17 and installed browser are the only verification inputs.

Reversed-only pre-start buy-ins qualify as absent. The host can uncheck the option to preserve intentional zero-buy-in play. Already-started legacy sets are never changed by this feature.

## Branch and rollback

After approval, record the answer and create `feat/default-opening-buy-ins` from current main in an isolated worktree. Preserve unrelated changes. Revert feature/docs commits to roll back behavior; leave the nullable schema column until a separately checked reverse migration. Do not delete recorded buy-ins; correct accepted records through reversals with reasons.

## Task board

- [ ] **1. Implement and verify the start behavior.** Add marker/migration, lifecycle hook and ledger logic, native option and focused tests. Update intentional money-free test fixtures with explicit opt-out rather than weakening assertions. Inspect existing browser fixtures before any start to avoid silently doubling manually recorded opening amounts.
  - Commit: `feat(ledger): add default buy-ins when starting a set`.
  - Done when AC1–AC7 pass and evidence is recorded below.
- [ ] **2. Rendezvous and sync docs.** Update wiki architecture/features/index, TODO and relevant built control documentation after verification. Follow any applicable bounded Impeccable finish/documentation requirements for the control extension. Merge to main, apply the additive migration locally, run tests on main and verify the running server serves the new native start form.
  - Commit: `docs: sync default opening buy-ins`.
  - Done when main contains verified behavior, the server answers and this plan is marked done.

## Verification

- Service tests: no-money roster, mixed accepted buy-ins, different manual amount, reversed-only player, left/withdrawn, current settings changes, pesos/chips, first/second set, opt-out, resume, late join, empty roster and legacy running set.
- Idempotency/transaction tests: same request retry, different request after start, retry after reverse, forced hook failure rolls back money/audit/marker/timers, PostgreSQL concurrent starts and manual buy-in/start serialization. Assert exact rows and amounts, not only HTTP success.
- View tests: checked default and formatted amount, request ID, host success/unchecked success, player 403 and outsider 404. Native form works without JS; repeated POST does not record twice.
- Full suite: SQLite before every commit; PostgreSQL before merge. Review fixture changes for their original intent. Check migration drift and forward migration on temporary data with existing sets.
- Browser: synthetic temporary database. Add players to first open set, start with default, inspect totals/count/log; manually buy in one player first and verify skipped; second set starts money-free, then receives fresh opening buy-ins; unchecked start produces no records. Check phone/desktop, native checkbox and focus. Report physical-device testing unavailable.

## Documentation sync

Wiki features: default start option, skip rule, reversal and late-join boundary. Architecture: hook ownership, atomic start and request marker. Wiki journal/README, TODO and plan evidence. DESIGN.md or surface brief only for the built control addition; preserve incumbent tokens. PRODUCT.md only if capability context requires it. Studies remain immutable; SPEC.md remains human-owned.

## Progress and blockers

2026-10-04: study and plan prepared. No external blocker. Awaiting human approval of this cycle; no source, model, migration or template change made.

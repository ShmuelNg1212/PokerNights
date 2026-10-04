# Add a player during play

Status: **awaiting-approval**. Date: 2026-10-04.

Source: [study](../study/1791091289_add_player_during_play.md), commit `7973c50`. Main implementation baseline: `e133a1a`. Canonical sources: AGENTS.md, SPEC.md, PRODUCT.md, DESIGN.md and current wiki. Baseline: 423 SQLite tests pass, with three PostgreSQL-only skips.

## OPEN QUESTIONS

The app already supports adding existing roster members while running. This plan proposes the missing new-name path and keeps Add players visible even when everyone on the roster is seated. The optional clarification has not received an answer. Approval of this plan confirms that the host should be able to create a roster player and join them to the current set in one action. Buy-in remains a separate action; no automatic late buy-in is proposed.

## Goal and acceptance criteria

Add a late arrival from the ongoing set without returning to group management.

- **AC1:** Hosts see Add players beside the player-list heading in setup, open and running sets, including when no existing roster member is eligible. Players do not receive this host action. It opens the existing picker page.
- **AC2:** The picker retains existing roster selection and adds a separate native form with Player name and Add new player. Explain that the name joins the group roster and that adding records no buy-in. The form remains available when everyone on the roster is at the table. At capacity, show the full-table explanation and disable unavailable add actions; server validation remains authoritative.
- **AC3:** A successful new-name submission creates exactly one active roster player without a login and joins that player to this set atomically. Apply existing name normalization and active case-insensitive uniqueness. During running play, start only the new player's interval at acceptance time. Keep existing clocks, set state, buy-ins and cash-outs unchanged. Return to the set with a success notice and the normal manual buy-in action.
- **AC4:** Under the set lock, recheck host, group, state and capacity. Refuse count-up, finalized and canceled sets. A name error, duplicate, full table, ended-set race or downstream failure creates no member, participant, timer or partial audit/version/request record. Show a useful error and retain the typed name for review; invalid-stage recovery shows the set's current state and a return link without permitting another add.
- **AC5:** Each new-name form carries a unique request UUID. Repeating an accepted request returns its original result without duplicate roster/player/timer/audit records or version changes, including after the set state changes. Concurrent retries and last-seat additions serialize. Same-name additions from different sets in the group accept one new identity and refuse the other without an orphan. Duplicate names guide the host to the existing roster selection; they do not silently join a different identity.
- **AC6:** Normal existing-member selection, returning players, live updates, timer behavior and opening-buy-in rules remain usable. Works without JavaScript on phone and desktop, with visible labels/errors, 48px actions and established Rack styles. No schema, new JS, dependency, asset or shared token change. Full SQLite/PostgreSQL suites and scoped browser checks pass.

## Scope and implementation

1. Add a games service to create a roster player and join them. Use an outer `transaction.atomic()`, require host and lock the set first. Detect a completed request before state refusal, then check state/capacity. Compose `groups.services.add_roster_player()` and the existing participant batch service. Reuse ParticipantBatch's unique set/request key for the accepted single-player operation; no new model is needed. Both forms use independent request IDs. Preserve groups → games dependency direction and service-only writes.
2. Verify group/set lock ordering against current writers. Existing group roster creation owns normalization, group locking, uniqueness and its audit. Existing participant addition owns joins, intervals, participant audit, request batch and set version. Do not duplicate those responsibilities in the view.
3. Extend `games.views.participants_add` with an explicit new-name form action and existing name validation. Keep the multi-selection action intact. Preserve refusal data/error next to the correct form; distinguish a changed set state from a name/capacity error. Re-resolve membership and never accept a client-provided group ID.
4. Extend `templates/games/add_players.html` using established native field/form components. Keep the search enhancement scoped to the existing selection form. Change `_players.html` visibility to depend on host/state rather than nonempty roster candidates. Do not add another sheet or move money controls.
5. Apply Impeccable as a narrow Operate extension during execution, inheriting the existing active-set/picker system. Use bounded phone/desktop captures and applicable finish-review/documentation roles. No visual direction exploration.

## Ordered task board

- [ ] Record approval, confirm current main and create isolated branch/worktree `feat/add-player-during-play`. Link the active plan from TODO during execution.
- [ ] **`feat(games): add new players from an ongoing set`**: implement the atomic operation, explicit form action, error preservation and visible entry point with directly related tests. Completion: AC1–AC5 demonstrated with exact record/timer/audit assertions and synthetic browser flows.
- [ ] Verify AC6 and address material in-scope findings: full SQLite/PostgreSQL, shared roster picker regressions, opening/default-late-buy-in boundary, native forms and required finish review.
- [ ] **`docs: document adding players during play`**: sync affected wiki/features/architecture, PRODUCT capability wording if needed, built design/surface notes, TODO and plan evidence. Completion: docs explain roster persistence, late timer start and separate buy-in.
- [ ] Rendezvous: merge verified work into local main, check the running app and record completion. No push or deployment.

## Verification and dependencies

- Service tests: running success, setup/open compatibility, exact new roster/participant/request/audit/version/interval records, normalized name, no money, duplicate/blank/long name refusal, permissions, cross-group denial, full table, non-addable state and forced failure rollback. Same-request retry must not write twice even after a state transition.
- PostgreSQL races: concurrent same request, new player versus existing-member add for the last seat, two sets adding the same case-insensitive name. Verify exact committed rows and no orphan; do not infer locking from SQLite.
- View tests: entry point when no unused roster candidates remain, new-name success/refusal with bound text, distinct action and request IDs, full-state guidance, unchanged multi-selection, host-only POST and outsider 404. Returned set exposes manual buy-in without recording it.
- Browser: ongoing set with all roster members seated; add a new name without JS and return to the running set. Verify new row/timer, unchanged existing totals, manual native-unit buy-in, second-host live arrival, duplicate name recovery, full table and stale/end-play refusal. Check roster member selection still works and the new name persists in the group's roster for later sets.
- Capture established phone and desktop sizes in one batch; check no overflow, labels, local errors and 48px actions. Report physical-phone testing unavailable. Run SQLite before each commit and PostgreSQL before merge; check migration drift and CSS budget (below 40,000 bytes). Added JS budget stays at the current 11,440 bytes.

Only local Django, databases and installed browser are required. Use fresh synthetic fixture data, never development money records. No external inputs or credentials are missing.

## Boundaries, rollback and docs

No automatic buy-in for late arrivals, account/invitation creation, new role, seat assignment or waitlist. No additions during count-up or after finalization, reopening, player removal redesign or historical backfill. SPEC.md remains human-owned.

Rollback by reverting the feature and its docs. There is no migration; accepted roster members remain ordinary valid roster data. Keep recorded game history intact.

Update current wiki features/architecture and journal/index; add a footgun only for confirmed unintuitive behavior. Keep studies immutable. DESIGN.md and existing surface notes describe only the built extension; preserve machine tokens and existing identity.

## Progress

2026-10-04: study and plan completed. Existing roster additions during running play are confirmed in code. New-name interpretation is proposed for approval. Implementation has not started.

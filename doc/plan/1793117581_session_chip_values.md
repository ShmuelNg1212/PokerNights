# Session chip values: plan

Date: 2026-10-28. Mode: mixed. Status: verified; local feature branch; awaiting ship. Frozen after rendezvous.

Study: [session chip values](../study/1793117529_session_chip_values.md).

## OPEN QUESTIONS

None. The human approved this scope on 2026-10-28 and asked for UI, UX and animation polish. These defaults are accepted:

- One optional chip-value table per session. All its sets share it.
- Only a host can edit it. Edits stop after the first submitted chip-based count, including an unconfirmed player count. Reopening or clearing a count does not unlock it.
- Values use the session unit: pesos or whole chip units. No exchange rate is introduced.
- Start each session without assignments. No automatic reuse from another session in this scope.
- Use whole-number quantities per denomination. Stack-of-20 shortcuts are deferred.

## Acceptance criteria

1. Two sessions can assign different values to the same colour without affecting each other.
2. Every set in a session uses the same saved assignments.
3. A host and a player can submit an ending stack by denomination. The server calculates the total exactly.
4. Chip entry preserves the existing host confirmation, cash-out and balance checks.
5. Saved counts retain their original denomination and quantity breakdown.
6. Direct amount entry and existing sessions keep working without setup.
7. Access, repeated requests, stale forms and concurrent edits cannot bypass these rules.

## Tasks

- [x] **1. Save session assignments. `tests: first`.**
  - Add session-owned denomination data, an assignment revision and a durable lock marker.
  - Use a fixed colour palette with written names. Allow an optional label of up to 40 characters. Allow 1 to 12 denominations, with no repeated colour in one table. Values must be positive integer minor units within the existing amount range. Two colours may have the same value.
  - Add a host-only write service. It replaces the table atomically before it locks. Serialize on the session row. Check the posted revision and a unique request ID. Audit the change and invalidate the relevant set live versions using the existing version rules.
  - Refuse closed or archived sessions. Preserve the app dependency direction.
  - Cover session isolation, shared sets, validation, permissions, stale revisions and idempotency. Add a PostgreSQL race check for edit versus first count.
  - **Complete when:** migrations and service tests pass and a concurrent write cannot change assignments used by a count.

- [x] **2. Calculate and record chip-based counts. `tests: first`.**
  - Add one shared calculation module. Accept saved denomination IDs and nonnegative integer quantities. Reject unknown IDs, negative or fractional quantities, duplicate rows, stale revisions and totals outside the existing amount range.
  - Blank quantities mean zero only within an explicitly submitted chip form. Require at least one explicit quantity or the Empty stack action. Keep a missing count distinct from zero.
  - Integrate at the existing count service seam. Calculate on the server, then run the existing player-entry or host-confirmation rules in the same transaction. Lock assignments only after a successful chip-based submission.
  - Store an immutable breakdown snapshot on each chip-based CountEntry and FinalCount. Copy the snapshot when a host accepts a player's entry. A manual replacement must not inherit an unrelated breakdown.
  - Keep existing signatures and callers compatible where practical. Add optional chip input rather than a second count workflow.
  - Cover exact centavos, whole chip units, zero, large values, retries, corrections, player confirmation and mismatched browser totals. Run existing ledger and settlement tests.
  - **Complete when:** persisted totals come from server arithmetic and existing count and cash-out rules still pass.

- [x] **3. Add setup and counting screens. `tests: alongside`.**
  - Add Chip values to the session page. All members can read the table. Only hosts see edit controls and the lock explanation.
  - Add Count by chips to host count rows and Your count when assignments exist. Use the current sheet and form patterns. Show colour plus written label, denomination, quantity, subtotal and total.
  - Use a labelled local preview with integer arithmetic. Submit denomination IDs, quantities and revision. Do not trust a posted total.
  - Show the saved breakdown when reviewing an entered or confirmed count. Preserve drafts on live updates and refused submissions. Warn clearly when the assignment revision changed.
  - Keep direct amount entry. Provide server-rendered setup and chip-count pages without JavaScript. No new animation is required.
  - Probe host setup, player submission and host confirmation at 320, 390 and 1280 px. Check 48 px targets, long labels, keyboard focus, reduced motion and no sideways scroll.
  - **Complete when:** the first real flow works from sign-in through a persisted chip-based count, as host and player, including without JavaScript.

- [x] **4. Rendezvous and sync docs. `tests: alongside`.**
  - Run the full Django suite and PostgreSQL suite. Review correctness, membership access, locking and money handling. Use independent read-only review agents under AGENTS.md.
  - Exercise two signed-in sessions with different assignments for the same colour. Submit a real count, confirm it, cash out and check the resulting balance. Exercise a second set that shares the first session's table.
  - Allow at most two fix-and-recheck rounds. Record commands, verdicts and browser evidence below. Stop and ask if a check still fails.
  - After approval, record the session-unit denomination decision in an ADR. Update the glossary, spec, features and architecture where required. State that chip denominations are an input method, not an exchange rate. Update DESIGN.md with the built forms.
  - Update TODO.md with unreleased phone checks. Refresh graphify. Leave a verified local feature branch. Do not merge or push until told to ship.
  - **Complete when:** checks pass, wiki facts match the implementation and phone checks are ready.

## Execution notes

Create `feat/session-chip-values` at execution. Stack it on the latest unreleased feature if one exists; otherwise use main. Keep existing unrelated local files out of commits.

This is larger than one commit. Implement in focused Conventional Commits. Write rule and arithmetic tests before implementation. Do not delegate code changes unless task files can be separated under AGENTS.md.

## Verification record

Verified 2026-10-28 on `feat/session-chip-values`. No merge or push.

- **Rules and arithmetic:** backend tests were written before each implementation slice. Red cases covered missing assignment service, chip count input and unit-change refusal. Final service tests cover request replay, stale revisions, zero, fractions, overflow, immutable breakdowns and confirmation.
- **SQLite:** `DEBUG=True .venv/bin/python manage.py test --noinput`. 1,429 tests, OK, 17 PostgreSQL-only skips. Log: `/private/tmp/pn-chip-sqlite-final.log`.
- **PostgreSQL:** `DATABASE_URL=postgres://localhost:5432/pokernights DEBUG=True .venv/bin/python manage.py test --noinput`. All 1,429 tests pass. No skips. Includes edit-versus-first-count and same-request concurrency checks. Log: `/private/tmp/pn-chip-postgres-final.log`.
- **Schema and source:** `manage.py makemigrations --check --dry-run` reports no changes. `manage.py check` reports no issues. `git diff --check` and `node --check static/js/denominations.js` pass.
- **Browser:** `node web/tests/browser/chip_values.mjs`, with a fresh synthetic SQLite database. All 34 checks pass. Started from signed-in host and player pages, saved values, submitted quantities, confirmed the player's entry, recorded cash-outs and checked balanced books. Also checked independent session values, a second set sharing assignments, native setup and count writes, invalid quantities, focus return, drafts, stale-value recovery and reduced motion. No runtime exceptions. Report and captures: `/private/tmp/pn-chip-review/`.
- **UI review:** inspected setup and count-sheet captures at 320, 390 and 1280 px. Fixed clipped colour names by stacking setup fields at narrow widths. Quantity fields are 48 px high with 20 px text. Visible labels supply colour and denomination to screen readers. Native pages keep unused sheet sources hidden.
- **Independent review:** standards/security review passes. Spec/UI/motion review passes after fixes. It checked integer arithmetic, access, request replay, locking, count evidence and the approved scope. Motion uses the existing sheet and 260 ms shift presets with transform and opacity only. Amounts do not animate.
- **Fix rounds:** the first full test run found six old assertions that matched the new script filename and one script-order expectation. Renamed the script to `denominations.js` and updated that expectation. Both full suites pass on their first recheck. Browser review found stale closed-draft repricing and a closing-sheet lifecycle error. Both are fixed; the final browser recheck passes within the two-round limit.
- **Docs:** ADR 0004 records the approved denomination rule. Spec, features, architecture, glossary, PRODUCT.md and DESIGN.md match the code. TODO.md has the unreleased phone check. Real hardware keyboard, touch and safe-area behavior remain for that phone check.

Implementation detail: configured chip values block a unit change, even before money is recorded. This prevents saved denominations from changing meaning. The parent session lock is now acquired before the set lock, to serialize count writes and assignment edits without opposite lock order.

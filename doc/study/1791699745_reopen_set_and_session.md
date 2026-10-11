# Reopen a finalized set or a closed session: study

Date: 2026-10-11, Asia/Manila.

## Request

The human said: "can you add a feature for reopening a finalized set or closed session."

Asked what it is for, the human chose **both**: to fix a wrong count, cash-out or buy-in found after finalizing, and to reopen a session that was closed too early so the table can play another set or settle up again.

Asked what happens to transfers already marked paid, the human chose **refuse until unmarked**: a session with a paid mark is not reopened; the host marks those transfers unpaid first.

## What happens today

- `settlement.services.finalize()` freezes a set: one `Finalization` and one `PlayerResult` per player, then the state `finalized`. No service leaves that state.
- `settlement.services.close_night()` closes a session: one `SettlementPlan` with its `Transfer` rows, then the status `closed`. No service leaves that status. A closed session takes no new set.
- The screens and documents say so: "A finalized set and a closed session cannot be reopened" (features, Limits today); "Finalizing asks once, because the app cannot reopen a finalized set" (PRODUCT.md).
- A mistake found afterwards stays in the results, the transfer list and the stats.

## What the first design already decided

The architecture study (`1791037419`, sections 7.10 case 6, 7.11 and the permissions table) designed reopening for Stage 2 and the code kept room for it:

| Designed | In the code today |
|---|---|
| A correction is a new revision; the old one stays, marked not current | `Finalization.revision`, `is_current`, the unique rules "one revision number per set" and "one current per set", and `PlayerResult.is_current`. `ledger.services.write_results()` already writes revision `n + 1` and retires the previous rows first |
| Reopen is a host action from the finalized state, with a reason | Not built |
| Stats read current results only | Built: `stat_results()` reads current results of finalized sets in closed, unarchived sessions |
| Payments made under the old revision count toward the new transfer list | Not built. The human chose the simpler rule for this cycle |

So the set side needs a state change and a record of why. The session side needs more, because the settle-up records were written as "once".

## Findings

1. **A set returns to counting up.** In `reconciliation` the host can already reverse a cash-out or a buy-in with a reason, clear and confirm counts, cash out, record or remove a balance override, and finalize. Finalizing again writes the next revision without new code.
2. **The plan is one-per-session in the database.** `SettlementPlan.night` is a one-to-one link and `Transfer` rows are never edited. `Payment` rows, reversed ones included, point at their `Transfer` with a protected link. Money records are append-only (AGENTS.md rule 4), so a reopened session's plan cannot be deleted. It has to stay, marked not current, and the next close writes a new one. That needs a migration: the one-to-one link becomes a plain link with "one current plan per session".
3. **Six readers assume one plan per session.** `night_outcome()`, the settle states of the session list, `unpaid_transfers()` (home page and member removal), `unpaid_in()` (archive confirmation), `_transfer()` (mark paid and unpaid) and the repeated-tap branch of `close_night()`. Each must read the current plan only, or a retired transfer would show as owed.
4. **Paid marks.** With "refuse until unmarked", a reopened session never has an active payment, so no transfer list has to account for money that already moved. `mark_unpaid()` keeps the payment row with a reversal, so the history of what was marked stays.
5. **Stats and results need no change.** A reopened set is not `finalized` and its results are not current, so it leaves the session's results and the boards at once. A reopened session is not `closed`, so all of its sets leave the boards until it is closed again. The first design wanted "under correction" results to stay on the boards; that is more to build and shows figures known to be wrong.
6. **A set inside a closed session.** Its results are in the session's transfer list. Reopening the set alone would leave a list that no longer matches. The session must be reopened first.
7. **A missed buy-in cannot be added while counting up.** Buy-ins are accepted only while a set is open or in play. A reopened set can resume play (then a buy-in is possible) unless a later set of the session exists; then nothing accepts it. See decision 3.
8. **Other guards already cover the new states.** Archiving, deleting, removing a member and archiving a group refuse while a set is counting up. An archived session takes no write. The set page polls `GameSession.version`, which both actions must bump.
9. **Idempotence.** Finalize and close carry no `request_id`; a repeated tap is recognised by the state. Reopening can follow the same pattern: a second tap finds the set counting up, or the session open, and does nothing.
10. **The closing recap** opens by itself once per session, viewer and browser. After a second close it does not open again by itself; "View session recap" shows the new figures.
11. **Partial unique rules are checked per statement** (footgun). Retire the old row before writing the new one, as `write_results()` does.

## Options for the retired plan

| Option | For | Against |
|---|---|---|
| A. Keep the plan, mark it not current; the next close writes a new plan | Append-only; reversed payments keep their transfer; the log can show what the list was | One migration; six readers change |
| B. Delete the plan and its transfers on reopen | No migration | Breaks rule 4; protected links from reversed payments block the delete |
| C. Keep one plan, replace its transfers on the next close | No new plan rows | Edits rows documented as never edited; loses what the first list said |

Recommend A.

## Risks

| Risk | Effect | Answer |
|---|---|---|
| A reader still counts a retired plan | A settled debt shows as owed on the home page | One helper for "current transfers"; a test per reader with a session closed twice |
| The migration runs on live data during the Vercel build | A failed build keeps the previous release; a half-applied change would not | Both steps are additive in effect (a unique index is replaced by a narrower one, columns are added with defaults). PostgreSQL runs the migration in one transaction. Run the PostgreSQL suite before release |
| A host reopens by accident | Results leave the boards until closed again | A confirmation sheet with a required reason; nothing is lost and closing again restores everything |
| Results change after players have read them | A player acts on the old figure | The set and session pages say the results were corrected, when, and why |

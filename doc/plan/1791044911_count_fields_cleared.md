# Plan: keep typed counts when confirming

- **Date:** 2026-10-04 00:28 (Asia/Manila), Unix timestamp `1791044911`
- **Status:** `done`
- **Study:** [../study/1791044894_count_fields_cleared.md](../study/1791044894_count_fields_cleared.md)
- **Workflow:** `agentic-workflow`. Phase 2 starts only after explicit human approval of this plan.
- **Approval record:** Approved by the human on 2026-10-04: "approved".

## OPEN QUESTIONS

None. One behavior to note before you approve: **each "Confirm count" button will confirm every count that is typed, not only its own row.** A "Confirm all counts" button is added under the list for the same action.

## Goal

A host types several final counts and confirms them without losing any typed value.

## Scope

- One submit confirms every filled count field of the set, in one transaction.
- A refused submit keeps each typed value in its field.
- The live refresh keeps typed, unsaved values in the set page's fields.
- Tests and a browser check that reproduce the bug first.

## Exclusions

- No change to what a count means, to statuses, to the batch cash-out or to finalization.
- No model or database change.

## Acceptance criteria

| # | Criterion |
|---|---|
| AC1 | The host types counts for three players and taps one "Confirm count". All three are confirmed and show "Ready to cash out". No typed value is lost |
| AC2 | A field left empty stays "Awaiting count". It is not read as zero. A typed 0 is confirmed as zero |
| AC3 | If one typed value is not valid, nothing is saved, the message names the player, and each typed value is still in its field |
| AC4 | A count field that is not changed does not create a new version of that player's count |
| AC5 | While the host has typed values that are not saved, a live update caused by someone else does not clear them |
| AC6 | The same protection applies to a typed buy-in amount and a typed reversal reason on the set page |
| AC7 | Sending the same confirmation twice confirms each count once |
| AC8 | A player still cannot confirm counts |

## Tasks

- [x] **1. Reproduce.** A browser check that types three counts, taps one "Confirm count" and expects three confirmed counts; and one that types a value, triggers a live update from a second session and expects the value to stay. Both must fail on the current code.
  - Done when: both fail for the stated reason.
- [x] **2. Confirm every typed count in one action.** `ledger.services.confirm_counts()` (several players, one transaction, all-or-nothing, `request_id`); the count fields join one form; "Confirm all counts" button; a refused submit shows the typed values again.
  - Commit: `fix(ledger): confirm every typed count instead of clearing the other fields`
  - Done when: tests cover AC1 to AC4, AC7 and AC8, and the first reproduction passes.
- [x] **3. Keep typed values across a live update.** `static/js/live.js` saves and restores the values of keyed fields around a refresh.
  - Commit: `fix(web): keep typed values when the live view refreshes`
  - Done when: the second reproduction passes, and AC6 is checked in the browser.
- [x] **4. Verify, merge, docs.** Full suite on SQLite and PostgreSQL. Browser run at phone width. Merge to `main`. Update `features.md`, `architecture.md` and add a footgun page. Restart the server.
  - Commit: `docs: sync living documentation`
  - Done when: `main` has the fix, the tests pass on `main`, and the server answers.

## Verification

| Topic | Test |
|---|---|
| Several counts | Three typed, one tap: three current counts, one version increment of the set, one audit event per player |
| Empty and zero | Empty skipped; "0" confirmed; a form with no typed value is refused with a message |
| Invalid value | "abc" for one player: no count saved for anyone; typed values shown again |
| Unchanged value | A second submit with the same figure: no new version |
| Already cashed out | A typed value for a player cashed out in the meantime: nothing saved; the message names the player |
| Retry | The same `request_id`: no second set of counts |
| Access | Player 403, stranger 404 |
| Live refresh | Browser: typed count, buy-in amount and reversal reason survive a refresh caused by another session |
| Regression | The existing 356 tests pass |

## Branch strategy and rollback

Branch `fix/count-fields` from `main`. No migration. Rollback is a revert of the merge commit. Local merge only; no push.

## Documentation sync

`doc/wiki/features.md`, `doc/wiki/architecture.md`, a footgun page on separate forms and live refresh.

## Progress log

| Date | Entry |
|---|---|
| 2026-10-04 00:28 | Study and plan written and committed. Status `awaiting-approval`. |
| 2026-10-04 | Human approved. Work is done in a separate git worktree so that the running dev server on `main` is not disturbed before the merge. |
| 2026-10-04 | Reproduced in headless Chrome on the old code: 7 of 11 checks failed (one tap confirmed one of three counts; a live update cleared a typed count, a buy-in amount and a reversal reason; a refused submit lost the typing). Fixed. Merged to `main` locally. Status `done`. |

## Verification results (2026-10-04)

| Check | Result |
|---|---|
| Reproduction on the old code | 7 of 11 browser checks failed, for the two causes in the study |
| The same browser checks on the fix | 11 of 11 pass, at 390 × 844 |
| `manage.py test` on SQLite | 368 tests, pass (12 new) |
| Same suite on PostgreSQL 17.11 | 368 tests, pass |
| `makemigrations --check` | No changes (no database change) |
| Screenshot of the counting screen | Reviewed by the AI |

| # | Result | Evidence |
|---|---|---|
| AC1 | Met | Browser check; `ConfirmSeveralCountsPageTests` |
| AC2 | Met | Browser check; service and page tests |
| AC3 | Met | Browser check; `test_refused_submit_saves_nothing_and_shows_the_typed_values_again` |
| AC4 | Met | `test_an_unchanged_count_gets_no_new_version` |
| AC5, AC6 | Met | Browser check with a second session |
| AC7 | Met | `test_repeated_submission_confirms_once` |
| AC8 | Met | `test_player_cannot_confirm_counts` |

Not checked: a physical phone. The earlier end-of-set browser script was not rerun, because it drives the old one-row form; its flow is covered by the page-driven tests, which pass.

Notes:

- The one-row request shape (`participant_id` and `amount`) is still accepted, so a set page that was open before the fix keeps working.
- Typed values that were refused are kept in the login session and shown once.
- Fields that the live refresh keeps: final counts, buy-in and cash-out amounts, reversal reasons, the override note and the cancel reason.

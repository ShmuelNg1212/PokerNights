# Reopen a finalized set or a closed session: plan

Status: approved 2026-10-11 ("approved"); all five decisions as recommended. Built and released. The human asked for the design and motion skills on the screens. Date: 2026-10-11, Asia/Manila. Study: [Reopen a finalized set or a closed session](../study/1791699745_reopen_set_and_session.md).

## Outcome

A host who finds a mistake after the fact can fix it in the app. A finalized set goes back to counting up, is corrected with the tools that exist there, and is finalized again. A closed session goes back to open, so a set can be corrected, another set can be played, and closing writes a new who-pays-whom list. Nothing that was recorded is removed: the earlier results and the earlier list stay in the log with the reason.

## Behaviour

| Moment | Today | After |
|---|---|---|
| Finalized set, session open, host | No way back | "Reopen set" under Host controls opens a sheet: what will happen, a required reason, one button. The set returns to counting up |
| Reopened set | — | Counts, cash-outs, reversals and the override work as in any count-up. The page says "Reopened to correct: *reason*". Finalizing again writes revision 2 |
| Set finalized a second time | — | The final page says "Corrected on Oct 11: *reason*". The set log lists both revisions, the earlier one marked "replaced" |
| Finalized set, session closed | — | No reopen button on the set. It says: "The session is closed. Reopen the session first." with a link |
| Closed session, no transfer marked paid, host | No way back | "Reopen session" among the session's host actions opens a sheet with a required reason. The session is open again: the transfer list goes away, results read "not final", Start next set and Reopen set are available |
| Closed session, some transfers marked paid | — | The sheet says "2 transfers are marked paid. Mark them unpaid first." and has no button. The service refuses the same way |
| Session closed a second time | — | A new transfer list from the current results. Every transfer starts unpaid |
| Results and stats while reopened | — | A reopened set is left out of the session's results. A reopened session is left out of the boards and of "what you owe" on the home page until it is closed again |
| A player on a reopened set | — | Sees the count-up page as in any count-up, with the reason line. Players never see a reopen control |
| Archived session | No write | Unchanged: restore it first |
| Repeated tap | — | The second tap changes nothing and writes no second log line |

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **A reason is required for both actions.** It is shown on the pages and in the log. Recommended, as cancelling a set and reversing a buy-in already ask for one.
2. **Reopened results leave the boards until finalized and closed again,** instead of staying up marked "under correction" as the first design had it. Recommended: it needs no new stats code and shows no figure known to be wrong.
3. **A missed buy-in.** Today a buy-in is accepted only while a set is open or in play, so a rebuy that was never recorded cannot be added to a reopened set if a later set exists. Recommended: a host may record a buy-in while a *reopened* set is counting up (not in an ordinary count-up). Say "leave it" to keep today's rule and correct such a case with a balance override and a note.
4. **Resume play stays available** on a reopened set under today's rule (no later set of the session has started). Say if a reopened set should never resume play.
5. **A switch, `REOPENING`, on by default.** Off hides both controls and makes both services refuse. It lets you turn the feature off in Vercel without a rollback, since you test on the live build. The migration stays either way.

## Implementation

Branch `feat/reopen` from `main` (nothing unreleased to stack on). Tests first for each service.

1. **Models and migrations.**
   - `ledger.Finalization`: add `voided_at`, `voided_by`, `void_reason` (all empty by default), the same idiom as `FinalCount` and `BalanceAdjustment`. `is_current` already exists.
   - `settlement.SettlementPlan`: `night` becomes a plain link (`related_name="plans"`); add `is_current` (default true), `voided_at`, `voided_by`, `void_reason`; add the rule "one current plan per session". Existing plans stay current.
   - No row is updated by the migrations beyond column defaults.
2. **`games.services`.** `mark_reopened(session)`: state `reconciliation`, `finalized_at` empty, version bumped; called only by the reopen service, as `mark_finalized` is by finalization. `ended_at` and the play periods are not touched.
3. **`ledger.services`.** `void_results(session, actor, reason)`: marks the current `Finalization` and its `PlayerResult` rows not current and fills the void fields. With decision 3: `record_buy_in` also accepts a host's buy-in in `reconciliation` when the set has an earlier finalization.
4. **`settlement.services`.**
   - `reopen_set(session_id, actor, reason)`: host only; locks the set (and its session row, as `lock_session` does); counting up already → return; not finalized → refuse; session closed → "Reopen the session first."; empty reason → refuse; `void_results`; audit `session.reopened` with the reason and the retired revision's nets; `mark_reopened`.
   - `reopen_night(night_id, actor, reason)`: host only; locks the session; open already → return; empty reason → refuse; any active payment on the current plan → refuse with the count; marks the plan not current with the void fields; status `open`, `closed_at` empty; audit `night.reopened`; bumps the version of every set.
   - `close_night`, `_transfer`, and through one helper in `settlement.queries` the six readers named in the study, use the current plan only.
5. **Views and routes.** `POST s/<id>/reopen/` and `POST n/<id>/reopen/`, resolved through the requester's membership like their neighbours; the role is checked in the service.
6. **Screens** (built with the design and motion skills, inside DESIGN.md's tokens; no new colour, font or asset):
   - set: a "Reopen set" row and sheet in Host controls on the final page; the reason line on the reopened count-up page; the "Corrected" line on the final page;
   - session: "Reopen session" beside Archive in the host's manage area, with its sheet and the paid-marks refusal; 
   - set log: every revision of the results, and every transfer list of the session, the retired ones marked "replaced" with the reason;
   - the finalize confirmation and any text that says a set cannot be reopened are reworded.
7. **Tests.**
   - Service: reopen then finalize gives revision 2, one current result per player, revision 1 kept with its reason; reopen refused for a player, a closed session, a set that is not finalized, an empty reason, an archived session; a repeated tap writes one audit event; the version is bumped.
   - Session: reopen refused with a paid mark and allowed after unmarking; the old plan is kept and not current; closing again writes a new plan whose transfers clear every balance; a next set can start after reopening.
   - Readers: after close → reopen → correct → close, the home page, the session list's settle state, member removal and the archive confirmation show only the new list. Stats leave out a reopened session and return the corrected figures after the second close.
   - Decision 3: a host's buy-in is accepted in a reopened count-up and refused in an ordinary one; rake applies as at any buy-in.
   - Migration test on a database with a closed session, as `ledger/tests/test_migrations.py` does.
   - Views: 404 for a non-member, refusal for a player, the controls absent when `REOPENING` is off.
   - Browser check at 390 and 1280px: both sheets, the refusal, the reason lines.
   - Both suites: SQLite and PostgreSQL.
8. **Documents.** Wiki (features, architecture: the two new transitions and the plan's new shape), PRODUCT.md and DESIGN.md where they state the old limit, TODO.md with the phone checklist. SPEC.md is not edited.

## Out of scope

- Counting earlier payments toward a new transfer list (the first design's "prior payments").
- Editing the end time of a set, or playing time.
- Reopening a canceled set.
- A second automatic showing of the closing recap.

## Acceptance

1. A finalized set with a wrong count: reopen with a reason, reverse the cash-out, count again, cash out, finalize. The final page shows the corrected results and the reason; the log shows both revisions.
2. A closed session: reopen with a reason, start another set, finalize it, close. The transfer list is new and nets all sets.
3. A closed session with a paid mark cannot be reopened until the mark is removed.
4. After a correction, the home page, the session list and the stats show only the corrected figures.
5. A player cannot reopen anything; a non-member gets 404.
6. Both test suites pass.

## Release

Not pushed without an instruction. One migration per app runs in the Vercel build after the tests. Rollback is the previous commit; the new columns and the wider link are harmless to the older code only if no session has been closed twice, so the first response to trouble is `REOPENING=False`, not a rollback.

## Progress

2026-10-11: Study and plan written. The human chose "both" purposes and "refuse until unmarked" for paid marks, then approved with "approved" and asked for the design and motion skills on the screens. Built on `feat/reopen` from `main`; kept local.

Changes from the plan:

- **Reopen set is its own block on the final page,** "Found a mistake?", not a row in Host controls: the final page has no host controls.
- **The reason is stored on the retired rows** (`voided_at`, `voided_by`, `void_reason` on `Finalization` and `SettlementPlan`), the idiom `FinalCount` already uses, and in the audit event. No new model.
- **Earlier transfer lists are on the session page,** beside Payment records, not in the set log. The set log shows the set's replaced results.
- **A player who had left can get a missed buy-in** in a reopened set. The plan did not say; without it a player who left early could not be corrected.
- **A missed buy-in does not turn the player's final cash-out into a partial one,** as a rebuy during play does. The cash-out was counted after the missed buy-in was played.
- **The session's Reopen form is an ordinary page load.** The set's is sent in place.
- **The earlier count-up (`COUNT_REVAMP=False`) has no "Add a missed buy-in".**
- **One existing test changed:** the finalize sheet's sentence in `web/tests/test_count_flow.py`.

Verification:

- 992 tests pass on SQLite (15 skipped) and 992 on PostgreSQL 17, 28 of them new (`settlement/tests/test_reopen.py`, `test_reopen_migration.py`).
- `reopen.mjs`: 24 of 24 on a fresh temporary database, at 390 and 1280px, with reduced motion and as a player. Captures of the final page, both sheets, the reopened count-up, the missed buy-in, the manage area and the reopened session were looked at once; the two failures of the first run were in the script (it read CSS-drawn quotation marks and an oklch colour wrongly).
- Skills: the design skill (context and craft floor) and the motion skill (vanilla best practices). The one moment reuses `mark-draw` and the `shift` preset.

Acceptance: 1 to 6 are met in tests and headless Chrome.

Not verified: an iPhone and Safari; a screen reader; the other browser scripts (`count_flow.mjs`, `end_set.mjs`, `night.mjs`) were not rerun; the migration against a copy of live data. A fresh reviewer did not read the branch; the author's own read of the diff is the only review.

Documentation synced: wiki (features, architecture, deployment), PRODUCT.md, DESIGN.md, browser README, TODO.

2026-10-11 release: the human said "go push it to livs". `feat/reopen` was merged to `main` as `be3bcf2` and pushed (previous production commit `800e29e`). 992 tests passed on SQLite and on PostgreSQL 17 on the merged `main` before the push. About two and a half minutes later the live site served the new stylesheet (it contains `reopen-arrived`), the login page answered 200 and the new reopen route answered a signed-out POST with 403, not 404. The two migrations run in the build before the new version goes live, so they are taken as applied; no signed-in page was opened on the live site to confirm it.

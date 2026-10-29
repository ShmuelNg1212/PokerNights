# Plan: table rake in settle-up, and live screens with several hosts

Study: [1793299490_table_rake_and_multi_host_live.md](../study/1793299490_table_rake_and_multi_host_live.md).

Status: waiting for approval. Two parts on one branch, `feat/table-rake-and-multi-host-live`, from `main`. Part 1 is one commit. Part 2 is several commits, one per task.

## OPEN QUESTIONS

Answers from the human on 2026-10-30 are folded in. Approving accepts the **bold** answer where one remains.

1. **Who receives the rake in settle-up?** Answer: the rake is a separate entity, and each group chooses how it is settled. Example: A and B buy in ₱1,000 each at 5% (₱100 rake). A cashes out ₱1,400 (+₱400), B ₱500 (−₱500).
   - "Returned to each player" (today's rule): B pays A ₱450.
   - "Paid into the rake fund" (new): B pays A ₱400 and pays the **Rake fund** ₱100. Each player's figure equals the standings. The Rake fund is the group's existing rake account, shown as its own line in settle-up. It is not a member. A host marks its transfers paid when the money goes into the fund.
   - **Default: today's rule for every group, so nothing changes until a host switches the option in Group settings.**
2. **Old sessions.** **Closed sessions keep their transfers.** The option applies at the next close, also after a reopen.
3. **Carried debts.** **A transfer to the Rake fund is never carried into a later session.** It stays open until a host marks it paid.
4. **Which screens lagged?** Answer: the count-up page. Task 2 measures it first; the other steps are measured too.
5. **Move people to the next step?** Answer: ok. Keep the notice, and move other hosts (not players) to the new set by themselves.
6. **How fast?** Answer: ok, about 2 seconds on a set that is in play or counting up, 4 seconds otherwise. Task 3 measures the server cost of one poll and records the monthly estimate against the Vercel Hobby limits (deployment.md, "Limits to know"). Polling still stops on a hidden tab, and slows to 4 seconds after one quiet minute.

## Part 1: rake in settle-up

### Task 1: settle-up follows the standings — `tests: first`

- [ ] ADR `0007-rake-settled-per-group.md` and GLOSSARY entry "Rake fund" (domain-modeling).
- [ ] Group setting `rake_settlement`: `returned` (default) or `fund`. Migration with the default. Host-only edit in Group settings (service, audit, `request_id`).
- [ ] `Transfer` gains `to_rake_fund` (boolean). `payee` becomes nullable. Check constraint: exactly one of `payee` and `to_rake_fund` is set. Existing rows are unchanged.
- [ ] `settlement_balances()`: under `fund`, each player's balance is `net`, and the Rake fund is one more party with the session's total rake. Under `returned`, unchanged. The plan records which option it used.
- [ ] Settle-up shows "Rake fund" as a payee line with the rake mark. Marking it paid works as for any transfer. Carry excludes it.
- [ ] Tests first: the example above; several sets; a chips game; zero rake (no fund line); `returned` unchanged; a closed session keeps its plan; reopen and close uses the current option; carried debts skip fund transfers; mark paid and Undo on a fund transfer.
- [ ] Replace the footgun `rake_results_and_settlement.md`. Update spec.md lines 46 and 67.

**Done when:** on the live site, with the option on "Paid into the rake fund", a closed session's settle-up shows each player's amount equal to their standing, and the Rake fund line equals the session's rake total.

## Part 2: live screens with several hosts

### Task 2: two-host browser check — `tests: alongside`

- [ ] New probe `multi_host.mjs` with `seed_multi_host.py`: two hosts and one player in three browsers on one set.
- [ ] It records, for each step, the time until the other two screens show the change: a buy-in, a count saved, a count saved while the other host has a field focused, the review page, finalize, start next set, close the session.
- [ ] Record the result in this plan before Task 3. Gaps that do not reproduce are dropped.

**Done when:** the probe runs and lists which steps fail and their delay.

### Task 3: close the gaps found — `tests: alongside`

Expected from the study; confirmed or dropped by Task 2.

- [ ] Count fields: keep only values this host typed since the last redraw. A count saved by another host replaces an untouched field and shows "Saved by Hana" for one redraw.
- [ ] Focus: apply an update while a field has focus. Keep the focused field and its typed value; replace the rest. Hold only while a sheet is open with typing in it.
- [ ] Review, chip count and add-players pages: poll the set's version. On a change, show "Another host changed this set" with Reload. On finalize or next set, go to the set page.
- [ ] Next step (question 5): other hosts go to the new set by themselves; players keep the notice.
- [ ] Poll every 2 seconds while the set is in play or counting up (question 6). Slow to 4 seconds after one quiet minute.
- [ ] Measure one unchanged poll (time and queries) locally. Record the monthly estimate against the Hobby limits in deployment.md.
- [ ] Query count tests stay within their limits.

**Done when:** the Task 2 probe passes for every step, with each change on the other screens within 3 seconds.

### Task 4: design pass — `tests: alongside`

- [ ] The "Saved by" mark and the "changed" banner follow DESIGN.md tokens and motion presets; reduced motion shows them without movement.
- [ ] `/impeccable critique` on the count-up page with two hosts.

**Done when:** screenshots at 320, 390 and 1280 px show the marks without layout shift.

## Rendezvous

- Both test suites (SQLite, PostgreSQL), `code-review`, `security-review` (money logic changes).
- On the local server: two hosts and one player count up, finalize and close one session. Settle-up equals the standings.

## Release

Kept local until you say "ship". One migration (group setting and session field), with defaults, so it fails safe.

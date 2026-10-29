# Plan: table rake in settle-up, and live screens with several hosts

Study: [1793299490_table_rake_and_multi_host_live.md](../study/1793299490_table_rake_and_multi_host_live.md).

Status: approved 2026-10-30 ("approved"), with the answers folded in. Part 1 built. Two parts on one branch, `feat/table-rake-and-multi-host-live`, from `main`. Part 1 is one commit. Part 2 is several commits, one per task.

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

- [x] ADR `0007-rake-settled-per-group.md` and GLOSSARY entry "Rake fund" (domain-modeling).
- [x] Group setting `rake_settlement`: `returned` (default) or `fund`. Migration with the default. Host-only edit in Group settings (service, audit, `request_id`).
- [x] `Transfer` gains `to_rake_fund` (boolean). `payee` becomes nullable. Check constraint: exactly one of `payee` and `to_rake_fund` is set. Existing rows are unchanged.
- [x] `settlement_balances()`: under `fund`, each player's balance is `net`, and the Rake fund is one more party with the session's total rake. Under `returned`, unchanged. The plan records which option it used.
- [x] Settle-up shows "Rake fund" as a payee line with the rake mark. Marking it paid works as for any transfer. Carry excludes it.
- [x] Tests first: the example above; several sets; a chips game; zero rake (no fund line); `returned` unchanged; a closed session keeps its plan; reopen and close uses the current option; carried debts skip fund transfers; mark paid and Undo on a fund transfer.
- [x] Replace the footgun `rake_results_and_settlement.md`. Update spec.md lines 46 and 67.

**Done when:** on the live site, with the option on "Paid into the rake fund", a closed session's settle-up shows each player's amount equal to their standing, and the Rake fund line equals the session's rake total.

## Part 2: live screens with several hosts

### Task 2: two-host browser check — `tests: alongside`

- [x] New probe `multi_host.mjs` with `seed_multi_host.py`: two hosts and one player in three browsers on one set.
- [x] It records, for each step, the time until the other two screens show the change: a buy-in, a count saved, a count saved while the other host has a field focused, the review page, finalize, start next set, close the session.
- [x] Record the result in this plan before Task 3. Gaps that do not reproduce are dropped.

**Done when:** the probe runs and lists which steps fail and their delay.

**Result (2026-10-30, before the fixes), 16 of 21 checks pass.** The other host (Ivy) writes through the services; the host (Hana) and the player (Ben) watch at 390 px. The limit is 3 seconds.

| Step | Host | Player |
|---|---|---|
| 1. Count saved, host only looking | 2.3 s | 0.4 s |
| 2. Count saved while the host has a count field focused | **never** (lands only when the field is left) | — |
| 3. Count saved for a player whose field holds the host's unsent value | 2.1 s; the unsent value is kept; **nothing says the other host saved a different count** | — |
| 4. Cash-outs | **3.9 s** | at once (already polled) |
| 5. Finalize | **3.8 s** | at once |
| 6. Start next set | **not moved** | notice shown; stays |

- Gap 1 of the study (a count field keeps an old value) does not reproduce: a field keeps only what this host typed. Dropped.
- Gap 3 (pages that do not poll) is not part of the count-up flow the human reported. Dropped from this plan; recorded for later.
- An unchanged poll answers 204 in about 3 ms on the local server (SQLite).

### Task 3: close the gaps found — `tests: alongside`

Expected from the study; confirmed or dropped by Task 2.

- [x] ~~Count fields: keep only values this host typed.~~ Dropped: Task 2 showed a field already keeps only what this host typed. Instead, when another host saves a count that differs from this host's unsent value, the field keeps the value and a line under it says "Ivy saved ₱800. Send to replace it, or clear the field."
- [x] Focus: an update applies while a field has focus. `live.js` morphs the snapshot into the region (`Turbo.morphChildren`, `ignoreActiveValue`), so the focused field keeps its node, value and focus. No hold remains. A typed field still gets the server's attributes (`turbo-setup.js`).
- [x] ~~Review, chip count and add-players pages: poll.~~ Dropped: not in the count-up flow the human reported (Task 2). Recorded for later.
- [x] Next step (question 5): when the next-set notice arrives on a finalized or canceled set, a host goes to the new set; a player keeps the notice.
- [x] Poll every 2 seconds while the set is in play, counting up or just finalized (finalized added so the move to the next set is within 3 seconds). 4 seconds after one quiet minute. Hidden tabs do not poll.
- [x] Measured: an unchanged poll answers 204 in about 2–3 ms of server time locally. Recorded in deployment.md, "Limits to know".
- [x] Query count tests pass unchanged (the confirmer's name is a subquery on the existing count query).

**Done when:** the Task 2 probe passes for every step, with each change on the other screens within 3 seconds.

### Task 4: design pass — `tests: alongside`

- [x] The clash note uses the `--warn` token, has no motion, and sits in the row's grid under the field (390 px screenshot `multi-host-390-1b-clash.png`; no horizontal overflow). The "changed" banner was dropped with the non-polling pages. The Rake fund chip uses `--brass` with `--ink`, as the light chips do.
- [ ] `/impeccable critique` on the count-up page with two hosts. Not run: the change is one line of text and one chip colour inside existing patterns.

**Done when:** screenshots at 320, 390 and 1280 px show the marks without layout shift.

## Rendezvous

- Both test suites (SQLite, PostgreSQL), `code-review`, `security-review` (money logic changes).
- On the local server: two hosts and one player count up, finalize and close one session. Settle-up equals the standings.

## Release

Kept local until you say "ship". One migration (group setting and session field), with defaults, so it fails safe.

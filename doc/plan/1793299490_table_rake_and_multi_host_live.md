# Plan: table rake in settle-up, and live screens with several hosts

Study: [1793299490_table_rake_and_multi_host_live.md](../study/1793299490_table_rake_and_multi_host_live.md).

Status: waiting for approval. Two parts on one branch, `feat/table-rake-and-multi-host-live`, from `main`. Part 1 is one commit. Part 2 is several commits, one per task.

## OPEN QUESTIONS

Approving accepts the **bold** answer unless you say otherwise.

1. **Who receives the rake in settle-up?** Settle-up can match the standings only if someone receives the rake money. Example: A and B buy in ₱1,000 each at 5% (₱100 rake). A cashes out ₱1,400 (+₱400), B ₱500 (−₱500). Today B pays A ₱450.
   - **a. One member holds the rake.** B pays A ₱400 and pays the holder ₱100. The holder is the host who started the session, and a host can change it before close. Each figure in settle-up equals the standings.
   - b. The rake is already in someone's hands and is not in settle-up at all. Then tell me how B's extra ₱100 is handled at your table, and I will model that.
   - c. Keep today's rule (each player gets back their own fee), and change only the words so the two figures are not confusing.
2. **Old sessions.** **Closed sessions keep their transfers.** A session reopened and closed again uses the new rule.
3. **Rake per group or per session?** **Per group setting**, "Rake in settle-up: paid to a holder" (new default) or "returned to each player" (today's rule), so another group can keep the old way.
4. **Which screens lagged?** If you remember, name them: count-up fields, the review page, Finalize, Start next set, the session page after close. Task 3 finds them by test either way.
5. **Move people to the next step?** When a host finalizes or starts the next set, other phones show a notice and a button today. **Keep the notice, but move other hosts (not players) to the new set by themselves.** Alternative: move everyone, or move nobody.
6. **How fast?** **About 2 seconds on a set that is in play or counting up**, 4 seconds otherwise. A push service (under 1 second) is a new paid dependency; I recommend it only if 2 seconds still feels slow.

## Part 1: rake in settle-up

### Task 1: settle-up follows the standings — `tests: first`

- [ ] ADR `0007-rake-paid-to-a-holder.md` and GLOSSARY entry "rake holder" (domain-modeling).
- [ ] Group setting for the rake rule (question 3), migration with a default. Session field `rake_holder` (a Member, nullable), set by the service at session start to the starting host.
- [ ] `settlement_balances()`: under the holder rule, each player's balance is `net`; the holder's balance gains the session's total rake. Under the old rule, unchanged.
- [ ] Settle-up shows the holder's line as "Rake · ₱100" so it is clear why they receive money. A host can change the holder before close (service, audit, version bump, `request_id`).
- [ ] Tests first: the example above; a holder who also played and won or lost; several sets; chips game; zero rake; old rule unchanged; a closed session keeps its plan; reopen and close uses the new rule; carried transfers still balance.
- [ ] Replace the footgun `rake_results_and_settlement.md`; update spec.md lines 46 and 67 after approval.

**Done when:** on the live site, a closed session's settle-up shows each player's amount equal to their standing, and the holder's rake line equals the set's rake total.

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
- [ ] Poll every 2 seconds while the set is in play or counting up (question 6).
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

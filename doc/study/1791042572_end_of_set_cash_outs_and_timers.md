# Study: end-of-set cash-outs and playing time

- **Date:** 2026-10-03 23:49 (Asia/Manila), Unix timestamp `1791042572`
- **Request:** Stop playing time at the moment play ends. Let the host confirm final counts, then cash out all counted players in one reviewed action, and repeat for the rest.
- **Workflow:** `agentic-workflow`, Phase 1 of a new cycle. `skill-router` was read; `agentic-workflow` is the one skill that fits this work. No code changes before approval of the plan.

Labels: **FACT** = verified today in the code. **REC** = recommendation. **ASSUMED** = needs confirmation.

## 1. Intended outcome

1. Ending play records one server timestamp. Each player's playing time stops there. Counting and administration add no playing time.
2. After play ends, the host confirms a final count per player. "Not counted" and "counted, zero" are different.
3. A button "Cash out counted players (N)" opens a review of those players and the total. One confirmation records a cash-out for each of them, or for none.
4. Uncounted players stay pending. The host repeats the action later.
5. The game stays unresolved until each player is cashed out and the balance check passes. Finalization and payment marks stay separate steps.

## 2. What the words mean in the app today (FACT)

| Word in the request | In the app |
|---|---|
| Set | A **game** (`GameSession`): one dated cash game at one table. The app has no larger "session" that contains several sets |
| End of set | The host action "End play and count up": state `running` → `reconciliation`. It stores **no timestamp** on the game. Only the audit log has the time |
| Resume | `reconciliation` → `running`. Allowed today with no conditions |
| Cash-out | A `CashOut` row: an **amount in the game's unit**, recorded at once. A player can have several. A host can reverse one with a reason while the game is running or counting up |
| Final stack / count | **Does not exist** as a separate record. Typing a cash-out is the only step |
| Chip conversion | **Does not exist.** It was removed on 2026-10-03 by the owner's decision. A pesos game stores peso amounts. A chips game has no peso value |
| Playing timer | **Does not exist.** No interval, start or stop is stored per player. `Participant.left_at` is the only per-player time |
| Break | **Does not exist.** "Left" is the nearest state: the seat is free and a host can bring the player back |
| Hourly results | **Do not exist.** Statistics are roadmap Stage 3 |
| Payment | A paid mark on a transfer, possible only after finalization |

Repository: branch `main`, clean. No `doc/canonical/`. All earlier plans have status `done`.

### Gates today

| Gate | Rule today |
|---|---|
| Cash-out | Allowed in `running` and `reconciliation`. The player needs an accepted buy-in. The amount is an integer ≥ 0. **No discrepancy blocks a cash-out** |
| Finalization | Each player with a buy-in needs at least one cash-out record. Total cashed out plus overrides must equal total bought in |
| Payment marks | Only after finalization |

So "a discrepancy that currently blocks cash-out" does not exist. Discrepancies block **finalization**. That stays.

One weak point exists today: a partial cash-out during play counts as "has a cash-out". A player who cashed out part of a stack and played on is not asked for a final figure. The totals then show a difference, but the screen does not name that player.

## 3. Conflicts between the request and the current app

| Request | Current fact | Consequence |
|---|---|---|
| "confirmed stack values, calculated peso cash-outs", "the set's recorded chip conversion" | No chip conversion exists, by an earlier decision | **Open decision Q1.** REC: the final count is typed in the game's unit, and the cash-out equals it. The review shows one figure per player |
| "Players already on a break" | No break feature | REC: not added here. "Left" already stops a player's time |
| "Follow existing rules for correcting end times" | No such rule | REC: no end-time editing in this change. Flagged as Q5 |
| "Follow existing rules for … resuming play" | Resume exists, with no rule about counts or cash-outs | **Open decision Q3** |
| "result-revision rules" | Revisions are designed (Stage 2) but not built. A finalized game cannot be reopened | Corrections here happen before finalization only, by reversal and re-count |
| "distort hourly results" | No hourly figure exists | REC: store each player's playing time with the frozen result, for Stage 3 |

## 4. Options

### Playing time

| Option | Pros | Cons |
|---|---|---|
| **A. Intervals per player** (`PlayInterval`: start, end). Opened and closed by the server at lifecycle events | Exact. Handles late joins, early leavers, returns and resumed play. One open interval per player is a database rule | A new table and hooks in five services |
| B. Derive from existing timestamps | No new table | `left_at` is overwritten on return, and the end of play is not stored. It cannot be correct |
| C. A timer in the browser | — | The request forbids it |

**REC: A.**

### Count and cash-out

| Option | Pros | Cons |
|---|---|---|
| **A. A `FinalCount` record, then a batch that creates `CashOut` rows** | The three states are real data. A count has a version, so a stale review can be detected. Cash-outs stay the only money record | Two new tables and one new column |
| B. One step with a "draft" flag on `CashOut` | Fewer tables | A draft would sit in the money table. Each total would need to exclude drafts |

**REC: A.**

### Where the review lives

**REC:** its own page, like "Add players". The live game page refreshes each 4 seconds and would redraw a review in place.

## 5. Recommended design

### 5.1 Time

- `GameSession.ended_at`: set by the server when the host ends play. Cleared when play resumes; the earlier end stays in the audit log and in the closed intervals.
- `PlayInterval(session, participant, started_at, ended_at)`. At most one open interval per participant (database constraint). `ended_at ≥ started_at`.

| Event | Effect on intervals |
|---|---|
| Host starts the game | Open one for each player at the table, all with the same timestamp |
| A player joins or is added while the game runs | Open one |
| A player is marked left, or cashes out with "Leaving the game" | Close theirs at that moment |
| A player returns while the game runs | Open a new one |
| Host ends play | Close each open interval of that game at **one** timestamp, equal to `ended_at` |
| Host resumes play | Open one for each player at the table who has no final cash-out |
| The same action sent twice | No effect. Closing closes only open intervals. Opening is refused by the one-open rule |

- Playing time = sum of closed intervals + (now − start) of an open one. The server calculates it. The page shows "Played 2 h 15 min" and "Play ended 11:00 PM".
- While a game runs, a small script advances the displayed minutes from the server's figure. A reload or a second tab gets the same figure from the server.
- At finalization, each `PlayerResult` stores `play_seconds`. Nothing uses it yet.

Four different times stay distinct: play ended (`GameSession.ended_at`), count confirmed (`FinalCount.created_at`), cash-out recorded (`CashOut.created_at`), payment confirmed (`Payment.created_at`).

### 5.2 Final counts

- `FinalCount(session, participant, amount, version, is_current, confirmed_by, created_at, voided_at, voided_by, request_id)`. Append-only. A new count for the same player gets `version + 1` and replaces the current one. "Clear" voids it.
- Allowed while counting up (`reconciliation`), by a host, for a player with an accepted buy-in and no final cash-out. The amount must parse in the game's unit and be ≥ 0. An empty field is refused; it is never read as zero.
- The count is **what the player has in front of them at the end**. An earlier partial cash-out is not included; it stays its own record.

### 5.3 Player status while counting up

| Status | Rule |
|---|---|
| **Cashed out** | The player has an accepted **final** cash-out |
| **Ready to cash out** | The player has a current confirmed count and no final cash-out |
| **Awaiting count** | Neither |

`CashOut` gains `kind`: `partial` (during play, the player stays) or `final` (the player's last). A cash-out with "Leaving the game", an individual cash-out while counting up, and a batch cash-out are `final`. `CashOut` also gains optional links to its `FinalCount` and its batch.

Payment status is shown apart from this: "Payment: after the results are final", then the existing paid marks.

### 5.4 The batch

- Button **"Cash out counted players (N)"** in the balance card. With N = 0 it is disabled and says "No player has a confirmed count yet."
- Review page: each ready player with the confirmed count, the cash-out amount, the batch total, and "Still to count: …". The form carries the exact count ids shown.
- `ledger.services.cash_out_counted(session_id, actor, count_ids, request_id)`, one transaction under the game lock:
  1. Host only. State `reconciliation`.
  2. A known `request_id` returns the first result.
  3. Each submitted count must still be current, not voided, and its player must have no final cash-out.
  4. If any check fails, nothing is recorded. The message names the player and the reason, and the review reloads.
  5. Create one `CashOutBatch`, one `final` `CashOut` per player linked to its count, one audit event per player plus one for the batch, and one version increment.
- A player who becomes ready after the review opened is not part of that batch. They stay ready.
- Result line: "4 players cashed out; 2 awaiting final counts."
- The batch does not finalize the game, mark any payment, or change the balance check.

### 5.5 Reconciliation

- The finalization gate changes in one point (Q2): each player with a buy-in needs a **final** cash-out. A partial cash-out during play is no longer enough. The message names who is missing.
- The rest is unchanged: totals must match, or the host records an override with a note.
- The review page shows "Counted and cashed out so far: ₱X of ₱Y bought in" as information. It blocks nothing.

### 5.6 Corrections

| Case | How |
|---|---|
| A count is wrong, not yet cashed out | Confirm a new count (new version) or clear it |
| A batch cash-out is wrong | Reverse that cash-out with a reason, as today. The player returns to "Awaiting count"; the old count is voided |
| After finalization | Not possible yet (Stage 2) |

### 5.7 Individual cash-out

Kept. While the game runs it is on the player row as today. While counting up it moves under the player's "Details" as "Cash out without a count", so that the row shows one main input.

### 5.8 Existing games

- `ended_at` is filled from the audit log's last "ended play" entry.
- Intervals are not invented for games played before this change. Their playing time shows "not recorded".
- Existing cash-outs become `final` if the player left or the game is past play, else `partial`.

## 6. External inputs

None. No new dependency.

## 7. Risks

| Risk | Mitigation |
|---|---|
| A hook is missed and an interval stays open | The one-open constraint, a close-all at end of play, and tests for each event |
| The stricter gate surprises a host | The message names the player. Q2 asks first |
| Two hosts confirm batches at once | The game lock, the count check and a threaded test on PostgreSQL |
| The host ends play late | The time is the tap time. Editing it is not in this change (Q5) |

## 8. Open questions

1. **Q1.** No chip conversion: is the final count typed in the game's unit, with the cash-out equal to it?
2. **Q2.** May finalization require a final cash-out for each player, so that a partial cash-out during play no longer counts?
3. **Q3.** Resume after counting has started: what happens to confirmed counts and to players already cashed out?
4. **Q4.** Breaks: leave them out of this change?
5. **Q5.** End-time correction: leave it out of this change?
6. **Q6.** Older games: end time from the log, playing time "not recorded"?

---

## Review addendum, 2026-10-03 23:56 (Unix `1791042979`): sessions contain sets

The human corrected section 2: **"a game can have multiple sets per ongoing session."** The sections above are not rewritten. Where this addendum differs from them, this addendum controls.

### A1. What was wrong

Section 2 said that a set is a game and that the app has no larger session. That described the code correctly, but it is not the product. The product has two levels. The code has one.

### A2. Decisions by the human (2026-10-03)

| # | Question | Answer |
|---|---|---|
| S1 | Does each set have its own money? | **Yes.** Each set has its own buy-ins, final counts, cash-outs and balance check. A new set starts with fresh buy-ins |
| S2 | When is who-pays-whom calculated? | **Once per session.** Each set freezes its own results. The transfer list nets all sets of the session |
| S3 | How does the next set start? | **The host starts it, and players carry over.** The host can then add or remove players |
| S4 | Can two sets of one session run at once? | **No.** One after another |

### A3. Terms from here on

| Term | Meaning | In the code |
|---|---|---|
| **Session** | One ongoing gathering at one table on one date. It contains one or more sets and has one settle-up | New model, `GameNight` |
| **Set** | One round of play with its own buy-ins, counts, cash-outs, balance check and frozen results | The existing `GameSession` model |

REC: keep the class name `GameSession` for a set and add `GameNight` for the session. A full rename of `GameSession` and of each `session` field would touch every app and migration for no change in behavior. The mismatch between the code name and the screen word is recorded as a footgun page. Screens say "Session" and "Set 2".

### A4. What exists today against what is needed (FACT, then REC)

| Topic | Today | Needed |
|---|---|---|
| Grouping | None. Each `GameSession` stands alone | `GameNight` with table, date, location, game type and unit. `GameSession.night` and `set_number` |
| Sequence | Any number of games can run at once | At most one set of a session in `setup`, `open` or `running`. A database constraint plus a check under a lock on the session row |
| Next set | The host creates a new game by hand and adds each player again | "Start next set": copies the table, seats, latest settings and the players still at the table. No buy-in is copied. The new set opens for changes before play starts |
| Results | `PlayerResult` per game | Unchanged: per set |
| Settle-up | `finalize()` writes results **and** the transfer list for that game | Finalizing a set writes results only. A new action "Close session and settle up" nets each player's results over the session's sets and writes one transfer list |
| Transfers and payments | Point to a `Participant` (a player in one game) | Must point to a **member**, because a player has one participant row per set. They attach to the session |
| Unit | Per game | Per session. Each set of a session uses the session's unit, so results can be added |
| Timers | — | Intervals belong to a set. Ending a set closes only that set's intervals. A player's session time is the sum over its sets |

### A5. How the earlier design fits

Sections 5.1 to 5.7 (end time, intervals, final counts, statuses, the batch, the gates, corrections) apply **per set** without change. Three points change:

1. **Finalization of a set** no longer creates transfers. It freezes that set's results. The set page then offers "Start next set" and "Close session and settle up".
2. **Resume (Q3)** applies to the latest set only. A set cannot resume after the next set has started.
3. **Payment status** belongs to the session. A set shows "Payment: at the end of the session".

### A6. Session settle-up

- Allowed when each set of the session is finalized or canceled, and at least one is finalized.
- Each player's session result = the sum of their set results. The sum over all players is zero, because each set sums to zero.
- The existing algorithm produces the minimum transfer list from those sums. Order of ties: the order in which players first joined the session.
- The session becomes `closed`. Paid marks work as today, on the session's transfers.
- Before closing, the session page shows each player's running result over the finalized sets, marked "not final".
- A session with one set works as before, with one more tap: finalize the set, then close the session.

### A7. Existing data

- Each existing game becomes a session with one set, number 1.
- Each finalized game becomes a **closed** session. Its transfers and paid marks move to the session and point to members. Amounts do not change.
- Games that are open, running or counting up become open sessions.

### A8. Consequences to confirm

| Topic | Consequence |
|---|---|
| Scope | This is now two pieces of work: (I) sessions with sets and session settle-up, then (II) end-of-set timers, counts and the batch. (II) depends on (I) for "stop only the timers of the ended set" |
| Carry-over | Players with status "joined" at the end of the previous set carry over. Players who left do not. The host can add them again |
| Canceled sets | A canceled set has no results and counts for nothing in the session settle-up |
| Closed session | It cannot get another set. Reopening is not built |
| Statistics later | Stage 3 must decide whether a "session played" is a set or a session. Results are stored per set, so both remain possible |

# Study: table rake in settle-up, and live screens with several hosts

Date: 2026-10-30, Asia/Manila. Source: the human's notes after a live session on the production build.

## 1. Rake in settle-up

### What the human said

"The rake fee is already settled and is reflected in the count up standings so the settle up should just match that as our group handles the rake not by a per player basis."

### What the code does today

- Each buy-in is gross. The rule takes the fee from each buy-in (`ledger`). The fee goes to the group rake account (`GroupRakeAccount`), which is not a Member.
- The standings and the final results show `PlayerResult.net = cash-out − gross buy-ins`. The fee is part of each player's loss.
- Settle-up does not use `net`. It uses `settlement.services.settlement_balances()` (`settlement/services.py:166`): `net + rake_total`, per player. Each player gets back the fee from their own buy-ins. The model is "each player paid their own fee in cash at buy-in".
- The footgun [rake_results_and_settlement.md](../wiki/footguns/rake_results_and_settlement.md) and the spec (lines 46, 67) record this rule.

### Worked example

A and B each buy in ₱1,000 at 5%. ₱950 each goes into play; ₱100 is rake. A cashes out ₱1,400, B ₱500.

| | Standings (`net`) | Settle-up today (`net + own rake`) |
|---|---|---|
| A | +₱400 | +₱450 |
| B | −₱500 | −₱450 |
| Sum | −₱100 | ₱0 |

Today B pays A ₱450. The standings say +₱400 and −₱500. The human sees two different figures for the same night.

### The constraint

Transfers are zero-sum. Player nets sum to −(total rake). For settle-up to show each player's standing exactly, someone must receive the total rake (₱100 above). Today nobody does, because the model assumes each player already paid their own fee.

There is no rule that makes settle-up equal the standings and also keeps every transfer between players only. So the human must say who holds the rake money. See the plan's OPEN QUESTIONS.

### Effect on existing records

- Finalized results do not change: `net` and `rake_total` are stored per result.
- Settlement plans are snapshots made at close. A closed session keeps its plan. A session closed again after a reopen uses the new rule.
- The rule changes money logic. It needs an ADR, a spec change and a replacement of the footgun.

## 2. Live screens with several hosts

### What the human said

Several hosts managed one game. Screens did not update seamlessly when hosts entered counts or moved the set and the session to the next steps. The human wants every player's screen to update live.

### What exists

- The set page polls `GET /s/<id>/state/?v=<version>` every 4 seconds (`static/js/live.js`). Each write bumps `GameSession.version`. A change returns the whole live region, which replaces `#live`.
- The session page, the home page and the Sessions tab poll a derived stamp every 5 seconds, slowing to 20 after two quiet minutes (`static/js/nightlive.js`).
- A host's own write redraws their own page at once (Turbo morph). Other phones wait for their next poll.

### Gaps found by reading the code

These are hypotheses. The plan's first task tests each one with two host browsers side by side.

1. **A count field keeps its old value after another host saves a count.** `live.js` `typedValues()` keeps every nonblank count input, also when the value equals the rendered default (architecture.md, "Live updates"). This protects typed drafts, but it also keeps a value this host never touched. Host B's saved count then shows only as a placeholder behind host A's stale value.
2. **An update waits while a field has focus.** `userIsTyping()` holds every snapshot while focus is in an input in `#live`. During count-up a host moves from field to field with the numpad, so focus can stay in the region for minutes. Host B's counts, a finalize or a next set do not arrive during that time.
3. **Some host pages do not poll.** Only `session.html`, `night.html`, `home.html` and `group.html` poll. The batch count review, the chip count page and the add-players page do not. A host on the review page does not see that another host changed a count or finalized the set. The server refuses a stale review (good), but the screen does not say so before the tap.
4. **Nobody is moved to the next step.** When host B finalizes or starts the next set, host A's page shows a notice ("Set 2 has started", Go to set 2). This was an earlier decision: nobody is moved by itself. With several hosts this may be the friction the human felt.
5. **Four to five seconds is visible.** Two hosts at one table see each other tap. A 4-second lag reads as "did not update".

### Options for transport

| Option | Delay | Cost | Note |
|---|---|---|---|
| A. Keep polling; close gaps 1–4; 2 s on an active set | ≤ 2 s | More requests; each unchanged poll is a 204 with one small query | No new dependency. Works on Vercel's serverless functions |
| B. Server-Sent Events from Django | < 1 s | Vercel functions have a time limit; each open phone holds a function | Weak fit for the host |
| C. A hosted push service (Pusher, Ably, Supabase Realtime) | < 1 s | New dependency, account and keys; a monthly limit | Needs a recorded requirement (AGENTS.md project facts) |

Recommendation: A. The gaps, not the transport, cause most of the felt lag. Option C stays open if 2 s is not enough after the fix.

## Sources

- `settlement/services.py:151-171`, `ledger/models.py` (`PlayerResult`), `doc/wiki/spec.md:46-67`, `doc/wiki/features.md` (Rake).
- `static/js/live.js`, `web/views.py:234-396`, `doc/wiki/architecture.md` (Live updates; Live updates of the session page), `doc/plan/1791706983_session_page_live.md`, `doc/plan/1792073300_next_set_for_players.md`.

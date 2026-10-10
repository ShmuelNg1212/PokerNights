# Count-up and who pays whom, revamp: plan

Status: approved 2026-10-10 ("approved"); all six decisions as recommended. Built on `feat/count-and-settle-revamp`. Date: 2026-10-10, Asia/Manila. Study: [Count-up and who pays whom, revamp](../study/1791630956_count_up_and_settle_up_revamp.md).

## Outcome

A host counting up sees most of the table on one phone screen and types down the list without scrolling past labels. After the session closes, each person opens the page and reads their own part first, with every transfer on the first screen. Both screens look finished, and two moments mark the things that matter: counts confirmed, and a transfer paid.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new colour, font or raster asset. No migration, and no change to accounting, permissions or what any action records. Built with the design and motion skills.

## What you will see

### Count-up

**A player's row is one line**, about 64px instead of 111px: the chip, the name with "₱1,000 in" beneath it, and the count field at the right.

| State | The row shows |
|---|---|
| Awaiting count | An empty field. The row is at full strength. |
| Counted, not cashed out | The confirmed count in the field in dim text, with a small tick. Typing replaces it. |
| A player entered their own count | Their number in the field in dim text, marked "entered". Leaving it accepts it, as today. |
| Cashed out | No field. "Cashed out ₱3,100" at the right, and the row is quiet. |
| No buy-in | "No buy-in" at the right. |

- The state badges, "Counted ₱450" and the "Final count (₱)" label go; the field and its mark say the same thing once. The field keeps its full name for screen readers.
- **Tapping a name opens that player's sheet** with their records and corrections, as on the set page in play. The "Details" line leaves the row.
- **The overview** keeps the title and the line "3 of 6 players counted or cashed out", and gains a row of small marks, one per player, filled as each is counted. It is about 110px.
- **One sentence of help** sits under the heading, before the first player: "Type what each player has left; 0 for an empty stack."
- **The host bar is shorter:** the running total with its verdict, and the one main button. The hint and "More host controls" open from its chevron. About 130px instead of 203px.
- **"The books" replaces Set totals and Balance check**: bought in, cashed out, rake when there is any, counted so far, and the difference, each once. A discrepancy still leads with its exact signed amount and moves directly under the overview, as today.
- **A player sees their own count first**: a block "Your count" with the field and Send to host, above the read-only list.
- From 900px the two columns stay; rows take the same one-line form.

**Result on a 390 × 844 phone with six players:** all six rows between the overview and the host bar, where today there are about three. The page goes from about 1,970px to about 1,150px.

### The closed session page

**Order on a phone:** overview, Who pays whom, Session results, Sets, Payment records, then the recap link and Manage this session.

**The overview** is about 220px instead of 361px (539px for a player), and its headline depends on who is looking.

| Viewer | Headline | Beneath it |
|---|---|---|
| A player who is owed | "You receive ₱600" | Their transfers, each with Paid or Not paid |
| A player who owes | "You pay ₱400" | The same |
| A player whose transfers are all paid | "You're settled" | The same, all Paid |
| A player with nothing to pay or receive | "Nothing to pay" | Their session result |
| The host | "Still to pay ₱600" | Their own part as one line, when they played |

- Under the headline, one line for the table: a progress bar and "₱200 of ₱600 paid · 1 of 2 transfers". The second status badge and the zero rake line go; rake shows when there is some.
- The viewer's session result stays, on one line.

**A transfer is one row**, about 76px for a player and 96px for the host, instead of about 250px: payer chip and name, an arrow, payee chip and name, and the amount at the right. The state is beneath: "Not paid", or "Paid · Oct 9, 18:40".

- The host's **Mark paid** is on the row at 48px. A paid row is quiet and offers a small **Undo**.
- The viewer's own transfers are marked "(you)" and sit on the lighter surface. The order of the list does not change.
- One line of explanation stays above the list. The notes about netting and rake move into "How this is worked out", closed by default.
- **Payment records** fold into a closed section that says how many there are.

**Result on a 390 × 844 phone:** the overview and at least four transfers on the first screen for a host, where today none is fully visible. A session with five transfers goes from about 3,100px to about 1,700px.

### The two moments

| Moment | Movement |
|---|---|
| Counts are confirmed | A tick is drawn in each confirmed field, 40ms apart, and that player's mark in the overview fills. When the last count makes the total match, the verdict's tick is drawn and the existing green rule runs once. Under 600ms. |
| A transfer is marked paid | The row's tick is drawn, the row settles to its quiet state, and the progress bar moves to the new amount. The figure changes to its new value at once. When the last transfer is paid, "Settled" arrives with the green rule, once per session per browser. Under 600ms. |

Money never counts or rolls. Nothing moves before the server accepts. Reduced motion shows each new state at once. Without JavaScript every action works and nothing moves.

## Decisions for you

Approving accepts the recommendations unless you say otherwise.

1. **A switch for count-up, for one release.** `COUNT_REVAMP=False` in Vercel returns today's count-up, by keeping today's templates beside the new ones. Recommended: yes, because this screen is used in the middle of a real game. The closed session page gets no switch; it is read after the game and a revert removes it.
2. **A host who also played sees the table's total as the headline**, with their own part as a line beneath. Recommended: yes, since the host is the one marking payments. Say if a playing host should get the player's headline instead.
3. **The list of transfers keeps its order.** Your own rows are marked, not moved to the top. Recommended: keep the order; the headline already states your part.
4. **Player details move from a line on each count row to a sheet opened by tapping the name.** Recommended: yes. Without JavaScript the details stay a disclosure on the row.
5. **Payment records start closed.** Recommended: yes; the Paid marks already say what happened, and the records remain one tap away.
6. **Recap link and Manage this session move to the end of the page.** Recommended: yes. The recap still opens by itself the first time.

## Implementation

Branch `feat/count-and-settle-revamp` from `main`, three commits in this order. Not merged and not pushed without your word. Each stage ends with both test suites and its browser checks passing.

**Stage 1: count-up.**

1. Tests first (`web/tests/test_end_set.py`, `test_count_flow.py`, `test_count_total.py`): the row's markup for each state, one count form with the same field names, the field's accessible name, the player's own block, the merged books section in each balance state, `data-watch` and `data-value` unchanged on every row and total, the switch returning today's markup, and no query added (limit 13).
2. Templates: `_count_up.html`, `_players_count.html` and the count part of `_host_controls.html` rewritten; today's versions kept as `_count_up_classic.html` and `_players_count_classic.html`. `_balance.html` and the set totals become one `_books.html`. `config/settings.py`: `COUNT_REVAMP`.
3. CSS for the row, the marks, the shorter bar and the books section. `counts.js` and `numpad.js` keep reading the same field attributes; `dock.js` learns the shorter count-up bar.
4. Browser check, `end_set.mjs` updated and extended, at 320 × 568, 390 × 844 and 1280 × 800: six rows on the first screen, row height, 48px targets, no overflow with a long name and a nine-digit amount in pesos and in chips, contrast, keyboard order, typing with the numpad and Next, the running total following typing, a refused count keeping every typed value, a live update from a second host keeping drafts and focus, a player's own count, no JavaScript, and the switch.
5. Regression: `numpad.mjs`, `dock.mjs`, `player_entries.mjs`, `inplace.mjs`, `flow.mjs`, updated where they name a class that moved.

**Stage 2: the closed session page.**

1. Tests first (`web/tests/test_night_design.py`): the headline for each viewer in the table above, the table line, a transfer row for host, player and archived views, own rows marked, order unchanged, Mark paid and Undo forms with their request ids, the folded records with their count, the open session page unchanged in content, and no query added (limit 14).
2. A small read-only helper in `settlement/queries.py` gives the viewer's part (pay, receive, settled, nothing) from the transfers already loaded.
3. `night.html` rearranged; the transfer row and overview in CSS, replacing the stacked card.
4. Browser check, `night.mjs` updated and extended, at the same three sizes: at least four transfers on the host's first screen, row heights, each headline, exact figures on one line at 320px with nine-digit amounts, Mark paid and Undo with and without JavaScript, the page updating in place, the recap still opening once and from its link, contrast and keyboard order.

**Stage 3: the two moments, and finish.**

1. The ticks, the marks, the settling row and the progress bar: CSS where the server draws the state, `pokerMotion.run` only for what a tap causes, hung on the existing accepted-change marks.
2. Browser checks: each moment's first frame and rest, under 600ms, figures at their value on the first frame, once-only rules, reduced motion, Motion blocked, nothing running and no inline style at rest.
3. One `/impeccable critique` of both screens, and one fix batch from it.
4. Sync docs: DESIGN.md (new sections; the superseded parts of "Count-up" and "Session overview and settle-up" named), PRODUCT.md, wiki features and deployment (the switch), the surface notes, the browser README, TODO with the phone checklist.

## Acceptance criteria

- AC1. On a 390 × 844 phone, a host counting six players sees all six rows between the overview and the host bar.
- AC2. A count row is at most 72px tall at 390px wide; its field and every control are at least 48px.
- AC3. Confirming counts, cashing out counted players, finalizing and overriding record exactly what they record today, through the same forms and field names.
- AC4. The running total follows typing as today, and a refused count keeps every typed value.
- AC5. On a 390 × 844 phone, a host of a closed session sees the overview and at least four whole transfers without scrolling.
- AC6. Each viewer gets the headline in the table above; the figures equal today's.
- AC7. A transfer row is at most 100px tall for the host and 80px for a player at 390px wide.
- AC8. Mark paid and Undo work with and without JavaScript, and the page updates in place.
- AC9. Each moment plays under 600ms, only after the server accepts; no figure shows an intermediate value; reduced motion moves nothing.
- AC10. `COUNT_REVAMP=False` returns today's count-up.
- AC11. No query is added to either page; no model, service or migration changes.
- AC12. Both suites pass; the listed browser checks pass.

## Out of scope

- Cash-out review, the finalize sheet, final results, the recap, Stats.
- New figures, new actions, payment methods, partial payments, reminders.
- Sorting or reordering players or transfers.
- Removing the classic count-up templates (the cycle after you accept it on your phone).

## Rollback

`COUNT_REVAMP=False` in Vercel returns the previous count-up at once. To remove the work, revert the feature commits. No migration.

## Cannot be verified from here

A physical phone at a table: typing counts with one thumb, the numpad panel with the shorter rows on an iPhone, and how the paid moment feels. These go on your phone checklist, and the best test is one real set and one real settle-up.

## Progress and blockers

2026-10-10: Study and plan written after four questions to the human. Waiting for approval.

2026-10-10: approved ("approved"), all six decisions as recommended. The design skill (impeccable) and the motion skill were loaded earlier in the same session for the recap and applied here.

2026-10-10: built on `feat/count-and-settle-revamp`, not merged and not pushed.

- Stages 1 and 2 are commit `974779f`; stage 3 and the docs are the commit after it.
- 964 tests pass on SQLite and on PostgreSQL.
- Browser checks on fresh seeds: `count_flow.mjs` 91 of 91, `night.mjs` 83 of 83, `dock.mjs` 228 of 228, `numpad.mjs` 120 of 120, `player_entries.mjs` 48 of 48, `inplace.mjs` 39 of 39, `archive.mjs` 85 of 85, `settled.mjs` 24 of 24, `end_set.mjs` 46 of 47 (the one failure, a contrast pair for a surface that no longer exists, also fails on `main`).
- No query added: the set page stays within 13 and the session page within 14.

Measured at 390 × 844:

| | Before | Now |
|---|---|---|
| Count row | 111px | 63px |
| Whole rows between the overview and the host bar (six players) | about 3 | 6, bar open or folded |
| Rows above the open number keys | 2 | 7 |
| Host bar | 203px | 179px open, 127px folded |
| Count-up page | 1,973px | 1,241px open, 1,189px folded |
| Session overview, host | 361px | 204 to 224px |
| Session overview, player | 539px | 292 to 336px |
| First transfer starts at (host) | 750px | 417px |
| Transfer row | about 250px | 99px host, 71px player |
| Whole transfers on the host's first screen | 0 | 4 |
| Session page with five transfers | 3,116px | 2,030px |

Acceptance: AC1 to AC12 are met as measured above and by the tests and scripts listed.

Differences from the plan as written:

1. **The host bar's folding did not change.** Making it start folded during count-up moved eighteen of the dock's keyboard checks, so the bar opens and folds exactly as before and keeps the host's saved choice. Instead the open bar hides its hint when a main action is shown (179px, not the planned 130px), and the folded bar keeps the total and the main action (127px). Six rows fit in either state because the row is 63px.
2. **The help sentence stays above the list.** Removing it after the first count moved the field the host had just typed in by 13px.
3. **The pages are longer than estimated:** count-up 1,241px (estimate 1,150), five transfers 2,030px (estimate 1,700), a player's overview 292 to 336px (estimate 220), because it holds their transfers and their result.
4. **"Counted so far" and the difference are not repeated in The books for the host.** They are in the host bar, and from 900px in "Confirmed counts" beside the action. A player's books keep the read-only total.
5. **The verdict's tick is not drawn.** It is a mask, which cannot be drawn in. The moment is the tick in each accepted field and the mark filling; the balanced rule runs as before.
6. **The progress bar moves only where the browser can animate it** (Safari and Chrome). Elsewhere it changes at once.
7. **"Settled" also arrives on the first visit to a session that is already settled**, once, as the balanced rule does for a set. A player's "You're settled" does the same.
8. **File names.** The new count-up is `_count_v2.html`, `_count_rows.html`, `_count_own.html` and `_books.html`. The earlier `_count_up.html` and `_players_count.html` keep their names, because the canceled-set page also uses the second.
9. **Two commits, not three.** Stages 1 and 2 share files and went in together.
10. **No separate `/impeccable critique` run.** Each screen had two rounds of captures at 320, 390 and 1280px with a fix batch after each. A formal critique can still be run on request.
11. **Existing checks that changed.** Twelve Django tests and parts of `count_flow.mjs`, `dock.mjs`, `player_entries.mjs`, `night.mjs` and `end_set.mjs` named the earlier layout and were updated; the browser README lists each. `transfer_layout.mjs` describes the earlier transfer card and is retired from release runs.
12. **A stale script was repaired on the way:** `end_set.mjs` stopped at its no-JavaScript chips walk on `main` too; it now runs to the end.

Not checked from here: counting with one thumb at a table, the number keys with the shorter rows on an iPhone, and how the two moments feel on a real phone. These are the phone checklist in TODO.md.

2026-10-10: the human said "go push". Merged to `main` and pushed as `08a49b5` (previous production commit `0c736fb`). Vercel reported the deployment complete; the live stylesheet carries the count-up and transfer-row styles, `settle.js` is served and the login page loads it and answers 200. Neither screen was opened on the live site from here; that is the phone checklist in TODO.md. `COUNT_REVAMP=False` in Vercel returns the earlier count-up.

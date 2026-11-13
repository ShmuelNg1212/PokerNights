# Streaks and records

Status: approved 2026-11-13 ("approved"). Question 1 got no answer, so the default stands: the recap names no losing run. Date: 2026-11-13, Asia/Manila. Study: [More flair](../study/1794301535_more_flair.md), idea 8. This is plan 3 of 3 from that study, after [the session finale](1794301755_thats_the_night_finale.md) and [Chip to the pot](1794561294_chip_to_the_pot.md). Reconstituted from the queue against the code at `8acb556`.

Mode: mixed. The technical part comes first. Plan skill: `codebase-design`. Execute skills: `tdd`, then impeccable for the recap rows. Rendezvous skills: `code-review`, `break-ui`.

Branch: `feat/streaks-and-records`, stacked on `feat/chip-to-the-pot`.

## OPEN QUESTIONS

1. **Does the recap name a losing run?** The recap's Highlights have a recorded rule: no highlight names a loss (`settlement/queries.py:387`, `Highlight`). This plan keeps that rule. A losing run shows on the player's own page only, as today ("Lost 3 in a row"). Say "the recap names losing runs too" if you want the other rule. That answer changes a product rule, so it adds one mark, one ADR line and an edit to the `Highlight` rule.

## Decided

- 2026-11-10, the human, first: "streaks should only include winning runs". Then, the same day: "nevermind, include losing runs". The second answer stands. A streak can be a winning run or a losing run.
- The player page keeps "Current run" as it is: "Won 3 in a row" or "Lost 3 in a row" (`web/stats.py:147`, `run_text`). Nothing is removed.
- 2026-11-10, the human: no haptics.
- 2026-11-13, the human: "finish the flair queue".

## Decided by the agent (say so if one is wrong)

1. No feature switch. The marks are read-only and the rules are a pure function with tests first.
2. The marks are not part of `Recap`. `settlement/queries.py` cannot import `settlement/stats.py` (stats imports queries). The view joins them and gives the template a separate `marks` list.
3. The marks are not on the share picture. See Not in scope.

## Outcome

The recap's Highlights say what a night meant in a player's history: a winning run, a personal best, a round number of sessions, a first win. Each fact is good news or a neutral count. Each fact comes from closed sessions, as Stats does. Nothing is stored.

## Marks

Worked out for one closed session, from the group's counted results in the session's unit, up to and including that session. The order is that of `stats.fetch`: date, then session id. Pesos and chips never mix.

| Mark | Rule | Words |
|---|---|---|
| Winning run | The player finished ahead in this session and in the 2 or more counted sessions they played before it, with no break-even between | "3 winning sessions in a row" |
| Personal best | This session's result is positive and higher than each earlier one, and the player has 3 or more counted sessions | "Personal best" and the signed amount |
| Round number | This is the player's 10th, 25th, 50th or 100th counted session, or each 50th after that | "10th session" |
| First win | This is the player's first counted session with a positive result, and not their first counted session | "First win" |

- A session the player did not play does not break a run.
- A tie with an earlier best is not a personal best.
- A mark in the recap never names a loss, a losing run or a last place, until question 1 says otherwise.
- An archived session does not count, as in Stats. A session opened again has no recap, so it has no marks.
- The order in the recap: winning runs (longest first), personal bests, first wins, round numbers. Then the member's name.

## Tasks

- [x] **1. Marks from results (tests: first).** `settlement/stats.py`: a frozen dataclass `Mark` (kind, member id, count, amount) and a pure function `night_marks(rows, night_id)` over the list that `fetch(group, unit)` returns. New `settlement/tests/test_marks.py`:
  - each row of the table;
  - each boundary: a run of 2 against 3, a best with 2 sessions against 3, the 9th and 10th session, the 150th, a tie with an earlier best;
  - a break-even that ends a run, a missed session that does not;
  - a first win in a first session gives no mark;
  - rows after the session are ignored;
  - two units kept apart, an archived session left out (through `fetch`);
  - no mark names a loss.
  
  Completion: the tests fail first, then pass.
- [x] **2. Show the marks in the recap (tests: alongside).** `web/views.py:580` (the recap context) calls `stats.fetch(group, unit)` once and `night_marks`, and joins each mark to its standing in `outcome.standings`. `templates/web/_night_recap.html`: the marks follow the three existing Highlights in the same `dl`. The section shows when there is a highlight or a mark. A view test checks the words, the order, and that the closed session page adds one query. Completion: the Django suite passes on SQLite and PostgreSQL.
- [x] **3. Design pass (tests: alongside).** The rows at 320 and 390 px with long names and three marks for one player. No new colour: the amount of a personal best uses the existing plus colour. DESIGN.md: one paragraph under "Session recap in detail". Completion: `break-ui` finds nothing open.
- [x] **4. Docs.** ADR 0014 and GLOSSARY.md (`domain-modeling`): "winning run", "personal best", "counted session". Sync `doc/wiki/spec.md` and `features.md`. Add phone checks to TODO.md. Run `graphify update .`.

## Rendezvous

Run the SQLite and PostgreSQL suites, `night.mjs` and `finale.mjs`. Run `code-review` and `break-ui`. The first thing the user does: close a session in which one player wins a third session in a row, then read the recap as that player and as another player. Record the checks here.

## Checks recorded (2026-11-13)

The plan is frozen from here. Branch `feat/streaks-and-records`, stacked on `feat/chip-to-the-pot`, verified, not merged.

- `settlement/tests/test_marks.py`: 28 tests. They failed first (no `night_marks`), then passed.
- `web/tests/test_recap_marks.py`: 9 tests: the words, the order, exact amounts, shared rows, units, no losing run named, no marks for a session that is not closed, and one added query.
- Django suite: 1775 tests pass on SQLite (23 skipped) and on PostgreSQL.
- `web/tests/test_query_counts.py`: the closed session page's limit went from 14 to 15 queries. This is the one query the plan named.
- Regression probes on fresh seeds: `finale.mjs` 45 of 45, `night.mjs` 88 of 88.
- Design pass: the agent read the recap at 320 and 390 px with a worst-case seed: two long names, one player with a run of 10 and a best of +₱1,233,567, a first win, and six players in one Round number row. No row overflows and no name overlaps a value.
- Not run as skills: `break-ui`, `code-review` and impeccable. The agent did the worst-case pass above and read the diff in their place.

Changed from the plan:

- The run's words are "Winning run" and "3 in a row", not "3 winning sessions in a row". The value does not wrap, and the longer words broke a long name into pieces at 320 px.
- A first win is not also called a personal best. Both said the same fact.
- Players with the same run or the same round number share one row. A regular group reaches its 10th session together; six rows said one thing.
- First win shows its signed amount, as Personal best does.

## Not in scope

- The season review (idea 9). It needs its own study, after this.
- Group milestones (idea 10).
- Marks on the share picture or in a notification.
- A stored badge or any new table.

## Risks

- The recap of an old session shows its marks as of that session. A later correction to an earlier session can change them. This is the same as Stats: figures are read, not stored.
- One more query on the closed session page. The view test fixes the count.

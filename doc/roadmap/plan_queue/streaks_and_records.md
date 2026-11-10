# Streaks and records (queued)

Status: queued 2026-11-10. Study: [More flair](../../study/1794301535_more_flair.md), idea 8. The human sent it to a plan on 2026-11-10. It is plan 3 of 3, after [the session finale](../../plan/1794301755_thats_the_night_finale.md) and [Chip to the pot](chip_to_the_pot.md). Reconstitute against the current code before approval.

Mode: mixed. The technical part comes first. Plan skill: `codebase-design`. Execute skills: `tdd`, then impeccable for the recap rows. Rendezvous skills: `code-review`, `break-ui`.

## OPEN QUESTIONS

1. **The player page says "Lost 3 in a row" today** (`web/stats.py` `run_text`, `templates/web/player.html:34`). Your rule is that a streak is a winning run only. Recommended: "Current run" shows a winning run or "No run", and a losing run is not said. This changes a released behaviour, so it needs your yes. "Worst night" stays; it is a record, not a streak.

## Decided

- 2026-11-10, the human: "streaks should only include winning runs". No text counts losses in a row.
- 2026-11-10, the human: no haptics.

## Goal

The recap's Highlights say what a night meant in a player's history: a winning run, a personal best, a round number of sessions, a first win. Each fact is good news or a neutral count. Each fact comes from closed sessions, as Stats does. Nothing is stored.

## Marks

Worked out for one closed session, from the group's counted results in the session's unit, up to and including that session (order: date, then session id). Pesos and chips never mix.

| Mark | Rule | Words |
|---|---|---|
| Winning run | The player finished ahead in this session and in the 2 or more counted sessions they played before it, with no break-even between | "3 winning sessions in a row" |
| Personal best | This session's result is positive and higher than each earlier one, and the player has 3 or more counted sessions | "Personal best" and the signed amount |
| Round number | This is the player's 10th, 25th, 50th or 100th counted session, or each 50th after that | "10th session" |
| First win | This is the player's first counted session with a positive result | "First win" |

- A session the player did not play does not break a run.
- A mark never names a loss, a losing run or a last place.
- An archived session does not count, as in Stats. A session opened again has no recap, so it has no marks.

## Draft tasks

- [ ] **Marks from results (tests: first).** `settlement/stats.py`: a pure function `night_marks(rows, night_id)` over the list that `fetch(group, unit)` returns. It gives one item for each mark: kind, member id, count or amount. New `settlement/tests/test_marks.py`: each row of the table, each boundary (run of 2 against 3, best with 2 sessions against 3, the 9th and 10th session, a tie with an earlier best), a break-even that ends a run, a missed session that does not, two units kept apart, an archived session left out, and "no mark names a loss". Completion: the tests fail first, then pass.
- [ ] **Winning runs only (tests: first), if question 1 is yes.** `PlayerRecord.current_run` gives a winning run or None. `run_text` loses "Lost". Update `web/tests/test_stats_pages.py` and the sentence on runs in `doc/wiki/features.md:547`. Completion: no template or test has "Lost N in a row".
- [ ] **Show the marks in the recap (tests: alongside).** `web/views.py` (the recap context, line 580) calls `night_marks` with one `stats.fetch` and joins the marks to the recap's players. `settlement/queries.py` does not import `stats` (stats imports queries). `templates/web/_night_recap.html`: the marks follow the three existing Highlights, in the same rows. A view test checks the words and that the recap adds one query. Completion: the Django suite passes on SQLite and PostgreSQL.
- [ ] **Design pass (tests: alongside).** The rows at 320 and 390 px with long names and four marks for one player. No new colour: the amount of a personal best uses the existing plus colour. Completion: `break-ui` finds nothing open.
- [ ] **Docs.** Record the rules in `doc/adr/` and GLOSSARY.md (`domain-modeling`): "winning run", "personal best", "counted session". Sync `doc/wiki/spec.md` and `features.md`. Add phone checks to TODO.md.

## Not in scope

- The season review (idea 9). It needs its own study, after this.
- Group milestones (idea 10).
- Marks on the share picture or in a notification.
- A stored badge or any new table.

## Risks

- The recap of an old session shows its marks as of that session. A later correction to an earlier session can change them. This is the same as Stats: figures are read, not stored.
- One more query on the closed session page. Fail-safe: the view test fixes the count.

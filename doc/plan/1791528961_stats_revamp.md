# Stats revamp: plan

Status: approved 2026-10-09 ("approved"); all nine decisions as recommended. Date: 2026-10-09, Asia/Manila. Study: [Stats revamp](../study/1791528884_stats_revamp.md).

## Outcome

A player opens Stats and sees their own answer first, then a board they can sort by what they care about and trust, and one tap takes them to anyone's page: how their money has moved over time, their best and worst nights, and what the game costs them.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. New here: the app's first charts, drawn in SVG by the server with the existing tokens. No new colour, font or raster asset. No migration.

## Behaviour

### 1. Your summary (top of the Stats tab)

A lead panel for the viewer, for the unit and period chosen:

- Their profit or loss, large, signed, with the direction icon.
- "3rd of 9" (or "Not ranked yet: 1 of 3 sessions").
- Their last result and its date.
- A link **Your stats** to their page.

A viewer with no result in the period sees one line: "You have no closed session in {period}."

### 2. The board

**Periods:** pills **All time**, **This year**, **Last 3 months**, and a **Month** select listing the months that have a closed session. Pesos games and Chips games stay as they are, shown only when the group has both.

**Sort:** a row of pills, **Profit** first:

| Sort | Figure at the right of each row |
|---|---|
| Profit | Profit or loss |
| Average | Average result per session |
| Return | Profit as a percent of money bought in |
| Per hour | Profit per hour at the table (offered only when the period has recorded time) |
| Sessions | Sessions played |

**A row:** rank, a movement mark, the player's token and name, a line "12 sessions · won 58%", and the sorted figure at the right. When the sort is not Profit, the profit or loss sits small under the figure. The whole row is a link to that player's page.

**Movement:** "up 2", "down 1" or "New", with a drawn arrow, against the same board one period earlier (study, Options). No mark when the place is the same or there is no earlier period.

**Ranked and not ranked:** a player needs 3 sessions in All time and This year, 2 in Last 3 months, and 1 in a single month. Players under it are listed below under "Not ranked yet", without a number, with a line saying how many sessions rank a player.

A player who was removed from the group stays on the board with "Left the group" under the name.

The three explanations under the board are rewritten for the new figures and folded into one closed disclosure, **How these are worked out**.

### 3. A player's page

Address `g/<group>/players/<member>/`, with the same unit and period controls. Open to every member of the group.

- **Head:** token, name, "(you)" where it applies, "Left the group" where it applies, and "14 sessions since Aug 2026". A back link to the board keeps the unit, period and sort.
- **Lead figure:** profit or loss for the period, with the rank beside it.
- **Running profit** (3 sessions or more): a line of the running total after each session, with a zero line, the first and last dates under it, three amounts at the side (lowest, zero, highest), and the latest total written at the end of the line. Under it, on the same horizontal positions, **Each session**: a thin bar up or down for that night's result.
- **Touch or hover** on either chart shows that session: date, table, the night's result and the running total. Arrow keys move along the sessions when the chart has focus.
- **Tiles:** Average per session · Return on buy-ins · Per hour · Win rate · Rebuys per session · Total bought in · Rake paid · Time at the table.
- **Highlights:** Best night, Worst night (each links to its session), Current run ("Won 3 in a row", "Lost 2 in a row") and Longest winning run.
- **Sessions:** the last ten, newest first: date, table, the result with its sign and icon, bought in, and time. "Show all 14" lists the rest. Each links to its session.

With one or two sessions the charts are left out, and a line says they appear after three.

### 4. How the figures are worked out

All from closed, unarchived sessions with a counted result, one unit at a time. Several sets in one session count once.

| Figure | Rule |
|---|---|
| Average | Profit or loss ÷ sessions, rounded toward zero to the centavo or chip |
| Return | Profit or loss ÷ total bought in, whole percent, toward zero. Bought in is gross, before rake |
| Per hour | Profit or loss of the sessions with recorded time ÷ their hours at the table. The page says "over 9 of 14 sessions" when some have none; "—" when none have |
| Win rate | Sessions that ended in profit ÷ sessions, whole percent. Break-even is played, not won (unchanged) |
| Rebuys per session | Buy-ins beyond the first in each set, added up, ÷ sessions, one decimal place |
| Rake paid | The rake taken from the player's buy-ins, added up. It is already inside the profit or loss |
| Run | Sessions in a row with a profit, or in a row with a loss, by date. A break-even session ends either |
| Rank | Place on the board for the chosen sort among ranked players. Ties share the order by name |

### 5. Look and movement

- **The board** keeps the Rack's rows and signed, icon-marked figures. The viewer's own row carries a quiet "(you)" and the Rail-2 surface, not a colour.
- **Charts** sit on a neutral panel. The line is Bone at 2px with a ring-marked end point; the bars use Up and Down with 4px rounded ends and a 2px gap; axes and the zero line are Rule and Line; every label is Bone or Bone Dim text. No gradient, glow or 3D.
- **Tiles** are a two-column grid of label over figure in tabular numerals, three columns from 900px beside the charts.
- **Movement, all once and all short:**
  - The line draws from left to right in 600ms, then the end label appears; the bars rise from the baseline, staggered, within 540ms.
  - Changing the sort moves each row to its new place with the `shift` spring instead of blinking.
  - A movement mark on the board springs in with `arrive`.
  - The crosshair follows the finger without easing.
  - Money never counts up: every figure appears at its final value.
  - Under reduced motion everything is in place at once.
- Built with the design, motion and dataviz skills, inside DESIGN.md's tokens and motion presets.

### 6. Switch

`STATS_PAGES=False` in Vercel returns the Stats tab to today's single list and makes player pages not found, without a release. Default on.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise. The reasons are in the study.

1. **Every member of a group can open every player's page.** The alternative is the player and hosts only.
2. **Minimum sessions to be ranked:** 3 for All time and This year, 2 for Last 3 months, 1 for a month.
3. **Periods:** All time, This year, Last 3 months, and a month chosen from a list. The row of month pills goes.
4. **Movement** compares with one period earlier, and All time compares with the board before the latest session.
5. **Rounding is toward zero** for averages, percentages and hourly figures.
6. **The chart's horizontal axis is the order of sessions, evenly spaced,** not the calendar.
7. **Per hour uses only sessions with recorded time** and says how many.
8. **A removed player stays on the board,** marked "Left the group", as today.
9. **The names and wording** of the figures in sections 2 to 4. Change any of them.

## Implementation

Tests are written first for each step.

1. **`settlement/stats.py` (new, pure).**
   - `fetch(group, unit) -> list[SessionResult]`: one query over `counted_results()` grouped per member and session: date, session id, table name, net, bought in, buy-in count, set count, rake, known seconds.
   - `Period` (all time, year, last three months, a month) with `contains(date)` and `previous()`.
   - `PlayerRecord`: a member's sessions in a period, with `net`, `sessions`, `wins`, `average`, `return_percent`, `per_hour`, `timed_sessions`, `rebuys_per_session`, `bought_in`, `rake`, `seconds`, `best`, `worst`, `current_run`, `longest_win_run`, `running` (the running totals). Integer arithmetic only.
   - `board(rows, period, sort, today) -> Board`: ranked and unranked records, the minimum for the period, and each ranked player's movement against `period.previous()`.
   - `group_stats` and `member_records` in `queries.py` stay for Your groups and the switched-off tab.
2. **`web/charts.py` (new, pure).** `running_chart(record, unit) -> Chart`: the view box, the line's path, the points, the bars, the zero line's position, and the three side labels, as plain numbers and strings for the template. No SVG is built by string concatenation in Python beyond the path's `d`.
3. **`web/views.py`.** `group_stats_context` builds the summary and the board from one `fetch`. New `player(request, group_id, member_id)` resolves through `member_for`, 404s for a member of another group, and renders the page. The player need not be an active member.
4. **`web/urls.py`.** `g/<int:group_id>/players/<int:member_id>/` named `player`.
5. **Templates.** `web/_group_stats.html` rewritten (today's markup kept as `_group_stats_legacy.html` for the switch); new `web/player.html`, `web/_stat_tiles.html`, `web/_running_chart.html`; new drawn icons in `table_tags.ICONS` for movement.
6. **`static/js/stats.js` (new).** The hover layer and keyboard steps on the charts, the Month select submitting on change, and row movement on a sort change. Registered with `page.js`; every page is complete without it.
7. **CSS.** A "Stats" section in `app.css`: the summary panel, sort pills, board rows, tiles, chart panel, tooltip. Chart reveal as CSS animations that Motion takes over when it runs, as the rest of the app does.
8. **Setting.** `STATS_PAGES = env.bool("STATS_PAGES", default=True)`.
9. **Colour check.** Run the dataviz validator on Up and Down against the Rail surface; record the result in DESIGN.md. If the pair fails separation for colour-blind readers, the Down bars take the dataviz texture fill as a second cue.
10. **Tests.**
    - `settlement/tests/test_stats_engine.py`: each figure in section 4 on hand-worked sessions, including a loss rounding toward zero, a zero bought-in guard, sessions with and without time, two sets in one session, rebuys across sets, runs broken by a break-even night, best and worst ties; each period's bounds on the first and last day of a month and a year in Asia/Manila, and `previous()`; the minimum per period and the unranked list; every sort and its tie order; movement up, down, New and none; pesos and chips never mixed; archived, unclosed and canceled sessions left out; agreement with `group_stats` on profit, sessions and wins; one query however many players and sessions.
    - `web/tests/test_charts.py`: point and bar positions for all-positive, all-negative and mixed runs, the zero line inside the box, a flat run of equal totals, three sessions and two hundred, and no `NaN` or negative size in the output.
    - `web/tests/test_stats_pages.py`: the summary for a ranked viewer, an unranked one and one with no result; each sort and period in the page; the Month select lists only months with sessions; rows link to player pages with the unit and period kept; the player page's tiles, highlights, list and "Show all"; no chart under three sessions; a removed player's page; another group's member is 404 and a non-member is 404; the page's query count does not grow with players or sessions; the switch off renders the old tab and 404s the page.
    - Existing `test_stats.py` page tests are updated for the new markup; the query tests stay.
    - Browser check `stats.mjs` with a seed of nine players and fourteen sessions over five months, in pesos and chips, with a removed player, a one-session player and sessions without time: the board and a player page at 320, 390 and 1280px; no horizontal overflow; 48px targets; contrast of every text style and of the line against the panel; the tooltip by touch and by keyboard; the sort moving rows; the Month select; reduced motion (nothing moves, everything visible); no JavaScript (charts and lists complete); no script error. Captures inspected.
11. **Verify.** SQLite and PostgreSQL suites. `stats.mjs`, then `home.mjs` and `navigate.mjs`, which share the group page and screen changes. A design critique of the board and the player page, with every P1 fixed.
12. **Sync docs.** Wiki features and architecture, deployment (the switch), DESIGN.md (a Charts section and a Stats addendum), PRODUCT.md addendum, roadmap Stage 3 and its stats decisions, TODO. SPEC.md is the human's.

Work is done on branch `feat/stats-revamp` from `main`, in this order: the engine, the board, the player page and charts, movement and polish. The tests pass after each. Nothing is merged or pushed without an instruction.

## Acceptance criteria

- AC1. The Stats tab opens with the viewer's own profit or loss, rank and last result for the chosen unit and period.
- AC2. The board sorts by profit, average, return, per hour and sessions, and each row opens that player's page.
- AC3. Players under the period's minimum are listed as not ranked and never hold a place.
- AC4. All time, This year, Last 3 months and any month with a session can be chosen, and the figures match the sessions in that period.
- AC5. A player's page shows the running profit chart, the per-session bars, the eight tiles, the four highlights and the session list, and every figure matches a hand calculation from the sessions.
- AC6. Profit, sessions and win rate equal what the current Stats tab shows for the same unit and period.
- AC7. Pesos and chips are never added together on any figure or chart.
- AC8. Every chart's figures are also in text on the page, a result is never shown by colour alone, and the pages are complete without JavaScript and under reduced motion.
- AC9. A member of another group cannot open a player's page.
- AC10. The Stats tab and a player page each take a fixed number of queries, whatever the number of players and sessions.
- AC11. `STATS_PAGES=False` restores today's Stats tab without a release.
- AC12. No migration. Existing tests pass on SQLite and PostgreSQL after the listed markup updates.

## Out of scope

- Seasons and any host setting for stats.
- Group records, head-to-head, and anything about hands.
- A player's record across groups.
- Changes to Your groups.
- Export or sharing of a board or chart.

## Rollback

Set `STATS_PAGES=False` in Vercel for an immediate return to the old tab. To remove the code, revert the feature commits; there is no migration and nothing is stored.

## Progress and blockers

2026-10-09: Study and plan complete. Waiting for the human's approval. No code written.

2026-10-09: The human approved with "approved"; all nine decisions as recommended. Built on `feat/stats-revamp` from `main`; kept local.

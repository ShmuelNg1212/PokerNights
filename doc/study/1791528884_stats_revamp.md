# Stats revamp: study

Date: 2026-10-09, Asia/Manila.

## Request

The human asked to revamp which stats are shown and how, as one release, and chose five parts from a list of six: a page for each player, stats that explain the number, a board that can be sorted and trusted, better periods, and the viewer's own summary. The human added: "make sure to construct a beautiful and dynamic UI for these stat pages and displays."

This is roadmap Stage 3 ([roadmap](../roadmap/README.md)) and `SPEC.md` step 5, including its "Later: bankroll graph over time". Seasons stay out.

## What exists today

- The Stats tab of a group (`templates/web/_group_stats.html`, `web.views.group_stats_context`) is one ranked list per unit: profit or loss, sessions, sessions won, win rate. Periods are All time and one pill per month that has a closed session.
- `settlement.queries.group_stats` adds a player's sets per session, so a session counts once, and ranks by profit. `counted_results()` defines what counts: current results of finalized sets in closed, unarchived sessions.
- A removed player stays on the board. Pesos and chips are never added together.
- `PlayerResult` already freezes, per player per set: `buy_in_total`, `buy_in_count`, `cash_out`, `net`, `rake_total`, `play_seconds` (empty for sets from before time was recorded), `game_date` and `unit`. Nothing shown today uses the buy-in, rake or time figures.
- Your groups shows each viewer their record and last result per group (`member_records`, `web/home.py`).
- There is no page about one player, no chart anywhere in the app, and no chart library.
- Roadmap decisions already made: a "session played" is a closed session; win rate is profitable sessions over sessions played; profit is after rake; a ranking threshold of 3 sessions is the Stage 3 proposal.

## Constraints

1. **Totals are queries; only finalization writes snapshots** (AGENTS.md rule 7). Every new figure is computed when read, from frozen results. No new table and no migration.
2. **Integers only** (rule 1). Averages, return and per-hour rates are divisions. They are done in integer arithmetic with a stated rounding rule, never with `float`.
3. **Units never mix** (roadmap). Every figure and chart is for one unit.
4. **Views only read here.** The pages write nothing, so there is no audit event, lock or `request_id` to add.
5. **Access** (rule 5): a player page resolves the group through the viewer's active membership; a member id from another group is a 404.
6. **Query count must not grow with players or sessions.** A group's counted results are a few thousand rows at most (players × sessions). One query can fetch them all, and every figure, rank and period can be worked out in Python from that one list.
7. **Money figures appear at their accepted value** (rule 9; DESIGN.md: "Don't animate money through intermediate values"). No counting-up numbers.
8. **Never colour alone** for a win, a loss or a player (DESIGN.md). Up and Down are the only colours that mean a result; they come with a sign and an icon or a position.
9. **No front-end framework** (AGENTS.md stack). Charts are inline SVG drawn by the server. A small script may add a hover layer.
10. **Phones first:** one column, 48px targets, dark, a dim room. A chart must read at 390px wide.
11. **No preview deployments.** The revamp needs a switch back to today's Stats tab without a release.

## What the data can and cannot say

- **Can:** profit or loss, sessions, win rate, average per session, return on money bought in, rebuys, rake paid, best and worst nights, streaks, a running total over time, and rank in the group.
- **Per hour** only where time was recorded. Older sets have none, so the rate uses only sessions with a known time and says how many those are.
- **Cannot:** anything about hands, luck or skill. The app records no hands.
- **Small samples mislead.** One good night gives a 100% win rate and the top average. A minimum number of sessions for ranking is needed, and it must not empty a short period.

## Chart form (dataviz method)

The job picks the form, and colour comes last.

- **Running profit over sessions** is change over time for one series: a line, 2px, with a zero baseline. One series needs no legend; the title names it. The latest point carries a direct label with the signed total.
- **Each session's result** is polarity around zero: thin bars up from or down from a baseline, with 4px rounded ends and a 2px gap.
- These are two measures on different scales. They are **two charts stacked on one shared horizontal position**, never one chart with two y-axes.
- **Horizontal position is the session's order, evenly spaced,** not the calendar. Home games are irregular: a calendar axis would bunch a busy month into a smudge and leave long flat gaps. The first and last dates label the axis.
- **A headline figure is not a chart.** Profit, average, return and the rest are stat tiles. With fewer than three sessions the page shows the tiles and the list, and no chart.
- **Text wears text tokens.** Values and labels are Bone or Bone Dim; the mark beside them carries Up or Down.
- **A table view exists:** the list of sessions under the charts holds every plotted figure.
- **Hover layer:** a crosshair and a tooltip on the line and bars (date, table, that night's result, running total), reachable by touch and by keyboard. Without JavaScript the charts and the list are complete.
- **Colour check:** Up and Down against the Rail surface are run through the dataviz validator for colour-blind separation and contrast before they are used as bar fills. Position above or below the baseline carries the same meaning.

## Options

**Who sees a player's page**

- **A. Every member of the group (recommended).** The board already shows each player's total, and every session's results are open to members.
- **B. Only the player and hosts.** Would hide what the sessions already show.

**Minimum sessions to be ranked**

- **A. By period (recommended):** 3 for All time and This year, 2 for Last 3 months, none for a single month. Players under it are listed below as "Not ranked yet" with their figures.
- **B. 3 everywhere.** A month with four games would rank almost nobody.
- **C. None.** One lucky night tops the averages.

**Periods**

- **A. All time, This year, Last 3 months, and one month chosen from a list (recommended).** Three pills and one native select, instead of a pill per month that grows without end.
- **B. Keep a pill per month and add the two new ones.**

"Last 3 months" means the current calendar month and the two before it, by session date in Asia/Manila.

**What "movement" compares**

- **A. The same board one period earlier (recommended):** a month against the month before; Last 3 months against the three before; This year against last year; All time against all time before the latest session. A player not on the earlier board is "New".
- **B. No movement.** Simpler, and the board says less.

**Rounding**

- **A. Toward zero, to the unit's smallest step (recommended):** an average of −₱166.666 shows as −₱166.66. Return and win rate are whole percent, toward zero. Per hour is to the centavo or the chip.
- **B. Half up.** Can show a loss as larger than it is.

**Where the arithmetic lives**

- **A. One query, then plain Python over the rows, in a new `settlement/stats.py` (recommended).** Rank, periods and movement all come from the same list; the functions are pure and easy to test.
- **B. A SQL aggregate per figure and period.** Many queries, and streaks and running totals do not aggregate.

## What stays outside this release

- Seasons, and any host setting for stats.
- Group records (biggest win, longest session).
- Head-to-head and anything about hands.
- A player's record across several groups.
- Changing the figures on Your groups.
- Export or sharing of a board or chart.

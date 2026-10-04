# Your groups page revamp

Date: 2026-10-04, Asia/Manila. Status: complete. Repository baseline: main `5a45792` plus the ignore-file commit, clean working tree, pushed to `origin/main`.

## Outcome

Revamp the first page a signed-in person sees, "Your groups" (`/`, `templates/web/home.html`). The human finds it bland. Answers to the discovery questions on 2026-10-04:

- **Target.** The Your groups page, not the group page.
- **Job.** A home for each group: one glance shows what is live now, the next action, my own record, and the last session's result. The full lists stay one tap away.
- **Boldness.** Bolder within the Rack: same palette, Archivo and chip tokens, with a real focal point. No new visual world, charts or emblems.

Sources: AGENTS.md, PRODUCT.md, DESIGN.md, the wiki, the group-and-home surface record and the [UI evolution plan](../plan/1791098885_ui_evolution.md).

## What the page is today

`web.views.home` runs one query for the viewer's active memberships. The template shows a heading, one row per group (name and role badge, 76 px link) and an always-open Create a group form. The capture from the UI evolution check (`/private/tmp/pn-uie/s2/home.png`) shows it with one group: a title, one line and a form. Two thirds of a phone screen are empty.

Diagnosis:

1. **Nothing is happening on it.** The page knows only names and roles. A set can be in play at the table and the home page does not say so. Reaching the table takes three taps: group, session, set.
2. **The least-used action is the largest thing.** Creating a group happens once; its form takes more space than the groups.
3. **Most people have one group.** PRODUCT.md describes private groups of friends. A list built for many rows shows one, so the page looks unfinished.
4. **No identity for a group.** The row has no players, no date, no figure. The Rack's own materials (chip tokens, compressed figures, the in-play felt) are absent.

## What the data already supports

Everything below is read from existing tables. No model, migration or write is needed.

| Fact for one group | Source | Cost |
|---|---|---|
| Open sessions and their latest visible set and state | `GameNight` + `sets`, the `visible_nights` rule (drafts are host-only) | 2 queries for all groups |
| A set in play: table, set number, players at the table, timer | `GameSession`, `Participant`, `games.clock` | timer costs 2 queries per running set |
| Money still in play | `ledger.queries.summary` | several queries per running set |
| Last closed session: table and date | `GameNight` (`status`, `game_date`, index exists) | in the same nights query |
| My result in that session | `PlayerResult` filtered to my member | 1 query for all groups |
| My record: profit or loss and sessions, per unit | `settlement.queries.stat_results` filtered to my members | 1 grouped query for all groups |
| What I still owe or am owed | `Transfer` without an active `Payment`, where I am payer or payee | 1–2 queries for all groups |
| Active players | `Member` | 1 query for all groups |

Rules that carry over unchanged: each fact resolves through the viewer's active membership; a player never sees a draft set; pesos and chips are never added; stats count closed sessions only and use the result after rake; unpaid figures come from the frozen transfer plan and active payments.

The home page has no live polling today. The set page polls every four seconds; the session page does not poll.

## Options

1. **Restyle the rows.** Bigger type, a chip stack, a count of players. Cheap, but the page still says nothing about tonight. It stays a directory.
2. **A card per group that reports its state (recommended).** Each group becomes a card with a status band, the viewer's own figures and one primary action that goes straight to where the viewer is needed. A set in play uses the indigo felt band, which DESIGN.md reserves for exactly that state, so the page has a focal point only when something is live. Create a group shrinks to a secondary disclosure once the viewer has a group.
3. **Skip the page for one group.** Redirect a one-group member to the group page. Fastest, but it removes the place to create or switch groups and gives two different landings. It also leaves the page bland for everyone else.
4. **A cross-group dashboard.** One merged feed of sessions, debts and standings across groups. More than the audience needs, and it mixes groups that the rest of the app keeps apart.

Recommendation: option 2. It answers the three chosen points (live now, next action, my record and last result) with facts the app already stores, and it stays inside the Rack.

## Risks and open questions

- **Query growth.** A card per group can turn into a query per group. The plan sets a fixed budget and builds the page from batched queries. Money still in play is the only expensive figure, and only for a running set.
- **Stale live figures.** Without polling, an in-play amount on the home page can be minutes old. The plan shows the server time of the figure, or leaves the amount out and shows state, players and timer only. This is a product choice for the human.
- **Privacy inside a group.** My record and what I owe are shown only to me. The card must not reveal another member's balance on this page.
- **One group versus several.** The card must look complete alone and still scan as a list of three or four.
- **Felt rule.** The felt band is allowed only for a set in play. Counting, open and closed states use neutral surfaces.
- **No external input, dependency or schema change is expected.** JavaScript should not be needed.

Baseline: 498 SQLite tests pass with ten PostgreSQL-only skips; all 498 passed on PostgreSQL in the previous cycle.

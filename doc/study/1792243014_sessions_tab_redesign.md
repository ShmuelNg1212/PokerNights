# Sessions tab redesign: study

Date: 2026-10-17. Mode: design. Shape brief for `/impeccable shape`.

## Request

The human wants a redesign of the Sessions tab of the group page (`templates/web/_group_sessions.html`). The request came right after a question about several sessions in one group at the same time. The redesign must therefore work well when two or more sessions are open.

The human said "the sessions tab in group settings". Group settings has no sessions section. The agent reads the request as the Sessions tab beside Stats and Group settings.

## Decisions from the human (2026-10-17)

| Question | Answer |
|---|---|
| What must a person do first on this tab during a game night? | Reach my table. Sets in play come first, and the session where I am seated is marked. |
| What does a past-session row lead with? | My result and my debt for that night. The table's settle status gets quieter. Rows are grouped by month. |
| How large is the change? | A bolder structure inside the Rack: current sessions become richer cards (player chips, clock), with more than one column on a wide screen. Same tokens and fonts. |

## What exists now

### Several open sessions already work

- `games.services.create_session` does not check for other open sessions. The model has no such constraint.
- The group view gives the template all open sessions (`web/views.py` `group`). The host's New session button stays visible while sessions are open.
- Home shows one open session per group and a "More open sessions" row (`web/home.py`, `templates/web/_group_card.html`).

### The current tab

Captured on a seeded copy at 390 px and 1280 px, as host `hana` and player `ben`. The group had four open sessions: a set in play at Garage (set 2), a set in play at Upstairs, an open set at Upstairs, and a host-only draft for next week. It also had five unsettled past sessions and one archived session.

Problems found:

1. **Wrong order.** Current sessions sort by `-game_date, -id`. Next week's draft is first. The two sets in play are last.
2. **Rows that look the same.** Two rows read "Upstairs · Sat, Oct 17". Nothing tells them apart: no location, no players, no clock, no seat count.
3. **No "you are here".** Ben sits at two tables. No row says so.
4. **Loud past list.** Every past row has a brass "Unsettled" pill. No row shows the viewer's result or what they owe. The list has no grouping and no end.
5. **Wasted desktop width.** The tab is one 728 px column. The surface brief still describes a 1.25:1 two-column group page, which the tabs replaced (2026-10-04 UI evolution).

### Data that already exists

- `settlement.queries.session_nets(night_ids, member_ids)`: the viewer's net per session, over finalized sets.
- `settlement.queries.unpaid_transfers(member_ids)`: transfers that the viewer still pays or receives, with the session.
- `settlement.queries.settle_states(night_ids)`: the table's settle status and still-to-pay amount.
- `games.clock.seconds_by_set(set_ids)` and the `clock_value` tag: a timer that ticks in the page; the server value is the truth.
- Seated players: `Participant` rows with status `joined` on the latest set.
- `member_token`: the player chip, as used on home.
- Live redraw: the tab polls `group_state`, which returns `hub_stamp`. The stamp covers set states, seat counts per set, members, transfer lists and payments. The page redraws itself by morph.

The stamp counts seats, but it does not record who is seated. If one player leaves and another joins between two polls, the chips do not redraw. This is acceptable: the next change redraws them. Record it as a footgun if the build shows chips.

## Shape brief

### 1. Job and audience

Mode: Operate. A host or player opens the group during a game night, in a dim room, with one hand, between hands. The first job is to reach their own table. The second job, after the night, is to see what they won or lost and what they still owe.

### 2. Outcome and proof

- Success: a seated player reaches their table in one tap from the top of the tab. A host reaches any table in one tap.
- Each current session can be told apart at a glance: table, location, players, set and clock.
- Each past row tells the viewer their own result and debt without opening the session.

### 3. Direction

Visual authority: the incumbent Rack (DESIGN.md). No new world, colour, font or raster asset. The structure changes; the materials do not.

Thesis: **the tab is a rail of live tables, then a ledger of your nights.**

- **Current sessions are table cards.** A set in play is a felt card: the only place where felt appears on this tab. Every other state is a rail card (`.panel` surface). Each card shows the table name, then the location or the date, the set and its state, up to six seated chips with "+N", "N at the table", and the ticking clock for a set in play.
- **Your table leads.** A card where the viewer is seated says "You're playing" in words, beside the chips. It carries the one bone action: "Open the table". Other cards are one link each, without a button.
- **Order of cards:** (1) sets in play where you are seated, (2) other sets in play, (3) open or ended sets where you are seated, (4) other open or ended sets, (5) drafts, for hosts only. In each band, the earliest date comes first, then the oldest session.
- **New session** for a host moves to after the cards. It still comes before the past list. With no current session, the empty state keeps its New session button.
- **Past sessions are a ledger grouped by month.** Each month has a small heading ("October 2026"). Each row: table name, then a muted line "Sat, Oct 10 · 2 sets". At the right: the viewer's signed result in the session's unit with the direction icon, or "Did not play" in Bone Dim.
- **Your debt sits in the row.** When the viewer still pays or receives money for that session, a second line names it: "You pay Carlo ₱500" in Down, or "Dina pays you ₱200" in Up. There can be more than one line.
- **The table's settle status gets quieter.** It becomes muted words at the end of the date line ("· Settled", "· ₱900 still to pay"), not a brass pill. The brass pill stays only on rows where the viewer has an unpaid transfer. The heading count "N not settled" stays.
- **Archived sessions** stay a closed disclosure at the end, for hosts.

### 4. Scope and boundaries

- Target: `templates/web/_group_sessions.html`, its view context in `web/views.py`, a new partial for a session card, and `static/css/app.css`.
- Keep: the routes, the tabs, the polling and morph, the host gates, drafts hidden from players, the empty states and their prerequisites, and what each link opens.
- Do not change: home, the session page, any money record or settlement rule.
- Anti-goals: no money still in play on a card (the pot is on the set page); no player's result other than the viewer's; no colour without a word; no new JavaScript except what the existing clock and morph already do.

### 5. States and ranges

- Current sessions: 0, 1 (typical), 2–3 (this request), up to 6. Players per table: 2–10. Table names up to the model limit; long names wrap to two lines.
- Card states: set in play; open; ended (count-up or review); finalized with the session still open; draft (host only).
- The viewer is seated at 0, 1 or 2 tables. A host who is not seated sees no "You're playing".
- Past sessions: 0 to 200 or more. Months with one row. A session the viewer sat out. A session in chips. A session with two debts for the viewer. A reopened session (open again, so it is a current card).
- No JavaScript: every card and row is a plain link; the clock shows its server value.

### 6. Interaction and layout

- Phone (one column): heading "Now playing" with the cards, New session, then "Past sessions" with the month groups.
- From 700 px of content width, the cards flow into two columns. A single card takes the full width. The past ledger stays one column with a 65ch measure, so the amounts stay near the names.
- The whole card is the link target. "Open the table" is a 48 px bone button inside "your" card. Every row and link is at least 48 px.
- Motion: none new. The morph redraw keeps the scroll position. Reduced motion changes nothing.

### 7. Constraints and open decisions

- Queries: the tab must stay a fixed number of queries as sessions grow. Add at most four batched queries: seated players, clock seconds, the viewer's nets, the viewer's unpaid transfers.
- Accessibility: 4.5:1 text contrast, written state on every coloured element, a visible brass focus.
- Open for the plan: whether the past ledger needs a limit (for example, this year open and earlier years in closed disclosures). The agent recommends year disclosures once a group has more than 12 months of sessions.

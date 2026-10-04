# Your groups page revamp: plan

Status: approved 2026-10-04. Date: 2026-10-04, Asia/Manila. Study: [Your groups page revamp](../study/1791102379_your_groups_home.md).

## Outcome

The Your groups page (`/`) becomes a home that reports each group's state. A person who opens the app sees, without a tap: whether a set is in play, the one action they are needed for, their own record, what they owe or are owed, and how the last session went. Mode: Operate. Visual authority: the built Rack in DESIGN.md; this is a bolder composition inside it, not a new world.

## Design brief

**Job and audience.** A host or player opens the app on a phone, often at the table in a dim room. Most belong to one group; a few belong to two or three.

**Thesis.** One card per group, and the card says what is true right now. The page is loud only when a set is in play.

**The group card, top to bottom.**

1. **Identity.** Group name at headline size, the viewer's role, and a short overlapping row of player chip tokens with the player count ("7 players").
2. **Status band.** Exactly one of these, chosen by the server:
   - **In play.** The indigo diamond felt band (the only use of felt on this page): table name, "Set 2 · in play", players at the table and the running timer. Primary action: **Open the table**, straight to the set.
   - **Needs the host.** Neutral band for a set that is open, counting up, or a session ready to close: the written state name ("Set 1 · Counting up"; no count progress on this page) and the action that fits (**Open set 1**, **Go to the session**).
   - **Open session, nothing for me.** Neutral band naming the session and its state, with **Go to the session**.
   - **Quiet.** "No session in progress" with the date of the last one. A host gets **New session** (or **Add a table** when the group has none); a player gets no button.
3. **My figures.** Up to three compact facts, shown only to the viewer about themself:
   - **My record**: signed profit or loss over closed sessions and the number of sessions, per unit. Green or red with the direction icon, as elsewhere.
   - **To settle**: "You owe ₱425 to Miguel" or "Jerome owes you ₱1,375", summed over unpaid transfers in closed sessions, linking to the session. Hidden when nothing is unpaid.
   - **Last session**: table, date and my signed result in it. Hidden when the group has no closed session.
4. **Footer links.** Sessions, Stats (when the group has stats) and Group settings, as ordinary 48 px links.

The whole card is not one link; it has one primary button and named secondary links, so every target is explicit.

**Rest of the page.**

- Heading stays "Your groups". The subtitle is dropped when there are groups.
- **Create a group** becomes a closed disclosure under the cards. It opens by itself when its form has an error.
- **No groups.** The empty state becomes the focal point: the mark, one sentence, the create form open, and a line about invite links.
- **Several groups.** A group with a set in play sorts first, then groups with an open session, then by name.
- **From 900 px**, cards sit in two columns; a single group keeps a comfortable fixed width instead of stretching.

**States and ranges.** 0, 1 and 4 groups; host and player; draft set (host only); open, in play, counting, finalized-not-closed, closed; pesos and chips, and both in one group; very long group and player names; amounts up to ₱199,999,999.98; a member with no results yet; a group with no table; more than eight players (tokens stop at six with "+N").

**Boundaries.** No model, migration, URL pattern, money rule or permission change. No new dependency. No JavaScript added. The group page, set page and session page are untouched. No balances of other members appear on this page.

## Decisions I need from you

1. **Money still in play on the home card.** The page does not refresh by itself, so the amount can be stale. I recommend leaving the amount off the card and showing state, players and timer; the table is one tap away. The alternative is to show it with its time ("₱9,850 in play · as of 16:03").
2. **"To settle" on the home page.** I recommend showing it: it is the fact people open the app for after a game. It is shown only to the person it concerns.
3. **One group.** I recommend keeping the page for a one-group member instead of redirecting to the group, because the card now carries the next action.

## Commit sequence

Each step is one Conventional Commit, with the full SQLite suite and `manage.py check` before it.

1. `feat(web): gather group home facts in batched queries`
   - A read-only `home_cards(user)` composition in `web` that returns one record per active membership: visible open sessions with latest set, the chosen status and action, player tokens and count, my record per unit, my unpaid transfers, and my last closed session.
   - Reuse `visible_nights` rules, `stat_results`, the transfer plan and active payments. Add small read helpers in `settlement.queries` where the query belongs to that app; `web` only composes.
   - Tests at the query boundary: drafts hidden from players; status choice for each set state; units kept apart; unpaid sums match the session page for payer and payee; paid and undone transfers; a removed member; another group's data never appears; query count fixed for one and for four groups.
2. `feat(ui): rebuild Your groups as group home cards`
   - New `home.html` and a `_group_card.html` partial; card, status band, figure and token-row styles from existing tokens and components. Felt band only for a set in play.
   - Create a group as a disclosure; the empty state as described; ordering and the two-column layout.
   - Page tests: each status renders its one action with the right address; a player sees no host action and no draft; my figures are absent for another viewer; the create form still keeps its typed value and error.
3. `docs(ui): record home revamp verification and sync documentation`
   - Browser check at 375, 768 and 1280 px over every state and range above on a synthetic database: overflow, 44 px targets, contrast of the new pairs, keyboard order, reduced motion, and that felt appears only for a set in play.
   - PostgreSQL suite. Compare models, migrations and URL patterns with the baseline.
   - Sync DESIGN.md, the group-and-home surface record, PRODUCT.md, the wiki, TODO and this plan's progress. Rendezvous into local main. No push without an instruction.

## Acceptance criteria

- AC1. With a set in play, the home page shows it on the group's card and one tap reaches the set.
- AC2. Each card shows exactly one primary action that fits the viewer's role and the group's state, or none for a player in a quiet group.
- AC3. My record, what I owe or am owed, and my last result match the Stats tab and the session page for the same data, per unit.
- AC4. A player never sees a draft set, a host action, or another member's balance on this page.
- AC5. Create a group still works, keeps a refused name with its error, and no longer dominates the page.
- AC6. The page looks complete with one group and scans with four; no horizontal overflow from 320 px; every target is at least 48 px; felt appears only for a set in play.
- AC7. The number of queries does not grow with players and stays within a fixed budget per page, recorded in the progress notes.
- AC8. No change to models, migrations, URL patterns, money rules or permissions. Existing tests pass on SQLite and PostgreSQL.

## Exclusions and rollback

Not in this cycle: live polling on the home page, a cross-group feed, charts, group emblems or colours, RSVP, and any change to the group page. Roll back by reverting the two feature commits; no data is written, so nothing needs repair.

## Progress and blockers

2026-10-04: Study and plan complete. Discovery answers recorded in the study. Implementation awaits approval of this plan and the three decisions above.

2026-10-04: Human approved this plan with “approved” and answered the three decisions: leave money still in play off the card; show “you owe / owes you”; keep this page for one-group members. Execution uses branch `feat/group-home`, worktree `/private/tmp/pn-home`.

2026-10-04 execution: two feature commits on `feat/group-home`, each after the full SQLite suite and `manage.py check`.

1. `b882610` `web/home.py` with `home_cards()`, three read helpers in `settlement.queries` (`member_records`, `unpaid_transfers`, `session_nets`; `stat_results` now builds on `counted_results`) and `games.clock.seconds_by_set()`. Eight query tests.
2. `874b985` new `home.html`, `_group_card.html` and styles. Four page tests. The blocks are unboxed sections with one status band each, not nested cards.

2026-10-04 verification: 510 SQLite tests pass (ten PostgreSQL-only skips); all 510 pass on a temporary PostgreSQL 17 instance, now stopped. System and migration-drift checks pass. No change to models, migrations, URL patterns, services or `static/js/`. Query budget (AC7): 11 queries for one group and for four groups with eight players each. Browser, synthetic database, four viewers (host with four groups, player with dues and both units, no group, empty group) at 320, 375, 768 and 1280px: no horizontal overflow; after one fix to the Last session link no target under 48px; new text pairs from 7.58:1; felt present only with a set in play; keyboard order follows the page and every stop shows the focus ring. CSS is 42326 bytes; the 40,000-byte figure from earlier plans is exceeded and was not a criterion of this plan.

Not verified: a physical phone, a screen reader, and the page with JavaScript off (the page has no script of its own; the timer then stays at the server figure). No independent finish review was run.

AC1–AC8 are met. Documentation synced: DESIGN.md, PRODUCT.md, the group-and-home surface record, wiki features and architecture, TODO.

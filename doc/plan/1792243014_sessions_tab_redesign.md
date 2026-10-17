# Sessions tab redesign: plan

Study: [doc/study/1792243014_sessions_tab_redesign.md](../study/1792243014_sessions_tab_redesign.md). Mode: design.

Goal: the group page's Sessions tab leads with live table cards, with the viewer's own table first and marked. Past sessions become a ledger of the viewer's nights, grouped by month, with their result and debt on each row.

## OPEN QUESTIONS

1. **Shape brief.** Confirm the brief in the study (section "Shape brief"), or correct it. Key points: felt cards only for sets in play; "You're playing" plus one bone **Open the table** button on your own table; New session moves to after the cards; the past rows show your result, your debts, and the table's status in muted words.
2. **Long past list.** Recommended: this year's months stay open. Each earlier year becomes one closed disclosure ("2025 · 48 sessions"). Alternative: show every month, with no limit, as now.
3. **Card heading.** Recommended: "Now playing" over the cards, because the cards show tables in use. Alternative: keep "Current sessions".

## Tasks

Branch: `feat/sessions-tab` from `main`. One Conventional Commit per task. Run the SQLite tests before each commit. No subagents: the work is in one area.

### 1. Sessions tab data (`web`)

- [ ] Add `web/sessions_tab.py` with `sessions_context(me)`. Move the Sessions branch of `web.views.group` into it. Keep `visible_nights`.
- [ ] Current cards. For each open session with shown sets, use the latest shown set. Add: seated members of that set (joined `Participant` rows, in join order), `at_table`, `seconds` from `clock.seconds_by_set`, `mine` (the viewer is seated), and `when` (location if set, else "Today" or the date in Asia/Manila).
- [ ] Order the cards by band: in play and mine; in play; open, ended or finalized and mine; the rest; drafts last. Inside a band: `game_date`, then `pk`, both ascending.
- [ ] Past rows. Use `session_nets(night_ids, [me.pk])` for the viewer's net, or `None` for "Did not play". Use `unpaid_transfers([me.pk])`, grouped by session, for the debt lines. Keep `settle_states` for the table status. Group the rows by month, newest first. Apply the year rule from OPEN QUESTION 2.
- [ ] Tests (`tdd`): card order across all five bands; `mine` for a seated player, not for a host who is not seated; a player never gets a draft; two sessions at one table on one date both appear; viewer net and "Did not play"; two debts on one row, in each direction; a chips session keeps its unit; month groups and the year rule; the query count does not grow with 3 or 30 sessions.

Acceptance: for the study's seed, Ben gets Garage set 2 first, then Upstairs in play, then Upstairs open; Hana also gets the draft last. Completion: tests pass; commit `feat: order the sessions tab around your table`.

### 2. Table cards and the ledger (design)

- [ ] `/impeccable` build pass inside DESIGN.md tokens. Read `reference/craft-floor.md` first.
- [ ] Add `templates/web/_session_card.html`: table name (two lines at most), the `when` line, set and state, chips (up to six, "+N", the count in words for screen readers), "N at the table", the ticking `clock_value` for a set in play, and "You're playing" in words. `.felt` only for a set in play; `.panel` for every other state.
- [ ] Your card holds **Open the table** (48 px, bone). Every other card is one link.
- [ ] Rebuild `_group_sessions.html`: heading (OPEN QUESTION 3), the cards, New session for a host, then "Past sessions" with month headings and rows. Keep the empty states, the "N not settled" count and the archived disclosure.
- [ ] Past row: table name; muted line "date · N sets · status words"; the signed net with its icon at the right, or "Did not play"; one line per debt, in Up or Down with words. The brass status pill appears only on a row with a debt of the viewer.
- [ ] CSS in `static/css/app.css`: the card grid becomes two columns from 700 px of content width (container query), with one card at full width. The ledger has a 65ch measure.
- [ ] `mobile-native` check: tap highlight, no hover-only state, 48 px targets.
- [ ] Add `web/tests/browser/seed_sessions_tab.py` (the study's seed) and `web/tests/browser/sessions_tab.mjs` at 320, 390 and 1280 px, as host and player: order, "You're playing" only on seated cards, felt only on cards in play, no overflow with a long table name and ₱199,999,999.98, 48 px targets, contrast of 4.5:1 or more, morph keeps the scroll, reduced motion, no JavaScript.

Acceptance: at 390 px, Ben's first card is his table in play with Open the table, and it is in the first viewport. Completion: browser checks pass; commit `feat: redesign the sessions tab as table cards and your ledger`.

## Rendezvous checks

- [ ] SQLite and PostgreSQL suites.
- [ ] `code-review`; `verification-before-completion`. No `security-review`: no auth, money record or user-data write changes. The tab shows only the viewer's own net and debts.
- [ ] `/impeccable critique` and `audit`, then `polish`; `break-ui` on the card and the past row.
- [ ] Phone screenshots of host and player at 390 px.

## Sync docs

- [ ] DESIGN.md addendum "Sessions tab (date)"; replace the stale 1.25:1 group layout text in Layout.
- [ ] Surface brief addendum for `templates-web-group-home`.
- [ ] spec.md and features.md: the Sessions tab behaviour.
- [ ] architecture.md: `web/sessions_tab.py`.
- [ ] Footgun if needed: the hub stamp counts seats, not who sits, so a swap does not redraw the chips.
- [ ] TODO.md phone checks.

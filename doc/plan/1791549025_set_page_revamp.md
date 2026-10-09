# Set page revamp, preparing and in play: plan

Status: approved 2026-10-09 ("approved"); all six decisions as recommended. The human asked for the installed design and motion skills, and to try apple-design. Date: 2026-10-09, Asia/Manila. Study: [Set page revamp](../study/1791548918_set_page_revamp.md).

## Outcome

A host preparing a set sees what is done and what is next. A host running a set sees the pot and most of the table on one phone screen and reaches Rebuy without scrolling past buttons. The page looks finished, and starting a set feels like the start of something.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new colour, font or raster asset. No migration, no change to accounting, permissions or what an action records. Built with the design and motion skills.

## What you will see

### Preparing: a draft or an open set (host)

The panel of totals is replaced by **"Get this set ready"**, four steps, each with a mark, a name, one line of facts and its own link:

| Step | Its line | Its action |
|---|---|---|
| Players | "3 added · 6 seats free", or "Nobody yet" | Add players |
| Stakes and rake | "₱5 / ₱10 · buy-in ₱500 to ₱5,000 · rake off" | Change |
| Open for players | Draft: "Players cannot see this set yet." Open: "Players can see it and join." | Back to draft, once open |
| Start | "Adds the usual buy-in (₱1,000) for players without one", with its tick box | — |

- A step is marked **Done**, **Next** or **Later**, in words as well as by the mark.
- One main button always names the next step: Add players, Open for players, Start the set. On a phone it stays in the bottom menu, as today.
- Money appears when there is money: one line, "₱500 bought in · 1 buy-in". No row of zeros.
- The badge reads **Draft** or **Open** (not "Setup").
- A player looking at an open set sees the table, the date, the stakes, who is in, and Join. No checklist.

### In play

**The felt panel, on a phone.** The table name and badge, the large "Still in play" figure with the timer and blinds beside it, then one line: "₱12,500 bought in · ₱2,650 cashed out", with **Details** to open the rest (buy-in count, rake, available to play, date and place). About 230px tall instead of 351px. From 900px the details stay open, since the column has room. The badge reads **In play**.

**A player's row.** One line: the chip, the name with its buy-in line, the amount, and one **Rebuy** button (Buy-in before the first one). About 64px instead of 142px.

- Tapping the row anywhere else opens that player's sheet. The sheet leads with **Cash out**, then the player's records with their reversals, then Remove where it applies.
- A small chevron at the row's end shows it opens.
- Under 360px wide the amount sits under the name so the button keeps its size.
- From 900px rows keep both written buttons, as now.

**The list.** A player sees their own row first. A host who is not seated finds "Join this set" as a quiet line under the list, not above it. A player who may join still gets Join first.

**The bottom menu.** While a set is in play it starts folded to its one-line bar, "Next: End play and count up". If you open it, it stays open, as your choice does today.

**Result on a 390 × 844 phone, eight players:** the panel and about six players on the first screen, where today the first row is partly covered. The page goes from about 1,760px to about 1,000px.

### Finish and movement

| Moment | Movement |
|---|---|
| A step is completed | Its mark is drawn as a tick and the "Next" mark moves to the following step |
| The set starts | Once: felt sweeps across the panel from the left in about half a second and the timer appears running. Under 900ms |
| Details opens | The facts fade in over 6px, as disclosures do elsewhere |
| A row is tapped | The row takes the pressed look from the first frame; the sheet rises as now |
| Everything already moving on this page | Unchanged: rows arriving, the buy-in edge, the underline of "Still in play", marks on changed rows |

Money never counts or rolls. Reduced motion removes the movement and keeps every state.

## Decisions for you

Approving accepts the recommendations unless you say otherwise.

1. **A player sees their own row first.** For that viewer only; the host's order does not change. Recommended: yes.
2. **The bottom menu starts folded while a set is in play.** It changes "starts expanded" for that one state. Recommended: yes; End play is pressed once a night.
3. **Words: Draft, Open, In play** wherever a set's state is shown (this page, the session page's list of sets, the group's list). Recommended: yes, one vocabulary.
4. **Players who left stay where they are in the list.** The app's rule is that live rows never reorder. Recommended: keep the rule.
5. **A switch for one release.** `TABLE_REVAMP=False` in Vercel returns the page as it is today, by keeping today's templates beside the new ones. They are deleted in the cycle after you accept it on your phone. Recommended: yes, because this is the screen in use during a real game.
6. **Desktop keeps both buttons on a row.** The choice of "Rebuy on the row, the rest behind a tap" is applied below 900px, where space is short. Recommended: yes. Say if you want one behaviour at every width.

## Implementation

Branch `feat/set-page-revamp` from `main`, three commits in this order. Not merged and not pushed without your word. Each stage ends with both test suites and its browser checks passing.

**Stage 1: in play.**

1. Try first: opening the cash-out sheet from inside the player's sheet. If `sheets.js` cannot, the cash-out form goes inside the player's sheet under its own heading.
2. Tests first (`web/tests/test_table.py`, `test_live.py`): the row's markup and targets, one row action below the breakpoint's markup, the sheet's order, the own row first for a player and unchanged for a host, the quiet Join line, the summary line and its details, rake rows only with rake, state words, `data-watch` and `data-value` unchanged on every row and on the pot, and the switch returning today's markup.
3. Templates: `_session_live.html` and `_players.html` rewritten; today's versions kept as `_session_live_classic.html` and `_players_classic.html`. A template filter for the state's word. `config/settings.py`: `TABLE_REVAMP`.
4. CSS: the panel, the summary line, the row, the chevron, the under-360px arrangement. `dock.js`: the folded default while in play.
5. Browser check, new `table.mjs`, at 320 × 568, 390 × 844 and 1280 × 800: the first screen's contents, row height, 48px targets, no overflow with a long name and a large amount, contrast on felt and on ground, keyboard order, Rebuy from the row, Cash out from the sheet, a live update from a second host keeping scroll, typed text and an open sheet, no JavaScript, and the switch.
6. Regression: `flow.mjs`, `inplace.mjs`, `numpad.mjs`, `dock.mjs`, `player_entries.mjs`, `late_player.mjs`, `navigate.mjs`, `screens.mjs`, `motion.mjs`, `lifetime.mjs`, updated where they name a class that moved.

**Stage 2: preparing.**

1. Tests first: each step's state and line for an empty draft, a draft with players, an open set, an open set with buy-ins, a full table, and a chips set; the next-step button per case; a player's view; no totals without money.
2. A small read-only helper in `web` builds the steps from what the view already loads. No query is added (the query-count test stays).
3. Templates and CSS for the checklist; `_host_controls.html` names the next step.
4. `table.mjs` gains the preparation cases, including the whole walk: draft → add players → open → start, with and without JavaScript.
5. Regression: `opening`-related checks, `rake_controls.mjs`, `session_form.mjs`.

**Stage 3: finish and movement.**

1. The tick and the moving "Next" mark, the start of the set, the details fade, the pressed row. CSS where the server draws the state; `pokerMotion.run` only for what a finger causes.
2. `table.mjs`: each movement's first frame and rest, the start under 900ms and once per set per browser, figures at their value on the first frame, reduced motion, Motion blocked, nothing running and no inline style at rest, late frames with the processor slowed four times.
3. One `/impeccable critique` of the page in both jobs, and one fix batch from it.
4. Sync docs: DESIGN.md (new sections; the superseded lines of "Player rows", "Start controls" and "Collapsible host dock" named), PRODUCT.md, wiki features and deployment, browser README, TODO with the phone checklist.

## Acceptance criteria

- AC1. On a 390 × 844 phone, a host of a running set with eight players sees the whole panel and at least five whole rows without scrolling, with the menu folded.
- AC2. A row is at most 72px tall at 390px wide, and every control on it is at least 48px.
- AC3. Rebuy is one tap from the row; Cash out is two taps (row, Cash out) and records exactly what it records today.
- AC4. A draft shows the four steps with the right state in each case of stage 2, one main button for the next step, and no zero totals.
- AC5. A live update from another device changes the page in place: scroll position, typed text and an open sheet are kept, and changed rows are marked as today.
- AC6. Without JavaScript every action on the page works.
- AC7. `TABLE_REVAMP=False` returns today's page.
- AC8. No query is added to the set page; no model or service changes.
- AC9. The start of a set plays once, under 900ms; money never shows an intermediate value; reduced motion moves nothing.
- AC10. Both suites pass; the listed browser checks pass.

## Out of scope

- Count-up, cash-out review, final results, the session page and the set log.
- Seating, a blind-level clock, new figures, new actions.
- Sorting or filtering players; moving players who left.
- Removing the old templates (the cycle after acceptance).

## Rollback

`TABLE_REVAMP=False` in Vercel returns the previous page at once. To remove the work, revert the feature commits. No migration.

## Cannot be verified from here

A physical phone at a table: thumb reach of the Rebuy button on the right edge, the row as a tap target in a dim room, and the iPhone keyboard with the folded menu. These go on your phone checklist, and the best test is one real set.

## Progress and blockers

2026-10-09: Study and plan written after three questions to the human. Waiting for approval.

2026-10-09: approved ("approved"), all six decisions as recommended. The human asked for the installed design and motion skills and to try apple-design; impeccable, motion, apple-design and redesign-existing-projects were loaded. Built on `feat/set-page-revamp`.

Checkpoint, 2026-10-09 (the human asked to compact the conversation here):

- **Stage 1 (in play)** committed as `7f73722`. **Stage 2 (preparing)** committed as `cd39b39`. **Stage 3** movement (`static/js/table.js`) and the browser check `web/tests/browser/table.mjs` are committed with this note.
- 934 tests pass on SQLite. `table.mjs` passes 63 of 63 on a fresh seed, with the second server for the switch.
- Measured at 390 × 844 with eight players: panel 223px (was 351), row 65px (was 142), six whole rows on the first screen, page 1,114px (was 1,758). The start of a set runs 780ms; no late frame with the processor slowed four times.
- A sheet could not open another sheet, so `sheets.js` gained a swap: the player's sheet gives way to the cash-out form in the same open sheet.

Still to do in stage 3:

1. `table.mjs`: the check "open: the menu is at most 260px" measured a folded menu (the script had folded it earlier). Clear the stored choice first, then re-measure.
2. Regression browser checks, updated where they name a class that moved: `flow`, `inplace`, `numpad`, `dock`, `player_entries`, `late_player`, `navigate`, `screens`, `motion`, `lifetime`, `rake_controls`, `session_form`, and the opening checks.
3. The PostgreSQL suite.
4. One `/impeccable critique` of the page in both jobs, and one fix batch.
5. Sync docs: DESIGN.md, PRODUCT.md, wiki features and deployment (`TABLE_REVAMP`), browser README, TODO with the phone checklist.
6. State words on the session page's and the group's lists of sets (decision 3) are not done yet; only the set page uses them.

2026-10-09, finished:

- All six remaining steps are done. Commits on `feat/set-page-revamp`: `7f73722`, `cd39b39`, `36797c8`, `40c929c` (state words), `a9f1918` (regression fix), then the critique's fix batch and the docs. Not merged, not pushed.
- **A fault the regression run found:** on a screen 900px or wider the facts faded in on first sight of the page. Fixed in `table.js`.
- **Browser checks:** `table` 63 of 63, `flow` 52, `numpad` 120, `dock` 228, `motion` 34, `inplace` 39, `navigate` 52, `screens` 46, `lifetime` 22, `session_form` 69, `player_entries` 48, `rake_controls` 25: all pass. Five were updated to follow the new page (browser README). `opening`, `opening_drafts`, `rake` and `late_player` fail the same way with the switch off, so they were already out of date.
- **Suites:** 934 pass on SQLite and on PostgreSQL 17.
- **Critique:** 28 of 40, no P0. One fix batch: the pot on one line at 320px, finished steps of an open set on one line, "Choose rake" on the stakes step, a line telling the host a tap reaches cash-out, the hint colour on the rail. Left open (P3): ragged amounts on rows without a button, the lone Details line when open, an action in the draft's empty list.
- **Differs from the plan:** AC8 said no model or service change. Decision 3 (one set of words) needed `GameSession.state_word`, a property with no migration, and four refusal messages now say "in play" and "draft" where they said "running" and "setup". A sheet cannot open a second sheet, so Cash out swaps the content of the open one.
- **Acceptance:** AC1 to AC10 met as measured above, with AC8 as noted. The phone checks in TODO.md are the human's.

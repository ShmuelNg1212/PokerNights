# Plan: parlor revamp from the Stitch concepts

Study: [1795008949_parlor_revamp.md](../study/1795008949_parlor_revamp.md). Mode: design. Skills: `/impeccable` refine commands, `mobile-native` (execute); `/impeccable critique` and `audit`, then `polish`; `break-ui`, `review-animations`, `code-review` (rendezvous).

Branch: `feat/parlor-revamp`, stacked on `feat/table-moments` (unreleased: `build/parallel-tests`, and the declined table-moments docs). One branch for all slices. One commit or more for each slice. No code-writing subagents: slices 1 to 6 all edit `static/css/app.css`.

Reference pictures: [assets](../study/1795008949_parlor_revamp_assets/). `concept_*.png` is the target feel. `now_*.png` is the start.

## OPEN QUESTIONS

Answered 2026-11-18: approved, all four recommendations. The human added: focus on the layout; add movement that suits the new layouts; keep the design system and the material feel. See "Movement" below.

1. **Player rows as Rail cards (study idea 4).** The concepts put each player on a raised Rail card with an 8px gap. Slice E (2026-11-01) chose ruled rows: "A set in play is the only blue card." Recommendation: **yes, cards**, on the set page, count-up, home "To settle" and the transfers. Keep ruled rows in long reading lists (the group's Sessions tab, Stats board, set log). Condition: a table of six still fits one 390 × 844 screen above the dock. If it does not fit, the set page keeps ruled rows. If no, tasks 2.3 and 4.3 keep ruled rows and use only the new spacing.
2. **The next step as a bone button in the collapsed dock (idea 6).** Now the collapsed dock says "Next: End play and count up" behind a chevron. The concept shows a full-width bone button. Recommendation: **yes**. End play is one POST today, and Resume play undoes it. The other host controls stay behind the chevron. If no, delete task 2.4.
3. **Home record as three tiles (idea 16).** Recommendation: **yes**, per unit: Sessions, Win rate, Net. All three come from figures that the card already has (`record.sessions`, `record.wins`, `record.net`). "Avg net" from the concept would be a new figure on this page; leave it on Stats. If no, delete task 3.4.
4. **Log in | Sign up tabs on the front door (idea 17).** Recommendation: **yes**. Two links styled as a segmented control, on top of the raised sheet. The "No account? Sign up" line goes. The description stays on Sign up only (2026-10-17). No tagline pill on Log in. If no, delete task 6.1.

## Outcome

- Each main screen reads like the concepts: Brass section labels, inset felt, inset fact tiles, raised player cards, transfer cards and a ledger table.
- The materials, words, motion and money rules are unchanged. What each action records, and who may do it, is unchanged.

## Non-goals

These are in the concepts. Do not build them (study Finding 3):

- No bottom tab bar. No blind clock, levels, rounds or level progress bar.
- No "In stack" figure during play. No money in play on Your groups.
- No Cash out button on each row in play. No "Busted" badge. No loss called out.
- No felt outside a running set. No version pill, no claims cards, no "encrypted" or "offline" text.
- No schedules, RSVP restyle, "Seat N" labels, payment-app names, food pool or new chip calculator.
- No new font file. No new colour token. No model, service or migration change.

## Design decisions

| Item | Decision |
|---|---|
| Section label | `.section-label`: 13px, weight 700, uppercase, `letter-spacing: .06em`, Brass, `font-stretch: 85%`. A 16px drawn icon before it (from the existing icon set). An optional count pill at the right in Bone Dim on Rail 2 ("4 / 6"). An optional muted aside at the right ("Net −₱750"). It is still an `h2`/`h3`, so headings stay in the outline. |
| Fact tiles | `.facts`: a grid of 2 or 3 equal tiles with an 8px gap. Each tile is Ground (or Felt Deep on felt) with a 10px radius and 12px padding. A 12px Bone Dim label over a 22px compressed tabular figure. Below 340px, three tiles become one column. |
| Rail card row | `.row-card`: Rail, 1px Rule border, 12px radius, 12px padding, 6px gap between cards. No shadow. The token, name and amount keep their current grid. The changed-row Brass mark is drawn inside the card. |
| Felt card | On phones the felt has 16px side margins, a 26px radius on all corners and the same grain. From 900px it is unchanged. |
| Badges | Host: Brass outline pill with a star icon. Dealer: Brass fill, Ink "D", 24px. Status pill with a dot: In play (Up dot), Counting up, Settled, Not paid. Words always; colour never alone. |
| Count row edit | The row has a 2px Brass inside edge while its field has focus (`:focus-within`). The field's own focus ring is unchanged. |
| Net on a count row | Shown only when the server has a confirmed count or a cash-out for the player. Signed, with the arrow icon, in Up or Down. No net for a typed count that is not confirmed. |
| Transfer card | Payer token over name at the left, payee at the right. In the middle: the amount (28px, the existing length rules), a Brass arrow under it, and "pays" for a screen reader. Then a status line (Not paid in Brass with a clock icon; Paid in Up with a check and time) and the action at the right (Mark paid bone, Undo quiet). Names wrap under their token. |
| Ledger table | Columns Player, In, Out, Net. Tabular figures, right-aligned. Meta under the name: "N buy-ins". A footer row: totals of In and Out, and Net ₱0. When rake was collected, a row "Rake" above the footer. It is a real `<table>` with a caption. |

## Movement

Rules: DESIGN.md "Motion system". Only `transform` and `opacity`. Existing presets only (`press`, `release`, `shift`, `arrive`, `fade`, `progress`). An interaction ends within 300ms. Money never counts. Reduced motion and a missing Motion file show the end state at once. No control waits for a movement.

| Item | Decision |
|---|---|
| Card press | A Rail card row that is a link or a tap target sinks to `scale(.985)` under a finger with `press` and comes back with `release`, as a button does. Its Rule border stays. Not on a card that holds a field. |
| Facts arrive | Fact tiles rise 8px and fade in, 40ms apart, at most four steps, with `arrive`, on a full page load or a screen change. Not on a poll or a redraw of the same page. The figures are at their value from the first frame. |
| Transfer arrow | The Brass arrow under a transfer's amount grows from the payer's side (`scaleX` 0 to 1, origin left) with `progress`, 40ms apart down the list, on arrival only. |
| Paid | When a transfer is marked paid by this phone, the status line's check scales in from 0.6 with `arrive`. The card does not move. |
| Count edge | The Brass inside edge of a count card is a pseudo-element that fades in over 120ms when its field gets focus. |
| Books status | When the books panel's status changes after an accepted count, the new status line fades up 4px with `fade`. The existing balanced rule reveal stays and plays once. |
| Tab marker | The selected Log in / Sign up pill slides to the chosen tab on the screen change, as the group page's tab marker does. |
| In play dot | The In play pill's dot keeps the Live dot's existing treatment. Nothing new. |

## Tasks

### Slice 1: shared parts

- [x] **1.1 Section label, fact tiles, Rail card row, badges, felt card.** tests: alongside. Add the five parts to `app.css` with the values in the table. Change no page yet. Done when: a style test page in the Django test client renders each part, and `surfaces.mjs` shows no change on the current pages.

- [x] **1.2 Movement parts.** tests: alongside. Card press, facts arrive and the count edge, in `motion.js` and `app.css`. Done when: `motion.mjs` passes, and a probe shows each one uses only `transform` and `opacity` and is off under reduced motion.

### Slice 2: set in play (`concept_live_table_in_play.png`)

- [x] **2.1 Inset felt.** tests: alongside. Apply the felt card on phones. Keep the pot figure, the In play badge and the Details disclosure with their IDs and classes. Done when: `pot.mjs`, `overture.mjs` and `chip_pot.mjs` pass, and nothing spills past the felt's corners at 320px.
- [x] **2.2 Facts on felt.** tests: alongside. Replace the "₱4,000 bought in · ₱0 cashed out" line and the right column with a 2 × 2 fact grid: Bought in, Cashed out (Rake when rake is on), Blinds, Set timer. "Still in play" stays the display figure above it. Done when: every figure in the grid equals the figure on the current page for pesos and chips, with and without rake.
- [x] **2.3 Player cards.** tests: alongside. Section label "PLAYERS" with the count pill ("4 / 6"). Each player is a Rail card row. Host badge on a host's row. Dealer badge on the dealer's row when the set has a current seat draw. Rebuy stays the only button. Done when: a table of six fits above the dock at 390 × 844 (or open question 1's fallback applies), and `dock.mjs`, `inplace.mjs` and `sheet_drag.mjs` pass.
- [x] **2.4 The next step in the collapsed dock.** tests: alongside. The collapsed dock shows "End play and count up" as a full-width bone button. The chevron still opens the other controls. Done when: one tap ends play, Resume play still works, and `dock.mjs` and `mobile_motion.mjs` give their known results (58/60).

### Slice 3: Your groups (`concept_your_groups_home.png`, `concept_your_groups_the_rack_home.png`)

- [x] **3.1 Group card head.** tests: alongside. Name with the role badge (Host with a star). A line under the name with the player count. The chips stay, and "+7" stays. Done when: `home.mjs` and `arrivals.mjs` pass, and the name still travels to the group heading.
- [x] **3.2 In-play card.** tests: alongside. The felt band becomes an inset felt card inside the group card: an In play pill at the top left, "Set N" at the top right, the table name, "N at the table · timer", the bone button. No money figure. A group with nothing in play gets a quiet Rail panel: "No set in play · Last played Oct 24". Done when: the card shows the same facts as now for in play, joining, counting up and quiet.
- [x] **3.3 To settle cards.** tests: alongside. Section label "TO SETTLE" with the net at the right. Each row is a Rail card row with the other player's token, "You owe **Name**" or "**Name** owes you", the session date under it, the amount at the right and Paid or Not paid under it. At most three rows, then the count of the rest, as now. Done when: the rows link to the same sessions and show the same amounts as now.
- [x] **3.4 Record tiles.** tests: first. Section label "YOUR RECORD". For each unit, three tiles: Sessions, Win rate (wins ÷ sessions, whole percent, rounded as Stats rounds it in `settlement/stats.py`), Net (signed). Then the Last session row with "Top result" when the viewer was first. Write the tests before the template: the win-rate rounding, zero sessions (no tiles), both units, and a tie for first. Done when: those tests pass and the tiles match Stats for the same period.

### Slice 4: count-up (`concept_host_count_up_reconciliation.png`)

- [x] **4.1 Books panel at the top.** tests: alongside. In the neutral overview: section label "COUNT-UP" with "1 of 2 counted" pill. An inset panel: Total bought in, Cashed out plus confirmed counts, and a status row ("The books balance" with the double rule's colour, or "₱500 still to account for" in Brass). It uses the confirmed figures only. The dock's running total stays. "The books" section further down goes. Add the books status movement. Done when: `count_flow.mjs`, `counts.mjs`, `books_gap.mjs` and `books_motion.mjs` pass, and the balance reveal still plays once.
- [x] **4.2 Net on a count row.** tests: first. When the player has a confirmed count or a cash-out, show the signed net beside the field. The net is the figure that the results use: the cash-out or confirmed count minus gross buy-ins. Write the tests before the template: no net without a confirmed count, rake as a loss, chips and pesos. Done when: the tests pass and the net equals the final result for the same player.
- [x] **4.3 Count cards.** tests: alongside. Each count row is a Rail card row. The field is an inset Ground field at the right. The row has the Brass edge while its field has focus. "by chips" stays. Done when: `numpad.mjs` and `chip_numpad.mjs` pass, and the fields do not move when a count is accepted.

### Slice 5: settle-up and recap (`concept_session_settle_up_transfers.png`)

- [x] **5.1 Recap head card.** tests: alongside. "SESSION RECAP" label and Settled / Partly settled / Unsettled pill. Table name, "Closed 2:15 AM · 12 players". "Still to pay" stays the display figure. Three fact tiles: Play time, Total bought in (with the buy-in count), Rake (only when collected). The top result sits on Rail 2 with a Brass edge, not on felt. Done when: `finale.mjs` and `night.mjs` pass, and the figures match the current page.
- [x] **5.2 Transfer cards.** tests: alongside. Section label "WHO PAYS WHOM" with "N transfers" pill. Each transfer is a transfer card. Mark paid and Undo stay native POST actions. Add the transfer arrow and Paid movement. Done when: `transfer_layout.mjs`, `debts.mjs` and `carried_debts.mjs` pass, and "Maria Clara de los Santos" stays readable at 320px.
- [x] **5.3 Ledger table.** tests: first. In the recap's "Everyone's results" and the session results, replace the wrapping meta line with the ledger table. Write the tests before the template: the footer totals equal the session's totals, the Net column sums to zero without rake, the Rake row appears only when rake was collected and the footer then still balances, and a reopened session's replaced results are marked as now. Done when: the tests pass, and at 320px the table fits without sideways scroll (names wrap; figures do not).
- [x] **5.4 Share card.** tests: alongside. "SHARE RESULTS" label. A Rail card shows the same text that Share sends, then two buttons: Copy text and Share picture. They call the existing share code. Done when: `share.mjs` passes and the shown text equals the copied text.

### Slice 6: front door (`concept_pokernights_front_door_home.png`)

- [x] **6.1 Log in | Sign up tabs.** tests: alongside. Two links styled as a segmented control at the top of the raised sheet, with the tab marker movement. The current page has the selected state and `aria-current="page"`. An invited Sign up keeps the group's name heading. Done when: `door.mjs` and `entry.mjs` pass, and a phone's password manager still sees the same form fields.
- [ ] ~~**6.2 Field rows.** tests: alongside. Show stays on the label line at the right, as in the concept. Field icons are not added. Done when: the form fields, names and autocomplete values are unchanged.~~ Dropped; see the execution notes.

## Execution notes (2026-11-18)

Where the build differs from the tasks above, and why.

- **1.1, 1.2.** No style test page; each part is checked on the screen that uses it. The card press is CSS (`scale` on `:active` of the row's opener), not `motion.js`: Motion already animates the rows' `transform` (flow.js), and the separate `scale` property cannot fight it. Facts arrive only on Your groups (with its arrival), not on the set page, whose felt has the overture.
- **2.2.** The felt keeps its old height so that six players still fit: timer and blinds are two inset tiles beside the figure, and the facts line is an inset bar. No 2 × 2 grid.
- **2.3.** The Host mark is a small Brass disc with a star on the chip (a pill squeezed the name). No Dealer badge: the overture's dealer button lands on the dealer's chip, and a second mark would sit under it. The count pill keeps "6 · 2 seats free". At 390 × 844 the folded dock's top is at 779px. With the 25-letter name last (three lines, as before the revamp), the sixth row ends at 796px, 17px under it; with short names all six fit (about 764px).
- **2.4.** The bone button and a round chevron share one row, so the folded dock grows by about 10px only.
- **3.1, 3.2.** The visible player-count pill was dropped (it pushed Host to its own line); the count is still read out. The In play pill gets a dot. The open and quiet bands are inset Ground panels.
- **3.3.** No net at the right of "To settle": the rows can mix pesos and chips. No Paid line: every row there is unpaid.
- **3.4.** No "Top result" tag: it needs a new query. The tiles use `PlayerStats.win_percent`, which Stats uses.
- **4.1.** "The books" stays where it is and becomes a Rail panel with an inset list. Reason: the dock already keeps the running total in view, and gap.js, the override and the balanced reveal use that section. The overview is an inset card.
- **4.2.** The net is under the name, after "₱1,000 in", not beside the field. `PlayerLine.count_net`.
- **5.1.** The session's head is an inset card. No new tiles there: the recap sheet already has them.
- **5.2.** The transfer markup is unchanged (its container-query layout stays); each transfer is a card, the arrow is Brass and draws on a page load. The existing Paid tick and dim stay; no second Paid movement.
- **5.3.** The ledger table replaces the closed session's results list. In the recap sheet the ranking and its bars stay, and each fact in its line no longer breaks inside itself. Footer: with rake, a "Rake already collected" row makes Out and Net balance. A reopened session is not closed, so it keeps the old list.
- **5.4.** A card with the first lines of the share text over the existing Share results button. The sheet still holds Copy and the picture.
- **6.1.** The tabs show only where sign-up is open; an invited Sign up keeps its own line. The current tab is a label, the other a link (`.entry-alt a`, which door.js and the probes use). The selected pill carries `view-transition-name`, so it slides between the screens. On Log in the heading is visually hidden, because the tab says the same.
- **6.2.** Dropped. The Show button stays in the field: door.js turns the moon with it, and the field must not change for password managers.
- **Probes changed on purpose.** `dock.mjs`: the folded bar in play now holds End play, so the visible-part count leaves that form out and a check asks for it. `home.mjs`: records are read from the tiles too, and the cap on small text is 15 pieces (the floor of 11px stays).

## Rendezvous checks

Recorded 2026-11-18 on `feat/parlor-revamp` (`3401c66`, `e0debf5`). Baseline is a clean worktree of `49e070f`, the same fixture, the same day.

- [x] SQLite suite: 1801 tests OK. PostgreSQL suite: 1801 tests OK on the final code. (A first PostgreSQL run caught 2 front-door tests failing on `<h1>Log in</h1>`; the heading is now hidden by CSS, not a class.)
- [x] New tests first: `ledger/tests/test_count_net.py` (7), `web/tests/test_ledger_table.py` (7), three record-tile tests in `web/tests/test_home.py`. Each failed before its code.
- [x] Browser probes (branch, then baseline): pot 53/53; overture 53/53; chip_pot 32/32; sheet_drag 40/40; finale 45/45; motion 40/40; arrivals 45/45; chip_numpad 24/24; books_gap 36/36; home 60/60 (base 60/60 with the old checks); entry 91/91; night 88/88; dock 226 pass, 2 fail = base (toggle focus after a live update; bar verdict); count_flow 89/2 = base; books_motion 17/2 = base; numpad 103/2 = base; door 140/1 = base; share 28/1 = base; carried_debts 31/1 = base; debts 0/1 = base (fixture); inplace 24 then the same stop at line 93 as base; transfer_layout 100 pass, 55 fail, base 96/59 (four base failures fixed, none added); mobile_motion 58/60, the two known WebKit fallback failures.
- [x] Each probe failure the branch added was a real change or a real fault, and was fixed: the folded-dock part count (probe updated), the keyboard check 9px short (count spacing tightened), 44px tabs (now 48px), the lost `.night-results` hook (restored: it also carries chips between screens), transfer chips off their first name line and a card over 100px (fixed), the moved Share button and the tab order (probes updated).
- [x] `break-ui` by hand: a fixture with a 57-letter group name, a 33-letter player name, CJK and emoji names, ₱636,854.64 in play, ₱500 / ₱1,000 blinds, a 15,000,000-chip game, 5% rake and twelve players with centavos. Found and fixed: felt tiles past the felt's edge, amounts under Rebuy at 320px, ledger names cut to 60px and clipped Net cells (two-line ledger; 0 clipped cells at 320 and 390), a rake figure broken in the session head.
- [x] Captures at 320, 390 and 1280px of the set page, Your groups, count-up, the closed session and the front door, beside the concepts.
- [x] The host's first steps, 390px with touch, 8/8: the tabs, the record tiles, Go to the table, a rebuy accepted (pot +₱1,000), End play from the folded dock, count-up, the Brass edge while typing, a confirmed count with its net (+₱200), no page errors.
- [ ] `/impeccable critique` and `audit` were not run as skills. The design pass was done by comparing captures with the concepts and DESIGN.md.
- [ ] Not checked: a real iPhone (press feel, the tab slide in Safari, the keyboard over count fields). These are in TODO.md.

## Completion

All tasks ticked, the rendezvous checks recorded here, and a verified branch. Then sync docs: DESIGN.md (an addendum that revises the Slice E ruled-rows rule if question 1 is yes), a PRODUCT.md addendum, and TODO.md phone checks.

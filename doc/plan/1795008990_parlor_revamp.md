# Plan: parlor revamp from the Stitch concepts

Study: [1795008949_parlor_revamp.md](../study/1795008949_parlor_revamp.md). Mode: design. Skills: `/impeccable` refine commands, `mobile-native` (execute); `/impeccable critique` and `audit`, then `polish`; `break-ui`, `review-animations`, `code-review` (rendezvous).

Branch: `feat/parlor-revamp`, stacked on `feat/table-moments` (unreleased: `build/parallel-tests`, and the declined table-moments docs). One branch for all slices. One commit or more for each slice. No code-writing subagents: slices 1 to 6 all edit `static/css/app.css`.

Reference pictures: [assets](../study/1795008949_parlor_revamp_assets/). `concept_*.png` is the target feel. `now_*.png` is the start.

## OPEN QUESTIONS

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

## Tasks

### Slice 1: shared parts

- [ ] **1.1 Section label, fact tiles, Rail card row, badges, felt card.** tests: alongside. Add the five parts to `app.css` with the values in the table. Change no page yet. Done when: a style test page in the Django test client renders each part, and `surfaces.mjs` shows no change on the current pages.

### Slice 2: set in play (`concept_live_table_in_play.png`)

- [ ] **2.1 Inset felt.** tests: alongside. Apply the felt card on phones. Keep the pot figure, the In play badge and the Details disclosure with their IDs and classes. Done when: `pot.mjs`, `overture.mjs` and `chip_pot.mjs` pass, and nothing spills past the felt's corners at 320px.
- [ ] **2.2 Facts on felt.** tests: alongside. Replace the "₱4,000 bought in · ₱0 cashed out" line and the right column with a 2 × 2 fact grid: Bought in, Cashed out (Rake when rake is on), Blinds, Set timer. "Still in play" stays the display figure above it. Done when: every figure in the grid equals the figure on the current page for pesos and chips, with and without rake.
- [ ] **2.3 Player cards.** tests: alongside. Section label "PLAYERS" with the count pill ("4 / 6"). Each player is a Rail card row. Host badge on a host's row. Dealer badge on the dealer's row when the set has a current seat draw. Rebuy stays the only button. Done when: a table of six fits above the dock at 390 × 844 (or open question 1's fallback applies), and `dock.mjs`, `inplace.mjs` and `sheet_drag.mjs` pass.
- [ ] **2.4 The next step in the collapsed dock.** tests: alongside. The collapsed dock shows "End play and count up" as a full-width bone button. The chevron still opens the other controls. Done when: one tap ends play, Resume play still works, and `dock.mjs` and `mobile_motion.mjs` give their known results (58/60).

### Slice 3: Your groups (`concept_your_groups_home.png`, `concept_your_groups_the_rack_home.png`)

- [ ] **3.1 Group card head.** tests: alongside. Name with the role badge (Host with a star). A line under the name with the player count. The chips stay, and "+7" stays. Done when: `home.mjs` and `arrivals.mjs` pass, and the name still travels to the group heading.
- [ ] **3.2 In-play card.** tests: alongside. The felt band becomes an inset felt card inside the group card: an In play pill at the top left, "Set N" at the top right, the table name, "N at the table · timer", the bone button. No money figure. A group with nothing in play gets a quiet Rail panel: "No set in play · Last played Oct 24". Done when: the card shows the same facts as now for in play, joining, counting up and quiet.
- [ ] **3.3 To settle cards.** tests: alongside. Section label "TO SETTLE" with the net at the right. Each row is a Rail card row with the other player's token, "You owe **Name**" or "**Name** owes you", the session date under it, the amount at the right and Paid or Not paid under it. At most three rows, then the count of the rest, as now. Done when: the rows link to the same sessions and show the same amounts as now.
- [ ] **3.4 Record tiles.** tests: first. Section label "YOUR RECORD". For each unit, three tiles: Sessions, Win rate (wins ÷ sessions, whole percent, rounded as Stats rounds it in `settlement/stats.py`), Net (signed). Then the Last session row with "Top result" when the viewer was first. Write the tests before the template: the win-rate rounding, zero sessions (no tiles), both units, and a tie for first. Done when: those tests pass and the tiles match Stats for the same period.

### Slice 4: count-up (`concept_host_count_up_reconciliation.png`)

- [ ] **4.1 Books panel at the top.** tests: alongside. In the neutral overview: section label "COUNT-UP" with "1 of 2 counted" pill. An inset panel: Total bought in, Cashed out plus confirmed counts, and a status row ("The books balance" with the double rule's colour, or "₱500 still to account for" in Brass). It uses the confirmed figures only. The dock's running total stays. "The books" section further down goes. Done when: `count_flow.mjs`, `counts.mjs`, `books_gap.mjs` and `books_motion.mjs` pass, and the balance reveal still plays once.
- [ ] **4.2 Net on a count row.** tests: first. When the player has a confirmed count or a cash-out, show the signed net beside the field. The net is the figure that the results use: the cash-out or confirmed count minus gross buy-ins. Write the tests before the template: no net without a confirmed count, rake as a loss, chips and pesos. Done when: the tests pass and the net equals the final result for the same player.
- [ ] **4.3 Count cards.** tests: alongside. Each count row is a Rail card row. The field is an inset Ground field at the right. The row has the Brass edge while its field has focus. "by chips" stays. Done when: `numpad.mjs` and `chip_numpad.mjs` pass, and the fields do not move when a count is accepted.

### Slice 5: settle-up and recap (`concept_session_settle_up_transfers.png`)

- [ ] **5.1 Recap head card.** tests: alongside. "SESSION RECAP" label and Settled / Partly settled / Unsettled pill. Table name, "Closed 2:15 AM · 12 players". "Still to pay" stays the display figure. Three fact tiles: Play time, Total bought in (with the buy-in count), Rake (only when collected). The top result sits on Rail 2 with a Brass edge, not on felt. Done when: `finale.mjs` and `night.mjs` pass, and the figures match the current page.
- [ ] **5.2 Transfer cards.** tests: alongside. Section label "WHO PAYS WHOM" with "N transfers" pill. Each transfer is a transfer card. Mark paid and Undo stay native POST actions. Done when: `transfer_layout.mjs`, `debts.mjs` and `carried_debts.mjs` pass, and "Maria Clara de los Santos" stays readable at 320px.
- [ ] **5.3 Ledger table.** tests: first. In the recap's "Everyone's results" and the session results, replace the wrapping meta line with the ledger table. Write the tests before the template: the footer totals equal the session's totals, the Net column sums to zero without rake, the Rake row appears only when rake was collected and the footer then still balances, and a reopened session's replaced results are marked as now. Done when: the tests pass, and at 320px the table fits without sideways scroll (names wrap; figures do not).
- [ ] **5.4 Share card.** tests: alongside. "SHARE RESULTS" label. A Rail card shows the same text that Share sends, then two buttons: Copy text and Share picture. They call the existing share code. Done when: `share.mjs` passes and the shown text equals the copied text.

### Slice 6: front door (`concept_pokernights_front_door_home.png`)

- [ ] **6.1 Log in | Sign up tabs.** tests: alongside. Two links styled as a segmented control at the top of the raised sheet. The current page has the selected state and `aria-current="page"`. An invited Sign up keeps the group's name heading. Done when: `door.mjs` and `entry.mjs` pass, and a phone's password manager still sees the same form fields.
- [ ] **6.2 Field rows.** tests: alongside. Show stays on the label line at the right, as in the concept. Field icons are not added. Done when: the form fields, names and autocomplete values are unchanged.

## Rendezvous checks

- [ ] SQLite suite and PostgreSQL suite.
- [ ] Browser probes named in each task, on a fresh seed for each.
- [ ] `/impeccable critique` and `audit` against the concept pictures and DESIGN.md, then `polish`.
- [ ] `break-ui` on the set page, count-up and recap: long names, twelve players, large amounts, chips games, rake on.
- [ ] Captures at 320, 390 and 1280px of each screen, beside its concept.
- [ ] The first thing the host does: log in, open Your groups, open the set, record a rebuy, end play, type a count, finish, close, mark a transfer paid.

## Completion

All tasks ticked, the rendezvous checks recorded here, and a verified branch. Then sync docs: DESIGN.md (an addendum that revises the Slice E ruled-rows rule if question 1 is yes), a PRODUCT.md addendum, and TODO.md phone checks.

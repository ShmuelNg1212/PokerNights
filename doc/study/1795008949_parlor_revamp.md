# Study: parlor revamp from the Stitch concepts

Date: 2026-11-18. Mode: design. Branch: `feat/parlor-revamp`.

## Request

The human gave six Stitch concept screens and one concept DESIGN.md ("Warm Tactile Parlor"). The request: take inspiration from the screens and revamp the UI. Keep the feel of the app.

## Sources

- Concepts: [assets](1795008949_parlor_revamp_assets/), files `concept_*.png`. The originals are in `~/Downloads/stitch_pokernights_ui_revamp/`. Each folder also has a `code.html`. This study did not use the HTML. Use the pictures only.
- Current screens: the same folder, files `now_*.png`. Captured at 390 × 844 from the `seed_sheet_drag.py` fixture with reduced motion.
- [DESIGN.md](../../DESIGN.md) and [PRODUCT.md](../../PRODUCT.md).

## Finding 1: the concepts use our own tokens

The concept DESIGN.md has the same colours as The Rack: Ground, Rail, Bone, Ink, Felt, Brass, Up, Down and chips c1 to c10. It has the same radii: 16px surfaces, 15px buttons, 10px fields, 26px sheets. It has the same bone button with a short underside. Stitch made the concepts from our design system.

So this revamp is about **composition**, not a new palette. The feel stays because the materials stay.

The concept type is Archivo Narrow. Our Archivo is a variable face with widths from 62% to 125%. We already use compressed widths for figures. A narrower width for labels needs no new font file.

## Finding 2: what the concepts do differently

| # | Idea | Where | Current app |
|---|---|---|---|
| 1 | Uppercase Brass section labels with a small drawn icon and a count pill at the right ("ACTIVE SEATS 6/8", "TO SETTLE", "YOUR GROUP RECORD") | all screens | Bone headings in title case ("Players", "The books") |
| 2 | Felt as an inset card with 16px margins and all corners round | set page, home | Felt is full width with bottom corners only (phones) |
| 3 | A darker inset grid of facts inside a card (2 × 2 or 3 tiles) | set page, home record, recap | Facts are one text line or ruled rows |
| 4 | Each player is a raised Rail card with an 8px gap | set page, count-up | Ruled rows (decided in UI revamp Slice E) |
| 5 | A seat or role badge beside the name ("Seat 2", "HOST") | set page, count-up | Not shown |
| 6 | The main next step is a full-width bone button in the thumb zone | set page | The dock is collapsed: "Next: End play and count up" behind a chevron |
| 7 | A balance panel at the top of count-up: bought in, against cash-outs plus stacks, and a status row ("Books are balanced") | count-up | "The books" is below the player list; the running total is in the dock |
| 8 | Each count row shows the player's net beside an inset count field | count-up | The row shows "₱1,000 in" and the field |
| 9 | The row being edited has a Brass edge | count-up | Only the field has focus |
| 10 | A transfer is a card: payer left, amount in the middle over a Brass arrow, payee right, then a status line and the action | settle-up | One line: "Jun → Trina ₱200", then "Not paid" and Mark paid |
| 11 | A ledger table: Player, In, Out, Net, with a footer row | settle-up | Recap rows put "₱1,000 in · ₱2,000 out · 1 buy-in · under 1 min" in one wrapping line (see `now_recap.png`) |
| 12 | A share card that shows the summary text with Copy and Get card | settle-up | One "Share results" button |
| 13 | A recap head card: outstanding amount with a Pending badge, and three fact tiles | settle-up | "Still to pay" figure and fact lines |
| 14 | Home group card: a group icon, a line under the name, and an "8 active players" pill beside the chips | home | Chips with "+7" and a Host outline |
| 15 | Home "To settle" rows carry the other player's chip and a status line | home | Ruled rows with words only |
| 16 | Home record as three tiles (Sessions, Win rate, Avg net) and a Last session row with a "Top winner" tag | home | Ruled rows |
| 17 | Log in and Join with invite as two tabs on top of the form | front door | "No account? Sign up" link under the form |
| 18 | A quiet "No active set · Last played Oct 24" panel for a group with nothing in play | home | "Last session Oct 9 · Did not play" |

## Finding 3: what the concepts invent

These parts show features or claims that PokerNights does not have. Some break product rules. Do not build them.

- **Bottom tab bar** (Table, Clock, Ledger, Split, Config). There is no blind clock, and these tabs do not match the app's pages. The group page already has four tabs.
- **Blind levels, rounds, "08:42 left" and a level progress bar.** The app has a set timer, not a blind clock.
- **"In stack" during play.** The app does not know a player's stack during play. It knows what they bought in.
- **Money in play on Your groups.** PRODUCT rule: Your groups does not show money still in play, because it does not refresh by itself.
- **Two buttons on every player row (Rebuy and Cash out).** The set page addendum (2026-10-09) puts cash-out behind a tap on the row so that a table of six fits one screen.
- **"BUSTED" badge on a count of 0.** The recap rule says losses are never called out.
- **"Night high-roller" on felt.** Felt marks only a running set. A top result can use the finale's Brass edge on Rail 2.
- **The front door "code" cards** ("Zero real money held", "3 AM book balancing", "offline resilient", "Ledger core: active & encrypted") and a version pill. PRODUCT bans invented claims. The app has no offline mode.
- **Schedules, RSVPs, "Seat ID", "Pay via GCash", "Rake pool (5%)" as a fixed figure, "Shared food pool".** None of these exist.
- **The "Physical chip calculator" with three fixed chips.** The app has its own chip calculator with host-chosen colours ([ADR 0004](../adr/0004-session-chip-values.md)). Keep it.

## Finding 4: earlier decisions that the concepts touch

- **Ruled rows** (DESIGN.md, Slice E, 2026-11-01): "A set in play is the only blue card. The rest are ruled rows." Idea 4 reverses this. It needs the human's choice.
- **Collapsible host dock** (2026-10-04): idea 6 changes what the collapsed dock shows. The dock still collapses.
- **Description on Sign up only** (front door second pass, 2026-10-17). Idea 17 keeps that. A tagline pill on Log in would undo it. Do not add the pill.
- **Accepted Change Rule.** A net figure on a count row (idea 8) must come from an accepted count or cash-out. A typed count that is not confirmed gives no net, or a net labelled as a preview.
- **One running total always in view** at count-up. Idea 7 adds a panel at the top. The dock total stays.

## Finding 5: risk

Many browser probes read the DOM of these screens: `pot.mjs`, `overture.mjs`, `chip_pot.mjs`, `finale.mjs`, `home.mjs`, `count_flow.mjs`, `door.mjs`, `sheet_drag.mjs`, `mobile_motion.mjs`, `motion.mjs`, `arrivals.mjs`. The pot figure, the In play badge (the overture's ring origin), the row tokens (chip-to-pot targets) and the name that travels between screens must keep their element IDs and classes. Each slice runs the probes for its screen.

A restyle can fail safe: it changes templates and CSS only. It records nothing new. No model, service or migration changes, except where a slice reads a figure that a service already gives.

## Recommendation

Build the 18 ideas as six slices, one per screen, plus a shared first slice: section labels, the inset fact grid, the Rail card row and the status pill. Leave out everything in Finding 3. Ask the human about ideas 4, 6, 16 and 17 before the plan is approved.

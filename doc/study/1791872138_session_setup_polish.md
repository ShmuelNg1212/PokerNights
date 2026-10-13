# Session setup polish: study

Date: 2026-10-13, Asia/Manila.

## Request

The human said: "can you refine the session setup UI using impeccable to polish out any misalignments and awkward elements. start studying and planning."

## Scope studied

The path a host walks from "New session" to a set that is ready to open:

1. **New session** (`templates/games/session_form.html`).
2. **Set settings** (`settings_form.html`), which shares the Game, Stakes and Rake parts with New session.
3. **The draft set**: "Get this set ready" and what surrounds it (`templates/web/session.html` and its parts).
4. **Add players** (`add_players.html`), reached from step 1 of the draft set.

The seat draw, the opening buy-ins and everything from Start onward are outside this study.

## Method

Impeccable, polish playbook: refinement, not redesign. The Rack in DESIGN.md is the visual authority. Mode: Operate.

- A temporary database seeded with `web/tests/browser/seed.py` plus two presets, served locally, driven by headless Chrome as host `hana`.
- Full-page captures at 390 px and 1280 px, with reduced motion on. Seven are kept in [the assets folder](1791872138_session_setup_polish_assets/).
- Every visible label, field, hint and button on each page was measured (left, top, right, bottom, font size and weight). The figures below are CSS pixels at 390 px unless a width is given.
- No earlier critique of these pages is stored. The 2026-10-04 session form cycle ([plan](../plan/1791121411_session_form.md)) and the rake controls cycle ([plan](../plan/1791096125_rake_controls.md)) built what is here.

Not done: a real phone, a screen reader, the in-app numpad open over these fields, a group with no table or no preset, a chips game.

## What is sound and stays

- One 16 px left edge and one 374 px right edge for every field, label and button on all four pages. No field is off the grid.
- Every control is 48 px high. Paired fields (blinds, buy-in limits) share tops and bottoms exactly.
- The group rhythm on New session is regular: 41 px from the last field of a group to the next title, 12 px from a title to its first label, 4 px from a label to its field, 12 px between fields.
- The refusal state keeps typed values, marks the field and puts the message under it.
- At 1280 px the form is one 600 px column, with Poker variant and Unit side by side. Nothing stretches.

## Findings

Each is classified as the polish playbook asks: **local defect** (simply inconsistent), **one-off** (a shared pattern exists and is not used), or **awkward** (works, but reads or behaves oddly; changing it changes words or behaviour and so needs a decision).

### New session and Set settings

| # | Finding | Evidence | Class |
| --- | --- | --- | --- |
| N1 | The "Rake per buy-in" title is lighter than the other three group titles. | 17 px / weight 600 against 17 px / 650. Cause: `.rake-settings legend { font-weight: 600 }` (app.css line 133) overrides `.group-title`. | Local defect |
| N2 | The Rake hint touches the first choice; the Stakes hint does not touch its first field. | Rake hint bottom 1446, "Off" row top 1446: 0 px. Stakes hint to "Small blind": 12 px. | Local defect |
| N3 | The preset row is the only block that is not a group. It has a field label where the others have a title, no rule above the next block, and a larger gap under it. | 60 px from the preset field to "When and where"; 41 px between all other groups. | One-off |
| N4 | The choices Off, Flat amount and Percentage are set in a lighter weight than every other piece of text on the page. | `.check` is weight 400; body text and fields are 500, labels 600. | Local defect |
| N5 | About 136 px of empty page under "Create session", and the same under "Save settings". | Button bottom 1923, page bottom 2059. No dock or bar sits there on a form page. The cause is to be found in the build. | Local defect |
| N6 | Choosing a preset is two taps and a page load, and it throws away what was typed. | The preset form is a separate GET form. `session_new` builds the form from the preset alone, so a typed Location, a changed Date or a changed Table are lost on "Use". | Awkward |
| N7 | Both rake value fields show under every choice. With Off chosen the host still reads "Flat amount per buy-in", a 0, "Percentage (%)" and two hints that each start by saying which choice they belong to. | 250 px of the 390 px page (1602 to 1851) is fields that do not apply to the default choice. Flat shows `0`; Percentage shows nothing. PRODUCT.md records "Both value fields stay visible" as a decision of 2026-10-04, made so the form works without JavaScript. | Awkward |
| N8 | The Stakes hint repeats the Unit hint three lines above it. | "Pesos: amounts are money. Chips: amounts are chip counts with no peso value." then "Type each amount in pesos, or in chips for a chips game." | Awkward |
| N9 | Set settings opens with a sentence set larger and brighter than every hint on the page, and a "Game" group that holds one field. | Intro 16 px against hints at 13.6 px. | One-off |

Looked at and left alone: the Date field shows the date the way the phone's own language setting writes it (10/13/2026 in the capture), while the app writes "Tue, Oct 13". It is the phone's date control; replacing it would lose the phone's date picker.

### The draft set

| # | Finding | Evidence | Class |
| --- | --- | --- | --- |
| D1 | Step 2, "Stakes and rake", carries a tick and a button that says "Choose rake". It reads as done and as waiting at once. | The mark announces "Done:"; the button names a choice not yet made. | Awkward |
| D2 | Step 2's line breaks in the middle of a phrase: "₱10 / ₱20 · buy-in ₱500 to" then "₱2,000 · rake off". | The line is 197 px wide beside a 109 px button. It breaks the same way at 1280 px, where the panel is no wider. | Local defect |
| D3 | The two step buttons are different widths, so the text beside them ends at a different place on each row. | "Add" 53 px, "Choose rake" 109 px; text column ends at 309 and 253. | Local defect |
| D4 | With no players, the page says "Players" twice and offers adding them three times. | Step 1 "Players · Nobody yet" with "Add"; the Players section "0 · 9 seats free" and "No players yet. Add players to start buy-ins."; the dock's main button "Add players". A fourth, "Or add one player", is under More host controls. | Awkward |
| D5 | The empty Players section is loose. | 32 px between "0 · 9 seats free" and the sentence under it; 12 px is the page's gap elsewhere. | Local defect |
| D6 | On a phone the dock's arrow sits below the line of "Host controls". | Seen in the capture; about 6 px low. To be measured in the build. | Local defect |
| D7 | At 1280 px "More host controls" is larger than on a phone, and "Full set log" sits alone in the middle of the page, far from everything. | 16 px against 13 px for the same control; the link is centred under two columns that are both left-aligned. | Local defect |

### Add players

| # | Finding | Evidence | Class |
| --- | --- | --- | --- |
| A1 | "Choose from the roster" has a larger gap under it than "Add a new player" has. | 52 px against 40 px from title to first label. | Local defect |
| A2 | The page has two main buttons, and the rarer task comes first. | "Add new player" and "Add players" are both the bone primary button. Most players at a table are already on the roster. | Awkward |
| A3 | Roster rows are loose next to the set page's rows. | Each player takes 73 px (a 48 px row and 25 px between rows). Nine players need 650 px. | Local defect |
| A4 | The roster's choices use the lighter weight of N4. | Same `.check` rule. | Local defect |

## What this is not

Nothing found is broken: every task on the path can be completed, no figure is wrong, no control is too small to tap. The path's order, its words about money, and what each step records are sound. This is a finish pass. No finding calls for a new colour, font, token or picture.

## Options

| Option | For | Against |
| --- | --- | --- |
| A. Fix the local defects and one-offs only (N1–N5, N9, D2, D3, D5–D7, A1, A3, A4) | No word and no behaviour changes; nothing to decide | The four things a host is most likely to call awkward stay: the preset reload, the rake fields, the ticked step that says "Choose", the three ways to add players |
| B. A, and the awkward items, each as a separate decision (N6, N7, N8, D1, D4, A2) | Addresses what the request names | N7 revises a recorded decision; each item changes a word or what a tap does |
| C. Redesign the form as steps or a sheet | — | Not polish. The form's order and grouping are sound |

Recommended: B, built in two stages so stage 1 can be accepted by itself.

## 2026-10-13 addendum

- **N2 is withdrawn.** The Rake hint's box touches the first choice's box, but a choice is a 48px row with a 24px mark in its middle, so the eye already sees 12px between the hint and the mark, the same as under the Stakes hint. Nothing was changed.
- **N5, cause found.** Every page has 96px under its content, and the form added 40px of its own. Form pages now end 48px under the last button.
- **D1.** The button already read "Change" once rake was chosen; it read "Choose rake" only while rake was off and could still be chosen. It now always reads "Change".
- **D6, cause found.** The dock's bar is a grid whose two rows shared its spare height, so the arrow was centred on a taller box than the title's.
- The human confirmed the scope: the four screens.
- The human approved all six decisions and added one request: movement when "More host controls" opens. It is stage 3 of the plan.

# New session form revamp: plan

Status: approved 2026-10-04 ("approved. i dont need a separate branch for a private preview." Decision 4: release to production and fix forward). Date: 2026-10-04, Asia/Manila. Study: [New session form revamp](../study/1791121357_session_form.md).

## Outcome

Every input on New session and Set settings lines up on the same left and right edges at the same height, on an iPhone as elsewhere, and the form reads as four short groups instead of one list of 15 controls.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new colour, font or asset. No change to what the form saves.

## Design brief

**Job and audience.** A host setting up tonight's game on a phone, usually accepting most preset values and changing one or two.

**Layout, top to bottom.**

1. Back link and the heading "New session".
2. "Start from a preset" with its Use button, as today, when the group has presets.
3. **When and where.** Table. Date. Location.
4. **Game.** Poker variant and Unit side by side. The unit help under the pair.
5. **Stakes.** The line "Type each amount in pesos, or in chips for a chips game." Small blind and Big blind side by side. Minimum and Maximum buy-in side by side. Usual buy-in, full width, with its help.
6. **Rake per buy-in.** The three choices, then Flat amount and Percentage, both visible as approved.
7. The full-width Create session button.

Each group has a small heading and a hairline rule above it. A pair sits in two equal columns with the labels on one line and the inputs on one line; help and errors go under their own input without moving the partner. Below 360 px a pair stacks.

**Set settings** gets the same Game, Stakes and Rake groups (it has no table, date or location). The preset form gets the same Game and Stakes groups.

**Alignment rules, applied to every form in the app through the shared stylesheet.**

- Text fields, the date field and dropdowns share one box: full width, 48 px high, 12 px text inset, 16 px text.
- **Date field on iPhone.** The native appearance is switched off and the box is stated explicitly, so it stretches to full width, keeps 48 px when empty and left-aligns its value. Tapping it still opens the iPhone date picker.
- **Dropdowns** lose the browser-drawn style and get the app's own chevron at the same distance from the right edge as other icons, with the same 12 px text inset as typed text.
- **Radios and the rake legend** start on the same left edge as the fields.

**States and ranges.** Empty; filled from a preset; every field refused at once; one field of a pair refused; long table names in the dropdown; a locked unit and rake on Set settings; pesos and chips; 320, 390 and 1280 px; keyboard only; no JavaScript.

## What I cannot verify

The Date field problem exists only in Safari's engine on an iPhone. This machine has Chrome only, which does not reproduce it. I will write the standard fix and prove in Chrome that nothing regresses, but **whether the Date field lines up on your iPhone is something only you can confirm**. The plan therefore ends with a preview link for you to open on your phone before the change goes to production.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **Group names:** "When and where", "Game", "Stakes", "Rake per buy-in".
2. **Pairs:** Poker variant | Unit, Small blind | Big blind, Minimum | Maximum buy-in. Everything else is full width.
3. **Dropdowns get the app's own arrow** on every form, not only this one. Recommended, so all forms match.
4. **Check on your iPhone before release.** Recommended: I push the branch (not `main`), Vercel builds a private preview, and you open it on your phone. Preview links need your Vercel login. The alternative is to release straight to production and fix forward if the Date field is still off.

## Implementation

1. **CSS (`app.css`).**
   - Extend the shared field rule: `appearance: none`, `min-width: 0`, `display: block`, a fixed line height, `text-align: left`.
   - `input[type=date]`: `::-webkit-date-and-time-value { text-align: left; }` and a minimum height that holds when empty.
   - `select`: own chevron as a background image built from the existing Lucide path, right inset, 12 px left inset; disabled state.
   - Radios: margin reset. `fieldset` and `legend`: padding reset.
   - `.form-group` (heading, rule, spacing) and `.field-pair` (two-column grid, start-aligned, stacking below 360 px).
2. **Templates.**
   - `games/session_form.html`, `games/settings_form.html`, `games/preset_form.html`: render the groups by field name with a small `partials/field.html` for one field (label, control, help, error, same ids as today).
   - `games/_rake_fields.html`: the group heading replaces the bare legend; the `fieldset` stays for the radios.
   - `partials/form_fields.html` is unchanged for every other form.
3. **Forms (`games/forms.py`).** No field, name or validation change. The one-line amount help moves from the template top into the Stakes group.
4. **Tests first.**
   - `games/tests`: the three pages render every field once, in the group order; pairs are in `.field-pair`; ids, `for` attributes and `aria-describedby` still match; a refused form keeps typed values and shows each error under its field; Set settings with money shows the locked unit and rake; creating a session through the page saves the same values as before.
   - Browser check `session_form.mjs` on a fresh temporary database at 320, 390 and 1280 px, for New session, Set settings and a preset: every text field, date field and dropdown shares the same left edge, right edge and height; the two inputs of each pair share one top edge, including when one has an error; radios and legends share the fields' left edge; text is 16 px; no overflow with a long table name; 48 px targets; keyboard order follows the visual order; submission without JavaScript; the preset chooser still fills the form.
   - Run `rake.mjs`, `rake_controls.mjs` and `rake_extra.mjs`, which drive these forms.
5. **Verify.** SQLite and PostgreSQL suites; the browser checks; captures inspected in Chrome.
6. **iPhone check.** Push the branch for a Vercel preview and give the human the address and what to look at: Date field width, height, text alignment, and the dropdowns.
7. **Sync docs.** DESIGN.md addendum (form groups, pairs, the shared field box), wiki features, a footgun page on the iOS date input, browser README, TODO.

## Acceptance criteria

- AC1. On New session, Set settings and the preset form, every text field, date field and dropdown has the same left edge, right edge and height at 320, 390 and 1280 px in Chrome.
- AC2. The human confirms the Date field lines up on their iPhone.
- AC3. The controls appear in the four groups, with the three pairs side by side from 360 px.
- AC4. The form saves exactly what it saved before; the rake rules behave as approved.
- AC5. Every other form in the app still renders with aligned fields.
- AC6. Existing tests pass on SQLite and PostgreSQL.

## Out of scope

- A multi-step form, or hiding the rake value fields behind the chosen option.
- A custom date picker. The iPhone's own picker stays.
- Changing which fields exist, their defaults or their validation.
- The Add players screen.

## Rollback

Revert the feature commit. No migration and no data change.

## Progress and blockers

2026-10-04: Study and plan complete after one discovery round (iPhone; the Date field; regroup and align). The human approved and declined the private preview, so decision 4 is: release to production and fix forward.

2026-10-04 execution on `feat/session-form`, tests first.

Changes from the plan:

1. **Poker variant | Unit pair only from 480px.** At 390px the value “No-Limit Hold'em” was cut off in a half-width dropdown. The two blinds pairs keep the 360px threshold.
2. **Duplicate error ids removed in three shared partials.** Each field error had the same id on its wrapper and on Django's error list. Found by a layout test. The wrapper lost the id; the list keeps it.
3. **The amount hint is one line in the Stakes group**, reworded to “Type each amount in pesos, or in chips for a chips game.”

2026-10-04 verification:

- 595 tests pass on SQLite (ten PostgreSQL-only skips) and all 595 on local PostgreSQL 17, started for the run and stopped after. Six new tests in `games/tests/test_form_layout.py`, including that New session saves the same values.
- `session_form.mjs`: 69 of 69. `dock.mjs` 145, `archive.mjs` 85, `entry.mjs` 81 and `settled.mjs` 24 still pass, which covers the other forms that share the field box. `rake_controls.mjs` passes 25 of 25. `rake.mjs` and `rake_extra.mjs` stop at the same point with the same counts on unmodified `main` (stale scripts, already listed in TODO).
- Captures inspected at 320, 390 and 1280px, empty and refused.

**Not verified: the Date field on an iPhone.** No browser here reproduces it. AC2 is open until the human looks. Also not verified: a screen reader.

AC1 and AC3 to AC6 are met. Documentation synced: DESIGN.md, wiki features, the new footgun page, browser README, TODO.

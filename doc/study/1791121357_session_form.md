# New session form revamp: study

Date: 2026-10-04, Asia/Manila. Captures of the current form: [1791121357_session_form_assets/](1791121357_session_form_assets/).

## Request

The human asked to revamp the New session screen because some form inputs are misaligned.

## Discovery answers (2026-10-04)

1. **Where.** On an iPhone (Safari or Chrome; both use Safari's engine there).
2. **Which input.** The Date field.
3. **How far.** Regroup and align: fix every alignment problem, organise the controls into titled groups with short pairs side by side, and apply the same to Set settings.

## What exists today

`templates/games/session_form.html` renders one column of 15 controls from `SessionForm`: Table, Date, Location, Poker variant, Unit, Small blind, Big blind, Minimum buy-in, Maximum buy-in, Usual buy-in, three rake radios, Flat amount, Percentage. An optional "Start from a preset" chooser sits above. On a 390 px phone the page is about 1,900 px tall. `settings_form.html` (Set settings) and `preset_form.html` render the same stakes fields through the same partial.

All text fields, selects and the date field share one rule (`app.css`, "Forms"): `width: 100%; min-height: 48px; padding: 8px 12px`.

## The Date field on an iPhone

`game_date` is `<input type="date">`. iOS Safari draws a date input as its own control and ignores part of the shared rule:

- it keeps an intrinsic width, so `width: 100%` does not stretch it and it ends short of the other fields;
- its value is centred, while every other field is left-aligned;
- with no value it is shorter than a text field.

This is the misalignment the human sees. It does not appear in Chrome on a computer or on Android, where the captures show the Date field at the same 358 × 48 px as its neighbours.

The usual remedy is to switch off the native appearance and state the box explicitly (`appearance: none`, `min-width: 0`, `display: block`, a fixed line height, and `::-webkit-date-and-time-value { text-align: left }`). The native date picker still opens on tap.

**This cannot be verified here.** The machine has Chrome only. Headless Chrome with phone emulation does not reproduce Safari's date control. The fix can be written and checked for no regression in Chrome; whether it lines up on an iPhone is confirmed only by the human on their phone.

## Other misalignments found in Chrome

Measured at 390 px (fields start at x = 16):

- **Rake radio buttons start at x = 21.** The browser's default radio margin pushes them 5 px right of the field edge.
- **The "Rake per buy-in" legend is 2 px right** of the labels, from the legend's default padding.
- **Dropdown text is 3 px further in than typed text** (browser default select padding on top of the shared 12 px).
- **Dropdown arrows and the date icon are browser-drawn** and sit at different distances from the right edge. On an iPhone, selects are also drawn in Safari's own style.
- **Help text and errors lengthen single fields unevenly**; in a side-by-side pair this would push one input lower than its partner unless the pair is aligned on the inputs.

## Constraints

1. **Rake rules stay as approved** (PRODUCT.md, "rake setup controls"): Off, Flat amount and Percentage as native choices; both value fields stay visible; only the chosen rule's value validates; refused submissions keep the choice and typed values.
2. **Server behaviour is unchanged.** Field names, validation, the preset chooser (a GET form), `preset_id`, and what `create_session` receives.
3. **Shared templates.** `partials/form_fields.html` is used by many forms. `games/_rake_fields.html` is shared by New session and Set settings. Set settings can lock the unit and rake (disabled fields with a changed help text).
4. **Design rules.** Single column on phones, 48 px targets, visible focus, labelled controls, errors beside their field (AGENTS.md rule 9, DESIGN.md). A pair of short fields side by side is still one column of groups; below 360 px pairs must stack.
5. **No JavaScript needed** for the form to work.
6. **Tests and scripts.** `games/tests`, `web/tests/test_rake.py`, `test_remaining_design.py` and the rake browser scripts address fields by `name` and submit with `form.form-section button`. Names and that form class must stay.
7. **Font size.** iOS zooms the page when a focused field's text is under 16 px. The shared rule inherits 16 px; it must stay.

## Options for the layout

- **A. Titled groups with pairs (chosen by the human).** Four groups under small headings: When and where; Game; Stakes; Rake per buy-in. Pairs: Poker variant | Unit, Small blind | Big blind, Minimum | Maximum buy-in.
- **B. Align only.** Declined.
- **C. A multi-step form.** Not asked for; more taps for a host who usually accepts the preset values.

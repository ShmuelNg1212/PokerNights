# Chip value presets and in-app keys: study

Date: 2026-10-28. Mode: mixed.

## Request

1. Chip value and chip quantity fields must use the app's own number keys, not the phone keyboard.
2. A group must be able to save chip denomination presets. A host then fills a session's chip values from a preset.

## Evidence: number keys

- `static/js/numpad.js` serves only `input[data-numpad]`. It switches the phone keyboard off with `inputmode="none"` when its keys exist. Other fields keep the phone keyboard.
- The setup value field has only `inputmode` (`games/chip_views.py:22`). It has no `data-numpad`.
- The quantity field has only `inputmode="numeric"` (`templates/ledger/_chip_count_form.html:14`). It has no `data-numpad`.
- A field inside a `dialog` needs a `[data-numpad-slot]` in its form (`numpad.js` `served()`). The chip count form has no slot, so in the count sheet the keys would not show even with the marker.
- The `chips` rule accepts 0 to 12 digits up to `MAX_AMOUNT`. That is the same limit as a quantity in `games/chips.py`. The `whole` rule allows only 2 digits, so it does not fit quantities.
- `denominations.js` recalculates on `input` events. The keys send `input`, so the preview keeps working.
- This change stays in templates, one form widget and one numpad rule. It fits one commit.

## Evidence: presets

- `SettingsPreset` (`games/models.py:63`) is the group's stakes preset. It has a name, a unit and an archive marker. A session copies it; a later edit changes no session. Hosts manage it on the group settings page (`templates/web/_group_settings.html:224`) through `save_preset` (`games/services.py:79`).
- A session's chip values are a JSON list on `GameNight` (`games/models.py:146`). `chips.denominations()` validates them. `set_chip_values()` (`games/services.py:1281`) is the only writer. It checks host role, closed state, lock, revision and `request_id`.
- ADR 0004 excludes presets and automatic reuse from its first scope. It states that a new session starts without assignments. A preset that the host applies by choice does not conflict with this. An automatic default would need an ADR change.
- A value is in the session unit. Nothing converts pesos and chips. A preset must store its unit, and only a preset with the session's unit can apply.

## Proposed shape

A group owns zero or more chip presets. Each has a name, a unit and 1 to 12 denominations, validated by the same `chips.denominations()` rule. Hosts create, edit and archive them. All members can read them.

On the session's Chip values page, a host can choose a preset with the session's unit. Choosing it fills the form. Nothing saves until the host selects Save. The save runs through `set_chip_values()`, so all existing checks stay in force. The host can also save the session's current values as a new preset.

A session copies the values. A later preset edit or archive does not change any session. This is the same rule as stakes presets.

## Design brief

Group settings gets a Chip presets section below Presets. Each row shows the name, a Chips badge for a chips unit, and a line of swatches with values. A host opens a page with the same row editor as the session's Chip values page.

The session's Chip values page shows "Start from a preset" above the rows when a matching preset exists. Use a select and a Fill button that works without JavaScript. With JavaScript, filling replaces the rows in place. Show which preset filled the form. Keep "Save as a group preset" as a quiet action below Save.

Use the app's number keys for every value and quantity field. In the count sheet, put the key slot below the total so the total stays in view. Use DESIGN.md tokens, 48 px targets and existing motion presets only.

## Risks

- A preset edit must not change a session. Copy, never reference.
- A preset with the wrong unit would change meaning. Filter and validate by unit on the server.
- Two hosts can save at once. Preset saves are not money writes, but names must stay unique among active presets.
- A long preset list on a phone. Keep one select, not a list of buttons.

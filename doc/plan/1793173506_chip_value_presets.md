# Chip value presets: plan

Date: 2026-10-28. Mode: mixed. Status: approved 2026-10-28; executing on `feat/chip-presets`.

Study: [chip value presets and in-app keys](../study/1793173506_chip_value_presets.md).

The in-app keys for chip fields fit one commit. They run separately on `feat/chip-numpad`. This plan covers presets only. Stack its branch on `feat/chip-numpad`.

## OPEN QUESTIONS

None. The human approved the defaults on 2026-10-28:

1. The host chooses a preset on the session's Chip values page. It fills the form. The host saves. No automatic default; ADR 0004's empty start stays.
2. The Chip values page has "Save as a group preset".
3. Hosts manage presets. All members can read them.
4. Chip presets are not linked to stakes presets.

## Acceptance criteria

1. A host can create, edit and archive a chip preset in the group. Players can read it. Players cannot write it.
2. A preset holds a name, a unit and 1 to 12 denominations under the same rules as session chip values.
3. A host can fill a session's chip values from a preset with the same unit. Nothing saves until the host saves.
4. A preset of the other unit is not offered, and the server refuses it.
5. A later preset edit or archive does not change any session.
6. The existing session lock, revision, request ID and closed-session checks still apply to the save.
7. Every flow works without JavaScript. Every value field uses the in-app keys.

## Tasks

- [ ] **1. Store and save chip presets. `tests: first`.**
  - Add `ChipPreset` in `games`: group, name (60), unit, values (JSON), archived_at, created_at. Name is unique among active presets in a group.
  - Add `save_chip_preset(actor, data, preset_id=None)` and `archive_chip_preset(actor, preset_id)` in `games/services.py`. Require host. Validate values with `chips.denominations()`. Resolve the preset through the actor's group; a miss is a `RuleError`. Call `audit.record()`.
  - Add `chip_presets_for(group, unit)` as a query.
  - Cover validation, duplicate names, group isolation, player refusal and archive.
  - **Complete when:** service tests pass and migrations check clean.

- [ ] **2. Fill a session from a preset. `tests: first`.**
  - On the Chip values page, a host posts `intent=preset` with a preset ID. The view resolves the preset through the actor's group and the session unit. It fills the formset. It does not save.
  - The save stays `set_chip_values()`. Record the preset name in that audit entry's data when the form came from a preset.
  - Add `intent=save_preset` with a name. It validates the form rows and calls `save_chip_preset()`. It does not change the session.
  - Cover the wrong unit, another group's preset, an archived preset, a locked session and a later preset edit that leaves the session unchanged.
  - **Complete when:** a filled and saved session holds a copy of the preset values, and all refusals return without a write.

- [ ] **3. Screens. `tests: alongside`.**
  - Group settings: add a Chip presets section below Presets. Show name, unit badge and swatches with values. Hosts get New and Edit links.
  - Add a preset page with the same row editor (`_chip_value_row.html`, `denominations.js`), a name field, a unit choice and Archive.
  - Session Chip values page: show "Start from a preset" when a matching preset exists. Use a select and a Fill button. With JavaScript, fill in place and keep focus on the first value. Show "Filled from {name}". Add "Save as a group preset" below Save.
  - Use `data-numpad` on every value field. Follow DESIGN.md. Use existing motion presets only.
  - Probe at 320, 390 and 1280 px: create a preset, fill a session, save, count by chips. Check 48 px targets, no sideways scroll, keyboard focus and no JavaScript.
  - **Complete when:** a signed-in host goes from an empty group preset list to a chip-based count that uses preset values.

- [ ] **4. Rendezvous and sync docs. `tests: alongside`.**
  - Run the SQLite and PostgreSQL suites, `code-review` and `security-review` (host role and group isolation change).
  - Run `/impeccable critique` on the two new screens.
  - Add ADR 0005 for presets. Update GLOSSARY.md, spec.md, features.md and DESIGN.md. Update TODO.md phone checks. Run `graphify update .`.
  - **Complete when:** checks pass and the docs match the code.

## Verification record

Not started.

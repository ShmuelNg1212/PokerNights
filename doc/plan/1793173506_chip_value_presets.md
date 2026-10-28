# Chip value presets: plan

Date: 2026-10-28. Mode: mixed. Status: verified 2026-10-28 on `feat/chip-presets`; awaiting ship. Frozen after rendezvous.

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

- [x] **1. Store and save chip presets. `tests: first`.**
  - Add `ChipPreset` in `games`: group, name (60), unit, values (JSON), archived_at, created_at. Name is unique among active presets in a group.
  - Add `save_chip_preset(actor, data, preset_id=None)` and `archive_chip_preset(actor, preset_id)` in `games/services.py`. Require host. Validate values with `chips.denominations()`. Resolve the preset through the actor's group; a miss is a `RuleError`. Call `audit.record()`.
  - Add `chip_presets_for(group, unit)` as a query.
  - Cover validation, duplicate names, group isolation, player refusal and archive.
  - **Complete when:** service tests pass and migrations check clean.

- [x] **2. Fill a session from a preset. `tests: first`.**
  - On the Chip values page, a host posts `intent=preset` with a preset ID. The view resolves the preset through the actor's group and the session unit. It fills the formset. It does not save.
  - The save stays `set_chip_values()`. Record the preset name in that audit entry's data when the form came from a preset.
  - Add `intent=save_preset` with a name. It validates the form rows and calls `save_chip_preset()`. It does not change the session.
  - Cover the wrong unit, another group's preset, an archived preset, a locked session and a later preset edit that leaves the session unchanged.
  - **Complete when:** a filled and saved session holds a copy of the preset values, and all refusals return without a write.

- [x] **3. Screens. `tests: alongside`.**
  - Group settings: add a Chip presets section below Presets. Show name, unit badge and swatches with values. Hosts get New and Edit links.
  - Add a preset page with the same row editor (`_chip_value_row.html`, `denominations.js`), a name field, a unit choice and Archive.
  - Session Chip values page: show "Start from a preset" when a matching preset exists. Use a select and a Fill button. With JavaScript, fill in place and keep focus on the first value. Show "Filled from {name}". Add "Save as a group preset" below Save.
  - Use `data-numpad` on every value field. Follow DESIGN.md. Use existing motion presets only.
  - Probe at 320, 390 and 1280 px: create a preset, fill a session, save, count by chips. Check 48 px targets, no sideways scroll, keyboard focus and no JavaScript.
  - **Complete when:** a signed-in host goes from an empty group preset list to a chip-based count that uses preset values.

- [x] **4. Rendezvous and sync docs. `tests: alongside`.**
  - Run the SQLite and PostgreSQL suites, `code-review` and `security-review` (host role and group isolation change).
  - Run `/impeccable critique` on the two new screens.
  - Add ADR 0005 for presets. Update GLOSSARY.md, spec.md, features.md and DESIGN.md. Update TODO.md phone checks. Run `graphify update .`.
  - **Complete when:** checks pass and the docs match the code.

## Verification record

Verified 2026-10-28 on `feat/chip-presets`, stacked on `feat/chip-numpad`. No merge or push.

- **Tests first:** service and page tests were written before each slice and failed first. They cover validation, case-insensitive names, group isolation, player refusal, archive, request replay, late retries, wrong unit, archived and foreign presets, locked sessions and copies that later edits do not change.
- **SQLite:** `DEBUG=True .venv/bin/python manage.py test --noinput --parallel 1`. All tests pass, 17 PostgreSQL-only skips. Log: `/private/tmp/pn-chip-presets-sqlite.log`.
- **PostgreSQL:** `DATABASE_URL=postgres://localhost:5432/pokernights DEBUG=True .venv/bin/python manage.py test --noinput`. 1,459 tests pass. Log: `/private/tmp/pn-chip-presets-postgres.log`.
- **Schema:** `makemigrations --check --dry-run` reports no changes.
- **Browser:** `node web/tests/browser/chip_presets.mjs` after `seed_chip_presets.py`, with emulated touch. 34 of 34 checks pass. The flow starts at an empty Chip presets section. It creates a preset with the number keys, fills a session in place, saves, and a player sends a chip count of ₱100 from the preset's values. It also checks a chips session, Save as a group preset with Enter, a fill and save without JavaScript, the player's read-only view and no sideways scroll at 320, 390 and 1280 px. Captures: `/private/tmp/pn-chip-presets-review/`.
- **Code review (`code-review`, medium):** nine findings, all fixed. Each preset write now has a `ChipPresetChange` row with a unique request ID, so archive after an edit and a late retry of an older edit behave correctly. Names compare without case. The session audit names a preset only when the rows equal it. A locked session keeps its rows after Save as a group preset. Preset errors show beside their control. Tests cover each fix.
- **Security review:** no findings at confidence 8 or above. It checked host role, foreign preset IDs, foreign request IDs, XSS through names and labels, CSRF and injection.
- **Fix rounds:** round 1 changed the browser probe to focus the Unit select before a change, as a tap does; the page was correct. Round 2 fixed the review findings. Every recheck passed.
- **Design:** captures show the picker, settings list and preset page at 320, 390 and 1280 px. The preset page's first row got spacing from the unit hint.
- **Deviation:** after Fill, focus stays on Fill and the note announces the result. Focus on a value field would open the number keys over the rows the host must check.
- **Open item:** an "Uncaught (in promise)" page error appeared in 2 of about 8 browser runs on this branch and on `feat/chip-numpad`. The fill code's motion promises handle rejection. The source is not found. Later runs were clean.
- **Docs:** ADR 0005, GLOSSARY.md, spec.md, features.md, architecture.md and DESIGN.md match the code. TODO.md has the phone check.

# 0005: A group can save chip presets that a session copies

Date: 2026-10-28. Status: accepted. Plan: [chip value presets](../plan/1793173506_chip_value_presets.md). Extends [ADR 0004](0004-session-chip-values.md).

## Context

A group often plays with the same chip set. Entering the same chip values for each session takes too much effort. The human approved group chip presets and chose the defaults in the plan.

## Decision

- A group owns zero or more chip presets. Each has a name, a unit and 1 to 12 denominations. The session chip-value rules validate them.
- Hosts create, edit and archive presets. All members can read them. Active preset names are unique in a group, without regard to capitals.
- A host fills a session's Chip values form from a preset of the session's unit. Nothing saves until the host saves. The save uses `set_chip_values()`, so the lock, revision and request rules of ADR 0004 still apply.
- A session copies the values. A later preset edit or archive changes no session.
- A new session still starts without chip values. No preset applies automatically. [ADR 0008](0008-new-session-options.md) adds one exception: a host can select a preset on New session.
- A host can save a session's values as a new preset. This changes no session.
- A chip preset is not linked to a stakes preset.
- Each preset write has a `ChipPresetChange` row with a unique request ID. A repeated or late request writes nothing.

## Consequences

Presets of the other unit are not offered and the server refuses them, because nothing converts pesos and chips. The session audit names a preset only when the saved rows equal its values.

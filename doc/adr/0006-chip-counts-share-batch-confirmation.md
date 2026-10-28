# 0006: Chip counts share the final-count confirmation

Date: 2026-10-28. Status: accepted. Plan: [batch chip confirm and rack](../plan/1793185391_chip_count_batch_and_graphic.md). Extends [ADR 0004](0004-session-chip-values.md).

## Context

The host needs to collect chip counts and typed amounts before confirming the set's counts. The human approved a shared confirmation and a drawn chip rack.

## Decision

- The inline chip sheet fills the player's count field. It keeps quantities and the chip-value revision with that draft.
- The host confirms chip counts and typed amounts in one atomic batch. A refusal saves no count and keeps the drafts.
- The server calculates each chip total. It refuses a typed amount that differs from that total and names the player.
- Each accepted chip count writes its breakdown and a new count version, even when its total did not change. The first accepted chip count locks the session's chip values.
- A player fills Your count from the sheet, then sends from the card. The host still confirms that count.
- Editing a filled amount by hand removes the chip draft. The standalone chip page keeps direct submission for use without JavaScript.

## Consequences

Using the inline sheet does not save a count. Confirmation and cash-out remain separate actions. A rack stack is 20 physical chips for every colour. It does not change the session's unit or convert chips to pesos.

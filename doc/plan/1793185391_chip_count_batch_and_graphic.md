# Chip count: one batch confirm and a graphic chip sheet: plan

Date: 2026-10-28. Mode: mixed. Status: waiting for approval.

Study: [chip count batch and graphic sheet](../study/1793185391_chip_count_batch_and_graphic.md).

Stack the branch on `feat/count-chip-flow` (unreleased). Part 1 (batch) and part 2 (rack) are separate commits. Part 1 can ship alone.

## OPEN QUESTIONS

1. **Player sheet.** Should the player's chip sheet also fill "Your count" and let the player send from the card? Default: yes, the same as the host. The sheet becomes a calculator; sending always happens from the card.
2. **A chip count with an unchanged total.** Today the batch skips a typed amount equal to the current count. Default: a chip count is never skipped; it writes the next version with its breakdown.
3. **Direction.** A (chip rack, recommended), B (steppers) or C (one colour at a time). See the study.
4. **Stack size.** Default: 20 chips for every colour. Alternative: the host sets a stack size per colour on Chip values (a schema change to chip values and presets).
5. **Vibration** on a full stack, where the browser allows it. Default: no.

## Acceptance criteria

1. "Confirm all counts" writes every typed and chip count in one all-or-nothing action. A refusal saves nothing and keeps every draft, chip quantities included.
2. A chip count from the batch stores its breakdown and locks the chip values, the same as the single chip write.
3. The server calculates each chip total. A typed amount that differs from a player's chip total refuses the batch and names the player.
4. Without JavaScript, the chip page still confirms one player directly.
5. The chip sheet shows each colour as a drawn chip with a stack that follows the quantity. A chip tap adds one. A stack control adds one stack. The number keys still set an exact quantity.
6. 12 colours fit at 320 px with no sideways scroll and 48 px targets.
7. Reduced motion shows every state change without movement. The total never counts through other values.

## Tasks

- [ ] **1. Batch confirm takes chip counts. `tests: first`.**
  - `confirm_counts()` gains `chips={participant_id: {"quantities": pairs, "revision": int, "empty_stack": bool}}`.
  - For each chip entry: `_chip_amount()`, then `_check_countable()`, under the existing lock. Write with `chip_breakdown`. Call `_lock_chip_values()` once if any chip count is written.
  - Refuse when a typed amount and a chip total differ for one player. Do not skip a chip count with an unchanged total (question 2).
  - Tests: mixed typed and chip batch; refusal saves nothing; stale revision; empty stack; mismatch; repeated request; values lock once; breakdown stored.
  - **Complete when:** service tests pass.

- [ ] **2. The count form carries chip quantities. `tests: first`.**
  - `count_confirm` reads hidden `chips_{pid}` fields (quantities, revision, empty stack) and passes them on. A refusal keeps them as drafts.
  - View tests: posted chip fields reach the service; a refusal redraws them.
  - **Complete when:** view tests pass.

- [ ] **3. The sheet fills the field. `tests: alongside`.**
  - In the inline sheet, the primary action becomes "Use ₱X". It writes the total into the count field and the quantities into the hidden fields. Then it closes and returns focus to the field.
  - The row says "by chips" and shows the breakdown under the field.
  - Editing the field by hand clears the chip fields and the marker.
  - The native chip page keeps its direct confirm.
  - Player card: the same, if question 1 is yes.
  - Browser probe: fill by chips, type another player, confirm all: both counts are saved and the chip breakdown shows. Edit after filling: the chip data goes.
  - **Complete when:** the probe passes at 390 and 320 px.

- [ ] **4. The chip rack. `tests: alongside`.** (Direction A, if chosen.)
  - Drawn chip per colour: real colour, striped edge, value on the face. Tap: +1.
  - Side-view stack drawn with CSS; full stacks as columns with "×N". "+ stack" control.
  - A thin make-up bar in the dock. The total rolls only changed digits.
  - Motion: disc drop with `press`/`release`; no queued drops; reduced motion still.
  - Browser probe: taps, stacks, keys, 12 colours at 320 px, reduced motion, no script errors.
  - **Complete when:** the probe passes and the `/impeccable critique` finds no major issue.

- [ ] **5. Sync docs.** spec.md (batch rule: an intent change, so add an ADR), features.md, DESIGN.md, TODO.md phone checks.

## Checks

Recorded at rendezvous.

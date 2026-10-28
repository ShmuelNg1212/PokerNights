# Chip count: one batch confirm and a graphic chip sheet: study

Date: 2026-10-28. Mode: mixed.

## The request

The human reviewed the count-up flow on 2026-10-28. Two requests came from that review:

1. "Confirm all counts" commits every count at once, chip counts included. Today the chip sheet confirms one player immediately.
2. "Make the chip counting UI more interactive and graphic."

The first pass shipped on `feat/count-chip-flow` (commit `b9f38ac`): the Chips key on the number keys, the dock with the total and Confirm, and one line per colour. This study starts from that state.

## Current behaviour

### Two kinds of write

- The count list posts to `count_confirm`. It calls `ledger.services.confirm_counts()` with typed amounts and accepted player entries. It is all or nothing. It derives one request ID per player with `uuid5`. It skips a player whose current count already equals the typed amount.
- The chip sheet posts to `chip_count` (`ledger/chip_views.py`). For a host it calls `confirm_count()` for one player with `chips`, `chip_revision` and `empty_stack`. That write stores `FinalCount.chip_breakdown` and locks the session's chip values (`_lock_chip_values`).
- `confirm_counts()` takes no chip quantities. A batch count therefore cannot keep a chip breakdown today.

A host who types two counts and counts a third by chips makes two separate writes. The chip write happens first, without the "Confirm all counts" step.

### What a chip count must keep

- The server calculates the total from the quantities with integer arithmetic (`games.chips.calculate`). It never trusts a client total.
- The quantities carry the chip values revision. A stale revision is refused.
- The first chip-based count locks the chip values.
- A blank form is not a zero count. Zero needs the explicit empty-stack action ("No chips left").
- The form works without JavaScript.

### The sheet today

One line per colour: a 28 px flat swatch, the name, the value of one chip, the subtotal and a quantity field. The dock holds the total preview and Confirm above the keys. Input is by number keys only. Nothing on screen looks like chips.

## Findings: the batch confirm

1. **The service change is small and stays inside the existing lock.** `confirm_counts()` can take a `chips` map: participant ID to quantities, revision and empty stack. For each entry it calls `_chip_amount()` under the same session lock, then `_check_countable()`. It writes the count with `chip_breakdown`. If any written count came from chips, it calls `_lock_chip_values()` once.
2. **A typed amount and chip quantities for one player can disagree.** The page must send only one of them. A safe rule: when both arrive for one player and the typed amount differs from the calculated total, refuse the whole batch and name the player. The page clears the chip quantities when the host edits the field by hand, so this refusal is rare.
3. **The skip rule needs care.** Today a typed amount equal to the current count is skipped. A chip count with the same total but a new breakdown is new information. Recommendation: do not skip a chip count; write the next version.
4. **No-JavaScript stays as it is.** Without scripts, the chip page still confirms one player directly. This degrades to current behaviour.
5. **Drafts.** The chip quantities travel as hidden fields of `counts-form`. They need `data-keep` so a live redraw keeps them, as the count fields already do.
6. **Player side.** `enter_count()` already accepts chips. The player card has one field and one "Send to host" button. The same pattern fits: the sheet fills "Your count", and the player sends from the card.

## Findings: a graphic sheet

### What the person is doing

At count-up a person has a pile of chips in front of them. They sort by colour, make stacks, count stacks, then count the loose chips. Typical stacks are 20 chips; some tables use 25. A good tool follows that order: colour, stacks, loose chips.

### Constraints from DESIGN.md

- Money does not animate its value. Since 2026-10-11 a changed digit of the pot may roll to its accepted value. No figure counts through other values.
- Reduced motion removes movement and keeps the state change.
- Interactions end within 300 ms. Springs for things a finger touches.
- 48 px targets. Dark ground. Up to 12 colours must fit at 320 px.
- Player chips already use a striped edge. A denomination chip can share that language.

### Directions

**A. Chip rack.** Each colour line shows a drawn chip (real colour, striped edge, value printed on its face) and, beside it, a side-view stack that grows with the quantity. One disc per chip up to one stack; past that, full stacks show as columns with a "×3" label. Tap the chip: +1, and a disc drops onto the stack. A "+ stack" control adds a full stack. The number keys still give an exact quantity. The dock adds a thin bar of the total's make-up by colour. *Strength:* matches the physical task, and the chip tap is fast for loose chips. *Cost:* the most drawing work; the stack must stay legible at 12 rows and 320 px.

**B. Steppers.** Keep the list. Add − and + buttons beside each quantity and a "+20" button. Replace the flat swatch with a drawn chip. *Strength:* small change, easy to test. *Cost:* it is not much more graphic than today; three buttons per row crowd 320 px.

**C. One chip at a time.** The sheet shows one big colour at a time, with a large drawn stack, stack and loose-chip controls, and Next colour. A strip of small chips at the top shows progress. *Strength:* the most focused and the most graphic. *Cost:* more taps for a person who already knows the numbers; it hides the other colours, so a check means paging back.

### Recommendation

Direction A. It keeps every colour in view (scan and correct), adds the two real gestures (a stack, a loose chip), and makes the screen look like the table. B is a subset of A and can be its fallback at narrow widths. C suits a first-time player but slows a host.

Motion for A, inside DESIGN.md's rules:

- A disc drops with the `press`/`release` springs, about 200 ms. A fast run of taps does not queue drops; the stack shows the latest count.
- The total rolls only its changed digits, as the pot does. It never counts through other values.
- Reduced motion: the stack changes height at once.
- No sound. A short vibration on a full stack where the browser allows it, with a setting to turn it off: OPEN.

## Risks

- **A drawn total that disagrees with the server.** The client total stays a labelled preview. The server recalculates. The batch refusal names the player.
- **Tap accuracy.** A +1 chip tap next to a +stack control can mis-tap. Keep 48 px targets and space between them. Undo is the number keys or Delete.
- **Performance with 12 stacks.** Draw with CSS (stacked radial gradients or a repeated background), not one element per disc. Animate only `transform` and `opacity`.
- **Scope.** The batch change touches money logic (a service, a view, a form). The graphic sheet is front end only. They can ship separately: batch first, then the rack.

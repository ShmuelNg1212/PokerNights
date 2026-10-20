# A press that interrupts a combined animation leaves its other property inline

- **Trigger:** A `.btn` animates two properties in one `pokerMotion.run` call, for example `{ opacity: [0, 1], y: [8, 0] }`, and `pokerMotion.settle` is to clear both. A finger presses the button before the animation ends; `motion.js` then runs `{ y: 3 }` on the same element.
- **Observed behavior:** The press becomes the element's latest animation, so `settle` for the first call does nothing. The first call's opacity animation still reaches 1, but `opacity: 1` stays in the inline style. A callback on the first call's `finished` did not clear it either.
- **Impact:** Found on 2026-10-20 in `nextstep.js`. Visually harmless (opacity 1), but inline styles left behind can fight later CSS changes.
- **Evidence:** The motion browser check pressed the Settle up card 200 ms after the page: the card ended with `style="opacity: 1;"` until the rise was split.
- **Remedy:** Animate the property that a press takes over (`y`) and the other property (`opacity`) in two `run` calls. `settle` the `y` call for `transform`. Clear `opacity` from the `opacity` call's own `after`, because no press interrupts it.
- **Not changed:** `pokerMotion.run` and `settle`. Their "latest animation wins" rule is correct for one property.

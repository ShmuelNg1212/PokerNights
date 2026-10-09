# Numpad digit motion: study

Date: 2026-10-09, Asia/Manila.

## Request

The human said: "the animation when every number gets typed out is awkward. can you make it a smooth animation." This is the movement the field makes on each accepted key, released today in [numpad motion](../plan/1791533332_numpad_motion.md) as `ee18667`.

## What happens today

`tick()` in `static/js/numpad.js` runs after every accepted key:

- **A digit:** the whole field is set to 102% of its size and eases back to 100% in 140ms.
- **Delete:** the whole field is set 3px to the left and eases back in 140ms.

The new digit itself appears with no movement.

## Why it reads as awkward

Read from the code and the stylesheet. It was not watched on a phone from here.

1. **It starts with a jump.** The first keyframe is written at once (the [frame-late footgun](../wiki/footguns/motion_starts_a_frame_late.md) requires it), so the field snaps to 102% and only the way back is eased. Half of the movement is a cut.
2. **The wrong thing moves.** The border, the background and every digit already typed all swell together. On a field about 340px wide that is roughly 3px at each edge. The one thing that changed, the new digit, does nothing.
3. **Fast typing restarts it.** Each tap cuts the last pulse wherever it was and snaps to 102% again. Four quick digits are four jolts of the whole box.
4. **Scaled text shimmers.** A browser redraws the glyphs of a scaled text field at each step, which shows at 2.5rem.
5. **Delete moves the box sideways,** which is also how a refusal is shown (a wider shake). Two meanings share one gesture.

## Constraints

1. **Typing must not get slower.** A key acts as the finger goes down; nothing waits.
2. **The field stays a real text field** with its caret, its focus, form submission, the count preview and live updates.
3. **Money never shows a value it does not have** (AGENTS.md rule 9). The last study read this strictly and refused any movement of a digit. See "The rule" below.
4. **Transform and opacity only.** The field's size, caret and focus ring do not change.
5. **Reduced motion:** nothing moves. Without Motion the keys work as before.
6. **No preview deployments.** The human tests on the live build on a phone, so the change must fail safe: if anything is off, the field must look exactly as a plain field does.
7. **A text field cannot animate one of its characters.** Moving a digit needs a drawn copy of the figure over the field.

## Options

**A. Each digit arrives; the box stays still (recommended).**

- A typed digit fades in and rises about 5px into its place in 180ms, with the same ease-out the rest of the app uses. No bounce: it is money.
- In a right-aligned field (final counts) the digits already there glide left to make room instead of jumping.
- A deleted digit fades and drops out in 100ms, and the others glide back.
- A held Delete fades every digit out together.
- The field's box, border and caret never move. A refusal keeps its shake, which is now the only time the box moves.
- How: while keys are being tapped, a layer of one span per character sits exactly over the field and the field's own text is made invisible (`-webkit-text-fill-color`; the brass caret stays). About 200ms after the last key the layer is removed and the field shows its own text again. At rest nothing is different from a plain field.
- Fail-safe: the layer is used only if its measured text width equals the field's and the text does not overflow the field. Any mismatch or error and the field simply shows its text, with no movement. `NUMPAD=False` still returns the phone's keyboard.

**B. Nothing moves in the field.** The lit key is the only answer. No risk, about ten lines removed. Quiet, but the large figure in a sheet pops with no life.

**C. A gentler pulse of the whole box.** Ease in as well as out, smaller, not restarted by the next tap. It removes the jump (cause 1) and keeps causes 2 and 4. Not recommended.

## The rule

DESIGN.md says: "A digit appears whole and at once. No number rolls, counts or slides." Option A changes the first sentence. What the rule protects is that a person never reads an amount that is not the amount: no counting up through other values, no rolling digits. Under A the digit shown is always the true digit in its true place, and for about a tenth of a second it is faint. No other value is ever on screen. The human decides whether that is acceptable; if not, B is the choice.

## What stays outside this cycle

- The keys' own light, the Delete fill, the refusal shake, the keys rising into a sheet, and Next. They stay as released.
- What a key does, the limits, and which fields use the keys.

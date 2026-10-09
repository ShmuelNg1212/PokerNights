# Numpad digit motion: plan

Status: approved 2026-10-09 ("approved"); all three decisions as recommended. Built and released. Date: 2026-10-09, Asia/Manila. Study: [Numpad digit motion](../study/1791538181_numpad_digit_motion.md).

## Outcome

Typing an amount on the app's number keys looks smooth. The field's box stays still. Each digit arrives in its own place, and the digits around it make room without a jump. Typing stays exactly as fast as it is.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new colour, font or asset. No migration, no server change.

## Behaviour

| Moment | Today | After |
|---|---|---|
| A digit is typed | The whole field snaps to 102% and eases back | The box is still. The digit fades in and rises 5px into place in 180ms |
| Typing in a right-aligned field (final counts) | The digits jump left | They glide left in 180ms as the new one arrives |
| Delete | The whole field jumps 3px left and eases back | The digit fades and drops out in 100ms; the rest glide back |
| Delete held to the end | The field fades in from 40% | Every digit fades out together in 120ms |
| A key is refused | The key and the field shake | Unchanged, and now the only time the box moves |
| Fast typing | Each tap restarts the jolt | Each digit runs its own arrival; none is cut by the next |

Rules that hold throughout:

- A key acts the moment the finger goes down. Nothing waits for a movement.
- The digit on screen is always the true digit in its true place. Nothing rolls, counts or shows another value.
- No bounce. One curve, the app's ease-out (`--ease-out`), for arriving and gliding; a shorter ease-in for leaving.
- Only transform and opacity change. The field's size, caret and focus ring are untouched.
- About 200ms after the last key the field is a plain text field again, with nothing added to the page.
- Under reduced motion, or without Motion, nothing moves and the digit appears at once.

Built with the design and motion skills.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **A digit fades in over about a tenth of a second** instead of appearing at once. DESIGN.md's line "A digit appears whole and at once" becomes "The digit shown is always the true digit; it may fade and rise into place. No number rolls or counts." Say "B" to have no movement in the field at all, with the lit key as the only answer.
2. **Every field the keys serve gets it,** large (sheets) and small (counts, stakes, rake, seats). Say if you want it in the sheets only.
3. **No new switch.** The layer checks itself and falls back to a plain field; `NUMPAD=False` remains.

## Implementation

1. **`static/js/numpad.js`.**
   - `tick()` and the hold-clear fade are replaced by a small `figure` helper: `figure.typed(field, before, after, caret)`.
   - On the first key it builds a layer: an absolutely placed, `aria-hidden`, `pointer-events: none` box over the field with the field's computed font, padding, alignment and line height, holding one inline-block span per character. The field gets a class that hides its own glyphs with `-webkit-text-fill-color: transparent`; the caret keeps its brass colour.
   - Each key diffs the old and new text. Kept spans are measured before and after and glide from where they were drawn (FLIP on `transform`, started from their current position so a second tap does not snap). New spans start at `opacity: 0; translateY(5px)` written inline first. Removed spans are taken out of the flow and fade.
   - A timer of 200ms after the last key removes the layer and the class. Blur, Next, Done, a closing sheet, a live or in-place update, and leaving the page remove it at once.
   - Self-check before each use: the layer's text width equals the field's measured text width within 0.5px, and the field's text does not overflow (`scrollWidth <= clientWidth`). If not, or on any error, the layer is dropped for that field and the field shows its own text. An error here never reaches `giveUp`; the keys keep working.
   - The layer is kept out of in-place morphs the same way the keys in a slot are.
2. **CSS (`app.css`, numpad motion section).** `.numpad-figure` (the layer) and `input.is-figured` (hidden glyphs). Nothing under `prefers-reduced-motion`, because the layer is never built there.
3. **Tests (`web/tests/browser/numpad.mjs`).** The two checks of the old pulse are replaced. New checks:
   - after a key the field has no animation and no transform, and its box is the same size and place before, during and after;
   - the first frame after a key shows the new digit's span at opacity 0 and every earlier digit where it was drawn the frame before;
   - each span's left edge matches the position of that character in the field within 0.5px, in a left-aligned sheet amount and a right-aligned count, at 320 and 390px;
   - ten taps within 300ms type ten digits and leave ten spans, none stuck below opacity 1 after 400ms;
   - Delete, and Delete held to the end, leave the right value and no orphan span;
   - 400ms after the last key: no layer, no class, no inline style, and the field's text is visible;
   - a field whose text overflows gets no layer and types normally;
   - a forced width mismatch drops the layer and types normally;
   - a live update and an in-place update while the layer is up leave the value and no layer;
   - reduced motion and no Motion: no layer is ever built.
4. **Verify.** SQLite suite. `numpad.mjs`, then `count_flow.mjs` and `player_entries.mjs`, which type through the keys. Frame captures of a digit mid-arrival in a sheet and in a count row inspected once, at 390px.
5. **Sync docs.** DESIGN.md numpad motion table and rule, wiki features, the frame-late footgun if anything new is learned, TODO with a phone check. SPEC.md is the human's.

Work is done on branch `feat/numpad-digit-motion` from `main`. Nothing is merged or pushed without an instruction.

## Acceptance criteria

- AC1. The field's box does not move or change size when a key is accepted.
- AC2. A typed digit fades and rises into its place; a deleted one fades out; neighbours glide and never jump.
- AC3. Ten taps in a third of a second type ten digits, and every digit ends fully visible.
- AC4. The drawn digits sit exactly where the field's own digits are; removing the layer shifts nothing.
- AC5. No value other than the field's value is ever shown.
- AC6. The caret, focus, form submission, the count preview and live updates behave as before.
- AC7. At rest the field is a plain text field: no layer, class or inline style.
- AC8. If the layer cannot match the field, the field shows its text with no movement and the keys work.
- AC9. Under reduced motion, and without Motion, nothing moves.
- AC10. Existing tests and the three browser checks pass.

## Out of scope

- The keys' light, the Delete fill, the refusal shake, the keys rising into a sheet, Next.
- What a key does, the limits, and which fields use the keys.
- Vibration and sound.

## Rollback

Revert the feature commit. `NUMPAD=False` in Vercel returns every field to the phone's keyboard at once.

## Progress and blockers

2026-10-09: Study and plan complete. Waiting for the human's approval. No code written.

2026-10-09: The human approved with "approved". Built on `feat/numpad-digit-motion` from `main`; kept local.

Changes from the plan:

- **Each character is placed where the browser sets it,** read from a hidden copy of the same text, instead of being laid out as separate boxes and then compared by width. The position is right by construction, so the width comparison was not needed. The check that remains is that the text fits the field.
- **The copy stays 300ms after the last key, not 200ms,** so an arrival of 180ms always finishes before it is removed.
- **The rise is 0.16em, not 5px,** so it is in proportion in a 40px sheet amount (about 6px) and in a 16px field (about 3px).
- **A digit that replaces a selection does not cross-fade with it.** What it replaces goes at once. Only a plain Delete is seen leaving.
- **The movement uses the browser's own animation calls,** not Motion, because they start on the first frame. Motion still decides whether anything moves (reduced motion, library missing).
- **A refused key shakes the drawn digits with the field.** Not in the plan; without it the box would shake around still digits.
- **The picture comparison was run at 390px only,** for a left-aligned sheet amount and a right-aligned setup field, not also at 320px.

Verification:

- 891 tests pass on SQLite. PostgreSQL was not run: nothing on the server changed.
- `numpad.mjs`: 120 of 120 on a fresh temporary database. `count_flow.mjs`: 89 of 89. `player_entries.mjs`: every check passes.
- Two captures of a field, one with the drawn copy up and one with the field's own text, differ by at most 1 shade in 255 on any pixel. A capture 60ms into an arrival was inspected.

Acceptance: AC1 to AC10 are met in headless Chrome.

Not verified: an iPhone and Safari, where the hidden glyphs, the caret and the exact placement matter most; a slow phone's frame rate while typing fast.

A fresh reviewer did not read the branch; the author's own read of the diff is the only review.

Documentation synced: DESIGN.md, wiki features, browser README, TODO.

2026-10-09 release: the human said "go push". `feat/numpad-digit-motion` was merged to `main` as `6119dd4` and pushed (previous production commit `ee18667`). 891 tests passed on PostgreSQL 17 and SQLite on the merged `main` before the push. No migration. The live site was not checked from here. Phone acceptance remains open.

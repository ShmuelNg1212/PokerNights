# Numpad motion: plan

Status: approved 2026-10-09 ("approved"); all four decisions as recommended. Date: 2026-10-09, Asia/Manila. Study: [Numpad motion](../study/1791533294_numpad_motion.md).

## Outcome

The app's number keys feel alive under a finger: a key answers the tap, the amount shows it was typed, holding Delete shows that it is about to clear, and the keys arrive with the sheet instead of popping in. Typing stays exactly as fast as it is.

Mode: Operate. Visual authority: the built Rack in DESIGN.md and its motion presets. No new colour, font or asset. No migration, no server change.

## Behaviour

| Moment | What moves |
|---|---|
| The keys appear in a sheet (Buy-in, Rebuy, Cash out) | The four rows rise 10px and fade in, 30ms apart, about 220ms in all. A key can be tapped before its row has landed |
| A key is tapped and accepted | The key sinks as today and lights with the Pressed tint, fading over 160ms. The figure in the field makes one 2% pulse |
| Delete is tapped | The same light on the key; the field makes a 3px nudge to the left |
| Delete is held | A fill runs across the key for the half second the hold takes. Letting go early takes it back. When it completes, the field clears and fades back in from 40% |
| A key is refused | The field nudges and turns its border to Down, as today. The key now shakes with it and takes the Down border for 260ms |
| Next in the bottom panel | The field's name and note slide up and out, and the next field's come in from below, 160ms |
| The bottom panel opens and closes | Unchanged: it rises with the `sheet` spring and leaves |

Rules that hold throughout:

- A key still acts the moment the finger goes down. Nothing waits for a movement, and a second tap restarts it.
- A digit appears whole and at once. No number rolls, counts or slides.
- Only transform and opacity change. The field's size, caret and focus ring are untouched.
- Under reduced motion nothing moves. If Motion did not load, the keys behave as they do today.

Built with the design and motion skills, inside DESIGN.md's tokens and presets.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **The field pulses on every accepted key.** It is small (2%). Say if you would rather have the key light alone.
2. **Holding Delete shows a fill across the key.** The alternative is to leave the hold hidden as today.
3. **No vibration.** It would work on Android and not on an iPhone.
4. **No new switch.** `NUMPAD=False` already returns every field to the phone's keyboard if anything misbehaves.

## Implementation

1. **`static/js/numpad.js`.**
   - `lit(key)`: add `is-hit`, remove it after 160ms; a second tap restarts the timer.
   - `tick(field)` after an accepted `write`: one `pulse` on the field with the first keyframe written inline first; an earlier one still running is cancelled.
   - Delete: `tick` becomes a 3px nudge; on `pointerdown` the key gets `is-holding` (a CSS fill over 500ms, the hold's own length); `lift` and the completed clear remove it; a completed clear fades the field from 40%.
   - `refuse(field, key)`: the key gets the same nudge and `is-refused` for 260ms.
   - `show()` in a slot: when the keys enter a slot they were not in, the rows rise (`arrive` without bounce: `shift`), each key's start written inline first.
   - `openPanel()` on a change of field while the panel is open: the label and note are swapped inside a 160ms slide.
   - Every movement goes through `pokerMotion.run` and `settle`, so reduced motion and a missing library leave today's behaviour, and no inline style is left behind.
2. **CSS (`app.css`, numpad section).** `.numpad-key.is-hit` (Pressed tint with a 160ms fade out), `.is-refused` (Down border), `.is-holding::before` (a fill scaled from the left over 500ms, removed under reduced motion), and clipping for the panel's label.
3. **Tests.** The numpad's behaviour tests in Django stay as they are; nothing on the server changes. The browser check `numpad.mjs` (87 checks today) gains:
   - ten taps within 300ms type ten digits, with and without Motion;
   - the first frame after the keys enter a sheet shows them at their starting point, and 400ms later every key is at rest with no inline style;
   - a tapped key carries `is-hit` and loses it; the field has a running animation after an accepted key and none after 300ms;
   - holding Delete: the fill is running at 250ms, the field is not yet cleared, and letting go leaves the value; held to the end, the field is empty;
   - a refused key and the field both carry their refusal marks and lose them;
   - Next: the panel's label changes to the next field's name and nothing is left clipped or styled;
   - reduced motion: none of the above animates and every key works;
   - the field's width, height and caret position are the same before and during a pulse.
4. **Verify.** SQLite suite (the script list in the head is unchanged). `numpad.mjs`, then `count_flow.mjs` and `player_entries.mjs`, which type through the keys. Captures of a sheet mid-arrival and of Delete mid-hold inspected.
5. **Sync docs.** DESIGN.md numpad addendum (the motion table above), wiki features, TODO. SPEC.md is the human's.

Work is done on branch `feat/numpad-motion` from `main`. Nothing is merged or pushed without an instruction.

## Acceptance criteria

- AC1. Ten taps in a third of a second type ten digits, as before.
- AC2. A tapped key lights and the field pulses once; neither changes the field's size or caret.
- AC3. Holding Delete shows a fill for the length of the hold; releasing early clears nothing; completing it clears the field.
- AC4. A refused key marks both the key and the field, and nothing is typed.
- AC5. The keys rise into a sheet and can be tapped before they land.
- AC6. Next shows the change of field in the panel.
- AC7. No number is ever shown that the field does not hold.
- AC8. Under reduced motion, and without Motion, everything works and nothing moves.
- AC9. No inline style or marker class is left on a key or a field at rest.
- AC10. Existing tests and the three browser checks pass.

## Out of scope

- What a key does, the limits, and which fields use the keys.
- Vibration and sound.
- The phone's own keyboard.

## Rollback

Revert the feature commit. `NUMPAD=False` in Vercel returns every field to the phone's keyboard at once if the keys misbehave.

## Progress and blockers

2026-10-09: Study and plan complete. Waiting for the human's approval. No code written.

2026-10-09: The human approved with "approved"; all four decisions as recommended. Built on `feat/numpad-motion` from `main`; kept local.

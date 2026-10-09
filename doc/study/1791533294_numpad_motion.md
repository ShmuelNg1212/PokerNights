# Numpad motion: study

Date: 2026-10-09, Asia/Manila.

## Request

The human asked: "can you implement animations to the built in keyboard". The built-in keyboard is the app's own number keys (`static/js/numpad.js`), used on a phone for amounts, final counts, stakes, rake and seats ([plan of 2026-10-05](../plan/1791202390_host_gaps_numpad_count_up.md)).

## What exists today

- **Two places.** In a sheet (Buy-in, Rebuy, Cash out) the twelve keys sit in a slot inside the form. On a page with several number fields (count-up, New session) they are a panel fixed to the bottom, with the field's name, a note, **Next** and **Done**.
- **A key acts as the finger goes down** (`pointerdown`), so typing is as fast as a real keyboard. The field stays a real text field with its caret.
- **What already moves:**
  - The bottom panel rises with the `sheet` spring and leaves with `leave`.
  - Every key is a `.btn`, so it sinks 3px under a finger and springs back (`motion.js`).
  - A refused key (a third decimal place, an amount over the limit) nudges the field sideways and turns its border to Down for 260ms.
- **What does not move:**
  - In a sheet the keys simply appear.
  - Nothing answers an accepted key except the digit appearing in the field.
  - Delete has no answer of its own. Holding Delete for half a second clears the field, and nothing shows that it will.
  - On **Next** the panel's label and note change at once.
  - A refused key itself shows nothing; only the field does.

## Constraints

1. **Typing must not get slower.** Nothing may wait for a movement, and a key tapped again before its movement ends must act and restart it. Ten taps in a third of a second must still type ten digits.
2. **Money never shows a value it does not have** (AGENTS.md rule 9, DESIGN.md). A digit appears whole, at once. Movement may mark that something was typed; it may not roll, count or interpolate a number.
3. **Only transform and opacity** on the keys and fields, so a slow phone does not lay the page out on every tap. No change to the field's size, the caret or the focus ring.
4. **Motion starts a frame late** ([footgun](../wiki/footguns/motion_starts_a_frame_late.md)): anything that arrives is put at its starting point before the first frame.
5. **Reduced motion:** nothing moves, as everywhere else. Without Motion the keys behave as they do today.
6. **The keys can fail safe already:** `NUMPAD=False` returns every field to the phone's keyboard without a release.
7. **DESIGN.md:** springs for what a finger touches, eases for what arrives or leaves; one authored moment per surface, not a flourish on every element. The existing presets cover what is needed.
8. **iPhones give web pages no vibration.** `navigator.vibrate` works on Android only.

## Options

**An accepted key**

- **A. The key lights for a moment and the field ticks (recommended).** The key takes the Pressed tint, fading in 160ms, on top of its sink. The figure in the field makes one small pulse (2%), so the eye that is on the keys still catches that the amount changed.
- **B. The key only.** Quieter; says nothing about the field.
- **C. Each new digit slides or rolls into the field.** Refused by constraint 2, and a real text field cannot animate one character.

**Delete, and hold to clear**

- **A. A fill that runs across the Delete key while it is held, and a clear that is seen (recommended).** The fill takes the half second the hold already takes, so it shows when the field will empty; letting go early takes it back. When the field clears, it fades back in from 40%.
- **B. Leave it hidden.** The hold stays something a person finds by accident.

**The keys arriving in a sheet**

- **A. The four rows rise 10px and fade in, 30ms apart (recommended).** About 220ms in all, as the sheet itself settles. A key can be tapped before its row has landed.
- **B. Nothing.** The sheet already moves.

**Next in the bottom panel**

- **A. The field's name and note slide up and the new ones come in under them (recommended),** 160ms, so the eye sees the keys now belong to another player.
- **B. Leave the swap instant.**

**A refused key**

- **A. The key shakes with the field and takes the Down border for 260ms (recommended).** The finger is on the key; the refusal should be where the finger is.
- **B. The field only, as today.**

**Vibration**

- **A. Not included (recommended).** It would work on Android and not on the human's iPhone, so the same key would feel different on two phones at one table.
- **B. A 5ms tick on Android.**

## What stays outside this cycle

- Any change to what a key does, to the limits, or to which fields use the keys.
- Sounds.
- The phone's own keyboard on text fields.

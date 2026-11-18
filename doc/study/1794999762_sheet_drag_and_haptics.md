# Study: drag a sheet down to close it, and haptics

Date: 2026-11-18. Mode: design. Skills: `animate`, `mobile-native`.

## Question

How can a sheet close by a downward drag, and how can the phone give a short vibration at the moments that matter, without breaking the motion rules in DESIGN.md?

## What exists

### Sheets

- `static/js/sheets.js` makes one native `<dialog class="sheet">` for each page, in `#table-sheets`. `open()` calls `showModal()`, sets the entry transform, then runs the `sheet` spring. `close()` runs `leave` from the current position to the sheet's height. A close during the rise turns the sheet around.
- The dialog is the scroll container: `overflow-y: auto`, `max-height: 85dvh` (`static/css/app.css:261`). The head (title and Close) is at the top of the scroll. The recap sheet has a sticky head (`app.css:529`).
- From 900 px the sheet is centred, not against the bottom edge (`app.css:296`).
- A sheet closes now by Close, Escape, a tap on the backdrop, or an accepted write (`inplace:updated`).
- No code reads pointer movement or touch movement on a sheet. Nothing can drag it.
- The number keys (`static/js/numpad.js`) act on `pointerdown`. A drag that starts on a key would type a digit.

### Motion

- `static/js/motion.js` supplies `run`, `after`, `settle` and `timing`. `on()` is false under reduced motion and when the Motion file did not load.
- Footgun [motion starts a frame late](../wiki/footguns/motion_starts_a_frame_late.md): write the first keyframe inline before Motion starts.
- Footgun [press interrupts a combined animation](../wiki/footguns/press_interrupts_a_combined_animation.md): one property per `run` call where a press can interrupt.

### Haptics

- No script vibrates the phone. `grep` finds no `vibrate` outside the Turbo vendor file.
- The moments that a haptic could mark already have a code point:
  - own write accepted or refused: `answered()` in `motion.js`, after `inplace:updated` / `inplace:failed`;
  - books balance, once per set per browser: `changes.js`, the `balanced:` key;
  - dealer chosen in the seat draw: `seats.js`;
  - a number key: the `pointerdown` handler in `numpad.js`.

### Script loading

- Every page script loads in the head of every page, in one fixed order. `ScriptsLoadOnceTests.NAMES` in `web/tests/test_inplace.py` lists that order. A new script must go into the base template and into that list.

## Platform facts

| Platform | Mechanism | Limits |
|---|---|---|
| Android Chrome, Firefox | `navigator.vibrate(pattern)` | Needs a tap on the page before (sticky activation). Patterns in ms. |
| iPhone Safari 17.4+ and the installed app | No `navigator.vibrate`. A click on the label of an `<input type="checkbox" switch>` toggles the switch and plays the system switch haptic. | Not a documented haptics API. One kind of tick only. Silent when the person turns off System Haptics. **Unknown:** whether it plays outside a direct tap (after a server answer, after a poll). **Unknown:** whether iOS 26 keeps it. |
| Desktop | None | Nothing happens. |

Consequence: a haptic in direct response to a finger (a number key, a drag) is likely to work on the iPhone. A haptic after a server answer or a poll may do nothing on the iPhone. That failure is silent and safe. Only the human's phone check can settle it. No browser probe can feel a vibration.

## Touch facts for the drag

- A sheet that scrolls cannot use `touch-action: none` on its body: that stops scrolling. The common solution (iOS sheets, Vaul): start a drag only when the content is at its top and the finger moves down first. Then call `preventDefault()` on `touchmove` from a non-passive listener.
- `overscroll-behavior: contain` on the dialog stops the page under it from scrolling and stops the iOS bounce from fighting the drag.
- Touch events, not pointer events, keep a mouse from dragging on a desktop.
- `::backdrop` inherits custom properties from its dialog in current Chrome and Safari. Older browsers ignore it, so a backdrop that fades with the drag is a safe extra.

## Risks

1. **The iPhone haptic trick can move focus or toggle a form value.** The helper switch must be outside every form, hidden from assistive technology, and must leave focus where it was. A probe must check focus.
2. **A modal dialog makes the rest of the page inert.** A helper outside the open dialog may not get the click. Put the helper in the open dialog when there is one.
3. **Drag against scroll.** A drag from the body when the content is not at its top would fight scrolling. Start a drag from the body only at `scrollTop` 0.
4. **Number keys.** Exclude the keys from drag starts.
5. **A drag during a send.** A sheet dragged away while its write is sent would hide a refusal. No drag while a form in the sheet is sent.
6. **Too much vibration.** Haptics on every button, or on other people's changes, would make the phone buzz all night. Keep a short list of moments.

## Conclusion

Both parts are additive. Without touch, without Motion, under reduced motion, or without a vibration mechanism, every screen works as it does today. The plan can go straight from this study. The iPhone outcome of the haptics after a server answer stays open until the phone check.



For motion between screens, seed a fresh temporary database with `seed.py`, serve it, then run `screens.mjs` (42 checks). It wraps `document.startViewTransition` and records, for every screen change the browser animates, the direction on `<html>` when it began, the animations that ran on each layer and how long they last. It walks Your groups → group → session → set → set log and back at 390 and 1280px, the three tabs, the phone's Back and Forward, the carried name on every hop, the chips between a closed session and its set, a real pointer tap during a movement, an action on a set page, twenty changes, and reduced motion. It records one buy-in on set 3. It cannot judge how the movement feels, and headless Chrome is not Safari.

Since 2026-10-05 `motion.mjs` waits 150ms after closing a sheet under reduced motion before reopening it: the dialog's `close` event arrives a moment after `close()`, and one run in five reopened the sheet before it.

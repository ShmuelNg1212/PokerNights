# The look of the table in the seat draw: study

Date: 2026-10-12, Asia/Manila.

## Request

The human said: "can you improve the look of the poker table during the draw animation."

Asked two questions, the human chose:

- **Direction:** a real poker table. A racetrack shape, a padded rail, felt with a betting line and a light from above, a small mark in the middle. Drawn in the app's own colours, no photo.
- **With it, all four:** seats as chairs; a proper dealer disc; the same look on the still table of the set page; more drama in the draw (a light that follows the disc, and a brighter moment when the winner is named).

## What is there today

- The table is one element: an ellipse with a 9 to 11px flat border in `--rail-2` and the set page's felt gradient. No highlight, no shadow that reads as padding, nothing on the felt.
- Seats are placed on an ellipse by one formula, written twice: `games/seats.py` (`spot`, in percent, for the still table) and `static/js/seats.js` (`at`, in pixels, for the stage).
- An empty seat is a 48px dashed ring with a number. A taken seat is the player's chip with the name under it. The dealer disc is a 22 to 30px flat Brass circle with "D".
- During the draw the disc runs around the ring and lights the chip it passes with a Brass ring. Nothing else on the table changes.

## Findings

1. **A racetrack needs its own geometry.** Seats spaced by angle bunch up on the round ends of a racetrack and leave the straight sides empty. They must be spaced by distance along the edge. Both copies of the formula change together, and each seat also needs the direction it faces, for the chair.
2. **The stage is tall on a phone and the page's table is wide.** The same shape must work upright and lying down. Seat 1 stays at the top in both.
3. **Depth can be drawn without a picture.** A rail is three bands: a dark outer edge, a lit top, a shadow where it meets the felt. The felt is a gradient lit from above with a thin line a little inside the rail. All of it is CSS on two or three elements; nothing is downloaded.
4. **The mark in the middle.** The app's own mark exists as a drawn icon. Faint, on the felt, it reads as the table's logo and costs no new asset. The winner's chip covers it while a seat is chosen, which is fine.
5. **Chairs.** A small rounded seat behind each place, turned to face the table. An empty chair with its number says "a place" better than a floating ring. The tap target stays 48px whatever the chair's drawn size.
6. **The light must not repaint the felt each frame.** Moving a gradient's centre is painted on every frame. A separate soft disc of light moved by `transform`, and a dimming layer faded by `opacity`, give the same picture from the compositor. The stage's rule stays: Motion moves only `transform` and `opacity`.
7. **The dealer disc.** A real button is white with a dark rim. In the app's colours: Bone with an Ink rim and a Brass inner ring, "D" in Ink. Larger while it travels, settling to its size when it lands.
8. **DESIGN.md.** "Don't add casino imagery" was answered in the seat draw by drawing with the app's own shapes. A drawn rail, chairs and a button stay inside that; cards, chips stacks in the pot and photos stay out. The addendum must say where the line is.
9. **Twelve players at 320px** is the tight case and has a check already: every seat 48px, on screen, none overlapping, every chip clear of Done. A racetrack has a longer edge than the ellipse inside the same box, so there is more room, not less; the check decides.
10. **Nothing on the server's records changes.** No migration. `seats.spot` gains the table's proportions and returns the facing angle.

## Risks

| Risk | Effect | Answer |
|---|---|---|
| More layers cost frames on a slow phone | A stuttering draw | Only transform and opacity move; the existing check with the processor slowed four times must still show no late frame |
| The look drifts from the rest of the app | The stage feels like another product | Only existing tokens (rail, felt, bone, brass, ink); captures at 320, 390 and 1280px are looked at before it is called done |
| The page's small table gets heavy | The set page grows or gets noisy | The still table keeps its size; chairs are small and the light is still |
| Seats land differently on the page and on the stage | The page and the stage disagree | One rule in both places, and a test that compares them for 2 to 12 seats |

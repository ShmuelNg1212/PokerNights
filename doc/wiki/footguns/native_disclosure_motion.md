# Native disclosure motion and temporary open state

## Check the content height, not the animation list

- **Trigger:** A browser check opens a native disclosure. It reads `details.getAnimations({subtree:true})` to prove that the content height moves.
- **Observed behavior:** Chrome 156 omits the `::details-content` height transition from that list. The list can contain the chevron's 180 ms transition instead.
- **Impact:** A working disclosure fails the check. A chevron animation can also make a broken height transition appear to pass.
- **Remedy:** Read `getComputedStyle(details, "::details-content").blockSize` before, during and after opening. Check that the intermediate height is between zero and the final height. Read the declared transition duration as a separate check.
- **Evidence:** The Slice F probe measured 0 px before opening, 88.7 px during opening, and 107.5 px at rest. The computed content transition was 0.2 s. The animation list contained only the chevron's 180 ms transform. `web/tests/browser/fluid.mjs` checks the intermediate height and the 200 ms duration. The rule is in `static/css/app.css`.

## Do not save an automatic open as a user choice

- **Trigger:** A completed checklist step opens `.prep-done` for 80 ms so its tick can be read. A live poll arrives during that hold.
- **Observed behavior:** `live.js` saves open disclosures before it sends `live:updating`. The completion cleanup closes the fold. If the saved list includes the temporary open, the poll then restores it and leaves the fold open.
- **Impact:** The person sees an expanded checklist that they did not choose to open.
- **Remedy:** Exclude `.prep-completing` from the saved disclosure list. Keep a fold that the person opened in that list.
- **Evidence:** `static/js/live.js` applies this exclusion before `live:updating`. `static/js/table.js` marks the automatic hold. `web/tests/browser/fluid.mjs` asks for a fresh server snapshot during the hold and checks that the fold stays closed after the poll.

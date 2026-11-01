# Native disclosure motion and temporary open state

## Give each disclosure one motion owner

`disclosures.js` uses native height motion only when both `interpolate-size: allow-keywords` and `details::details-content` are supported. The scoped CSS uses the same test. Otherwise, the script animates the measured height for 200 ms. Rapid changes start from the current height. Completion restores the original height and overflow styles.

The account flyout, RSVP confirmation disclosures and app-link disclosures keep their own owner. The script also excludes `.sheet-source`. Reduced motion, a hidden page or an instant request sets the state without fallback motion. A live update, page cleanup or a change to reduced motion finishes active fallback motion.

`web/tests/browser/mobile_motion.mjs` probes Chromium and WebKit at 390 × 844 with touch enabled. Its forced fallback disables both the native CSS rule and the JavaScript capability test. It checks intermediate heights, rapid changes, close-state styling, live updates, checklist completion and reduced motion. A separate context checks disclosure use without JavaScript. These probes do not verify a physical iPhone or an installed app.

## Check the content height, not the animation list

- **Trigger:** A browser check opens a native disclosure. It reads `details.getAnimations({subtree:true})` to prove that the content height moves.
- **Observed behavior:** Chrome 156 omits the `::details-content` height transition from that list. The list can contain the chevron's 180 ms transition instead.
- **Impact:** A working disclosure fails the check. A chevron animation can also make a broken height transition appear to pass.
- **Remedy:** For native motion, read `getComputedStyle(details, "::details-content").blockSize` before, during and after opening. Check that the intermediate height is between zero and the final height. Read the declared transition duration as a separate check. For fallback motion, sample the disclosure's bounding height between its closed and open values.
- **Evidence:** The Slice F probe measured 0 px before opening, 88.7 px during opening, and 107.5 px at rest. The computed content transition was 0.2 s. The animation list contained only the chevron's 180 ms transform. `web/tests/browser/fluid.mjs` checks the intermediate height and the 200 ms duration. The rule is in `static/css/app.css`.

## Save the requested state before a live update

- **Trigger:** A live poll arrives during a fallback close or the checklist's automatic 80 ms open hold.
- **Observed behavior:** The fallback keeps `open` set until the close finishes. It marks the requested closed state with `data-disclosure-closing`. `table.js` marks its automatic hold with `.prep-completing`. `live.js` saves open disclosures before it sends `live:updating`. That event finishes motion and clears completion state. If the saved list includes either temporary open, the poll can restore it after cleanup.
- **Impact:** A disclosure can remain open after the person closes it. An automatic checklist hold can also become a persistent open state.
- **Remedy:** Exclude both markers from the saved open list before `live:updating`. Preserve a fold that the person opened. Keep `details.prep-completing::details-content { transition: none; }` in the native CSS. It shows the completed step at full height during the short tick hold. Close-state CSS must also exclude `data-disclosure-closing`, so the caret and summary respond when closing starts.
- **Evidence:** `static/js/live.js` applies both exclusions. `static/js/disclosures.js` owns fallback cleanup. `static/js/table.js` owns the checklist hold. `fluid.mjs` requests a fresh snapshot during that hold. `mobile_motion.mjs` probes a live update during closing and a second poll during completion. The probes check that the fold ends closed and temporary styles and classes are cleared.

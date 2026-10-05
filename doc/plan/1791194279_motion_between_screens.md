

2026-10-05: approved by the human, with four answers: the agent decides how the player chip is carried; the Sessions, Stats and Group settings tabs are to have movement too; the iPhone runs iOS 18 or later; the implementation note is acknowledged. Built on `motion-stage-3`. Tests were written first and seen to fail.

Changes from the plan:

1. **Tabs move** (the human's instruction, replacing decision 4). The content shifts towards the side the chosen tab is on, the marker slides to it, and the back link, heading and tab bar stay still.
2. **Chips are carried** (the agent's decision, replacing decision 3): between a session's results and one of its sets' rows, for a player who has one chip in each list with the same colour and letters, when the chip was on screen. Chips are coloured by joining order within a set and by standing within a session, so in a session of several sets some chips differ and stay put. From the top of a session page the results are usually below the screen, so the chips are seen mostly on the way back from a set, or after scrolling to the results.
3. **The transition no longer goes through Turbo's own.** The implementation note the human acknowledged said it would. Turbo starts its transition before it tells the page what the new screen is, and the browser photographs the old screen at that moment, so nothing could be marked as carried in time. `turbo-setup.js` now pauses Turbo's render, sets the markers, starts the browser's transition itself and resumes the render inside it. This is Turbo's documented way to pause a render. Turbo's `view-transition` meta tag is removed from `base.html`. Motion's `animateView` is still not used.
4. **A tap during a movement is passed on by script.** `pointer-events: none` on the transition layer did not work in Chrome: the tap went to the page and the browser reported nothing under the finger. The script finds the control by its position and clicks it when exactly one control is there. Where two overlap (the host bar over a row), the tap is dropped and has to be repeated.
5. **The name is also carried from a card's "in play" band** on Your groups to the set it opens.
6. **A name is carried only when the words match.** A link that jumps levels (a "To settle" line on Your groups to a session) has no matching name and only shifts.
7. **The depth of forms:** a form opened from a group is 2, the Manage page of a session is 3, forms opened from a set are 4.
8. **`motion.mjs` was hardened.** One run in five stopped under reduced motion when the check reopened a sheet in the same instant it closed it. The check now waits 150ms there. The cause is inferred from the code (the dialog's `close` event is delivered late), not proven; it ran clean three times after the change. A person cannot tap that fast.

Verification:

- `screens.mjs`: 42 of 42 on a fresh temporary database. Every movement lasts 260ms or less; a whole change, from the tap's response to the end of the movement, took up to about 480ms in headless Chrome.
- `lifetime.mjs` 22, `flow.mjs` 52, `dock.mjs` 175, `inplace.mjs` 38, `navigate.mjs` 37 pass. `motion.mjs` 34 in four of five fresh runs before the hardening (change 8).
- Mid-movement captures were inspected at 390px (a tab change with the marker sliding; chips travelling from a session's results to a set).

**AC4 is open: only the human can judge it on a phone.** Not verified: Safari and the installed app on an iPhone (whether a tap during a movement reaches its control there, how the carried name looks when its two sizes differ a lot, and whether the phone's Back gesture plays cleanly with the cross-fade); frame rate on a long page.

2026-10-05 release: the human merged and pushed `main` at `648cca8` (previous production commit `8190e23`). The suite had passed on local PostgreSQL 17 for this code. About two and a half minutes after the merge commit the live site served the new `turbo-setup.js` (byte-for-byte the local file) and the stylesheet with the screen movements, and the login page no longer carried Turbo's `view-transition` meta tag. Not checked on production: any signed-in page, and anything on a real iPhone (AC4).

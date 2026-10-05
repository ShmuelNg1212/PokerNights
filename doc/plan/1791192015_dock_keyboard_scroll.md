

2026-10-05: approved by the human ("approved"), who did not describe the fault further. Built on `fix/dock-keyboard-scroll`. The new checks were written first and six of them failed on the old script.

Changes from the plan:

1. **The keyboard's height no longer uses the dock's position at all.** The plan measured from the dock's bottom edge, which rests on the unproven assumption in the study. The script now compares the visible frame's height with its height when no text field is in use. Whether the keyboard is open therefore depends on one number an iPhone is known to report.
2. **"No field in use" means no keyboard.** When focus leaves every text field, the dock returns to the bottom at once, a moment before the keyboard has finished closing.
3. **The readout sits at the top of the visible frame** and also shows the heights the browser reports and whether the page runs as the installed app. It is shown to whoever opens a set page with `?kb=1` and has the dock, that is, hosts.
4. **The readout cannot be opened from the home screen app**, which has no address bar. It is for Safari. If the fault appears only in the installed app, say so and the readout gets a switch inside the app.
5. **Found while building:** the per-frame watcher started a second copy of itself each frame and froze the page within seconds. Fixed, with a check that one watcher runs once per frame.

Verification:

- `dock.mjs`: 175 of 175 on a fresh temporary database (the 163 earlier checks unchanged, plus 12).
- `lifetime.mjs` 22, `motion.mjs` 34, `flow.mjs` 52, `inplace.mjs` 38 and `navigate.mjs` 37 pass.
- 642 tests pass on SQLite (ten PostgreSQL-only skips) and in the build-style run. PostgreSQL was not rerun: a script and CSS changed.

AC1 and AC2 are met. **AC3 is not met yet: it needs the human's iPhone after release.** Not verified: anything on a real iPhone. The checks use a stand-in keyboard; they prove the script's logic for a sliding visible frame, not that an iPhone reports the values assumed, nor how smooth the bar is while the page moves.

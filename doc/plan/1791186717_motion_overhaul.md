# Motion overhaul with Motion (motion.dev): plan

Status: approved 2026-10-05 ("approved"); stage 1 in progress. Date: 2026-10-05, Asia/Manila. Study: [Motion overhaul](../study/1791186418_motion_overhaul.md).

## Outcome

The app keeps its look and gains a motion system built on Motion: screens move in a direction, sheets and buttons respond with springs, rows on the live set page arrive, leave and reorder visibly, and a few moments (books balanced, session closed, transfer paid) are marked. It stays as fast to operate as today.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new colour, font or raster asset.

## Motion principles (all stages)

1. **Motion explains.** Each animation answers one of: where did I go, what just changed, did my tap work.
2. **Never in the way.** No control waits for an animation. Every animation can be interrupted by the next tap. Interactions finish within 300ms; a signature moment within 900ms, and it plays once.
3. **Money does not animate its value.** A figure appears at its accepted value. Its row may move; its digits do not count.
4. **Reduced motion** removes movement and keeps the state change. A fade of 100ms or less is allowed.
5. **Springs for things you touch, eases for things that arrive.** One small set of named presets, recorded in DESIGN.md, used everywhere.
6. **Additive.** Without JavaScript, or if Motion does not load, every screen works as it does today.

## Stages

Each stage is released on its own and tried on your phone. Stages 2 to 4 each get their own study and plan for approval; this approval covers stage 1.

| Stage | Contents |
|---|---|
| **1. Foundation, buttons and feedback** | Motion added to the app; presets; buttons, pending and result states, toasts, sheets and the host menu moved to springs |
| **2. The live set page** | Rows arrive, leave and reorder; a buy-in lands on its stack; count-up verdict changes; the books-balanced moment |
| **3. Moving between screens** | Deeper and back have directions; a session title and a player chip carry across screens |
| **4. Results and settle-up** | Final results reveal; session recap; marking a transfer paid; closing a session |

Order: stage 1 builds what the others use. Stage 2 is next because it is the screen used most. Say so if you want another order.

## Decisions for the human

Approving the plan accepts the recommendations unless you say otherwise.

1. **How Motion is loaded.** Recommended: the full Motion file, stored in the app (48 KB compressed, downloaded once and cached for a year). The alternative is a trimmed file of about 10 to 20 KB, which adds a build step to repeat at each upgrade.
2. **Money figures stay still.** "Expressive" will not include counting or rolling numbers. That rule is in AGENTS.md; changing it is yours to do.
3. **The AI kit.** I run `npx motion-ai` for this project only and use its free docs search. If the installer needs an account or writes outside the project, I stop and tell you.
4. **Performance checks.** Motion's own audit is a paid feature. I check instead that animations use only movement and opacity and that none is left running.

## Stage 1: foundation, buttons and feedback

### What you will see

- **Buttons.** A press sinks the button and it springs back on release, in place of today's fixed 3px step. Works for every button and link styled as one.
- **Pending.** After a tap that sends something, the tapped control shows it is working: its label dims and a small brass progress line runs along its lower edge until the answer arrives.
- **Result.** When the action is accepted, the control settles with one short pulse. When it is refused, the field or notice with the error nudges sideways once (two short moves, 6px) and takes focus as today.
- **Toasts.** Spring up, and now also leave: they drop and fade. A second toast pushes the first up.
- **Sheets** (buy-in, cash-out, recap). Rise with a spring; leave faster than they arrive. A tap on Close during the rise reverses it from where it is.
- **Host menu.** The same spring as the sheets, replacing today's fixed-time slide. The keyboard behaviour released today is unchanged.
- **Reduced motion.** None of the above moves; states still change.

### Implementation

1. **Vendor Motion.** `static/js/vendor/motion-14.0.0.js` and its licence file, with the SHA-256 recorded in `doc/wiki/external-dependencies.md`. Loaded in `base.html` with `defer data-turbo-track="reload"`, before the app's motion script.
2. **`static/js/motion.js`** (new). Exposes `window.pokerMotion`: the named presets (`press`, `sheet`, `arrive`, `leave`, `nudge`, `pulse`), `on()` (false under reduced motion or when `window.Motion` is missing), and `run(element, keyframes, preset)`, which returns a no-op when `on()` is false. Registers with `window.pokerPage`; on stop it cancels every animation it started.
3. **Presets in CSS too.** The timing tokens in `app.css` stay as the no-JavaScript and reduced-motion values. Where Motion takes over an element, a class on `<html>` (`motion-on`) switches off the CSS animation for it, so nothing animates twice.
4. **Buttons.** Motion's `press` gesture on `.btn`, delegated from the document.
5. **Pending and result.** `forms.js` and `turbo-setup.js` already mark a sent control as busy and raise `inplace:updated` and `inplace:failed`. The progress line is CSS on the busy state; the pulse and the nudge are Motion calls from those events.
6. **Toasts, sheets, dock.** `toasts.js`, `sheets.js` and `dock.js` call `pokerMotion.run` in place of the CSS keyframes and the Web Animations call. Their existing behaviour without Motion remains as the fallback path.
7. **AI kit.** `npx motion-ai`, project scope, Claude Code only. Files it adds are listed in the plan's progress section.
8. **Tests first.**
   - Django: the pages load the vendored file and `motion.js` once, in order.
   - New browser check `motion.mjs` at 390 and 1280px: each animation above starts and ends in the right state; a tap during a sheet's rise closes it; a tap is accepted while a button animates; only `transform` and `opacity` animate (plus the dock's height); under reduced motion nothing animates and every state still changes; with the Motion file blocked, and with JavaScript off, every action still works; after ten screen changes no animation or listener is left over.
   - Existing checks: `dock.mjs` (163), `inplace.mjs`, `navigate.mjs`, `lifetime.mjs`, `entry.mjs`, `archive.mjs`.
9. **Verify.** SQLite suite, the build-style run, PostgreSQL before release. Captures of mid-animation frames inspected for the sheet, toast and button.
10. **Sync docs.** DESIGN.md: a "Motion system" section with the principles and presets. Wiki: features, architecture (the motion script and its lifetime), external dependencies, deployment if the header rules change. TODO: a phone checklist.

### Acceptance criteria

- AC1. Every item under "What you will see" is present and passes its browser check.
- AC2. Reduced motion, no JavaScript and a blocked Motion file each leave the app fully working.
- AC3. No action is slower: the time from tap to the request being sent is unchanged.
- AC4. All existing tests and the listed browser checks pass.
- AC5. **On your phone, after release:** the buttons, sheets, toasts and host menu feel right to you. This is a judgement only you can make; if something feels wrong, name it and it is adjusted.

### Out of scope for stage 1

- Rows arriving and reordering, screen directions, results and settle-up moments (stages 2 to 4).
- Any change to layout, colour, wording, services, models or URLs.
- Illustrations, animated chips or cards, sound, haptics.

### Rollback

Revert the stage's commits. No migration and no data change. The CSS animations it replaces come back with the revert.

## Progress and blockers

2026-10-05: Study and plan complete after one discovery round (motion on the current look; expressive; all four areas; free AI kit). Waiting for approval of the programme and stage 1.

2026-10-05: The human approved with “approved”. The four decisions stand as recommended.

2026-10-05 stage 1 execution on `feat/motion-foundation`. The script-list test was changed first and seen to fail; the browser check was written with the implementation.

Changes from the plan:

1. **The AI kit is not installed.** `npx motion-ai` (14.1.0) has no non-interactive mode; it asks questions in a terminal the agent cannot answer. The human can run it in the project folder. Stage 1 used the public Motion docs instead.
2. **The press is delegated by `motion.js`**, not Motion's `press` gesture. That gesture binds to the elements present when it is called; live updates and screen changes replace them.
3. **The dock stays on the Web Animations API** and takes the spring as a `linear()` easing from `Motion.spring`. Its checks and its interruption logic read `getAnimations()`. Closing keeps the 200ms ease-in. Where `linear()` is not supported it falls back to the previous curve.
4. **The accepted pulse** plays on the control that was tapped only if it is still on the page and not inside a sheet. After most actions the sheet closes or the control is replaced, so the pulse is rare; the row highlight remains the main confirmation. Stage 2 covers that.
5. **Toasts stack.** Two toasts used to sit on top of each other. The stacking is new behaviour, needed for "a second toast pushes the first up".
6. **No-JavaScript actions** were not rechecked in `motion.mjs`; `dock.mjs` covers them and passes.

2026-10-05 stage 1 verification:

- 639 tests pass on SQLite (ten PostgreSQL-only skips) and in the build-style run.
- `motion.mjs`: 34 of 34 on a fresh temporary database. Mid-animation captures of the sheet and the stacked toasts were inspected at 390px.
- `dock.mjs` 163, `inplace.mjs` 38, `navigate.mjs` 37, `lifetime.mjs` 22, `archive.mjs` 85 and `entry.mjs` 91 pass on fresh databases.

AC1 to AC4 are met, AC1 with change 4. **AC5 is open: how it feels on the human's phone.** Not verified: a real touch screen (the checks press with an emulated pointer), frame rate on a phone, and Safari, which draws `linear()` easing only from version 17.2.

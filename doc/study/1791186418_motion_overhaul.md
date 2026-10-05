# Motion overhaul with Motion (motion.dev): study

Date: 2026-10-05, Asia/Manila. This is stage 6 of the [app-like experience programme](../plan/1791172782_app_like_experience.md), which recorded the requirement for the library on 2026-10-04.

## Request

"I want to initialize a motion graphic and UI overhaul using motion.dev."

## Discovery answers (2026-10-05)

1. **Scope.** Motion on the current look. The dark Rack design stays; layout and colour change only where an animation needs it.
2. **Intensity.** Expressive: directional screen changes, springy sheets and buttons, rows that slide in and reorder, a few signature moments. Still fast during play. Not a showpiece.
3. **Priorities.** All four areas: the live set page, buttons and feedback, results and settle-up, moving between screens.
4. **AI kit.** The free kit only. No Motion+ membership.

## What moves today

All motion is CSS, plus one Web Animations call. Tokens: `--t-press` 110ms, `--t-fast` 180ms, `--t-sheet` 320ms, `--t-focal` 600ms, one ease-out and one ease-in curve.

| Where | Motion |
|---|---|
| Buttons | Press moves 3px and drops the shadow |
| Sheets | Rise 24px and fade in 320ms; leave in 200ms |
| Toasts | Rise 12px; no exit |
| Host dock | Height slide, 320/200ms (`dock.js`, Web Animations) |
| A changed row | Brass outline for 3s; a new buy-in edge drops in |
| Books balanced | A 600ms left-to-right reveal of the green rule, once per set |
| Session recap | Lines reveal by clip, staggered 60ms |
| Screen changes | A 180ms cross-fade (View Transitions through Turbo) |

There is no direction between screens, no entering or leaving of rows, no reorder motion, no pending or success motion on a control, and no springs.

## Motion, the library

Checked on 2026-10-05 against motion.dev and the npm registry.

- **Version and licence.** `motion` 14.0.0, MIT.
- **Without a build step.** The package ships one standalone file, `dist/motion.js`, which defines a global `Motion`. Measured: 143,867 bytes, 47,790 gzipped. The 2.3 KB "mini" `animate` exists only as an import that a bundler trims; this project has no bundler.
- **Functions in the standalone file.** `animate` (springs, sequences, interruption), `stagger`, `scroll`, `inView`, `hover`, `press`, `animateView` (a wrapper over the browser's View Transition API, with shared elements), and layout animation.
- **For comparison.** The app's own scripts total 43 KB unminified. Turbo is 217 KB. Motion would be the second library.

## The Motion AI kit

- Installed with `npx motion-ai`, per project or globally. It is an interactive installer.
- **Free:** search of the current Motion docs and best practices. No account or token.
- **Motion+ (paid):** MotionScore performance audits, CSS spring generation, the transition editor, source of premium examples. Declined by the human, so these are not available. A `motion-reviewer` agent is listed in this session; it reports MotionScore tiers, so it probably needs Motion+. Unverified.
- No Motion MCP tool is connected in this session.

## Constraints

1. **AGENTS.md rule 9.** Money figures appear at their accepted value: no counting up, no rolling digits. Reduced motion disables movement. Both stay.
2. **Works without JavaScript**, and must work if the Motion file fails to load. Motion only adds; no control may wait for an animation before it works.
3. **No build step.** A library is a vendored, pinned file with its licence, like Turbo.
4. **Script lifetime.** Every script registers with `window.pokerPage` and stops cleanly ([footgun](../wiki/footguns/scripts_run_once_per_tab.md)). Running animations must be cancelled on stop.
5. **Live updates replace the HTML** of the live region (`live.js`, `region.innerHTML`). Elements are new after each update, so nothing can animate from its old position unless the old positions are recorded by key first. Rows already carry keys (`data-watch`). Actions sent from the page use Turbo's morph, which keeps elements.
6. **Screen changes** already run through the View Transition API. Direction and shared elements can be added there. iOS supports it from version 18; older iPhones get no transition, which is acceptable.
7. **Speed at the table.** A host records a buy-in in a few taps. An animation must never delay the next tap; interactions stay under about 300ms and can be interrupted.
8. **Performance.** Animate `transform` and `opacity`; anything else (height, clip) only on small elements. Without MotionScore, this is checked by listing running animations in the browser checks.
9. **The offline and installed-app layer** serves scripts from the network with long caching. A new vendored file needs no change there.
10. **No preview deployment.** Each stage is released whole and tried on the human's phone. Each must be safe to leave live if it disappoints.
11. **Verification limit.** Browser checks prove that animations start, end in the right state, are skipped under reduced motion and leave no listener behind. They cannot judge whether motion feels right. Only the human can.

## Options for loading Motion

1. **Vendor the full standalone file** (recommended). 48 KB gzipped, cached for a year, no tooling. Every function is available to later stages.
2. **A one-off trimmed bundle.** Run a bundler once to keep only the functions used (perhaps 10 to 20 KB), and vendor the result. Smaller, but it adds a build step to repeat at every Motion upgrade and whenever a stage needs another function.
3. **A pinned CDN address.** Rejected: a third party in the path of every page load, and the installed app would depend on it.

## Size of the work

Four areas at an expressive level is several cycles. One plan cannot specify all of it well. The plan therefore sets the shared rules and the order, and details only the first stage.

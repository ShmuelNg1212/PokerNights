# Plan: installed iPhone motion fixes

Mode: mixed. Direction: refine The Rack. Base: `976b889`.

Study: [installed iPhone motion](../study/1793517118_iphone_motion.md).

Status: release authorized on 2026-11-01 after the 58/60 report. Source commits are `b287f66` and `af5daa2`, on `fix/iphone-motion` from `b969b2a`. Release gates and doc sync are complete. The plan is frozen with the verification limits below. Merge and push are authorized.

## OPEN QUESTIONS

The human approved this scope on 2026-11-01. The iPhone model, iOS version and worst affected button are still unknown. These details can refine the checks. They do not block the confirmed sheet and caret fixes.

Do not treat this plan as authority to change an unrelated navigation path. If a separate hitch needs another change area, report the repro and ask to extend the scope.

## Outcome

Sheets start in their entry position on their first visible frame. Expanding sections have useful motion on supported iPhone browsers. The account flyout stays aligned and answers rapid presses. Reduced motion keeps immediate, readable state changes.

The human used an iPhone app added to the Home Screen from Chrome. Desktop Chrome alone cannot verify that experience.

## Bounds and decisions for approval

- Keep the current palette, layout, 48 px targets, curves and motion presets.
- Keep native details and dialog semantics. Keep the current focus rules unless a repro proves a defect.
- Add a disclosure fallback only when native interpolation is absent. Prefer the existing native path when it works.
- Give each menu one motion owner. Exclude the account flyout and script-owned menus from generic disclosure motion. Check the RSVP and checklist owners before applying a fallback.
- Use measured height only for in-flow disclosure expansion. This is the existing layout exception. Use transform and opacity for overlays.
- Keep forms usable without Motion or JavaScript. Money remains at its accepted value.
- Change no service, database, amount, permission or session-state rule.
- The approved draw-from-draft plan remains separate.

Approval also permits a narrow DESIGN.md update. It will replace the Slice F statement that unsupported disclosures always snap with the new fallback behavior. This is a presentation change. It changes no product or money rule.

## Tasks

### 1. Fix the sheet's first frame — tests: alongside

- [x] Add a regression check at the real sheet opener. Sample from before opening. Fail if no sheet opens. Fail if it first appears at rest and then jumps to its entry position.
- [x] Confirm failure on the current source. The study failed three of three runs.
- [x] Set the sheet's entry position before Motion can draw its first frame. Use the existing sheet preset.
- [x] Clear the style after completion, close, interruption and page cleanup. Prevent an older completion from clearing a newer movement.
- [x] Check a rapid close during entry, reopening, and swapping from player details to cash-out. Check keyboard focus and typed values.

Files: `static/js/sheets.js`, `web/tests/browser/motion.mjs`. Extend an existing helper only when needed.

Acceptance: three consecutive openings start at entry and move toward rest. No fully visible frame appears at rest before the rise. A rapid close or reopen leaves one correct state and no stale transform. Reduced motion opens at rest at once. A blocked Motion file keeps the CSS or native fallback.

Complete when the regression and existing sheet checks pass on the source fix.

### 2. Give in-flow menus a compatible fallback — tests: alongside

- [x] Inventory the expanding sections on group settings, set Details, More host controls, result rows and preparation steps. Identify each motion owner.
- [x] Add a focused regression check with native interpolation unavailable. Check an intermediate content height. Do not count a turning chevron as content motion.
- [x] Keep the native path when both required CSS features work. Add a small shared fallback for the scoped in-flow disclosures when they do not.
- [x] Keep the content connected to its summary. Support open, close and reversal from the current position. Reuse the existing 200 ms disclosure timing and ease-out curve.
- [x] Exclude overlay and script-owned menus from the generic path. Do not run the native and fallback paths together.
- [x] Remove temporary size and clipping styles at rest. Release listeners and observers on page cleanup.
- [x] Check a live update during an open disclosure and during a checklist completion. Keep the person's choice. Do not restore a temporary automatic open.

Files: `static/css/app.css`, the existing page/motion registration, and a small disclosure module if needed. Register it through the existing script-loading path. Extend `web/tests/browser/fluid.mjs` or add one focused browser probe.

Acceptance: native and fallback paths each show a measured intermediate height. Rapid open-close-open reaches the final requested state. The header flyout and RSVP retain their own movement. Reduced motion and no JavaScript show correct content at once. No controls remain clipped at rest.

Complete when the capability-off check fails on the old source and passes on the fallback. WebKit must exercise the fallback when its capability check is false.

### 3. Fix the account flyout alignment — tests: alongside

- [x] Isolate the 8 px resting caret error. Compare untransformed panel geometry, entry geometry and the existing caret clamp. Do not change the clamp without evidence.
- [x] Fix the measurement at its owner. Keep the panel inside the viewport.
- [x] Check first open, close, reversal during close, Escape, outside press and navigation. Check ordinary and narrow widths.
- [x] If the bell uses the same defective measurement, add the same evidence before applying the bounded correction there.

Files: `static/js/account.js`, `web/tests/browser/header.mjs`. Touch shared panel CSS or `alerts.js` only if the same repro requires it.

Acceptance: the caret ends within 2 px of the token center at 320, 390 and 1280 px. The panel stays at least 8 px inside the screen. It does not flash or disappear during reversal. Focus returns correctly.

Complete when the failing header check and the related interaction checks pass.

### 4. Rendezvous — tests: alongside

- [x] Run the affected Django tests before each code commit. Run the SQLite suite before completion.
- [x] Run header, motion, fluid, table and dock browser checks sequentially. Use fresh synthetic fixtures for checks that consume records.
- [x] Compare any existing failure by name with the base. Do not waive a new failure because the suite already had failures.
- [x] Exercise the first signed-in action: open a player's sheet, close during entry, reopen, and make one synthetic buy-in. Verify one accepted record and exact displayed amount.
- [x] Check group settings and More host controls by real touch where possible. Check navigation to a set and Back. Keep no-navigation-rewrite scope unless a separate defect is reproduced.
- [x] Run a WebKit check in available automation or desktop Safari. Record the engine and version. A Chromium capability override is supplementary evidence.
- [x] Inspect phone-width screenshots and frame samples. Test reduced motion, blocked Motion, no JavaScript, long content and a live refresh.
- [x] Run independent read-only standards/spec and motion reviews under the AGENTS.md rendezvous rules. Request verdict, evidence and file:line for each finding.
- [x] Allow two fix-and-recheck rounds. If a check still fails, stop and ask. Record all verdicts below.

Acceptance: the new regression checks pass. Existing behavior remains correct. No unexplained new failure remains. Record every unverified phone behavior explicitly.

Complete when the local feature branch is verified and the checks below are recorded. Do not claim a physical-iPhone or installed-mode pass without that test.

### 5. Sync docs — tests: alongside

- [x] Update DESIGN.md and the relevant wiki behavior text. Delete the stale unconditional snap statement.
- [x] Add the first-frame sheet case to the existing motion footgun if the source fix confirms it.
- [x] Update TODO.md with unreleased phone checks. Keep it at 40 lines or fewer.
- [x] Update the browser README with the new regression command and fixture needs.
- [x] Run `graphify update .` after source changes. Keep graph artifacts out of commits.
- [x] Record final commits and checks in this plan. Freeze it after rendezvous.

Complete when the docs match the code, the branch is clean, and this plan has the verification record.

## Execution and release

Create a feature branch from the latest unreleased stack after approval. Keep related fixes in separate Conventional Commits. Tasks share files, so do not delegate code writing. Read-only rendezvous checks can run independently.

Do not merge or push until the human says ship or push. Run PostgreSQL before release. Follow the existing production verification rule. Do not offer a preview deployment.

After release, the phone checks are:

1. Launch the installed app. Open and close the account menu several times. Reverse it during close.
2. Open group settings, set Details and More host controls. Check that content expands and closes smoothly.
3. Open a player, then cash-out or buy-in. Close during entry and reopen. Check that no flash appears and the keyboard does not move the page unexpectedly.
4. Move from the group to a set and Back. Repeat with Reduce Motion on.

## Verification record

Task 1: the new checks failed on the old source (34/40). With the source fix and fresh fixtures, motion passed 40/40. The 7 in-place rendering tests passed. A first repeat used consumed fixtures and failed two write checks; reject that run. The fresh run passed those checks. Standards, spec and motion reviews later approved the source. The motion review correction is recorded below.


### Rendezvous checkpoint, 2026-11-01

- SQLite: 1,670 tests passed. 17 PostgreSQL-only tests were skipped.
- In-place rendering and script loading: 7 tests passed on the final source.
- Header: 106/106 passed at 320, 390 and 1280 px. Excluding `.account` from generic native height motion fixed the caret error. `account.js` needed no change.
- Sheet motion: 40/40 passed with fresh fixtures. The new first-frame and cleanup checks failed on the old source and passed with the fix.
- Chromium 156.0.8078.76 and WebKit 27.2: the original cross-browser probe passed 52/52. The expanded probe now passes 58/60. It covers native support and forced fallback, expanding content, reversal, live close state, sheet first frame, interrupted entry, swap focus, navigation, reduced motion, checklist polling and no JavaScript.
- Standards and spec reviewers approved. The motion reviewer found late closing indicators. The three CSS guards were corrected. The reviewer then approved.
- A new close-indicator assertion still fails in both Chromium paths after two rechecks. It reads caret matrix A as -1 at 50 ms. The requested closed state and restored summary text pass. Both WebKit paths pass the complete indicator assertion.
- A focused Chrome probe shows the caret moving correctly. It measured A=-1 at close, then A=0.900362 after 50 ms, then reached rest. This conflicts with the full probe. Do not claim that the timing assertion passes.
- One earlier run reported the exact browser view-transition rejection recorded in `doc/wiki/footguns/view_transition_opt_in_rejects_under_load.md`. The next two runs had no runtime errors. They failed only the new close-indicator assertion.
- The new probe's first checklist sample used only animation frames. A fast poll could end the hold before that sample. The probe now also records the completion event before the poll. It checks that the automatic open is not restored. All four checklist cases pass.
- The reduced-motion probe now starts from an explicit closed state. WebKit Back can retain an open disclosure. All four reduced-motion cases pass.
- The final sequential controller stopped at the mobile probe. Fluid, table, dock and the post-fallback motion rerun have not run. Do not record them as passed.
- The physical iPhone and installed mode remain unverified. No merge or push was made.

The agent stopped at the two-round limit. The human then said “shp it”. This authorizes the release after the stated 58/60 report. The timing assertion remains unresolved. The release record below keeps that limit explicit.


### Release checks, 2026-11-01

- Human authorization: “shp it”, after the known browser-check limit was reported.
- PostgreSQL: 1,670 tests passed. No skips.
- Vercel-style SQLite: 1,670 tests passed, 17 PostgreSQL-only skips. A second run with DEBUG disabled also passed all 1,670 tests with the same skips.
- Header: 106/106 passed. Table: 60/60 passed. Dock: 226/228. Its only failures are the known baseline checks `toggle keeps focus across live update` and `bar verdict follows typing`.
- Fluid: 23/24. The failure was `poll: the completed tick is visible before the fold closes`. Released `main` at `976b889` failed the same assertion with the same closed fold and missing tick. This is a baseline failure, separate from the unresolved new Chromium assertion.
- Independent standards and spec reviews found no actionable issue. Motion review approved after the bounded closing-state correction.
- Three doc agents each updated one wiki page. The main agent checked the text against the code. DESIGN.md and the browser README now describe the fallback and first-frame fix. TODO.md keeps the phone checks in 40 lines.
- The physical iPhone and installed-app experience remain phone checks. The new cross-browser probe is still 58/60. It is not a full pass.

- Final sheet motion rerun: 40/40 passed after the disclosure fallback changes. The first real sheet action added exactly one 50,000-centavo buy-in. The request ID was unique. The final database had three expected additions from normal, reduced-motion and blocked-library actions. All request IDs were distinct.
- Source commits: `b287f66` fixes the sheet's first frame. `af5daa2` adds compatible disclosure motion and isolates menu owners. No money, schema, permission or navigation rule changed.
- The local feature tree is ready for the authorized fast-forward merge and push. Production build and serving status must be checked after that push. Keep those results in work state. Do not rewrite this frozen task board.

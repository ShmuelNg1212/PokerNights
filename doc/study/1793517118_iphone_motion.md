# Study: installed iPhone motion

Date: 2026-11-01. Mode: mixed. Base: `976b889` on `main`.

## Report

The human reports missing flyout motion and screens that skip or hitch after a button press. Desktop feels more fluid. The affected app was added to the iPhone Home Screen from Google Chrome.

The iPhone model, iOS version and worst affected button are not known. A physical phone was not connected.

## Scope

Study the common menu, sheet and navigation paths. Keep The Rack and the current motion presets. This work needs more than one commit. Prepare a plan before source changes.

Skills used: diagnosing-bugs, mem-search, motion and mobile-native. Read the skills-per-stage table. Read the design-taste fallback. Its page-composition workflow excludes app screens, so use DESIGN.md for this app review. No domain rule changes are needed.

## Context

- Slice F replaced scripted disclosure motion with native CSS height interpolation. It deliberately leaves unsupported browsers with a snap.
- The account flyout has its own Motion animation. It is separate from an in-flow expanding section.
- The project already records the late-first-keyframe problem in [this footgun](../wiki/footguns/motion_starts_a_frame_late.md).
- Read the graph before source searches. Read the recent plan, git history, glossary and ADR list. No money, permission or session-state rule is in scope.
- Memory search used search, timeline, then selected observations 3383, 3384 and 117.

## Confirmed findings

### 1. A sheet has a wrong first animation frame

`static/js/sheets.js:14` shows the dialog. Line 16 starts its entry animation. The entry position is not set before Motion starts.

A temporary probe used the real sheet click handler on `/s/3/`, at 390 by 844. It sampled computed transform and opacity on each animation frame. It opened and closed the first buy-in sheet three times.

| Run | First open-frame Y | Later Y | Result |
|---|---|---|---|
| 1 | 0 px | 546.516 px | Fail |
| 2 | 0 px | 569.490 px | Fail |
| 3 | 0 px | 530.282 px | Fail |

The first open frame was fully opaque. It was already at rest. The next frames put it below the screen and then brought it back. This can read as a flash or hitch.

Command: `PN_REVIEW_DIR=/private/tmp/pn-mobile-study-probe node /private/tmp/pn-mobile-first-frame.mjs`. Exit: 1. Each run printed `FAIL sheet first visible frame starts in its entry position`.

This is computed frame evidence in desktop Chrome. It is not a film of the human's iPhone.

Ranked causes, before the browser-only experiment:

1. Motion applies the first keyframe late. Setting the entry transform before the call will remove the wrong first frame.
2. Focus changes the sheet position. A transform preset alone will not remove a focus-induced jump.
3. A viewport change moves the sheet. The jump will remain when only the entry transform changes.

The browser-only experiment changed one variable. A wrapper set the first transform before the existing Motion call. It did not change focus, content, timing or the viewport. All three repetitions passed. The first Y was 595 px in each run. The sheet then rose to rest.

Command: `PN_REVIEW_DIR=/private/tmp/pn-mobile-study-probe node /private/tmp/pn-mobile-first-frame-preset.mjs`. Exit: 0. All three runs printed `PASS sheet first visible frame starts in its entry position`.

Conclusion: a missing initial transform causes this measured first-frame defect. Source files were not changed. A source fix must also clear its own style after interrupted motion.

### 2. Expanding-menu motion has a browser support gap

`static/css/app.css:1166` requires both `interpolate-size: allow-keywords` and `details::details-content`. If either is absent, there is no height animation.

WebKit added `::details-content` in [Safari 18.4](https://webkit.org/blog/16574/webkit-features-in-safari-18-4/). WebKit lists `interpolate-size` as a new feature in [Safari Technology Preview 254](https://webkit.org/blog/18420/release-notes-for-safari-technology-preview-254/). Its [implementation issue](https://bugs.webkit.org/show_bug.cgi?id=324460) records the September 2026 change.

Inference: this gate can explain why expanding sections move on desktop Chrome and snap on the iPhone. The user's exact iOS capability is not verified. Do not claim that every iPhone lacks support. Test capability, not a browser name.

### 3. The account flyout caret is misaligned

Command: `PN_WIDTHS=390 PN_REVIEW_DIR=/private/tmp/pn-mobile-study-header node web/tests/browser/header.mjs`.

Result: 37 of 38 checks passed. The failing check was `390 the panel's caret points at the token`. A separate resting measurement found an 8 px alignment error. The screenshot shows the flyout inside the screen.

Open, close, Escape, outside press, reversal during close, same-page refresh and navigation passed. The reduced-motion and no-script checks passed. These results do not prove the same paths on an installed iPhone.

Relevant source: `static/js/account.js:19` measures the panel and token before entry. The cause of the caret error still needs isolation. Do not change its clamp from this measurement alone.

## Limits and rejected evidence

- A CDP display-mode override did not set `matchMedia('(display-mode: standalone)').matches` to true. Both measured runs remained in browser mode. They are not installed-app tests.
- An initial minimized touch probe targeted a hidden or unavailable opener. It did not open the sheet. Reject its empty samples. The final three-run repro used the real delegated click handler and refused an unopened sheet.
- The broader touch probe saw the same sheet first-frame pattern. Use the minimized handler probe for the repeatable signal.
- Chrome ran headless with GPU disabled, as the existing scripts do. These checks establish motion order and geometry. They do not measure real iPhone frame rate.
- The machine has desktop Safari. It has no cached Playwright WebKit runtime. No WebKit or physical-iPhone check ran in this study.
- No exact navigation hitch from the human's phone has been reproduced. Do not rewrite navigation on this evidence.

## Proposed scope

1. Lock the sheet's first frame and interruption cleanup with a browser regression check.
2. Add a bounded disclosure fallback where native height interpolation is absent. Keep one animation owner per menu.
3. Isolate and fix the account caret defect. Check rapid opening, closing and reopening.
4. Check touch, focus, navigation, reduced motion and missing-script behavior in Chromium and WebKit. Record real-phone checks separately.

No application code, design contract or wiki behavior changed during study.

## Reproduction setup

Use a fresh temporary SQLite database. Migrate it. Seed `seed.py`, `seed_end_set.py`, `seed_night.py` and `seed_opening.py`, in that order. Start Django on `127.0.0.1:8765` with that database. The fixture accounts are synthetic.

The temporary frame probes reuse the CDP setup and synthetic login from `header.mjs`. Sample `dialog.sheet.open`, its computed transform Y, and opacity with `requestAnimationFrame`. Start sampling before the first `[data-sheet-open^=buy]` click. Fail if the first open frame has Y zero and opacity one, followed by a large positive Y. Also fail if the sheet never opens. Wait for the close to finish between repetitions.

The existing motion check waits 60 ms before its first sheet sample (`web/tests/browser/motion.mjs:44`). It can miss this first-frame defect.

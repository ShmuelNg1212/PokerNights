# A splash screen for the installed app: plan

Status: approved 2026-10-14 ("approve", with the recommended answers: mark and name, the clear Android icon, no movement this cycle). Built on `feat/launch-splash`; released 2026-10-14 as `c222173` on the human's word "release" (previous production commit `6c39be3`). The first push, `ba7e297`, failed the Vercel build: a new test read `make_splash.mjs`, which `.vercelignore` leaves out ([footgun](../wiki/footguns/vercel_build_lacks_ignored_files.md)). The test now skips there; four minutes after the fix the live site served `splash-1179x2556.png` (46,544 bytes, as built) and a manifest naming `app-any-512.png`. Date: 2026-10-14, Asia/Manila. Study: [A splash screen for the installed app](../study/1791953082_launch_splash.md).

## Outcome

Opening PokerNights from the home screen of an iPhone shows the chip mark with "PokerNights" below it, centred on the app's dark ground, until the first screen paints. Today that moment is blank. Android already draws a splash; its icon loses the lighter square behind the chip, so both phones open the same way.

No migration, no new setting, nothing a person does in the app changes.

## Decisions for the human

1. **What the splash shows.** Recommended: the mark and the name (study, option B). Alternatives: the mark alone (A), or mark, name and a line (C).
2. **Android's icon.** Recommended: ship the transparent `any` icons, since Android players then see the same splash. Say no if nobody in the group uses Android.
3. **The movement into the first screen** (the mark gliding into the header on a cold launch). Recommended: not in this cycle. Look at the static splash on the phone first; the movement is its own small plan if wanted.

## Implementation

Branch `feat/launch-splash` from `main`.

1. **The source.** `static/branding/splash.svg`: the mark from `logo-mark.svg` above the outlined "PokerNights" from `logo-horizontal.svg`, on `#130e0a`. The group sits a little above the centre, as the front door's hero does, and is sized by the screen's width so it looks the same on every phone.
2. **The images.** `web/tests/browser/make_splash.mjs`, in the manner of `make_icons.mjs`: headless Chrome renders the SVG at each of the study's twelve sizes to `static/splash/splash-{width}x{height}.png`. Each under 60 KB.
3. **The tags.** `templates/partials/startup_images.html`, included in the head of `base.html`: one `<link rel="apple-touch-startup-image">` per size with its exact media query (`device-width`, `device-height`, `-webkit-device-pixel-ratio`, `orientation: portrait`). The sizes are listed once, in a module the template and the tests both read.
4. **Android.** `make_icons.mjs` also writes `app-any-192.png` and `app-any-512.png`: the chip on a transparent ground. The manifest's `any` entries point at them; `app-192.png` and `app-512.png` stay for anything that already links to them; the maskable icon and the 180 px iPhone icon do not change. If decision 2 is no, this step is left out.
5. **Caching.** `vercel.json` already gives `/static/branding/` and `/static/icons/` a week's cache; `/static/splash/` gets the same rule. New art later means new file names, as the icons note says.
6. **Tests** in `web/tests/test_branding.py`:
   - a page carries a startup-image tag for each size, with the right media query;
   - each image exists and its PNG header gives the size its tag promises, and it is under 60 KB;
   - the manifest's `any` icons exist, are the sizes they claim and have a transparent corner pixel; the maskable icon is unchanged.
7. **Docs.** `doc/wiki/features.md` "Installable app": splash images move from "Not built" to built, with the note about adding the app again; `DESIGN.md` gets one line on the launch screen; `TODO.md` gets the phone check.

## Acceptance

1. The Django suite passes on SQLite and PostgreSQL.
2. The twelve images are looked at, by rendering two of them (smallest and largest) side by side with a screenshot of Your groups at the same size: same ground, mark not clipped by the notch or the home bar.
3. On the human's iPhone, after removing the app and adding it again: a cold start shows the mark and the name, then the first screen, with no white flash.
4. If an Android phone is at hand: the splash shows the chip without a lighter square.

## Fail-safe

The images and tags only add to what a phone may show at launch. A phone with no matching size shows the blank launch it shows today. Removing the include from `base.html` undoes the iPhone part; pointing the manifest back at the old icons undoes the Android part. Both are one-line reverts.

## Not covered

- iPads and landscape.
- The movement into the first screen (decision 3).
- Installs made before the release: each person removes the app and adds it again to see the splash, and logs in once more inside it.

## Release

Built and checked locally, then held for the human's word, as usual. After a release, one request for one splash image and the manifest about four minutes after the push to confirm the live site serves them.

## Progress

- [x] Approve the plan and answer the three decisions. Approved 2026-10-14.
- [x] Build, test, and look at the images.
- [x] Say when to merge and release it. Released 2026-10-14.
- [ ] On your iPhone: remove PokerNights from the home screen, add it again from Safari, log in, close it fully, and open it. Say whether the splash looks right and whether the change to the first screen feels smooth.

## Verification record (2026-10-14)

- **Built with the design and motion skills**, as asked. The source page links the app's own `app.css` and copies the front door's mark, so the launch is the hero itself: the stacked chip at 96px, the name in `.entry-name`, on Ground, with the group a little above the middle (`padding-bottom: 9vh`). This replaced the plan's `splash.svg`: the real stylesheet keeps the colours and type from drifting.
- **Images.** Twelve, 27 to 49 KB. The renderer refuses to capture before Archivo has loaded.
- **Looked at, once:** the smallest (750 × 1334) and largest (1320 × 2868) beside the log-in page at the same size, reduced motion. Same ground, same mark and name; nothing near the notch or the home bar. The old `any` icon on the splash colour shows the lighter square the study expected; the new one sits clean.
- **Icons.** Re-running `make_icons.mjs` rewrote the four existing PNGs byte for byte; only the two new files changed.
- **Fail-safe confirmed:** static files are served by name (`config/storage.py`, no hashed manifest), so a missing image cannot break a page.
- **Tests.** 4 new in `web/tests/test_branding.py`. 1,118 pass on SQLite and on PostgreSQL 17. `manage.py test --parallel` stops with "cannot pickle 'traceback' object" on this branch and on `main` alike; the suite as AGENTS.md runs it passes.
- **Not checked:** the launch itself. No iOS simulator or Android device here.

### Ruling made while building

- **The front door's arrival after the splash.** On a signed-out cold launch the splash shows the chip, then the front door paints with its chip hidden and drops it in (`door-drop`, 700 ms), so the chip blinks out and back. Signed in, the launch goes to Your groups, which has no arrival, and the change is a cut. Left as it is: the plan adds no movement. If the blink shows on the phone, the movement follow-up (decision 3) is where it belongs: on a launch from the home screen, the hero should start visible and still.

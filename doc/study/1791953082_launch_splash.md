# A splash screen for the installed app: study

Date: 2026-10-14, Asia/Manila. Base: `main` at `6c39be3`.

## Request

The human wants a splash screen when the installed app opens, as part of making the app feel more premium.

## Understanding

- **Said:** a splash screen for the installed app.
- **Assumed:** the moment between tapping the home-screen icon and the first screen. Today that moment is blank on an iPhone. The human's phone is an iPhone; some players may use Android.
- **Success:** a cold start on the human's iPhone shows the PokerNights mark on the app's dark ground, then the first screen, with no white or empty flash.

## What happens now

- **iPhone.** `templates/base.html` has `apple-mobile-web-app-capable`, a title, a black status bar and the 180 px touch icon. It has no `apple-touch-startup-image`. Safari draws no splash of its own for a home-screen app, so the launch shows a blank screen until the first page paints. That wait includes the trip to Vercel (about 200 ms measured on 2026-10-06, more when a function starts cold).
- **Android.** Chrome draws a splash by itself from the manifest: `background_color` `#130e0a`, the `name` and a 512 px icon. It exists today. The `any` icons (`static/icons/app-192.png`, `app-512.png`) are the mark on a full `#231d17` square, so the splash probably shows a lighter square on the darker ground. This cannot be checked here; no Android phone or emulator is at hand.
- **Colours already agree.** The manifest's `background_color` `#130e0a` is the page's `--ground` (`oklch(0.17 0.012 60)`), and `theme_color` `#1e1813` is `--rail`. The splash can use the same ground, so the change from splash to page is one colour.
- **Tools.** `web/tests/browser/make_icons.mjs` renders `static/branding/app-icon.svg` to PNGs with headless Chrome. The same approach can render splash images. No ImageMagick, rsvg or iOS simulator is installed.

## What an iPhone needs

- One PNG per screen size, named in a `<link rel="apple-touch-startup-image">` whose media query gives the exact `device-width`, `device-height`, `-webkit-device-pixel-ratio` and `orientation`. A phone with no matching tag shows the blank screen, as now. A wrong size is not stretched; it is skipped.
- The app is portrait only (`"orientation": "portrait"` in the manifest), so portrait images are enough for iPhones.
- Current iPhone sizes, in CSS pixels at the pixel ratio, and the image each needs:

| Screen | Ratio | Image | Phones |
|---|---|---|---|
| 375 × 667 | 2 | 750 × 1334 | SE (2nd, 3rd), 8 |
| 414 × 736 | 3 | 1242 × 2208 | 8 Plus |
| 375 × 812 | 3 | 1125 × 2436 | X, XS, 11 Pro, 12 mini, 13 mini |
| 414 × 896 | 2 | 828 × 1792 | XR, 11 |
| 414 × 896 | 3 | 1242 × 2688 | XS Max, 11 Pro Max |
| 390 × 844 | 3 | 1170 × 2532 | 12, 13, 14, 16e |
| 428 × 926 | 3 | 1284 × 2778 | 12 Pro Max, 13 Pro Max, 14 Plus |
| 393 × 852 | 3 | 1179 × 2556 | 14 Pro, 15, 15 Pro, 16 |
| 430 × 932 | 3 | 1290 × 2796 | 14 Pro Max, 15 Plus, 15 Pro Max, 16 Plus |
| 402 × 874 | 3 | 1206 × 2622 | 16 Pro, 17, 17 Pro |
| 440 × 956 | 3 | 1320 × 2868 | 16 Pro Max, 17 Pro Max |
| 420 × 912 | 3 | 1260 × 2736 | Air |

  Twelve images. A flat dark field with a small mark compresses well; an estimate is 15 to 40 KB each. A phone downloads only the one that matches.
- **iOS reads the startup image when the app is added to the home screen.** An app installed before the release keeps its blank launch until it is removed and added again. This is widely reported and could not be confirmed here; the phone check will show it.
- The tags must be on whatever page the person is on when they tap Add to Home Screen, so they belong in `base.html` (every page). About 12 short lines; a few hundred bytes after compression.

## What the splash shows

Apple's guidance is that a launch screen should look like the first screen, not advertise. Android's own splash shows the icon and the name. The app's first screen is Your groups (or the front door when signed out), which carries the mark in the header and, on the front door, as the hero.

- **A. The mark alone, centred on the ground.** Quietest. Closest to the front door's hero.
- **B. The mark with "PokerNights" below it in Archivo (recommended).** Matches what Android already shows, so both phones open the same way. The lettering comes from the outlined Archivo in `static/branding/logo-horizontal.svg`, so the font file is not needed.
- **C. Mark, name and a line such as "Who pays whom, worked out."** More of a poster. It reads like an advert, and the moment is often under half a second.

## Carrying the mark into the first screen

A static splash ends with a cut to the page. A further step would be a short movement on a cold launch only: the centred mark shrinks and slides into the header's mark while the page fades in under it. The app already does this kind of carry on the front door (`door.js`, `DOOR_MOTION`).

- It needs a way to know the page is the first one after a launch from the home screen (`display-mode: standalone` and no earlier page in this tab), and it must not play on a reload after 30 seconds away (`app.js` reloads stale pages).
- It adds about half a second of movement, which a tap would end, and reduced motion would skip.
- It is separate from the images and can be added after the human has seen the static splash on the phone.

## Android's square

If the `any` icon shows as a lighter square on the splash, the fix is `any` icons with a transparent background (the chip alone), under new file names because icons are cached for a week without a version. The `maskable` icon, which Android uses on the home screen, keeps its square. Without an Android phone this is a probable flaw, not a seen one.

## Risks

- **Not verifiable here.** No iOS simulator and no Android device. The images and tags can be checked by size and by test; the launch itself only on a phone.
- **Existing installs.** The human, and every player who has installed the app, must remove it and add it again to see the splash on an iPhone. On an iPhone the installed app keeps its own login, so that means one log-in again.
- **A size missing.** A phone whose size is not in the list shows the blank launch, as now. Nothing breaks.
- **iPad.** Not covered; an iPad keeps the blank launch.
- **Fail-safe.** Removing the tags returns today's launch. Nothing a person does in the app changes.

## Conclusions

1. On an iPhone there is no splash today, and one needs twelve generated images and twelve tags in `base.html`.
2. On Android a splash exists; its icon probably needs a transparent version.
3. Option B (mark and name) makes both phones open the same way.
4. The movement into the first screen is worth deciding after the static splash has been seen on the phone.

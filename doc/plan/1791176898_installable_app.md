# Installable app (stage 2): plan

Status: approved 2026-10-05 ("approved"); all seven decisions as recommended. Date: 2026-10-05, Asia/Manila. Study: [Installable app](../study/1791176837_installable_app.md). Programme: [app-like experience](1791172782_app_like_experience.md).

## Outcome

A host or player can add PokerNights to a phone's home screen with its own icon and open it full-screen. Inside it, no screen is a dead end, screens are fresh when the person returns to the app, and losing the connection is stated plainly.

No app store, no offline recording, no ledger page stored on the phone. No migration.

## What gets built

### 1. Manifest and icons

- `manifest.webmanifest`: name and short name "PokerNights", description from PRODUCT.md, start address `/`, scope `/`, `display: standalone`, portrait orientation, and the app's ground colour for background and theme.
- PNG icons rendered from the existing `static/branding/app-icon.svg` with headless Chrome: 180 (iPhone), 192, 512, and a 512 maskable version with the mark inside the safe zone. New file names under `static/icons/`.
- `base.html`: the manifest link, the touch icon, the iPhone standalone meta tags and the app title.
- The `theme-color` is corrected to match the header surface exactly, so the Android toolbar and the header are one colour.

### 2. Full-screen behaviour

- **Status bar:** the default style. The system draws its own bar; no layout changes.
- **Fresh on return.** When the app comes back to the foreground after more than 30 seconds, a page that does not refresh itself reloads, unless the person has typed something that is not saved or a sheet is open. The set page keeps its own 4-second refresh.
- **No dead ends.** A browser check walks every screen in standalone display mode and asserts each has a link back or to Your groups. Anything missing is added.

### 3. Connection

- **Notice.** While the phone reports no connection, a fixed line at the top reads "You're offline. Changes can't be saved until you reconnect." It clears on return. It is announced to screen readers once.
- **Forms while offline.** Submitting shows the notice instead of sending, so a failed send cannot look like success. Typed values stay.
- **Service worker, minimal.** One job: if a page navigation fails for lack of a connection, show a self-contained "You're offline" page with **Try again** and **Go back**. It caches that page only. It never serves a ledger page, never answers a request that succeeded, activates at once when updated, and has a tested kill switch.

### 4. Words for hosts

- A short "Put PokerNights on your phone" section in the wiki with the iPhone and Android steps, and the two things to know: you log in once more inside the installed app on an iPhone, and invite links from a chat still open in the browser.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **PNG app icons**, as the one exception to "no raster imagery", generated from the existing mark. Recommended; an iPhone cannot use an SVG icon.
2. **Include the minimal service worker.** Recommended. Without it, a failed load inside the installed app leaves no way out except closing the app. Its risk is that a faulty one lingers on phones; the plan limits it to one job and tests a kill switch.
3. **Default status bar**, not the translucent one. Recommended; no layout risk. The translucent style can come with the motion stage if you want it.
4. **Reload on return after 30 seconds away.** Recommended over a Refresh button on every screen.
5. **No in-app "Add to Home Screen" hint yet;** instructions in the wiki only. Say so if you want a dismissible hint on Your groups.
6. **No iPhone splash images.** The app shows the plain dark background for a moment while opening.
7. **Release to production and test on your phone,** as you prefer. This stage is built so that a failure degrades to today's behaviour: a broken manifest or icon means "not installable", not a broken site. The service worker is the exception, which is why it gets the kill switch.

## Implementation

1. **Icons.** A small script in `web/tests/browser/` renders the SVG at each size with headless Chrome and writes the PNGs; the output is committed. A test asserts each file's pixel size from its PNG header.
2. **Manifest.** A static file linked from `base.html`. A test parses it and checks the required members and that every icon it names exists.
3. **`base.html`.** Head tags; the notice container; `app.js` loaded on every page.
4. **`static/js/app.js`** (new, small). Registers the service worker; shows and clears the notice on `offline` / `online`; stops form submission while offline; reloads on return when the rules in 2 allow. Each part works alone if another is unsupported.
5. **Service worker.** Served at `/sw.js` by a small Django view that needs no login, with a short cache lifetime, so it can cover the whole site in development and production alike. `offline.html` is a self-contained page (inline styles, inline SVG mark, no external file).
6. **CSS.** The notice; nothing else.
7. **Tests first.**
   - Django: head tags on signed-in and signed-out pages; `/sw.js` and the offline page answer without login, with the right content type and cache header, and contain no ledger data; the kill-switch setting serves the self-unregistering worker; HTML stays `no-store`.
   - Browser check `install.mjs`:
     - Chrome reports the page installable with no manifest errors (DevTools `Page.getInstallabilityErrors` and `Page.getAppManifest`);
     - the worker registers with scope `/`; its cache holds exactly the offline page;
     - going offline shows the notice within a second and blocks a form submit; going online clears it;
     - an offline navigation shows the offline page; **Try again** returns to the real page once online;
     - a successful page is never served from the worker's cache (two loads with a changed server value show the new value);
     - with the kill switch on, the worker unregisters and the cache is emptied;
     - after 30 seconds hidden, a session page reloads on return, and does not when a field holds typed text or a sheet is open;
     - every screen in standalone display mode has a way back;
     - with JavaScript off, nothing changes from today.
   - Existing scripts: `entry.mjs`, `dock.mjs`, `archive.mjs`, `settled.mjs`, `session_form.mjs` must still pass with the worker registered.
8. **Verify.** SQLite and PostgreSQL suites; the browser checks; captures of the notice and the offline page at 320, 390 and 1280 px.
9. **Release and phone checklist.** Release to production, verify the live manifest, icons and worker myself, then hand you the checklist below.
10. **Sync docs.** DESIGN.md addendum (icons, the notice, the offline page, the raster exception), wiki features and deployment, the host instructions, browser README, TODO, and the programme plan.

## Checklist for your iPhone, after release

1. In Safari: Share → Add to Home Screen. The icon is the chip-and-crescent on a dark square, named PokerNights.
2. Open it from the home screen: no address bar or toolbar.
3. Log in (once more, inside the app).
4. Walk Your groups → a group → a session → a set → the set log, and back each way using only on-screen links.
5. Switch to another app for a minute and return: the page refreshes.
6. Turn on Airplane Mode: the offline line appears. Tap a link: the "You're offline" page appears. Turn it off and tap Try again.
7. Check the top of the screen around the clock and the bottom around the home bar on the set page.

## Acceptance criteria

- AC1. Chrome reports PokerNights installable with no manifest error; the manifest and all four icons are served.
- AC2. The human confirms the checklist on their iPhone. Open until they do.
- AC3. In standalone display mode every screen has a way back.
- AC4. The offline notice appears and clears; a form cannot be sent while the phone reports offline; an offline navigation shows the offline page with a working Try again.
- AC5. The service worker's cache never contains anything but the offline page, and no successful page is served from it.
- AC6. The kill switch removes the worker and its cache.
- AC7. A stale non-live page reloads on return; typed text and open sheets are never discarded.
- AC8. All existing tests and browser checks pass; every flow works with JavaScript off.

## Out of scope

App stores; offline recording or viewing; push notifications; iPhone splash images; an in-app install prompt; the translucent status bar; making invite links open the installed app.

## Rollback

Revert the feature commits. If the service worker itself misbehaves, turn on the kill switch first and release that, so phones remove it; then revert. An icon already on a home screen keeps working and opens the site.

## Progress and blockers

2026-10-05: Study and plan complete. The human approved with “approved”; all seven decisions as recommended.

2026-10-05 execution on `feat/installable-app`.

Changes from the plan:

1. **iPhone status bar style is `black`, not `default`.** The plan said "the default style" meaning the opaque, non-translucent bar. On an iPhone the value named `default` is a light bar; `black` is the opaque dark one that suits this app. No layout change either way.
2. **The maskable icon is the same art as the 512px icon.** The existing SVG already keeps the mark inside the central 62% of the square, which is inside Android's safe zone.
3. **The refresh on return also skips pages rendered from a POST** (`<body data-method>`), found while writing it: reloading a refused form page would send the form again.
4. **The kill switch works from both sides.** The first browser run showed the page unregistering the worker before the self-removing worker could run, leaving its cache behind. Pages now also delete the cache when the switch is on.
5. **A select with no marked default was treated as unsaved typing,** so form pages never refreshed. Found by the browser check and fixed.
6. **Tests were written alongside the code,** not strictly first.

2026-10-05 verification:

- 626 tests pass on SQLite (ten PostgreSQL-only skips) and all 626 on local PostgreSQL 17, started for the run and stopped after. Eight new tests in `web/tests/test_install.py`.
- `install.mjs`: 33 of 33 on a fresh temporary database. Chrome's own report: manifest parsed with no error, no installability error.
- With the worker registered, `entry.mjs` 91, `dock.mjs` 145, `archive.mjs` 85, `settled.mjs` 24 and `session_form.mjs` 69 still pass.
- Captures of the notice and the offline page inspected at 390px.

Acceptance: AC1 and AC3 to AC8 are met. **AC2 (the iPhone checklist) is open** until the human confirms.

Not verified: anything on a real phone; the offline notice with a real loss of signal (emulated here); `navigator.onLine` behaviour on Wi-Fi without internet; a screen reader.

Documentation synced: DESIGN.md, wiki features (with the install instructions) and deployment (kill switch), browser README, TODO.

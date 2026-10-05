# Installable app (stage 2 of the app-like experience): study

Date: 2026-10-05, Asia/Manila. Programme: [app-like experience plan](../plan/1791172782_app_like_experience.md).

## Request

The human asked what stage 2 adds, liked it, and asked to start studying and planning. Stage 2 was deferred earlier the same day; this brings it back.

## What stage 2 is

Letting a phone put PokerNights on its home screen and open it full-screen, with a clear sign when there is no connection. It stays the website. Nothing goes to an app store, nothing is recorded offline and no ledger page is stored on the phone.

## What exists today

- `templates/base.html` has a viewport with `viewport-fit=cover`, `color-scheme: dark`, a `theme-color` of `#191511`, and an SVG favicon. It has no manifest, no touch icon and no iOS standalone meta.
- `static/branding/app-icon.svg` is a 512 × 512 square icon: the mark on `#231d17` with padding, drawn for this purpose. There is no PNG anywhere; DESIGN.md says the build ships no raster imagery.
- The fixed host dock and the toasts already respect `env(safe-area-inset-bottom)`. The sticky site header has no top inset.
- No script watches the connection. No service worker exists.
- Since stage 1, `vercel.json` header rules are proven to apply to static files, and `/static/icons/` and `/static/branding/` are cached for a week without a version tag.

## How installation works on each phone

**iPhone (Safari).** The person chooses Share → Add to Home Screen. Safari reads the page for `apple-touch-icon` (PNG, 180 × 180) and the manifest. With `display: standalone` the app then opens without Safari's bars. There is no install prompt a site can trigger.

**Android (Chrome).** Chrome offers "Install app" in its menu, and sometimes a prompt, when the manifest has a name, a start address, a standalone display and PNG icons of 192 and 512 px. A "maskable" icon lets Android crop it to its own shape without cutting the mark.

## Consequences of full-screen mode

These follow from the browser buttons disappearing, and they are the real work of the stage.

1. **No back button.** Every screen needs its own way back. Checked: every screen except the three roots (Your groups, Log in, Sign up) has a back link in its top bar or a "Back to…" link, and every signed-in page has the brand link to Your groups. No dead end was found by reading the templates; it must be walked on a phone.
2. **No reload button and, on an iPhone, no pull-to-refresh.** A set page refreshes itself every four seconds. Your groups, a group page and a session page do not: left open in the installed app, they would show old figures until the person navigates. They need to refresh themselves when the app comes back to the foreground.
3. **A failed load is a dead end.** In a browser, a page that fails to load offline can be retried with the reload button. Full-screen there is no such button; the person would have to close the app. Only a service worker can replace the browser's error with a page of ours that has a "Try again" button.
4. **A separate login on iPhone.** The installed app does not share Safari's cookies. The person logs in once more inside it. Sessions last two weeks (Django's default; no setting overrides it).
5. **Links from a chat open the browser, not the installed app,** on an iPhone. An invite link therefore still opens in Safari or the chat app's own browser. Nothing can change that from the site.
6. **The status bar.** With the "black-translucent" style the page draws under the clock and the sticky header would need a top inset on every screen. With the default style the system draws its own bar and no layout changes.

## The service worker question

A service worker is the one risky piece: a faulty one stays installed on phones and can keep breaking the site after the fault is fixed on the server.

- **Without one:** installation still works on both platforms (Chrome dropped the service-worker requirement for installability; this is from my knowledge and is verified in the build by Chrome's own installability report). The offline notice still works. But consequence 3 stays: a failed load in the installed app is a dead end.
- **With a minimal one (recommended):** it does one thing. When a page navigation fails because there is no connection, it answers with a small self-contained "You're offline" page that has "Try again" and "Go back". It caches that one page and nothing else. It never answers a successful request and never stores a ledger page.
- **Safeguards:** it lives at `/sw.js` so it can cover the whole site; it is never cached for long; it activates immediately on update; and a one-line change turns it into a version that unregisters itself, as a kill switch. All four are tested.

## Constraints

1. Money pages are never cached (programme constraint 4). HTML stays `no-store`.
2. Works without JavaScript: the manifest and icons need none; the notice and the service worker are enhancements.
3. No offline recording: when offline, submitting a form must not look as if it worked.
4. DESIGN.md: no raster imagery. PNG icons need the human's exception.
5. Icons are cached for a week without a version tag (stage 1), so a later change of icon needs new file names.
6. `navigator.onLine` is only a hint: it can say "online" on Wi-Fi with no internet. The notice is advice, never a guard on the money rules; the server remains the only judge.
7. Tools on this machine: headless Chrome can render the SVG to PNG at exact sizes. No design tool or image generator is needed.
8. The agent has no iPhone. Standalone behaviour, the icon on the home screen and the status bar can only be confirmed by the human.

## Options considered

- **Status bar:** default (recommended, no layout change) or black-translucent (more immersive; needs a top inset on every sticky header and more phone testing).
- **Staleness:** reload on return to the foreground after a pause (recommended), or a visible Refresh button on each screen, or nothing.
- **An in-app "Add to Home Screen" hint:** a dismissible line on Your groups for phones that are not yet installed, or documentation only (recommended for now; the programme plan said no in-app prompt).
- **iPhone splash screens:** each iPhone size needs its own image. Without them the app opens on the plain background colour for a moment. Left out.

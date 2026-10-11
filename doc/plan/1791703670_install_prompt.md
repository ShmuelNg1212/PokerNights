# Suggest adding the app to the home screen: plan

Status: approved 2026-10-11 with two changes (see "Changes at approval"). Date: 2026-10-11, Asia/Manila. Study: [Suggest adding the app to the home screen](../study/1791703645_install_prompt.md).

## Outcome

A person who has just signed up or logged in on a phone's browser is shown, once, how to put PokerNights on their home screen, in the words and pictures that fit their phone. On Android one tap installs it. They can dismiss it with one tap and find it again later. Inside the installed app it never appears.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new colour, font or raster asset. No migration, no server write, no dependency.

## Behaviour

| Moment | What happens |
|---|---|
| First ordinary page after a login or sign-up, on a phone, in a browser | After the arrival has finished (about a second), a sheet rises: "Put PokerNights on your home screen" |
| Android, the browser offers install | One line of why, a primary **Install** button that opens the browser's own install dialog, and "Not now" |
| iPhone in Safari (or Chrome and Firefox on iPhone) | Two numbered steps with drawn icons: tap **Share**, then **Add to Home Screen**. A line: "You log in once more inside the app." Buttons: "Done, it's there" and "Not now" |
| Inside a chat app's browser | "Open this page in Safari first" (or Chrome on Android), with a **Copy link** button, then the same steps |
| Any other phone browser | Both menus named in one short list |
| "Not now", Close, Escape, a tap outside | The sheet leaves. It is offered once more after the next login at least 7 days later, then never by itself |
| "Done, it's there", or the browser reports the install | Never shown again in this browser |
| Opened from the home screen | Never shown |
| The page after login is a join or claim confirmation, or a session whose recap opens by itself | Not shown there; it waits for the next login |
| Later, at any time | "Add to home screen" in the account menu at the top opens the same sheet (hidden inside the installed app) |
| Desktop | No popup. The account entry is shown only where the browser offers install |
| No JavaScript | Nothing appears |

Why it says what it says: full screen without the browser's bars, one tap from the home screen, and it stays logged in for two weeks. No claim about notifications or working offline, which are not built.

## Motion

- The sheet rises with the existing `sheet` spring, as every sheet does, about 900ms after the page shows so the arrival is never covered.
- **One authored moment, once per opening:** the app's own icon sits at the top of the sheet inside a drawn home-screen tile; it drops into the tile with the `drop` spring and the tile's label fades in. On the iPhone card the arrow of the Share glyph then lifts 4px and settles, once, to point at the first step; the steps themselves do not move.
- An accepted Install pulses the button once.
- It never blocks: every control works while anything moves. Reduced motion shows it at rest.

Built with the design and motion skills.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **Once, with one reminder.** Shown after the first login in a browser; after "Not now", once more at a login 7 or more days later; then only from the account menu. Say "once only" or "every login until installed" for a different rhythm. (The page cannot tell that the app is installed when it is opened in the browser, so "every login" keeps asking people who already installed it.)
2. **Phones only.** Recommended, because "home screen" means a phone. Say if desktop Chrome should get the Install card too.
3. **Remembered in the browser, not on the account.** Recommended: it is about this phone. A second phone is asked once.
4. **The iPhone card says "You log in once more inside the app."** Recommended; otherwise the first run looks broken.
5. **A switch, `INSTALL_PROMPT`, on by default.**

## Implementation

Branch `feat/install-prompt` from `main`. Tests first for the server part.

1. **`config/door.py`.** The existing arrival signal gains a second reading, `door.came_in`, true on the first page after a login whether or not `DOOR_MOTION` is on. `base.html` writes `data-came-in` on `<html>` when it is true, `INSTALL_PROMPT` is on, and the page has not opted out. Entry pages (join, claim) and a session page with an unseen recap opt out through a template block, as `entry.html` already empties the `welcome` block.
2. **`templates/_install.html`,** included once in `base.html` for signed-in pages: a `<dialog class="sheet install">` with the three variants as sibling sections, all hidden until the script picks one; and the account-menu entry.
3. **`static/js/install.js`,** registered with `page.js`:
   - keeps `beforeinstallprompt` (and prevents the browser's own mini-bar) and listens for `appinstalled`;
   - decides the variant: standalone → nothing; in-app browser by user-agent markers (`FBAN`, `FBAV`, `Instagram`, `Line/`, `Viber`); iPhone or iPad; Android with a kept event; otherwise generic;
   - shows the sheet when `data-came-in` is present, the viewport is a phone's, the remembered state allows it and no other dialog is open; waits for the arrival to end;
   - remembers `{dismissed: count, at: time}` or `done` in `localStorage`; storage that refuses means it is not shown by itself (never an endless loop);
   - focus goes to the sheet's first action, is kept inside it, and returns on close; Escape and outside tap close.
4. **CSS (`app.css`).** The install sheet's content, the home-screen tile, the step rows and their icons (inline SVG at the app's stroke), the one moment, reduced motion.
5. **Tests.**
   - Django: `data-came-in` is on the first page after login and after sign-up, not on the second page, not for a prefetch, not on join and claim pages, not with the switch off; the dialog markup is absent for a signed-out visitor.
   - Browser (`install_prompt.mjs`, new): with an iPhone Safari user agent, an Android one with a synthetic `beforeinstallprompt`, a Messenger in-app one and a desktop one: the right variant or none; it appears after the arrival and not over it; Install calls the kept event's `prompt()`; "Not now" then a login the same day shows nothing and a login 8 days later (clock moved) shows it once more and then never; "Done" and `appinstalled` end it; standalone shows nothing and hides the menu entry; the menu entry opens it on demand; focus, Escape, outside tap; 48px targets and no overflow at 320 and 390px; reduced motion; no script error. Captures of each variant are looked at.
   - `welcome.mjs` and `door.mjs` rerun, since the arrival's signal is touched.
   - Both suites: SQLite and PostgreSQL.
6. **Documents.** Wiki (features: the install section and its "Not built" line; architecture), PRODUCT.md and DESIGN.md addenda, deployment (the switch), browser README, TODO.md with the phone checklist.

## Out of scope

- Push notifications, offline use, splash images, an app-store app.
- Opening invite links inside the installed app.
- Sharing the login between Safari and the installed app on iPhone (the platform does not allow it).
- Knowing from the server who has installed.

## Acceptance

1. A new sign-up on an iPhone in Safari sees the steps once, after the arrival, and can close them with one tap.
2. On Android Chrome, Install opens the browser's install dialog; after installing, the suggestion never returns.
3. "Not now" is respected: no popup on the next login that week; one more a week later; none after that.
4. Inside the installed app there is no popup and no menu entry.
5. Join and claim pages and a session's first recap are never covered.
6. Both test suites pass; `welcome.mjs` and `door.mjs` still pass.

## Release

Kept local on its branch until you say to push. No migration. The first response to trouble is `INSTALL_PROMPT=False`.

## Changes at approval

2026-10-11. The human said: "approved. I would like the prompt to be shown if a user signs up or logs in using a mobile browser. I want links to be used in the installed app."

1. **Decision 1 becomes: every sign-up and every login in a mobile browser.** No "once" and no 7-day wait. The agent's reading, to be corrected if wrong: "Done, it's on my home screen" still ends it for that browser, since the person has said it is installed; and the sheet still waits for the first ordinary page, so a join or claim page or an opening recap is not covered. It is then shown on the next page instead of being skipped.
2. **Links in the installed app is now in scope,** as far as each platform allows:
   - **Android:** an installed web app opens links to its own address when they are tapped in another app. The manifest states the intent (`launch_handler`, `handle_links`) so an open app is reused. A chat app that opens links in its own built-in browser still does so; that is the chat app's setting.
   - **iPhone:** the system never opens a link in a home-screen web app; it opens the default browser. No web page can change this. The substitute: inside the installed app, Your groups has **Join with a link**: paste the invite, claim or reset link and it opens inside the app.
   - The "Add to home screen" entry for later sits at the end of Your groups, not in the top bar, which has no room at 320px.

## Progress

2026-10-11: Built on `feat/install-prompt` from `main`; kept local.

Changes from the plan, beyond "Changes at approval":

- **Nothing is remembered after "Not now".** The plan's count and date are gone with the every-login rule; only "done" is kept.
- **A page with its own business defers the sheet instead of skipping it.** A note in the browser session carries it to the next page.
- **The iPhone card has no primary button.** The action happens in the browser's own menu, so neither button is the one thing to do.
- **Declining Android's install dialog leaves the menu steps** in the open sheet. The browser lets a page ask once per event.
- **Three existing tests changed:** two in `accounts/tests/test_door.py` (the page after a login now also carries `data-came-in`; the cookie is unset only when both switches are off) and one in `web/tests/test_home.py` (the first-group screen holds the hidden link field).

Verification:

- 1011 tests pass on SQLite (15 skipped), 8 of them new (`web/tests/test_install_prompt.py`). PostgreSQL was not run: no model or query changed.
- `install_prompt.mjs`: 38 of 38 on a fresh temporary database, after one fix (the link field was drawn as a bare box). `welcome.mjs`: 35 of 35. `door.mjs`: 128 of 128.
- Captures of the iPhone, Android, in-chat and 320px sheets and of the link field were looked at, in two rounds.

Acceptance: 1, 3 (as changed: every login), 4, 5 and 6 are met in headless Chrome with each phone's user agent. 2 is met against a stand-in for the browser's install event.

Not verified: a real iPhone or Android phone; Chrome's real install dialog; whether Android opens a tapped link in the installed app (it depends on how the app was installed and on the chat app); the wording of the in-app browsers' own menus, which differ ("Open in browser", "Open in Safari", "Open in external browser"); an iPad. A fresh reviewer did not read the branch.

Documentation synced: wiki (features, architecture, deployment), PRODUCT.md, DESIGN.md, browser README, TODO.

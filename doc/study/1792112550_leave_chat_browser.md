# Leave the chat app's browser before signing up: study

Date: 2026-10-16, Asia/Manila.

## Request

The human said: "when a user opens an invite link in messaging apps, it opens the built-in browser for the respective app. I feel as though this is a roadblock in the smooth user experience being offered in the browser leading the user to install the app to their home screen. lets fix this issue."

## What happens today

- An invite is shared in a chat (Messenger, Viber, Instagram, LINE). A tap opens `/join/<token>/` in the chat app's own browser. A signed-out visitor is sent to `/signup/?next=/join/<token>/` (`groups/views.py`, `accept_invite`).
- The person signs up **inside the chat browser**. The account is made and they join the group there.
- Only then, on the first ordinary page, the install sheet (`static/js/install.js`, part `inapp`) says "This is a chat app's own browser, which cannot add apps", with steps to open the page in the browser and **log in there**. Its Copy link copies the site's root, not the page.
- So the person meets the problem after the work is done. They must leave, find the menu, open a browser, log in again, and only then see the home-screen steps. Many will stay in the chat browser, which also forgets the login sooner and cannot add the app, keep its alerts, or open from the home screen.

The 2026-10-11 install-prompt study saw this (finding 6) but put the answer after login, where the sheet lives.

## What a page can do inside a chat browser

| Chat app | How the page can leave | Reliability |
|---|---|---|
| LINE (both phones) | Add `openExternalBrowser=1` to the address. LINE documents it and opens the default browser | Good |
| Android, Meta apps and most others (Messenger, Facebook, Instagram, Viber) | A link to `intent://<host><path>#Intent;scheme=https;S.browser_fallback_url=…;end` asks Android to open the address in a browser. It must come from a tap | Varies by app and version. No current source confirms it for Messenger. When it fails, nothing happens or the fallback reloads the same page |
| iPhone, any chat app | No page-started route. `x-safari-https:` worked in some apps in 2023 and is reported broken in Instagram in 2026. Apple supports only documented schemes. The person uses the app's menu (`•••` or the compass) and **Open in Safari** / **Open in browser** | Manual only |
| WhatsApp on iPhone | Opens Safari already. Nothing to do | — |
| WhatsApp and Telegram on Android, Telegram on iPhone | A Chrome Custom Tab or Safari view. Their user agent reads as the plain browser, so the page cannot tell. Each shows its own "Open in Chrome/Safari" control | Cannot detect |

Sources: Escaping Instagram's in-app browser on iOS (dev.to, 2026), Safari URL scheme (christiantietze.de, 2023), Apple Developer Forums thread 757541, Branch's guide to Chrome intents.

## Findings

1. **The moment to act is before the account exists**, on the front-door pages a link lands on: Join, Sign up, Log in, Claim and Reset. Moving the person out there costs them nothing: they sign up once, in the browser that can keep the app.
2. **The address must survive the move.** The invite token is in the path. The card must open the current page's full address (`/signup/?next=/join/<token>/` still carries it), not the site root as today's Copy link does.
3. **No automatic redirect.** None of the routes is reliable, and a redirect that fails can loop or strand a person on a blank tab. The memory note says the human tests on the live build, so the change must fail safe: every route is a tap the person chooses, and **Continue here** always works.
4. **The server can decide.** The user agent arrives with the request, so the card can be drawn in the template and work with no JavaScript; the script only adds Copy and the Android tap. The markers already used by `install.js` (`FBAN`, `FBAV`, `FB_IAB`, `Instagram`, `Line/`, `Viber`, `MicroMessenger`, `Messenger`) move to one Python list that the template and the script share. Front-door pages are rendered per request and are not cached at the edge, so no `Vary` problem. `Vary: User-Agent` is still set on them.
5. **The words must fit the phone.** On iPhone: "Tap ••• at the top, then Open in Safari." On Android: a primary **Open in Chrome** button (the intent link, with the menu step under it as the fallback). For LINE: a button that opens the address with `openExternalBrowser=1`.
6. **The after-login sheet stays** as the back-up for a person who chose Continue here. Its Copy link should copy the current page too.
7. **Undetectable cases stay as they are.** WhatsApp and Telegram on Android are close to the browser, show their own control, and their person still gets the normal install sheet after login.

## Options

| Option | For | Against |
|---|---|---|
| A. A card at the top of the front-door sheet in a chat browser, with the route for that phone, Copy link and Continue here | Caught before sign-up; never blocks; works without JavaScript | One more element on the first screen |
| B. A full-screen stop page before the front door | Hard to miss | Feels like an error; a person who cannot find the menu is stuck behind it |
| C. Try the redirect on load | Zero taps when it works | Unreliable; a failure loops or shows a blank tab; Android blocks it without a tap anyway |

Recommend A.

## Risks

| Risk | Effect | Answer |
|---|---|---|
| The intent link does nothing in some app | The button seems broken | The menu step is printed under it; a short status line appears if the page is still visible after a second |
| A marker matches a normal browser | A card where none is needed | Continue here dismisses it for the tab; the markers are the ones in use since 2026-10-11 with no report |
| A new chat app is not matched | No card | Same as today; the after-login sheet still catches the known ones |
| The person continues in the chat browser | Same as today | The install sheet after login still explains, now with the right address |

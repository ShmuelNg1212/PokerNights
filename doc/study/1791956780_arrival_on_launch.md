# The arrival on every app open: study

Date: 2026-10-14, Asia/Manila. Base: `main` at `b446222`.

## Request

"Can the Your groups page animations play whenever a logged in user opens the app."

## Understanding

- **Said:** the Your groups arrival, for a signed-in person, each time they open the app.
- **Assumed:** "the Your groups page animations" is the arrival into the app (DESIGN.md, "Arrival into the app", 2026-10-09): the cards rise in turn, the player tokens slide in, the In play badge springs, a brass line draws under "To settle", and the header's chip lands. Today it plays only on the one page after a log-in. "Opens the app" is tapping the home-screen icon; the splash screen released today comes just before it.
- **Success:** on the phone, opening the app shows the splash and then Your groups arriving, every time it is opened; using the app afterwards plays nothing extra.

## What happens now

- The server decides. A log-in sets the cookie `arrived` for 30 seconds; the first page a signed-in person is shown writes `data-welcome` on `<main>` and the cookie is removed (`config/door.py`).
- The arrival is CSS keyed on `[data-welcome]` (end of `static/css/app.css`). `door.js` ends it on the first key or tap and takes the mark off after 1.2 seconds. It is over within 880 ms; a figure is at its value on the first frame; reduced motion stills it; `DOOR_MOTION=False` removes it.
- Your groups refreshes itself every 5 seconds (`data-state-url`), so `app.js` does not reload it when the app comes back. Other pages reload after 30 seconds away.
- The installed app on an iPhone is either **started** (the first time, or after iOS has closed it, which it does after a while in the background or when memory is short) or **resumed** (it was still in the background, and the screen is as it was left).

## What "opening the app" can mean to the page

| Case | What the page sees | Can the arrival play cleanly? |
|---|---|---|
| Started from the icon | A full page load of `/`, the first in this window | Yes. It is a first paint, as after a log-in |
| Resumed from the background | No load. The page is already on screen, and becomes visible again | Not cleanly. The cards are already in view; to rise they must first vanish. That is a flash, and it would also land under the iPhone's own snapshot of the screen |
| A page inside the app (a link, a form, Back) | A Turbo visit, or a reload | Should not play: DESIGN.md says a later visit, a reload or Back plays nothing |

A started app can be told apart before the first paint, with no server state:

- **A new window.** `sessionStorage` is empty in a window that has just been started. Written once, it stays for every later page in that window and is gone when iOS closes the app.
- **A fresh load.** The navigation's type is `navigate`, not `reload` or `back_forward`.
- **Early enough.** A short inline script placed as the first thing inside `<main>` runs before the cards are parsed, so it can add `data-welcome` to `<main>` before anything inside it is painted. Everything else then works as it does after a log-in: the same CSS, the same ending in `door.js`, reduced motion, the switch.

Turbo runs inline scripts in each new page's body. On those visits the `sessionStorage` mark is already set, so nothing plays.

## Options

- **A. Each time the app is started (recommended).** The arrival plays on the first page of a new app window, which is how a person reads "I opened the app" after any real time away, because iOS closes background apps. A quick switch away and back plays nothing.
- **B. Also on return after a long time away** (for example 15 minutes). Covers the case where iOS kept the app alive, at the cost of the flash above. A different, quieter movement for a resume (no vanishing) would be its own design.
- **C. Every return.** The flash every time the person switches back from the group chat during a game. Not proposed.

## Where it applies

- **Installed app and browser.** A new Safari tab opened on the site is the same moment as a started app: a first page in a new window. Recommended: both, which also makes it checkable in a desktop browser. The alternative is only the installed app (`display-mode: standalone`).
- **The landing page.** The app starts on `/`, which is Your groups. A browser tab may open on another page from a link; DESIGN.md already says that on any other landing page only the header's chip lands.
- **Signed out:** nothing changes; the front door has its own arrival. The chip blinking out on the front door after the splash (launch screen plan, "Ruling made while building") is not part of this.

## Costs and risks

- **About 880 ms of movement on every open.** The page is usable at once: a tap or key ends it, as today. With the phone at the table this is what the person will see most often of all the app's motion, so it must feel right the tenth time, not only the first. The phone decides.
- **Inline script.** The site sends no Content-Security-Policy, so an inline script runs. One line, about 200 bytes, on every page that has a `<main>`.
- **`sessionStorage` refused** (a private window that throws): the script catches it and plays nothing, as today.
- **The home-screen suggestion** (`data-came-in`, `install.js`) is a separate mark and does not change.
- **Fail-safe.** A switch turns it off and leaves the log-in arrival as it is; without the switch the page is exactly today's.

## Conclusions

1. Playing the arrival when the app is started is clean and small: the existing arrival, switched on by a first-thing script in `<main>`, with no new CSS and no server change.
2. Playing it on a resume means the cards vanish and rise again; that is not proposed.
3. Recommended: option A, in the installed app and in a new browser tab, behind its own switch.

## Addendum, 2026-10-14: where the script goes

"Early enough" above proposed a script as the first thing inside `<main>`. The project's rule is that no script is in the body (`ScriptsLoadOnceTests`; footgun "scripts run once per tab"). The script is therefore in the head, before the stylesheet, and marks `<html>` (`data-launch`) instead of `<main>`; the arrival's CSS answers both marks. The conclusions stand.

# Leave the chat app's browser before signing up: plan

Status: approved 2026-10-16 with the recommended answers. Date: 2026-10-16, Asia/Manila. Study: [Leave the chat app's browser before signing up](../study/1792112550_leave_chat_browser.md).

## Outcome

A person who taps an invite in Messenger, Instagram, Viber or LINE is told, on the first screen and before they sign up, to open the page in Safari or Chrome. They get the one step that fits their phone, and a button where the phone allows it. The invite comes with them. They sign up once, in the browser that can put the app on the home screen. Nobody is blocked: **Continue here** always works.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No migration, no server write, no dependency.

## Behaviour

| Where | What the person sees |
|---|---|
| Join, Sign up, Log in, Claim or Reset, inside a known chat browser, on iPhone | A card at the top of the sheet: "Open this in Safari". The line under it reads "This chat app's browser can't keep PokerNights on your home screen." Step: "Tap **•••** (or the compass) at the top, then **Open in Safari**." Buttons: **Copy link** and **Continue here** |
| The same, on Android | Same card, "Open this in Chrome". Primary **Open in Chrome** (the intent link to this exact address). Under it: "Or tap **⋮**, then **Open in browser**." Copy link, Continue here |
| The same, in LINE | Primary **Open in browser** (this address with `openExternalBrowser=1`) |
| **Continue here** | The card folds away for this tab. The form is as today |
| Copy link | Copies this page's full address, so the invite token comes along |
| Any other browser, or the installed app | No card. The page is as today |
| No JavaScript | The card and its steps show; Copy link and Open in Chrome are hidden; Continue here is a plain link to the same page with `?here=1` |
| After login, in a chat browser | The existing install sheet, as today, but its Copy link copies the current page |

## Motion

None new. The card is present at first paint (it is drawn by the server), so nothing shifts. Continue here collapses it with the existing `leave` timing. Reduced motion removes it at once.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **A card, not a stop page or a redirect.** Recommended because no route out of a chat browser is reliable, and a failed redirect would strand people.
2. **Every front-door page**, not only Join. Recommended because a claim or reset link is shared the same way.
3. **A switch, `CHAT_BROWSER_CARD`, on by default.** Off returns the pages to today.

## Implementation

Branch `feat/leave-chat-browser` from `main`. Tests first.

1. **`config/chat_browser.py`** (leaf, next to `pwa.py`): `MARKERS` and `kind(request)` → `None`, `"ios"`, `"android"` or `"line"`. The `flags` context processor adds `chat_browser` (the kind, or `None` when the switch is off or `here=1` is in the query).
2. **`templates/partials/chat_browser.html`**: the card. Each variant is drawn server-side. The intent address and the LINE address are built in the template from `request.build_absolute_uri`. Included at the top of `{% block content %}` in `entry.html`, so it covers every front-door page. Front-door views get `Vary: User-Agent` through a small decorator.
3. **`static/js/chat_browser.js`**, registered with `page.js`: shows Copy link (with the address-in-text fallback, as in `install.js`); Continue here hides the card and remembers it in `sessionStorage`; after a tap on Open in Chrome, if the page is still visible after 1.5 s, a status line says "Use the menu instead". The marker list reaches the script from a `json_script`, and `install.js` reads the same list in place of its own regex. Its Copy link uses `location.href`.
4. **CSS** in `app.css`: the card reuses `.notice-info` with the install sheet's step rows. 48 px targets. Single column.
5. **Tests**:
   - Python, one per kind, from a set of real user-agent strings: Messenger, Facebook and Instagram on iOS and Android, Viber, LINE, WeChat, plus Safari, Chrome and Samsung Internet giving no card.
   - The card on each front-door page, and the invite token kept in both addresses.
   - `here=1` and the switch both remove the card. `Vary` is set.
   - A browser check `web/tests/browser/chat_browser.mjs` with a Messenger user agent at phone width: the card shows, Copy copies `location.href`, Continue here folds it, and nothing overflows.
6. **Docs**: wiki `features.md` (front door) and the install-prompt footnote. A footgun note on chat browsers that cannot be detected (WhatsApp, Telegram).

## Verification after release

On your phone: send yourself an invite in Messenger and tap it. The card shows above Sign up. On iPhone, the menu step opens Safari on the same invite. On Android, **Open in Chrome** opens Chrome on the same invite, or the menu step does. Sign up there; the home-screen sheet follows.

## Rendezvous (2026-10-16)

Built on `feat/leave-chat-browser` with the design (impeccable) and motion skills. Not merged or released.

- **As planned:** the card on every front-door page, per phone, Copy link, Continue here with and without JavaScript, the switch `CHAT_BROWSER_CARD`, `Vary: User-Agent`, `install.js` reading the server's mark and copying the current page.
- **Changed while building:**
  1. The card names the app ("Messenger's browser…") and says "Your invite comes with you." when the address carries an invite, claim or reset link.
  2. The marker list is not shared with the script through `json_script`. The server writes `data-chat-browser` on `<html>`, and `install.js` also keeps its own short pattern. The reason is item 3.
  3. **The service worker hid the chat app.** A page the worker fetches is asked for with the worker's user agent, so a returning visitor's front door would have shown no card. The worker now leaves `/accounts/`, `/join/` and `/claim/` to the browser. Offline, those pages show the browser's error, not the offline page. See [the footgun](../wiki/footguns/service_worker_user_agent.md).
  4. While the card shows, the first field does not take focus. Focus scrolled a 320 × 568 screen past the card.
  5. Continue here remembers itself in a session cookie (`chat_here`), not `sessionStorage`, so the server leaves the card out of the next page instead of the script hiding it after paint.
- **Motion:** one CSS moment (the menu's dots light in turn at 900ms), replayed when Open in Chrome does not leave the page; Continue here folds with `leave` and `shift`.
- **Verified:** 1,193 tests on SQLite and on PostgreSQL. `chat_browser.mjs` 21 of 21; `install_prompt.mjs` 38 of 38. `install.mjs` fails 2 checks ("reloads on return"), and fails the same 2 on `main` (`81c25fc`), so they predate this work.
- **Not provable here:** whether Messenger, Facebook or Instagram on Android hand the `intent://` link to Chrome. When they do not, the status line and the menu steps remain.

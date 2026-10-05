# App-like experience on a phone: feasibility study

Date: 2026-10-05, Asia/Manila.

## Request

The human wants the app to function like a rich single-page application so that it is seamless to use on a mobile phone, and asked whether that shift in architecture is feasible.

## Discovery answers (2026-10-05)

1. **What feels least seamless.** Actions reload the page; moving between screens loads a fresh page each time; it feels like a website (browser tab, no home-screen icon, not full-screen). Slow or unreliable signal was not chosen.
2. **Offline.** No. Online only, with a clear sign when the phone is offline.
3. **Appetite.** Upgrade in place: keep the server-rendered screens and make them behave like an app. Not a rewrite in a JavaScript framework.

## Verdict

**Feasible, and without changing the architecture.** The three complaints have three separate causes, and each has a remedy that keeps Django templates, the write services, the tests and the "works without JavaScript" rule. A rewrite as a JavaScript application would address the same three complaints at many times the cost and would not make the server any faster, because the server is not the slow part.

## What was measured

**The server is fast.** Locally, with seeded data (SQLite; production uses PostgreSQL in the same region as the function):

| Page | Queries | Render | HTML |
|---|---|---|---|
| Your groups | 17 | 6 ms | 3 KB |
| Group, Sessions | 10 | 4 ms | 5 KB |
| Session | 23 | 7 ms | 13 KB |
| Set in play | 15 | 6 ms | 46 KB |
| Set poll, nothing changed | 4 | 1 ms | 0 |
| New session | 7 | 3 ms | 7 KB |

Production (Vercel, Singapore), signed-out login page from the development machine: 150–190 ms on a new connection, about 60 ms on a kept-alive connection. Signed-in pages could not be measured on production; no account is available to the agent.

**Every screen change re-checks every static file.** Production serves `/static/` with `Cache-Control: public, max-age=0, must-revalidate` and unversioned addresses (`/static/css/app.css`). So each navigation asks the server again about the stylesheet (51 KB, 13 KB compressed), the font (104 KB) and each script. A set page loads eight scripts. That is ten or more round trips per screen before the page is complete, on a phone connection, even though nothing changed. This is the largest avoidable cost and it is not caused by the page architecture.

**Every action is a full page cycle.** There are 53 POST forms. Each one posts, receives a redirect, and loads the whole page again from the top, with all the static re-checks. Recording a rebuy in a sheet does this. The scroll position is lost. The app already has the opposite capability for one case: the set page polls `/s/<id>/state/` and replaces its live region in place (`static/js/live.js`), keeping typed values, open disclosures and now keyboard focus.

**Navigation is a full document load,** softened only by a cross-document view transition (`@view-transition { navigation: auto }`), which Safari supports from version 18 and which does not remove the re-checks.

**Nothing makes it installable.** There is no web app manifest, no touch icon and no iOS standalone meta. Opened from a browser it always has the address bar and browser toolbar. The brand assets are SVG only; an iPhone home-screen icon must be PNG.

## Constraints that any solution must keep

1. **Stack rule** (AGENTS.md): Django templates, plain CSS, small vanilla JavaScript modules; "no front-end framework … without a recorded requirement". This request can be that recorded requirement if a library is chosen, but the rule's intent (no build step, no second codebase) is worth keeping.
2. **Works without JavaScript.** Every flow is a native form today, and the browser checks prove it.
3. **Server acceptance** (PRODUCT.md): success is shown only after the server accepts; amounts are never interpolated; typed values survive live updates. This rules out "optimistic" money updates.
4. **Money data is never stale.** HTML responses are `no-store`. No layer may cache a ledger page and show it later as current.
5. **The test suite.** 612 Django tests assert on rendered HTML and 19 browser scripts drive real pages. They are the safety net for the money rules.
6. **Vercel.** One Python function, static files on the CDN, no WebSocket layer.
7. **Standalone mode has no browser buttons.** Once installed, there is no back button and no reload. Every screen needs its own way back and the app must refresh itself. Today Your groups, Log in and Sign up have no back link (they are roots, which is fine); the other screens have one.

## Options

### A. Rewrite as a JavaScript application (declined by the human)

A framework front end with a new JSON API.

- Gains: full control of transitions and in-place updates.
- Costs: a new API surface over every service with its own permission checks; every one of 46 templates rebuilt; the 612 HTML-asserting tests replaced; a build step and a second codebase; the no-JavaScript rule dropped; months of work with the money rules re-proven from scratch.
- It does not fix static caching or installability by itself; those need the same work as below.

### B. Upgrade in place (chosen)

Four independent improvements, each shippable alone:

1. **Cache static files properly.** Fingerprinted file names and a one-year immutable cache. Removes about ten round trips from every screen change. No behaviour change.
2. **Make it installable.** Manifest, icons, iOS meta, standalone display, an offline notice. Fixes "feels like a website".
3. **Update in place after an action.** Submit forms in the background and apply the server's fresh HTML to the page without a reload, keeping scroll position. Fixes "actions reload the page".
4. **Change screens without a reload.** Intercept links, fetch the next page, swap the content, manage history and scroll, and fetch a link when the finger touches it. Fixes "moving between screens".

Items 3 and 4 are "HTML over the wire": the server keeps rendering HTML; a small client layer swaps it in. Two ways to get that layer:

- **A maintained library, Turbo (from the Hotwire project).** One vendored file, no build step. It provides link interception, background form submission, history, scroll restoration, prefetching and in-place page refresh. Known costs: pages that re-render a form with errors must answer with status 422 instead of 200 (about eight views); every script must initialise per page visit instead of once per load (ten modules); it becomes a dependency to keep current.
- **A small module of our own.** No dependency and exactly our behaviour, but history, scroll restoration and form semantics are easy to get subtly wrong and we would own them.

Which of the two is right should be decided by a short, timeboxed trial in stage 3's own study, measured on the set page. I lean towards Turbo because the hard parts are the ones it has already solved, but I have not verified its current behaviour against its documentation for this app, and I will not claim it fits until the trial shows it.

### C. Do only 1 and 2

The cheapest step. It would make navigation noticeably quicker and give the home-screen experience, but actions would still reload the page, which is the first complaint.

## Risks found

- **Fingerprinted static files on Vercel.** Django's manifest storage needs its manifest file at run time inside the function. Whether Vercel's Django build includes it must be proven on a preview deployment before production, with a fallback of setting the cache header only.
- **Raster icons.** DESIGN.md says the build ships no raster imagery. App icons must be PNG on an iPhone. This needs the human's exception, limited to app icons generated from the existing mark.
- **Standalone on iPhone.** No pull-to-refresh and no back gesture guarantee; a signed-out session inside the installed app must still reach Log in; links to other sites open outside. Needs a real iPhone to verify, which the agent does not have.
- **Script lifecycle.** `sheets.js`, `live.js`, `counts.js`, `clock.js`, `dock.js`, `changes.js`, `pick.js`, `forms.js`, `toasts.js` and `password.js` assume one page load. In-place navigation requires each to start and stop cleanly per visit. A leaked poll timer would poll a set the host has left.
- **Browser scripts.** They assume a click is followed by a page load and wait a fixed time. They need a shared "wait for the visit to finish" helper.
- **What this does not deliver.** Offline use, push notifications, and instant multi-device updates (the 4-second poll stays; WebSockets are excluded by the stack rule).

## How success would be measured

- Requests per screen change: from about ten to one or two.
- After a buy-in, cash-out, count or paid mark: no document reload, and the scroll position within a few pixels of where it was.
- Time from tap to the next screen on a throttled connection, before and after each stage, recorded with the browser's own timings.
- Installed from the home screen: opens full-screen with the app icon; no screen without a way back; an offline notice appears and clears.
- With JavaScript off: every existing flow still passes.
- All existing tests pass at every stage.

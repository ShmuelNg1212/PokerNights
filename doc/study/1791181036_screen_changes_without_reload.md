# Screen changes without a reload (stage 4 of the app-like experience): study

Date: 2026-10-05, Asia/Manila. Programme: [app-like experience plan](../plan/1791172782_app_like_experience.md). Builds on [stage 3](../plan/1791178826_actions_in_place.md), which vendored Turbo 8.0.23 with navigation switched off.

## Request

The human said "start stage 4". Stage 4 is the second complaint from the programme's discovery: moving between screens loads a fresh page each time.

## What happens today

Tapping a link unloads the page and loads the next one: the document is fetched, the stylesheet and twelve scripts are parsed and run again, and every script starts from nothing. Since stage 1 the static files come from the browser cache, so the network cost is one request; what remains is the teardown and rebuild of the page, a blank moment between screens, and the loss of anything the page was holding.

Turbo is already on every page. Switching its navigation on makes a link fetch the next page and swap the content in, without unloading.

## The trial

A throwaway spike: navigation switched on for links, forms left exactly as in stage 3, **no other change**. It was measured and then discarded.

### It works, and it is quicker

Tapping group → session → set → back, three times: **no document load at all**, no page reload.

Time from tap to the next screen ready, phone-sized headless Chrome, local server, emulated slow connection (400 ms round trip):

| | Today | Links on |
|---|---|---|
| Time per screen change | 865–873 ms | 449–472 ms |
| Requests per screen change | 10–11 | 3–4 |

A caution about these numbers. The local server does not send the long-lived cache headers production has had since stage 1, so "today" is worse here than on the live site, where stage 1 measured 516–595 ms for one request. **On production the speed gain will be smaller than this table suggests, perhaps 10–20%.** The real gain is what the numbers do not show: no blank moment, no rebuild of the page, and the ground for stage 6's transitions.

### What breaks, exactly as predicted

The page scripts assume they run once per page load. With navigation on, Turbo runs the scripts at the end of the body again on every visit, and nothing stops the previous copy.

| Probe | Expected | Found |
|---|---|---|
| Poll requests in 8.5 s on a set page, after visiting it four times | 2 | **9** (one poll loop per visit, all still running) |
| Poll requests in 8.5 s after leaving the set page | 0 | **2** (the set is still being polled from the group page) |
| Script errors while tapping around | 0 | **3** (`showModal` on a sheet that is no longer in the page) |

Left unfixed, a host who moves around during a game would multiply the polling against the server and collect dead handlers. This is the real work of stage 4.

### The existing browser checks under the spike

| Script | Result |
|---|---|
| `dock` 145, `archive` 85, `settled` 24, `session_form` 69, `install` 33 | all pass |
| `inplace` 37 | 35; the 2 failures assert that navigation is off and that a link loads a new page, which is what this stage changes |
| `entry` 91 | 89; 2 failures in the existing-account invite path, after a link to Log in was followed without a reload. Not investigated in the timebox |

So the app's flows survive link navigation almost untouched. The damage is in script lifetime, not in behaviour.

## What stage 4 has to do

### 1. Give every script a lifetime

Twelve modules, about 720 lines: `app`, `forms`, `toasts`, `turbo-setup`, `live`, `sheets`, `changes`, `clock`, `counts`, `dock`, `pick`, `password`.

Each needs the same shape:

- loaded once, from the `<head>`, on every page;
- listeners on `document` registered once, for the life of the tab;
- a **start** when a page arrives, which finds its elements or does nothing;
- a **stop** when the page leaves, which clears timers, aborts requests and drops references.

`live.js` (the poll), `clock.js` (a 5-second interval) and `sheets.js` (a dialog it creates) are the ones that leak today. The others mostly attach to `document` already.

This refactor changes no behaviour while navigation is off. That makes it releasable alone, with every existing check as its proof, before links are switched on.

### 2. Keep forms as they are

With navigation fully on, Turbo would also take over every form, and a form that is shown again with errors must then answer 4xx instead of 200. About ten views do that (log in, sign up, New session, Set settings, presets, Add players, the delete confirmations). Stage 3 already found this.

Turbo has a mode where links navigate and forms stay opt-in (`Turbo.config.forms.mode = "optin"`, read in its source). Stage 3's marked forms keep working; every other form posts natively and reloads the page, as today. A full reload after in-app navigation is harmless: everything simply starts again.

Converting those forms is a separate, optional step. It would make "Create session" or "Log in" arrive without a reload too, at the cost of touching ten views and the tests that expect status 200.

### 3. Never show an old ledger

- Turbo keeps copies of visited pages and can flash a copy while it fetches the fresh page. Stage 3 switched that cache off for every page; stage 4 must prove it with the Back button: an older figure must never appear.
- With the cache off, Back refetches the page. Scroll position on Back must still be restored; to be tested.

### 4. Prefetching

Turbo fetches a link when the pointer enters it and uses that response if the tap follows within 10 seconds. Reading its source, version 8.0.23 listens for `mouseenter` only. On a phone that event arrives with the tap, so it gains nothing there.

A few lines of our own can start the fetch at `touchstart`, about 100–200 ms before the tap completes. Consequences to weigh:

- A page fetched at touch time and shown at tap time is at most a fraction of a second old. On a desktop hover it can be up to 10 seconds old. A set page corrects itself by its 4-second poll; other pages show what the server said when the pointer arrived.
- Pages render one-time things when fetched: flash messages, a kept form after a refusal, a new invite link. A prefetch that is never shown would consume them. They are pending only between a POST and the page that follows it, so the window is narrow, but it must be closed: prefetch requests identify themselves with a header, and the server can decline to consume one-time state for them, or the app can prefetch nothing while such state is pending.
- Every touch on a link becomes a request to the function.

### 5. What full-page navigation gave for free

- **Offline.** Stage 2's service worker shows the offline page for a failed *page navigation*. A Turbo visit is a background fetch, which the worker ignores. A failed visit must fall back to a real navigation so the offline page appears.
- **Screen readers.** A real page load is announced by the browser. A swapped page is silent. The new page's title must be announced and focus moved to the top of the content.
- **A loading sign.** The browser's own progress indicator does not run. Turbo draws a thin bar at the top after 500 ms; it needs the app's colours.
- **The cross-page fade.** The existing CSS rule `@view-transition { navigation: auto }` applies to real page loads only. Turbo can use the same-document version of the feature when a page asks for it.
- **Refresh on return** (stage 2) reloads the page. It keeps working; it can later become an in-place refresh.

### 6. The browser checks

They click a link and wait a fixed 650 ms. That still passes locally, but two scripts detect "a new page loaded" by a marker on `window`, which now survives. Those assertions change to "the address and the content changed, and no document was loaded".

## Constraints

1. Money pages are never shown from a cache, including on Back.
2. Works without JavaScript: links are links.
3. Product principles from stage 3 still hold on the set and session pages.
4. No leak: after any number of screen changes there is exactly one poll loop on a set page and none elsewhere, one sheet dialog, and no script error.
5. The service worker, the offline notice and the installed app keep working.
6. No new dependency; Turbo is already vendored.
7. No preview deployment (the human's preference): each release must be safe by construction. The lifetime refactor is released first with navigation still off.

## Options

- **A. Links on, forms opt-in (recommended).** Fixes the complaint with the least change to the server.
- **B. Links and all forms.** Everything in-app, but ten views change status code and their tests change with them. Better as a follow-up once A has been used on a phone.
- **C. Chrome's built-in prerendering instead of Turbo navigation.** No script lifetime work, but nothing on an iPhone, which is the human's phone.

## Risks

- A script with a hidden once-only assumption that the checks do not exercise. Mitigation: a leak probe that taps through every screen many times and counts polls, dialogs, intervals and errors.
- A one-time message consumed by a prefetch. Mitigation in section 4.
- The Back gesture in the installed iPhone app with the page cache off. Cannot be tested here.
- The speed gain on production may be small. The human should expect smoothness more than speed from this stage.

# Actions update in place (stage 3 of the app-like experience): study

Date: 2026-10-05, Asia/Manila. Programme: [app-like experience plan](../plan/1791172782_app_like_experience.md).

## Request

The human said "start stage 3". Stage 3 is the first complaint from the programme's discovery: recording a buy-in, cash-out, count or paid mark reloads the whole page and jumps to the top. The programme plan required a short trial of two ways to fix it before recommending one.

## What happens today

There are 53 POST forms. Every one posts, gets a redirect and loads the page again. Measured with a probe that records a rebuy from a sheet on a running set (phone-sized headless Chrome, local server):

| | Today |
|---|---|
| Page reloaded | Yes |
| Scroll position after | Back to the top (0) |
| Text typed elsewhere on the page | Lost |
| Open "More host controls" | Closed |
| Requests for one rebuy | 16 (2 documents, then the stylesheet, font, logo and 11 scripts; in production the static files now come from the cache, so 2) |

The forms a host uses most, and where each lands:

| Action | Forms | Returns to |
|---|---|---|
| Buy-in, rebuy, cash-out (sheets on the set page) | `buy_in_add`, `cash_out_add` | The same set page |
| Confirm counts, clear a count | `count_confirm`, `count_clear` | The same set page |
| Open, start, end, resume, cancel a set | `session_transition` (6 forms) | The same set page |
| Add, withdraw, mark left | `participant_*` | The same set page |
| Reverse a buy-in or cash-out, override | 5 forms | The same set page |
| Finalize | `session_finalize` | The same set page |
| Mark paid, undo | `transfer_paid`, `transfer_unpaid` | The same session page |
| Close session, next set, cash out counted | 3 forms | **A different page** |
| Group settings, archive, sign-up, log in | about 20 forms | Mostly a different page, or the same form with errors and status 200 |

So about 25 forms return to the page they were sent from. Those are the ones that can update in place. The set page already has the machinery to replace its content without a reload: the 4-second poll in `static/js/live.js`, which keeps typed values (`data-keep`), open disclosures (`data-key`) and keyboard focus (`data-focus-key`).

## The trial

Two throwaway spikes, each on its own local branch, measured with the same probe and the existing browser checks. Neither is production code.

### Spike A: a small module of our own (`spike/own`)

A 2.4 KB script on the set page. It sends the form with `fetch`, follows the redirect, takes the new `#live` region out of the returned page and hands it to the existing `live.js` routine.

### Spike B: Turbo 8.0.23 (`spike/turbo`)

One vendored file, loaded on every page, with its "morph" page refresh and scroll preservation switched on. **No other line of the app was changed.**

### Results

| | Today | A: own module | B: Turbo, unconfigured |
|---|---|---|---|
| Page reloaded after a rebuy | Yes | No | No |
| Scroll position kept | No | Yes | Yes |
| Typed text elsewhere kept | No | **Yes** | **No** |
| Open disclosure kept | No | **Yes** | **No** |
| Refused amount: the sheet reopens with the error | Yes | Yes | **No** (error shown at the top only) |
| Requests for a rebuy | 16 | 2 | 3 |
| Script added | 0 | 2.4 KB | 217 KB (46 KB compressed) |
| Covers | — | Set page forms only | Every form and every link in the app |
| `dock.mjs` (145) | 145 | 134, then stopped at a state change | 145 |
| `archive.mjs` (85) | 85 | 85 | 84 |
| `settled.mjs` (24) | 24 | 24 | 24 |
| `entry.mjs` (91) | 91 | not affected (set page only) | 63, 2 failed, then stopped |
| `session_form.mjs` (69) | 69 | not affected | 68 |

What the failures mean:

- **A, `dock.mjs`:** after "Start the set" was sent in place, the next step found no dock. Not investigated within the timebox. It shows that even the small module has edge cases to find.
- **A, hidden hazard found while writing it:** the sheet's content, including its hidden `request_id`, is moved back into the page when the sheet closes. After an in-place update that would put the *old* form back, and the next rebuy would reuse a spent `request_id`, which the server treats as a repeat and ignores. The spike avoids it by emptying the sheet first. Any real implementation, with either approach, must test this.
- **B, the four failures** are one cause: pages that answer a refused form with status 200 (log in, sign up, New session, Delete group). Turbo requires 4xx for a form that is shown again. This was predicted in the programme study; it is about eight views.
- **B, lost typing and disclosures:** Turbo's morph makes the page match the server's HTML, so text typed in another field and an open disclosure are reset. This breaks a product principle ("preserve typed values during live updates") until handled. Turbo offers hooks for exactly this; I have not yet proven the fix, only the problem.

## What each choice means for the rest of the programme

- **Stage 4 (screen changes without a reload) needs JavaScript navigation on an iPhone.** Chrome can pre-render pages with a browser feature; Safari has no equivalent the app can rely on. So stage 4 means either Turbo or writing history, scroll restoration, prefetching and a page cache ourselves. Those are the parts that are easy to get subtly wrong.
- **With spike A's approach**, stage 3 is small and safe, but stage 4 starts from nothing, and if it then adopts Turbo the stage 3 module is thrown away.
- **With Turbo**, stages 3 and 4 are one mechanism switched on in two steps: forms first, links later.

## Facts about Turbo that matter here

Verified in the trial:

- It works with this app's server-rendered pages and redirects with no server change, for forms that redirect.
- It preserves scroll on a same-page refresh.
- The existing dock, archive and settle-up checks pass with it loaded.
- Size: 217 KB, 46 KB compressed. The app's own scripts total about 28 KB uncompressed. It is MIT-licensed, from 37signals.

From its documentation as I know it, **not yet verified in this app**; the plan makes each a test:

- It can be loaded with navigation switched off and enabled per form or per link.
- It keeps a cache of visited pages and can show a cached copy for a moment when returning. For a ledger that is a stale-money risk, so the cache must be switched off.
- It offers events before an element is morphed, which is where typed values and open disclosures would be preserved.
- When it replaces a page body it runs the scripts in it again. Ten of our modules assume they run once; that matters for stage 4, not for same-page refreshes in stage 3.

## Constraints

1. Product principles: success only after the server accepts; typed values survive; figures never animate between values.
2. `request_id` idempotency must keep working: one tap, one record; a refreshed form must carry a fresh id.
3. Works without JavaScript: every form stays a native form.
4. No ledger page from a cache (programme constraint 4), now including Turbo's own page cache.
5. Stage 1 gives scripts a per-release address. A 46 KB library that never changes should not be downloaded again on every release.
6. AGENTS.md: a front-end library needs a recorded requirement. The programme plan's decision 5 allowed one "if the stage 3 trial favours it", as one vendored file with no build step.
7. The service worker from stage 2 only handles page navigations; background form requests do not pass through its offline page. A failed background send needs its own honest failure state.

## Recommendation

**Turbo, switched on for forms only in this stage.** The trial shows the own module is the smaller answer to stage 3 alone, and it kept typed values where unconfigured Turbo did not. But it solves a quarter of the programme and leaves the hard quarter (stage 4) unsolved, while Turbo's gaps found in the trial are known, bounded and the same work stage 4 needs anyway.

The honest counter-argument: 46 KB compressed is nearly twice the app's whole JavaScript today, a dependency to keep current, and three behaviours I have read about but not yet proven here. If the human prefers the smallest possible change now and is content to revisit stage 4 separately, spike A's approach is a sound choice and the plan below would shrink to the set and session pages.

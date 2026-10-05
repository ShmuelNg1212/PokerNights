# Screen changes without a reload (stage 4): plan

Status: approved 2026-10-05 ("approved."); decisions as recommended, including prefetch at touch. Date: 2026-10-05, Asia/Manila. Study: [Screen changes without a reload](../study/1791181036_screen_changes_without_reload.md). Programme: [app-like experience](1791172782_app_like_experience.md).

## Outcome

Tapping from Your groups to a group, a session, a set and back changes the screen without unloading the page: no blank moment, one request, and nothing left running from the screen that was left. Forms that lead to another page still load a page, as today.

No migration. No change to any service, rule or message.

## Two releases

Because there is no preview deployment, the risky part is split so that the first release changes nothing a person can see.

### Release 4a: give every script a lifetime (navigation still off)

- All page scripts load once from the `<head>` of every page.
- A small registry, `static/js/page.js`: a module registers a **start** that runs when a page arrives and may return a **stop** that runs when it leaves. Until navigation is switched on, start runs once per page load, exactly as today.
- The twelve modules are rewritten to that shape. Listeners on `document` are registered once. `live.js` stops its poll and abandons a request in flight; `clock.js` clears its interval; `sheets.js` removes its dialog.
- Proof: every existing test and browser check passes unchanged, and a new lifetime check passes with navigation forced on in the test only.

### Release 4b: switch links on

- `Turbo.config.forms.mode = "optin"` and navigation on. Stage 3's marked forms keep updating in place; all other forms post natively.
- The items in "What must be true" below.

## What must be true, and how each is proven

Each line is a browser check.

1. **No document load** while tapping through Your groups, a group's three tabs, a session, a set, the set log and back.
2. **No leak.** After 20 screen changes: exactly one poll loop on a set page (2 requests in 8.5 s), none after leaving it, one sheet dialog, one clock interval, and zero script errors.
3. **Every page behaves as after a fresh load.** The dock toggle, sheets, count preview, toasts, password Show button, player picker, offline notice and refresh-on-return all work on a page reached by a tap, checked by running the existing assertions after arriving by link.
4. **Back and Forward** show a freshly fetched page, never an older figure: change a value in a second browser, press Back in the first, and the new value is there. Scroll position on Back is restored.
5. **In-place actions still work** on a set page reached by a tap (stage 3's rebuy, refused amount and count confirm).
6. **Forms that lead elsewhere still work** from a page reached by a tap: New session, close session, log out, log in.
7. **Offline.** A screen change with the server unreachable shows stage 2's offline page, and Try again recovers.
8. **Screen readers.** After a screen change the new page's title is announced once and focus is at the start of the content.
9. **A loading sign** in the app's colours appears when a screen takes longer than half a second.
10. **A link with an anchor** (`#tables`, `#manage`) lands on its section. A link to another site, to `/admin/` or to a file leaves the app the ordinary way.
11. **An expired login** during a tap leads to Log in.
12. **Without JavaScript** every link is an ordinary link.
13. **The installed app** (stage 2's checks) still passes.

## Prefetching: a decision

Recommended for this stage: **fetch at touch, with the one-time-state guard.** A link is fetched when the finger touches it; requests marked as prefetch never consume flash messages or kept forms. If the guard proves awkward, prefetching is left out of 4b and the stage still delivers its outcome.

## Implementation

1. **`static/js/page.js`** and the rewrite of the twelve modules (4a).
2. **`base.html`**: scripts in the head with `defer`; the per-page `scripts` blocks are removed; a visually hidden live region for announcements.
3. **`turbo-setup.js`** (4b): forms opt-in; start and stop wired to Turbo's page events; a failed visit falls back to a real navigation; announce and focus; the stage 3 logic unchanged.
4. **CSS**: the progress bar in Brass on the header surface; the same-document fade, off under reduced motion.
5. **Prefetch at touch** with a server-side guard (a small middleware or helper that leaves messages and kept forms alone when the request says it is a prefetch).
6. **Tests first.**
   - Django: scripts are in the head on every page; the prefetch guard leaves a flash message and a kept form for the real request.
   - Browser check `navigate.mjs`: one check per line above, plus the leak probe and the timing from the study, recorded before and after.
   - `inplace.mjs`: its two assertions about navigation being off change to the new truth.
   - `entry.mjs`: the two failures seen in the trial are investigated and fixed, not skipped.
   - Every other browser script passes unchanged.
7. **Verify** on SQLite and PostgreSQL; all browser checks; release 4a; check production; release 4b; check production; phone checklist.
8. **Sync docs**: wiki architecture (the script lifetime rule becomes a rule for every future script), features, a footgun page ("a script that runs once per page load leaks under in-app navigation"), DESIGN.md (progress bar, announcement), browser README, TODO, the programme plan.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **Links on, forms stay as they are.** Recommended. New session, log in and similar forms still load a page. Converting them is a later, optional step.
2. **Two releases, 4a then 4b.** Recommended, since you test on the live site: 4a should be invisible, and if it is not, that is found before links change.
3. **Prefetch at touch.** Recommended, with the guard. Say no if you prefer the simplest version first.
4. **Expectations.** On production the speed gain is likely modest (the study explains why the local numbers overstate it). What you should notice is that screens no longer blink. If that is not worth two releases to you, say so now.

## What I cannot verify

- The feel on your phone, and the Back gesture inside the installed app.
- Timings on production for signed-in screens; I have no production account.

## Acceptance criteria

- AC1. Lines 1 to 13 each pass their check.
- AC2. After release 4a, every existing test and browser check passes with no assertion changed.
- AC3. The leak probe's numbers are exactly the expected ones after 20 screen changes.
- AC4. Before-and-after timings are recorded for local and, for signed-out pages, production.
- AC5. All tests pass on SQLite and PostgreSQL; every flow works with JavaScript off.

## Out of scope

Converting forms that lead elsewhere; directional transitions and motion (stage 6); replacing the poll; changing what any screen shows.

## Rollback

4b: set navigation off again in `turbo-setup.js` (one line) and release. 4a: revert its commits; it changes no behaviour, so there is no data or state to undo.

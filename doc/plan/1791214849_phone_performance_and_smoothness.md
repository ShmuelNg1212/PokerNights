# Phone performance and smooth motion: plan

Status: stages 1 and 2 released 2026-10-06 as `c84f45a`; the tab fix as `fedaeb0`. Stage 3: A is built, B is the human's step, C and D have their own plan. Stage 3 waits for the phone's numbers. Approved 2026-10-05. Working branch: `perf/phone-smoothness`. Date: 2026-10-05, Asia/Manila. Study: [phone performance and smoothness](../study/1791214796_phone_performance_and_smoothness.md). Base: `main` at `90ff346`.

## Outcome

A tap is answered on the screen within one frame. The host dock slides without redoing the page's layout. The human can read, on their own phone, how long each screen takes and where the time goes. What is done about the server afterwards is decided from those numbers.

## What the study found, in four lines

1. The browser's own work is small: 15 ms of script on a reopened app with the processor slowed 4×, no long task anywhere.
2. The host dock animates `height` and restyles the whole page every frame: 27 to 55 layouts per slide, against 2 to 4 for everything else.
3. A screen change shows nothing until the server answers. Cards and rows that are links have no pressed state.
4. Signed-in pages make 10 to 24 database round trips each, on a new database connection per request. What that costs in production is unmeasured.

## Stages

Each stage is one release that is safe on the live build: it is either inert until asked for, or falls back to today's behaviour.

### Stage 1. A readout on the phone

- A middleware adds a `Server-Timing` header to every response: total time in the view, time in the database, and the number of queries. It reads only what Django already counts. It writes nothing and changes no response body.
- Opening any page with `?perf=1` turns on a small readout for that tab, in the manner of the existing `?kb=1` on the set page. After every screen change and every in-place action it shows: tap to response, response to settled screen, the server's total, database time and query count, and the number of frames longer than 25 ms while things moved. `?perf=0` turns it off. Without the parameter no code runs beyond one check.
- The human walks the usual path once on the phone and sends screenshots. Those numbers go into the study as a dated addendum.

Files: a new `config/timing.py`, `config/settings.py` (one middleware line), a new `static/js/perf.js`, `templates/base.html` (one script tag), `static/css/app.css` (the readout), tests in `config/tests.py`.

### Stage 2. The known fixes

- **Host dock.** The dock slides by `transform` and no longer by `height`. `--dock-h` is written once, at the end of a fold and at the start of an unfold, so the page's padding changes once per slide and the last row is never covered. The content still leaves with the edge on closing. The keyboard handling (`frame()`, `keyboard()`, `--kb`, `--kb-h`) is not edited. Target: at most 4 layouts per slide in the probe, from 27 to 55.
- **Pressed state for links.** Group cards, session rows, the home bands, the tabs and the back link take a pressed look from the first frame of a touch, in plain CSS from existing tokens, with no movement. A link whose screen is still on its way keeps that look until the screen changes. Reduced motion keeps it, since it does not move.
- **Marks that overlap (reported by the human at approval).** The brass mark on a changed player is an outline drawn 4 px outside its row, so it covers the rows above and below and two marked neighbours cross. "Rebuy added" is pinned to the row's top right corner, over the amount. Reproduced at 390 px: the badge covers 3 px of the figure and sits on the outline. The mark is drawn inside the row, and the badge takes a place in the line under the player's name, where it can wrap but cannot cover anything.
- DESIGN.md's motion section records all three.

Files: `static/js/dock.js`, `static/css/app.css`, `static/js/turbo-setup.js` (the waiting mark only), `static/js/changes.js`, `templates/web/_players.html`, `web/tests/browser/dock.mjs`, `navigate.mjs` and `flow.mjs`, `DESIGN.md`.

### Stage 3. The server, decided from stage 1's numbers

Not planned in detail, on purpose. Candidates, in the order the numbers are likely to favour:

1. Fewer queries on Session (24) and Your groups (17).
2. Keeping the database connection between requests. This is a Vercel environment variable (`DB_CONN_MAX_AGE`), set by the human, and is undone by setting it back.
3. Whatever the readout shows that this study did not expect.

Stage 3 gets its own addendum to the study and its own approval. If stage 1 shows the server at well under 100 ms per screen, stage 3 is dropped.

## Scope and exclusions

No change to services, models, money rules, polling interval, the service worker, or what is cached. No migration. No new dependency. No page is shown from a cache. No amount is shown before the server accepts it. The 220 ms screen slide and the button spring are left as they are. Turbo and Motion stay. Push and deployment require a new instruction per stage.

## Acceptance criteria

- AC1. With `?perf=1` on the phone, every screen change and in-place action shows its five figures. Without it, pages are byte-identical to today except for the `Server-Timing` header.
- AC2. `Server-Timing` reports the same query count as Django's own count in a test, on HTML pages, the poll and redirects.
- AC3. One fold and one unfold of the host dock cause at most 4 layouts each in the probe at 6× slowdown, and no frame over 25 ms.
- AC4. The dock still: remembers folded or unfolded, becomes the one-line bar on the keyboard, reserves room so the last row is reachable in both states, survives a live redraw mid-slide, and changes size at once under reduced motion. `dock.mjs` passes.
- AC5. Touching any link listed in stage 2 changes its look within one frame; the look is gone on the new screen and after a Back gesture. Contrast stays at or above the current values.
- AC5b. With three neighbouring players marked at once, no mark crosses another row's box, and no "Rebuy added" or "Updated" badge intersects a name, an amount or a button, at 320, 390 and 1280 px, as host and as player.
- AC6. Every flow still works with JavaScript off. All Django tests pass on SQLite and PostgreSQL. `dock.mjs`, `navigate.mjs`, `inplace.mjs`, `motion.mjs` and `flow.mjs` pass.
- AC7. Before and after figures from the phone are recorded in the study addendum.

## Ordered implementation board

- [x] **Stage 1, tests first.** Write failing tests for the header (present, well-formed, counts match, absent of side effects on a prefetch). Add the middleware. Add `perf.js` and its styles. Browser check: readout appears with `?perf=1`, survives a screen change, and is absent without it. Commit `feat(perf): server timing header and on-phone readout`.
- [x] **Stage 1 rendezvous.** Run both suites. Record in this plan. Update the wiki (architecture, a short "measuring on a phone" note) and TODO with the phone walk. Stop for the instruction to release.
- [x] **Stage 2, dock.** Extend `dock.mjs` with the layout-count check so it fails first. Change `slide()` and the `--dock-h` writes. Run `dock.mjs`, `count_flow.mjs` and `numpad.mjs`. Commit `perf(ui): slide the host dock without layout`.
- [x] **Stage 2, pressed links.** Add the check to `navigate.mjs` so it fails first. Add the CSS and the waiting mark. Commit `feat(ui): pressed state for links`.
- [x] **Stage 2, marks.** Add the overlap check to `flow.mjs` so it fails first. Draw the mark inside the row and move the badge into the line under the name. Commit `fix(ui): keep change marks inside their rows`.
- [x] **Stage 2 rendezvous.** Rerun the probe for before and after figures. Both suites and the browser checks. Update DESIGN.md, the wiki and TODO. Stop for the instruction to release.
- [ ] **Stage 3.** Addendum to the study from the phone's numbers, then a plan, then approval.

## Verification record (2026-10-06)

Branch `perf/phone-smoothness`: `9e684fc` (timing header and readout), `326f23d` (dock), `9dbd24f` (pressed links), `b615c44` (marks). Merged to `main` by fast-forward and pushed on 2026-10-06; the Vercel build passed and the live site carries the header about two minutes after the push.

| Check | Result |
|---|---|
| Django suite, SQLite | 682 pass, 10 skipped (PostgreSQL-only) |
| Django suite, PostgreSQL 17 | 682 pass |
| Build-style run (`VERCEL=1`, throwaway SQLite) | 682 pass, 10 skipped |
| `perf.mjs` (new) | 12 of 12 |
| `dock.mjs` | 228 of 228 (was 223; 3 of the 5 new checks failed before the change) |
| `navigate.mjs` | 48 of 48 (7 of the 16 new checks failed before the change) |
| `marks.mjs` (new) | 18 of 18 (12 failed before the change) |
| `flow.mjs`, `motion.mjs`, `count_flow.mjs`, `numpad.mjs`, `inplace.mjs` | 52, 34, 89, 87 and 38, all pass |

Host dock, same probe as the study, processor slowed 6×:

| | Before | After |
|---|---|---|
| Fold: main-thread work | 80 ms | 32 ms |
| Fold: layouts | 27 | 5 by the probe, 3 by `dock.mjs` |
| Unfold: main-thread work | 127 ms | 26 ms |
| Unfold: layouts | 55 | 5 by the probe, 3 by `dock.mjs` |
| Style work for one fold and unfold, 4× | 75 ms | 11 ms |

Acceptance: AC1 to AC6 met locally, with the rulings below. AC7 (figures from the phone) waits for the release of stage 1.

### Rulings made while building

1. **Opening a database connection is timed too.** The header has a third figure, `connect`, because a new connection per request is one of stage 3's candidates and query time alone would hide it. The middleware shadows the connection's `connect` method for the length of one request and removes it in a `finally`. If wrong: the figure reads 0 and nothing else changes.
2. **The page content glides with a folding dock.** Not in the plan. Writing `--dock-h` once makes a page that is scrolled to its end jump down when the dock folds. The elements beside the dock are moved back by transform and glide down with it, as before. If wrong: a jump of about 110 px at the end of the page on fold.
3. **AC3 measures 3 layouts in `dock.mjs` and 5 in the probe.** The probe's window includes its own reads. The criterion that matters, no layout per frame, holds in both.
4. **AC5's contrast clause could not hold as written.** On a near-black ground a pressed look that darkens cannot be seen, so the surface lightens by 12% bone. Bone text on it stays above 11:1. If wrong: the pressed look is one custom property, `--pressed`.
5. **A button link shows the existing busy line** while its screen is on the way, the same sign a sent form gives. Not in the plan; it reuses a built pattern.
6. **The mark reaches 8 px into the page's side margin.** Rows have no side padding, so a mark kept wholly inside would touch the player's chip. Above and below it stays 2 px inside the row. If wrong: one `inset` value.
7. **The overlap check is its own script, `marks.mjs`,** not an addition to `flow.mjs`. It only reads, so it can be rerun; `flow.mjs` uses up its fixtures.
8. **`navigate.mjs` and `inplace.mjs` take `PN_PORT`.** They restart "the server on 8765" themselves, and a server from an earlier session was running there. It was left alone.

Self-review only: no second reviewer read the branch.

## After the release: the phone's verdict (2026-10-06)

The human sent nine screenshots of the readout; they are tabled in the [study's addendum](../study/1791214796_phone_performance_and_smoothness.md). AC7 is met. Two results:

- **Tabs felt "not snappy anymore".** Timing is identical to the previous release (marker 180 ms after the tap, movement over at 446 ms, both builds). The one visible change is the pressed look on the tapped tab, which shows the wait and blurs the marker's slide. Fixed on branch `fix/tab-switch-feel`: tabs take no pressed look. `navigate.mjs` 48 of 48, with the changed check failing first. Not released.
- **Stage 3 has its numbers.** The proposal is in the addendum: (A) send the fetch at touch, which today has no head start and sends a duplicate on quick taps; (B) keep the database connection; (C) fewer queries on two screens; (D) actions without the redirect trip, as its own study; (E) a shorter slide if wanted. **Awaiting approval.**

## Stage 3, as chosen by the human (2026-10-06)

"A and B now, then plan for C, then D." The tab fix was released as `fedaeb0`.

- **A. Fetch at touch: built, not released.** Branch `perf/stage-3`, commit `d427f4b`. Turbo waits 100 ms after a hover before it prefetches; for the length of the one call that passes a touch on, its timer is given no delay. Measured with a real touch held 60 and 130 ms: one request, 2 ms after the finger lands (before: at the tap, plus a wasted second one at 107 ms for a quick tap). `navigate.mjs` 52 of 52, the two new checks failing first; `inplace.mjs` 38, `motion.mjs` 34, `perf.mjs` 12; Django 682 pass. Ruling: the vendored Turbo file is not edited, because its address is cached for a year under its version name. If wrong: the touch falls back to today's behaviour, a request at the tap.
  A page fetched ahead is rendered without flash messages (`config/prefetch.py`); they stay for the next ordinary page. Until now such a page was rarely the one shown; now it usually is. A message still waiting when a link is tapped is rare (messages come with form answers), and it is shown on the screen after.
- **B. Kept database connection: the human's step.** In Vercel set `DB_CONN_MAX_AGE` to `60` for Production (it is `0`). It takes effect with the next deployment, so set it before A is released. The readout's `open` figure is the proof: 0 on most taps instead of 16 to 33. The code path is the default everywhere else and runs in the PostgreSQL suite; connections are checked before reuse (`conn_health_checks`) and server-side cursors are off for the pooler. If `open` does not fall, Vercel is not reusing the connection between requests and the next step would be Django's own connection pool, which needs a package. If anything errors, set it back to `0` and redeploy.
- **C and D:** [plan](1791219154_fewer_queries_and_one_trip_actions.md), awaiting approval.

## For the human to do

- After stage 1 is live: open the app with `?perf=1` added to the address, walk Your groups → a group → a session → a set in play, record a rebuy, fold and unfold the host menu, go back to Your groups. Send the screenshots. Do it once on Wi-Fi and once on mobile data if you can.
- After stage 2 is live: say whether a tap on a card now feels answered, and whether the host menu slides cleanly, also during count-up with the keys open.

## Open question

Which moment made you ask? A screen, an action or an animation that feels slow or jerky, and on which phone. An answer moves that item to the front; without one the plan stands as written.

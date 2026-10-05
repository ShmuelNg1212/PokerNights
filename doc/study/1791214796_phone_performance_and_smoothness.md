# Phone performance and smooth motion: study

Date: 2026-10-05, Asia/Manila. Base: `main` at `90ff346`.

## Request

The human wants the app to run seamlessly on a phone, with the focus on performance and smooth animation. No symptom was named: not which screen, which action or which phone.

## Understanding

- **Said:** faster, and smoother motion, on a phone.
- **Assumed:** "seamless" means that a tap is answered at once, a screen arrives without a wait the eye notices, and nothing stutters while it moves. The phone is the human's iPhone, in Safari and as the installed app. The rules in AGENTS.md, PRODUCT.md and DESIGN.md stay: money shows only its accepted value, no page of money is shown from a cache, every flow works without JavaScript, reduced motion stays still.
- **Success:** numbers taken on the real phone before and after, and the human saying it feels right.

## What exists already

Four earlier cycles did most of the usual phone work, and this study does not repeat them:

- Stylesheets and scripts are cached for a year and versioned per release ([app-like experience](1791172718_app_like_experience.md)).
- Actions update the page in place and links change screens without a reload, through Turbo. A link is fetched when the finger touches it.
- Motion (motion.dev) runs buttons, sheets, toasts, row movement and screen changes ([motion overhaul](1791186418_motion_overhaul.md)).

## What was measured

Method: a fresh temporary SQLite database with the `seed.py` and `seed_flow.py` fixtures, a local server, and Chrome driven over CDP at 390 × 844, device pixel ratio 3, with the processor slowed 4× and 6×. Two probes: main-thread time per interaction with frame intervals, and a trace split by kind of work. Production was timed from the development machine, signed out. The probes are throwaway scripts and are not in the repository.

### 1. The browser has little to do

Full load of a set in play, processor slowed 4×:

| | Script | Style + layout | First paint |
|---|---|---|---|
| Nothing cached | 57 ms | 26 ms | 141 ms |
| Files cached (the app reopened) | 15 ms | 21 ms | 53 ms |

The two libraries cost 23 ms uncached and 5 ms cached (Turbo 19 → 3 ms, Motion 4 → 2 ms). No task over 50 ms was recorded on any page. The page has 444 elements; the stylesheet has 626 rules.

Interactions on the set page, processor slowed 6×:

| Interaction | Main-thread work | Layouts | Frames over 25 ms |
|---|---|---|---|
| Idle for 3 s (poll and clock) | 12 ms | 0 | 0 |
| Press a button | 45 ms | 3 | 0 |
| Open a sheet | 44 ms | 3 | 0 (2 in one run at 4×, worst 67 ms) |
| Close a sheet | 27 ms | 2 | 0 |
| **Host dock, fold** | **80 ms** | **27** | 0 |
| **Host dock, unfold** | **127 ms** | **55** | 0 |
| Rebuy sent in place | 102 ms | 4 | 0 |
| Live poll redraw | 28 ms | 4 | 0 |
| Scroll 1,200 px | 14 ms | 1 | 0 |

Sheets, the backdrop, toasts and screen changes animate only `transform` and `opacity`, which the browser moves without redoing layout.

### 2. One animation works against the browser: the host dock

The dock slides by animating its `height` (`dock.js`, `slide()`). Each frame changes the layout. A `ResizeObserver` then writes the new height to `--dock-h`, which changes the page's bottom padding, so the whole document is restyled every frame: 75 ms of style work for one fold and unfold at 4×, six times the cost of any other animation. It stayed inside the frame budget in emulation. It is the one place where a slower or busier phone would drop frames, and it is the control the host uses most during count-up.

### 3. A screen change waits for the server before anything moves

| Added delay per request | Tap to settled screen |
|---|---|
| None (local server) | 320–340 ms |
| 150 ms | 480–540 ms |

Of this, 220 ms is the slide. The rest is the request, and nothing on the screen changes during it. Buttons sink under the finger; a card or a row that is a link has no pressed state at all (`:active` exists only on `.btn`). On a phone connection the first sign of life after tapping a group or a session comes a few hundred milliseconds late. Each change also starts with one frame of 33–67 ms while the browser photographs the old screen. That is how view transitions work and is not ours to remove.

### 4. The server's share is unknown where it matters

Locally each page renders in 4–6 ms. The query counts are:

| Page | Queries |
|---|---|
| Your groups | 17 |
| Group | 10 |
| Session | 24 |
| Set in play | 15 |
| Poll, nothing changed | 4 |
| Poll, changed | 15 |

Production, signed out, on a kept connection: 60–90 ms to first byte for the login page, 45–58 ms for a static file, 12 ms ping. A new connection adds about 100 ms.

**Signed-in pages could not be measured**: the agent has no production account. Two facts suggest the cost is larger there. Every query is a network round trip from the function to Neon, and pages make 10 to 24 of them in sequence. `DB_CONN_MAX_AGE=0` opens a new database connection for every request, including each 4-second poll. Neon's free tier also suspends an idle database. None of this has a number yet, so none of it is a finding yet.

## Conclusions

1. The app is not slow in the browser. No rewrite, library removal or bundling step is justified by these numbers.
2. One animation should move off layout: the host dock.
3. Taps on links need an immediate answer on the screen, because the server's answer cannot be instant.
4. The largest remaining share of every tap is probably the server round trip in production, and it is unmeasured. It must be measured on the human's phone before anything is changed for it.

## Options

- **A. Measure on the phone first, fix the two known things, then decide the server work from the numbers (recommended).** Small, safe releases; each gain is proven where the human feels it.
- **B. Fix the known things only.** Cheapest. Leaves the probable main cost unexamined.
- **C. Optimise the server now** (fewer queries, kept database connections). Likely useful, but it is a guess until measured, and a kept connection behind Neon's pooler is a production change that deserves a number to justify it.

## Considered and not proposed

- **Removing Motion (144 KB) or Turbo (217 KB).** They cost 5 ms on a reopened app and are cached for a year.
- **Showing pages from a cache while the fresh one loads.** It would be the largest perceived gain and it breaks "money data is never stale".
- **Optimistic updates of amounts.** PRODUCT.md forbids them.
- **A shorter screen slide.** 220 ms is within DESIGN.md's limit; whether it feels slow is a question for the phone check, not a measurement.
- **The button press spring**, which runs in script. 45 ms of work at 6× with no slow frame.

## Risks

- Emulation is not an iPhone. Safari's compositor, the installed app's shell and a real radio behave differently. The on-phone readout in the plan exists for this reason.
- The dock is tied to the keyboard handling in `dock.js`, which took two cycles to get right on an iPhone ([footgun](../wiki/footguns/ios_keyboard_covers_fixed.md)). A change to how it slides must not touch how it sits on the keyboard.
- The human tests on the live build. Each stage must be inert unless asked for, or fall back to today's behaviour.

## Addendum, 2026-10-06: numbers from the human's iPhone

Source: nine screenshots of the `?perf=1` readout, taken at 12:25 to 12:28 on Wi-Fi in Safari, on the release `c84f45a`. One full game was played: a new session, a set opened and started, two rebuys, count-up, cash-out, finalize, the session closed and three transfers marked paid. Times are milliseconds.

### Screen changes (a link)

| Screen | Wait | Draw | Move | Total | Server | Queries | Database | Open |
|---|---|---|---|---|---|---|---|---|
| Group, Stats tab | 206 | 15 | 311 | 532 | 70 | 7 | 22 | 32 |
| Group, Settings tab | 176 | 21 | 307 | 504 | 54 | 10 | 15 | 16 |
| Group, Stats tab | 231 | 27 | 309 | 567 | 65 | 7 | 23 | 27 |
| New session | 155 | 27 | 308 | 490 | 43 | 7 | 9 | 19 |
| Session | 190 | 34 | 301 | 525 | 110 | 19 | 51 | 26 |
| Your groups | 216 | 19 | 297 | 532 | 59 | 12 | 17 | 18 |
| Your groups (once) | 2 | 13 | 310 | 325 | 121 | 12 | 63 | 33 |

### Actions (a form sent in place)

| Action | Wait | Draw | Move | Total | Server (last answer) | Queries | Database | Open |
|---|---|---|---|---|---|---|---|---|
| Open for players | 406 | 45 | 277 | 728 | 88 | 17 | 39 | 24 |
| Start the set | 606 | 35 | 604 | 1,245 | 88 | 15 | 36 | 27 |
| Confirm rebuy | 410 | 27 | 625 | 1,062 | 87 | 15 | 38 | 26 |
| Confirm rebuy | 406 | 24 | 614 | 1,044 | 88 | 15 | 37 | 26 |
| End play and count up | 388 | 45 | 264 | 697 | 91 | 14 | 35 | 24 |
| Confirm 4 counts | 367 | 42 | 1,020 | 1,429 | 81 | 14 | 33 | 24 |
| Finalize set | 449 | 46 | 400 | 895 | 63 | 16 | 20 | 17 |
| Mark paid | 392 | 23 | 607 | 1,022 | 69 | 23 | 25 | 18 |
| Mark paid | 342 | 24 | 283 | 649 | 118 | 23 | 59 | 26 |

Full loads: a set, server 165 (17 queries, database 106, open 25); a session, server 114 (23 queries, database 58, open 27).

Taps that ask the server nothing (sheets, the host menu, the number keys' Done): 0 to 3 late frames of about 42, the longest 59 ms. The host menu folded and unfolded with 0 and 1 late frames.

### What the numbers say

1. **The phone itself is not the limit.** Drawing a new screen takes 13 to 46 ms. Late frames are 1 to 3 per tap and the longest is 59 ms. This agrees with the emulated figures.
2. **A screen change is about half waiting and half movement.** Roughly 200 ms of wait, 20 ms of drawing and 300 ms of movement.
3. **Most of the wait is not our server's work.** Wait minus server is 110 to 170 ms on every screen change: the trip to Vercel and back, and Vercel's own handling. Nothing in this repository shortens that, except not making the trip at tap time.
4. **The server's own share is 45 to 120 ms**, of which opening a database connection is 16 to 33 ms on every request, queries are 9 to 63 ms (about 2.5 ms each), and Python is 15 to 25 ms.
5. **An action costs two trips.** The form is posted, the server answers with a redirect, and the page is fetched again. That is why an action waits about 400 ms where a link waits about 200.
6. **"Move" on actions is decoration, not delay.** It runs until the last animation stops: the sheet leaving, the toast, the pulse, the books-balanced moment (1,020 ms after confirming counts). The page is usable from "draw".

### The fetch at touch never had a head start

The readout shows one screen change with a wait of 2 ms and every other at 155 to 231 ms. The design says a link is fetched when the finger touches it, which should take a tap's length (about 100 ms) off every wait. It does not.

Cause: Turbo waits 100 ms after the pointer reaches a link before it sends the prefetch (`PREFETCH_DELAY`, meant for a mouse that is only passing over). `turbo-setup.js` reports the touch to Turbo as that pointer event, so the wait applies to a finger too. Measured locally with a real touch held for a set time:

| Finger down for | Requests for the screen | Head start |
|---|---|---|
| 60 ms | 2: at the tap, and a wasted one at 107 ms | 0 |
| 90 ms | 2: at the tap, and a wasted one at 110 ms | 0 |
| 130 ms | 1, at 103 ms | 33 ms |
| 200 ms | 1, at 103 ms | 103 ms |

So an ordinary tap gets nothing, and a quick tap also sends the request twice. The second one is thrown away after costing a function call and its queries.

### The tab report

The human found switching a group's tabs "not snappy anymore" after the release. Measured on the previous release (`90ff346`) and this one, side by side with a touch and 150 ms of added delay: the marker reaches the new tab 180 ms after the tap and the movement ends at 446 ms, in both, on all three tabs. Nothing became slower. One thing changed: the tapped tab now lights up at once (the pressed look from stage 2). A lit tab looks chosen, its content has not come yet, and for 200 ms the wait is on show; then the marker slides under a tab that is already lit, so the slide reads as a fade. The earlier build showed nothing until tab and content moved together.

This is a conclusion from a measurement that found no difference in time, plus reasoning about the one visible difference. It could not be confirmed on an iPhone here. The pressed look is removed from tabs; the phone decides whether that was it. The readout itself adds a little work on every frame while it follows a tap, so the feel should be judged with `?perf=0`.

### Proposal for stage 3, in order of gain per risk

| | Change | Expected gain | Size and risk |
|---|---|---|---|
| A | Send the fetch the moment the finger touches a link, and stop the duplicate | 70 to 120 ms off the wait of every screen change; one request less per quick tap | A few lines in `turbo-setup.js`; no server change |
| B | Keep the database connection between requests (`DB_CONN_MAX_AGE`, a Vercel variable) | 16 to 33 ms off every request; twice that off an action | No code. Needs a check that Neon's pooler and Vercel's function reuse behave; undone by setting it back |
| C | Fewer queries on Session (19 to 23) and Your groups (12 to 17) | 20 to 40 ms on those two screens | Read-only query work with tests |
| D | Answer an in-place action with the page itself, without the redirect trip | About 200 ms off every action, the host's most frequent taps | The largest change: it touches how every form answers and the no-JavaScript path must keep working. Needs its own study |
| E | A shorter slide between screens (220 ms now) | Up to about 80 ms of perceived time | One number; a matter of taste for the human |

Recommended: A and B now, C after, D as its own study. E only if the human asks.


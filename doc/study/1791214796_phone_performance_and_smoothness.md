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

# Optimize and clean up: study

Date: 2026-11-14, Asia/Manila. Request: "scan the whole codebase and see how it can be optimized and cleaned up". Code at `750fea5`. This study changes no code. The [general cleanup study](1793345855_general_cleanup.md) of 2026-10-30 is the earlier pass; this one repeats its method and adds speed.

## Method

1. `ruff check --select F,B,UP,SIM,PIE,RET,PERF` and the complexity rules (`C901`, `PLR09xx`), through `uvx`.
2. `vulture` over the apps, without migrations and tests. Each named function, method, property and class was searched for in Python, templates and scripts.
3. Each template and each file in `static/js` was searched for a reference. Each class selector in `static/css/app.css` was searched for in templates, scripts and Python.
4. File sizes, raw and with `gzip -9`, for the stylesheet and the scripts. The script tags in `templates/base.html`.
5. The full test suite on SQLite: in one process, with `--parallel`, and with `--durations 25`. One test module under `cProfile`. The `ledger` tests with three test-database settings.
6. The query-count tests, the polling views, the database settings and the middleware.
7. `git branch --merged main`, the repo root, and the tracked tool folders.

## Summary

The code is clean. Ruff finds no unused import or name. The dependency rule holds. Query counts are bounded by tests. The largest gains are not in the Python code:

| # | Finding | Gain | Risk |
|---|---|---|---|
| 1 | Each page asks for 47 scripts, 505 KB before compression | Faster first load after each release | Medium: touches every page |
| 2 | Each release makes every phone download every script and the stylesheet again | Less data after a release | Medium: static file addresses |
| 3 | The suite fails with `--parallel` | 62 s to about 16 s locally | Low |
| 4 | Five dead names in Python, four dead CSS classes | Smaller code | Low |
| 5 | 21 merged local branches, 20 leftover test database files | Tidy repo | None |
| 6 | Seven functions are far past the complexity limit | Easier changes | Medium: money and state logic |

## Findings

### 1. Page weight (optimize)

`templates/base.html` loads every script on every page: 45 own files and 2 vendored libraries.

| Part | Files | Raw | gzip -9 |
|---|---|---|---|
| Own scripts in `static/js/` | 45 | 341 KB | 97 KB (as one stream) |
| `vendor/turbo-8.0.23.js` | 1 | 217 KB | 46 KB |
| `vendor/motion-14.0.0.js` | 1 | 144 KB | 48 KB |
| `css/app.css` | 1 | 218 KB | 47 KB |

- The own scripts and the stylesheet are not minified. Turbo is not minified (7,298 lines). Motion is minified.
- The log-in page loads `seats.js`, `numpad.js`, `denominations.js` and 40 others that do nothing there. Each one registers with `page.js` and stops when its elements are absent, so the cost is download and parse only.
- Turbo keeps the scripts in memory between screens. The cost is paid once per tab, and again after each release (finding 2).
- The scripts use seven entry points of Motion, all through `static/js/motion.js`: `animate` and `spring`. 144 KB is large for that. Replacement with the Web Animations API and CSS `linear()` springs is possible but is a design decision with its own risk; see Open questions.

Options, smallest first:

- **A. Minified Turbo.** Replace the vendored file with the published minified build of the same version. About 217 KB to about 95 KB raw. No behaviour change.
- **B. One bundle at build time.** Join the 45 own scripts in the order of `base.html` into one file during the Vercel build, and minify it and the stylesheet. 47 requests become 4. This needs a build step. The project has none today, and "no extra package" is recorded in deployment.md. A join with no minifier needs no package.
- **C. Load by page.** Keep the shared scripts in `base.html` and move page scripts into the templates that use them. This conflicts with the rule in `base.html` ("Every page script loads once, here") and with [scripts_run_once_per_tab](../wiki/footguns/scripts_run_once_per_tab.md). Not recommended.

Not verified: that Vercel sends these files with Brotli. Two live requests did not reach the stylesheet (the log-in address in the probe was wrong), and the release rule allows no more.

### 2. Static addresses change on every release (optimize)

`config.storage.VersionedStaticStorage` appends `?v=<release>` to each own script and the stylesheet. The tag comes from the deployment, not from the file. A docs-only release changes all 46 addresses, and each phone downloads 560 KB raw again. There were about 20 pushes to `main` since 2026-11-01.

Option: tag each file by its own content (Django's `ManifestStaticFilesStorage`, or a hash of the file in `VersionedStaticStorage.url`). An unchanged file keeps its address and stays in the phone's cache for the year that `vercel.json` already allows. The current design chose a query string because the stylesheet refers to the font by a relative path; a content hash in the query string keeps that. [build_tests_see_production_settings](../wiki/footguns/build_tests_see_production_settings.md) applies: tests that compare addresses run with `VERCEL` set in the build.

### 3. Tests (optimize)

- One process: 1,775 tests, 23 skips, 62 s. All pass.
- `--parallel`: 16 s, but the run fails. `web.tests.test_concurrency.ConcurrentBuyInTests.test_buy_in_races_with_the_end_of_play` gets `OperationalError('database table is locked')` on the cloned SQLite file. The runner then stops with `TypeError: cannot pickle 'traceback' object`, which hides the cause. The 20 `test_db_N.sqlite3-wal` and `-shm` files in the repo root are from such runs.
- The time is not disk time. `PRAGMA synchronous=OFF` and an in-memory test database gave the same time for the `ledger` tests (12.8 s, 12.9 s, 12.6 s).
- Two migration tests take 11 s of the 62 s: `ledger.tests.test_migrations` (6.4 s) and `games.tests.test_nights.NightMigrationTests` (4.8 s). A third takes 0.8 s. They guard migrations that production applied in October.
- Creating the test database applies 58 migrations in about 4 s. `games` has 18, `ledger` 15, `settlement` 11.
- The Vercel build runs the suite in one process before each release.

Options:

- **A.** Make the threaded tests safe under `--parallel` (tag them and run them in a second, serial step), then use `--parallel` locally. The build can stay serial.
- **B.** Squash the migrations of `games`, `ledger` and `settlement`, and retire the three data-migration tests with them. Saves about 15 s per run and per build. A squash is a release risk: production must have applied every old migration first. It has.

### 4. Dead code (clean up)

No reference outside its own definition, except tests where stated:

| Name | Place | Note |
|---|---|---|
| `HomeCard.has_stats` | [web/home.py:77](../../web/home.py#L77) | No reference at all |
| `format_signed` | [ledger/money.py:57](../../ledger/money.py#L57) | One test only |
| `add_new_player` | [games/services.py:771](../../games/services.py#L771) | A write service used only by three test files; pages use `add_participants` |
| `.icon-bell-filled`, `.icon-bell-off`, `.stat`, `.transfer-bottom` | `static/css/app.css` | No template, script or Python builds them |

Checked and kept: `registration/login.html` (Django loads it by name); `clock.is_running`, `clock.running_participant_ids` and `CashOutLine.initial_buy_in` (kept on purpose by the earlier study); `.denomination-*`, `.k3`–`.k10`, `.is-ready`, `.is-cashed_out` and `.icon-bell` (built from a value); `.turbo-progress-bar` (Turbo adds it). All findings of the earlier study are gone.

### 5. Repository hygiene (clean up)

- All 21 local branches are merged into `main`. None is on the remote.
- 20 `test_db_N.sqlite3-wal` and `-shm` files are in the repo root. Git ignores them.
- `.impeccable/critique/` holds 14 dated critiques of screens that have since changed. They are tracked. They are frozen records of the same kind as `doc/study/`; they can stay or move there.
- `web/tests/browser/` holds 137 probe scripts. Each feature added one. They are not run by the suite or the build. No index says which still pass; the work-state notes record known failures in `fluid`, `dock` and one Chromium case.
- 20 feature switches in `config/settings.py` default to on. The human decided on 2026-10-12 that they stay. `DEBTS_VIEW` defaults to off and is on in production; its default can become on once the phone checks pass.

### 6. Complex functions (clean up)

Ruff's limit is 10 branches-and-loops per function. 20 functions outside tests are over it. The seven highest:

| Function | Place | Score |
|---|---|---|
| `home_cards` | [web/home.py:81](../../web/home.py#L81) | 23 |
| `transition` | [games/services.py:339](../../games/services.py#L339) | 21 |
| `confirm_counts` | [ledger/services.py:345](../../ledger/services.py#L345) | 17 |
| `calculate` | [games/chips.py:46](../../games/chips.py#L46) | 15 |
| `close_night` | [settlement/services.py:263](../../settlement/services.py#L263) | 15 |
| `add_participants` | [games/services.py:852](../../games/services.py#L852) | 14 |
| `session_context` | [web/views.py:277](../../web/views.py#L277) | 14 |

`games/services.py` is 1,466 lines and holds set lifecycle, participants, RSVP and seat services. `web.views.night` is 80 lines that build one context. These work and are covered by tests. A split is worth doing only before the next feature that changes them; `transition`, `confirm_counts` and `close_night` are money and state logic, so a refactor there needs `tests: first`.

### 7. Server (checked, no action)

- Query counts are fixed by tests: a set in play at most 14, a changed poll at most 13, a closed session at most 15, Your groups 11 whatever the number of groups.
- An unchanged poll is a 204. Each poll still reads the login session and the user from the database before the view runs. A cache would remove that, but the project rule forbids a cache server without a recorded requirement, and the measured cost is 2–3 ms.
- `conn_max_age` is 60. The six custom middleware classes are each used.
- Ruff style rules that remain are in tests only or are style only: `B905` (46), `B023` (26, same-pass closures), `SIM115` (13), `SIM117` (12), `UP031` (9). No action.

## Open questions for the human

1. **Page weight.** Which of 1A (minified Turbo only), 1B (one bundle at build time) or none? 1B adds the first build step to the project.
2. **Static addresses.** Do you want unchanged files to keep their address across releases (finding 2)?
3. **Motion library.** Keep Motion (144 KB), or study its replacement with the browser's own animation API? This is a design-mode task and can change how motion feels.
4. **Tests.** 3A, 3B, both or none?
5. **Dead code and branches.** May findings 4 and 5 (dead names, dead CSS, merged branches, leftover files) go in one `chore:` commit with no plan, as they fit the size gate?
6. **Browser probes.** Do you want an index of the 137 probes with a pass or fail mark, and the dead ones removed?

## Recommendation

Do 5 now as one commit. Then plan 2 and 1A together (same files, same release risk, fail-safe at build time). Then 3A. Leave 1B, 3, 3B and finding 6 until a need shows.

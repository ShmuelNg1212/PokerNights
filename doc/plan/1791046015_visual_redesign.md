# Plan: visual redesign

- **Date:** 2026-10-04 00:46 (Asia/Manila), Unix timestamp `1791046015`
- **Status:** `in-progress`
- **Study:** [../study/1791045491_visual_redesign.md](../study/1791045491_visual_redesign.md)
- **Workflow:** `agentic-workflow`. Phase 2 starts only after explicit human approval of this plan.
- **Visual direction:** **approved: A, The Rack**, with the two loans.
- **Approval record:** Human approved on 2026-10-04: "approved. continue with the plan." Defaults Q1–Q5 apply; preparation and slice 1 (tasks 1–7) are authorized.

Edit this file directly, or add a line that starts with `NOTE:`.

---

## OPEN QUESTIONS

| # | Question | Default (recommended) | Affects |
|---|---|---|---|
| **Q1** | **Which direction?** A "The Rack", B "Listahan", C "Night clock", or A with changes. See the [comparison image](../study/1791045491_visual_redesign_assets/mock/compare.png) | **A**, with the two loans in the study (ledger-style figure column, "books balance" moment) | The whole plan. B or C needs a revised system and new studies before work starts |
| **Q2** | **How much does this approval cover?** Slice 1 only (foundation, active table, buy-in), then I stop so you can use the real screens. Or all four slices in one run | **Slice 1 only.** A redesign needs your eyes on the real thing before the rest follows | Tasks 8–10 |
| Q3 | **"End play and count up" in a fixed bar at the bottom of the phone screen?** One tap ends play, as today. "Resume play" undoes it | Yes, fixed, no extra confirmation step | Task 4 |
| Q4 | **May I add two static assets?** The Archivo font file (SIL Open Font License) and about 10 Lucide icons (ISC licence) as inline SVG. Both are files in `static/` and templates. No package | Yes. If no: system font and text-only buttons, with a weaker result | Tasks 2, 3 |
| Q5 | **May I add Impeccable's project files?** `PRODUCT.md` and `DESIGN.md` at the repository root, and a small `.impeccable/` folder for the direction record. Review screenshots are gitignored | Yes. `DESIGN.md` is written at the end, from the built result | Tasks 1, 7 |

Stated for clarity:

- **Seat draw and statistics are designed, not built.** The app has no seating (Stage 4) and no statistics (Stage 3). The study holds their motion and chart rules. Each needs its own cycle.
- **"Reported" versus "confirmed" payments do not exist** in the app. A transfer is "Not paid" or "Paid, marked by the host". This plan does not add a second level.
- This work pulls the "design pass" forward from roadmap Stage 5.
- The dev server stops while templates change and starts again at the end.

---

## Goal

The app has one distinctive, tactile visual identity and a coherent motion system. A host records a rebuy faster than today. Accounting, permissions, routes and data stay as they are.

## Scope

- A design foundation: tokens, typeface, base elements, shared components, motion tokens, reduced-motion paths.
- Recomposed screens, in four slices (see Tasks).
- Presentation helpers only: a template tag for a player's token colour and initials; small JavaScript modules for the sheet, the change highlight and toasts.
- `PRODUCT.md`, `DESIGN.md`, wiki and `AGENTS.md` updates.

## Exclusions

- Seat draw, statistics, leaderboards, history screens (features do not exist).
- Any change to models, services, URLs, permissions, form field names or money formatting.
- A light theme.
- A front-end framework, a build step, a CSS or animation library, a CDN link.
- Sound.
- Stored player colours. A token colour comes from the player's join order in the set, so it can differ between sets.

## Acceptance criteria

| # | Criterion |
|---|---|
| AC1 | On a 390 px phone, the live set page with 8 players is at most 1,200 px tall (today 3,395 px). The money in play, the clock and the blinds are in the first screen |
| AC2 | The host records a default rebuy in two taps: `+` on the row, then confirm. The sheet opens with the set's default amount and shows the allowed range |
| AC3 | Success shows only after the server accepted the action: the row is highlighted and its figures are already final. No intermediate or counting amount is shown at any time |
| AC4 | A live refresh with no changed value plays no animation. A refresh with a changed value highlights only that row or total |
| AC5 | A live refresh does not close an open sheet, does not move or clear a focused field, and keeps typed values (the behaviour of the last fix stays) |
| AC6 | With "reduce motion" on, no element moves. Each state change is still visible as a static change |
| AC7 | Each action works with the keyboard. Focus is visible. A sheet takes focus when it opens, keeps it inside, closes with Escape and returns focus to its opener |
| AC8 | Text contrast is at least 4.5:1; large figures and control edges at least 3:1 (measured) |
| AC9 | Won and lost amounts carry a sign and an icon, not colour only. Each player token shows an initial |
| AC10 | "Total bought in" and "still in play" are separate, labelled figures. A set in count-up shows no result figure. Finalized results carry a "Final" tag |
| AC11 | In a chips game, no ₱ appears and amounts read as "1,600 chips" |
| AC12 | Without JavaScript, the host can still record a buy-in and a cash-out from the set page |
| AC13 | The 368 existing tests pass on SQLite and PostgreSQL. Tests that assert moved wording are updated, with no change to an accounting assertion |
| AC14 | The repository gains no package, no build step and no external request at runtime. Added CSS and JavaScript stay under 40 KB and 8 KB uncompressed; the font is one file under 150 KB |
| AC15 | At 1,280 px the set page uses two columns and shows row actions as buttons |
| AC16 | Empty, pending, validation-error, stale-connection and finalized states each match the study's specification on the screens of the slice |

Slices 2–4 add their own checks in the task list.

## Dependencies and external inputs

| Input | Purpose | State |
|---|---|---|
| Archivo variable font, with its licence file | Typeface. Must contain `₱` | To download in task 2 (Q4) |
| Lucide icon paths | About 10 inline icons | To copy in task 3 (Q4) |
| Impeccable launcher, detector and review agents | Direction record, mechanical scan, finish review, `DESIGN.md` | Installed |
| Headless Chrome | Screens, flows, reduced-motion and keyboard checks | Installed |
| PostgreSQL 17 | Second test run | Installed, started for the run |

## Branch strategy and rollback

- Branch `feat/visual-redesign` from `main`, in a separate worktree. One Conventional Commit per task. Tests pass before each commit.
- No database change. Rollback is a revert of the merge commit.
- Local merge to `main` at rendezvous. No push, no deploy.

## Tasks

### Preparation

- [ ] **1. Record the product context and the direction.** Write `PRODUCT.md` from section 10 of the study. Run Impeccable's direction roll, which needs that file. Your Q1 answer decides the direction; the roll's alternatives are recorded here with one line each on what they add. Write the direction record in `.impeccable/`. Add gitignore lines for review captures.
  - Commit: `docs: add product context and the design direction record`
  - Done when: both files exist and this plan names the direction as approved.

### Slice 1: foundation, active table, buy-in (recommended first slice)

- [ ] **2. Foundation: tokens, typeface, base elements.** New `app.css` structure: tokens, base, components. Font file in `static/fonts/`. Buttons, fields, tags, lists, tables, notices with all states. Every screen takes the new look through the shared classes.
  - Commit: `feat(web): add design tokens, typeface and base components`
  - Done when: each existing screen renders with no broken layout at 390 px and 1,280 px, and the suite passes.
- [ ] **3. Shell and motion foundations.** App bar with back link and live status. Felt field, chip token, dock, sheet (`<dialog>`), toast. Motion tokens, page transitions, reduced-motion rules. `changes.js`: the change check that drives highlights. Template tag for token colour and initials.
  - Commit: `feat(web): add app shell, sheet, toast and motion foundations`
  - Done when: unit tests cover the template tag (collision of initials, more than 10 players); the change check has a browser test for "same values, no highlight".
- [ ] **4. Active table.** Set page for setup, open and running: felt field with pot, clock, blinds and split bar; token rows; "Join this game" as a row-level action; host dock; two columns from 900 px.
  - Commit: `feat(web): recompose the active table`
  - Done when: AC1, AC10, AC11, AC15 hold in tests or browser checks.
- [ ] **5. Buy-in and player sheets.** One sheet outside the live region for buy-in or rebuy, with quick amounts. A player sheet for cash-out, details and corrections. The same forms, fields and routes. Inline fallback without JavaScript. Pending state and the confirmed highlight.
  - Commit: `feat(web): add the buy-in and player sheets`
  - Done when: AC2–AC5, AC7, AC12 hold.
- [ ] **6. Verify slice 1.** Tests on both database engines. Browser flows: host buy-in, rebuy, cash-out, reversal; player view; a second client changes data while the first types and while a sheet is open. Reduced-motion run. Keyboard run. Contrast measurement. Then the bounded visual review: screenshots at 390 px and 1,280 px together, Impeccable detector once, Impeccable finish review once, one batch of fixes, one confirmation round.
  - Commit: `test(web): cover the redesigned set page`
  - Done when: each criterion AC1–AC16 has a recorded result in this plan.
- [ ] **7. Rendezvous and docs for slice 1.** Merge to `main`. `DESIGN.md` from the built result. Update `AGENTS.md` (design rule 9, sources of truth), `doc/wiki/architecture.md` and `features.md`, a footgun page if one was found, the roadmap and `TODO.md`. Restart the server.
  - Commit: `docs: sync living documentation`
  - Done when: `main` has the work, the tests pass on `main`, and the server answers. **With the Q2 default, work stops here and I report.**

### Later slices (run only if Q2 says so, or after a later approval)

- [ ] **8. Slice 2: count-up, cash-out review, finalized set.** "Counted x of y" field, status tags, always-visible count fields in one form, "books balance" moment, review table, "Final" state.
  - Commit: `feat(web): recompose count-up and the finalized set`
  - Done when: the count-up browser check of the last cycle passes on the new markup; a set in count-up shows no result figure.
- [ ] **9. Slice 3: session page and settle-up.** "Still to pay" field with progress, transfer rows, result rows, payment records, set list, the once-only recap sheet.
  - Commit: `feat(web): recompose the session page and settle-up`
  - Done when: paid and undo flows pass; the recap opens once per session per browser and closes with one tap or key; results and payments are in separate, labelled sections.
- [ ] **10. Slice 4: group, home, sign-in, forms, log.** Sessions first on the group page; management sections; roster rows with tokens; form and error styles; log layout.
  - Commit: `feat(web): recompose the group, forms and log screens`
  - Done when: each form shows a field error with the typed value kept; the group page puts sessions in the first screen.

Each later slice ends with the same verification and doc steps as tasks 6 and 7.

## Verification

| Topic | Check |
|---|---|
| Behaviour kept | Full test suite on SQLite and PostgreSQL 17. The earlier browser scripts (units, add players, counts) rerun, with selectors updated |
| Host and player flows | Headless Chrome at 390 × 844: create or open a set, join, buy in, rebuy, cash out, reverse, as host and as player |
| Live updates | Two clients. Client B changes data while client A (a) types in a field, (b) has a sheet open, (c) is idle. Expect: no lost input, no closed sheet, one highlight in case (c), none when nothing changed |
| Motion | The same flows with `prefers-reduced-motion` emulated. A performance trace of the sheet and the highlight with 4× CPU slow-down as a stand-in for an ordinary phone; target: no long task over 50 ms from the animations |
| Layout stability | Layout-shift score of the set page during a refresh and during font load; target under 0.05 |
| Accessibility | Keyboard-only run, focus order, dialog focus handling, contrast measurement of each token pair in use, labels on icon buttons |
| Financial truth | No animated counting of amounts. Labels for bought in, in play, cashed out, result and payment checked against AC10 |
| Dependencies | `requirements.txt` unchanged. No external URL in templates or CSS |
| Visual review | One round at phone and desktop width together, one fix batch, one confirmation round. Then stop |

Not possible in this environment: a test on a physical phone. I will report it as not checked.

## Documentation sync

`PRODUCT.md`, `DESIGN.md`, `AGENTS.md`, `doc/wiki/architecture.md`, `doc/wiki/features.md`, `doc/wiki/footguns/` (if needed), `doc/roadmap/README.md`, `TODO.md`. `SPEC.md` is not edited by the AI.

## Blockers

None. If Q1 is answered B or C, I revise the design system and the studies and present the plan again before any production change.

## Progress log

| Date | Entry |
|---|---|
| 2026-10-04 | Study and plan written. Current app inspected in a browser on a temporary database. Three directions rendered as mockups. Status `awaiting-approval`. |

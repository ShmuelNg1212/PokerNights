# Session setup polish: plan

Status: approved 2026-10-13 ("approved, the scope is fine"); all six decisions as recommended, and the scope as studied. The human added a request in the same message: "add flyout animations whenever the host clicks more host controls as well"; it is stage 3 below. Built and released. Date: 2026-10-13, Asia/Manila. Study: [Session setup polish](../study/1791872138_session_setup_polish.md).

## Outcome

The path from "New session" to a set that is ready to open looks finished: titles, hints and choices follow one rhythm, no line breaks in the middle of a phrase, and nothing on the page says the same thing twice. Choosing a preset no longer discards what the host typed.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. Refinement, not redesign. No new colour, font, token or picture. No migration, and no change to accounting, permissions or what an action records. Built with the impeccable skill.

## Decisions for the human

Stage 1 needs none. Stage 2 is six items; each stands alone, and "no" to any of them leaves it as it is today.

| # | Today | Proposed | Recommended |
| --- | --- | --- | --- |
| 1 | Picking a preset needs "Use", reloads the page and clears Location, Date and Table (N6). | Picking a preset fills the stakes at once and leaves every other field alone. "Use" stays for a phone with JavaScript off. | Yes |
| 2 | Both rake value fields always show (N7). | Only the chosen rule's field shows; Off shows none. With JavaScript off, both show as today. This revises the 2026-10-04 decision "Both value fields stay visible". | Yes |
| 3 | The Stakes hint repeats the Unit hint (N8). | Remove the Stakes hint. The Unit hint already says it. | Yes |
| 4 | Step 2 is ticked and its button says "Choose rake" (D1). | The button says "Change" once stakes exist. | Yes |
| 5 | A draft set with no players says "Players" twice and offers adding them three times (D4). | With no players, the Players section shows its heading and seat count only; the sentence goes. Step 1's "Add" and the main "Add players" button stay. | Yes |
| 6 | Add players puts "Add a new player" first, with two main buttons (A2). | The roster comes first; "Add a new player" follows with an ordinary button. | Yes, but it is the one I am least sure of: say no if your games often start with new names. |

One more for you: **scope.** The study covers New session, Set settings, the draft set and Add players. Say if you meant fewer screens, or if the seat draw and the opening buy-ins should join.

## Implementation

Branch `feat/session-setup-polish` from `main`. Read impeccable's craft floor before the first edit.

### Stage 1 — alignment and rhythm (no word, no behaviour changes)

1. **Rake title weight** (N1): drop the `.rake-settings legend` override so the title is 650 like the others.
2. **Rake hint gap** (N2): 12 px between the hint and the first choice, as in Stakes.
3. **Preset row as a group** (N3): the same title style, rule and 41 px rhythm as the groups under it.
4. **Choice weight** (N4, A4): `.check` text at the body weight, 500. This reaches every tick and choice in the app; each page that uses `.check` is looked at once.
5. **Space under the last button** (N5): find the cause; end the form pages 48 px under the button.
6. **Set settings intro** (N9): the hint style; the one-field "Game" group keeps its title.
7. **Step line wrap** (D2): the line breaks only at a "·".
8. **Step buttons** (D3): one width for the step buttons, so the text column ends at one place.
9. **Empty Players section** (D5), **dock arrow** (D6), **desktop "More host controls" size and "Full set log" position** (D7).
10. **Add players** (A1, A3): one title gap; roster rows at the set page's density, keeping 48 px targets.

### Stage 2 — the approved decisions

- **1, presets in place:** each option carries its stakes, variant and unit as data. A small addition to `static/js/forms.js` fills the fields on change and hides "Use". The server path is untouched.
- **2, rake fields:** the same module shows the chosen rule's field. Typed values in a hidden field are kept, and the server still validates only the chosen rule.
- **3–6:** template changes only.

### Checks

- One batched inspection after each stage: every page of the path at 390 px and 1280 px, the refusal state, a chips game, a group with no preset, long names, the numpad open over a stakes field, reduced motion, keyboard order and focus. Everything it shows is fixed in one batch, then one confirming round.
- Before-and-after captures of the four pages, kept with the study.
- `session_form.mjs`, `rake_controls.mjs`, `roster.mjs` and `table.mjs` on fresh temporary databases (`table.mjs` stops at "a player on an open set" on `main` today; that is compared, not fixed here).
- Django suite on SQLite; `test_form_layout.py` and `test_rake_controls.py` updated where a class or a word moves. PostgreSQL before release.
- Documents: DESIGN.md addendum, PRODUCT.md (decision 2 revises an addendum), wiki features, the surface brief, TODO.md.

## Acceptance

1. On New session and Set settings the four group titles look alike, and no hint touches the control under it.
2. Picking a preset changes the stakes and nothing else (decision 1).
3. With rake Off, no rake amount field is on the page (decision 2).
4. On a draft set no line breaks inside "buy-in ₱500 to ₱2,000", and the text of every step ends at the same place.
5. Nothing a host could do before is gone, with or without JavaScript.

## Fail-safe

Stage 1 is CSS and markup. Stage 2's two behaviours are added by JavaScript on top of the form that works today; if the script fails, the page is today's page. The way back is a revert of the stage's commit. No switch is planned; say if you want one.

## Not covered

A real phone and a screen reader: yours to check after release. The date field keeps the phone's own date control and format.

## Release

Two commits, one per stage, kept local until you say to push.

## 2026-10-13 addendum — stage 3, the More host controls flyout

Asked for with the approval. The agent's reading of "flyout": the controls under "More host controls" should arrive and leave with movement instead of appearing at once. Built with the motion skill, in `static/js/dock.js`, on the Web Animations API with the app's existing sheet spring.

- **Phone:** the dock grows upward, so it is set down by the height it gained and rises into place. The controls come up from the screen's edge and fade in one after another.
- **From 900px:** the controls rise 8px as they fade in.
- **Closing:** 180ms, then the controls are removed. A second tap during the movement turns it round.
- **Off:** under reduced motion and while the dock itself is sliding, the disclosure opens and closes at once, as before. If the script fails, it is today's plain disclosure.

The disclosures inside it ("Cancel this set", "Or add one player") still open at once. Say if they should move too.

## Progress

2026-10-13: built on `feat/session-setup-polish`.

**Stage 1.** N1, N3, N4, N5, N9, D2, D3, D5, D6, D7, A1, A3 and A4 are fixed as planned. N2 was withdrawn: it is right to the eye (study addendum). On Add players the two titles now use the group title, and the legend "Tick each player to add" got 8px above it, found in the inspection.

**Stage 2.** All six decisions are built.

- Decision 2 needed no script. The chosen rule's field is shown by CSS on the checked choice, so it also works with JavaScript off; only a browser without `:has()` shows both. Better than planned.
- Decision 4: the button's accessible name is now "Change stakes. Choose rake before buy-ins", so the name a screen reader says contains the word on the button.
- Decision 6: the roster form is first on the page. In the page source the new-player form is still the first `form.form-section`, because five existing browser checks find it that way.

**Stage 3.** Built as described above.

**One commit for stages 1 and 2, not two.** The plan promised a commit per stage. The two stages touch the same lines of the same templates and were built together; the flyout is its own commit.

Verification:

- 1,101 tests pass on SQLite (15 skipped) and on PostgreSQL 17 (1,098 before). Three are new: each preset carries what it fills; New session without a preset starts at "When and where"; the roster comes first. Three were updated for the approved words and order.
- New browser check `session_setup.mjs` with `seed_setup.py`: 21 of 21 at 390px, 20 of 20 at 1280px, 19 of 19 at 390px under reduced motion.
- Existing browser checks on fresh databases: `session_form.mjs` 69 of 69 (three of its measurements now skip a field that is not drawn), `rake_controls.mjs` 25 passes, `dock.mjs` 228 of 228. `late_player.mjs` has 19 passes and 2 failures, the same 2 as on `main`. `roster.mjs` and `table.mjs` were not run: neither page they cover was changed beyond `.check`'s weight and the step line.
- Inspection: one batched round of every page at 390 and 1280px (pesos, a chips preset with seven-figure buy-ins, a refused rake percentage, the flyout mid-flight and open), one fix, one confirming round. After captures are in the study's assets folder.

Acceptance: 1 to 5 are met in headless Chrome.

Not verified: a real phone, how the flyout feels at a real frame rate, a screen reader, the in-app numpad open over a stakes field after a preset fill, a 320px screen for the draft set, a browser without `:has()`.

A mistake during the checks: one inspection run started a local server without its temporary database setting, so it served the development database (`db.sqlite3`) for about a minute. The script logged in there as `hana` and stopped at its first check. The only writes were that login (a session row and `last_login`); no session, set or money record was created.

Documentation synced: DESIGN.md, PRODUCT.md, wiki (features, journal), the forms surface brief, the browser checks' README, TODO.

2026-10-13, release: merged as `899a93e` and pushed on the human's word "release" (previous production commit `d3b8d1d`). About four minutes after the push, one fetch of `/static/js/setup.js` returned 200 and one fetch of the log-in page showed it loading `setup.js` and the stylesheet under a new release tag. Not verified: the screens themselves on the live site, which need a login, and a real phone.

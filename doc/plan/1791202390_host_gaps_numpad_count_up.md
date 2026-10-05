# Host control gaps, an in-app numpad, and the count-up to finalize flow: plan

Status: approved on 2026-10-05 with every recommendation (numpad on every number, Finalize asks once, all seven critique issues); all five stages built, verified and merged locally as `0dc4c37`; documentation synced; released as `4a80de9`; phone acceptance pending. Date: 2026-10-05, Asia/Manila. Study: [Host control gaps, an in-app numpad, and the count-up to finalize flow](../study/1791201933_host_gaps_numpad_count_up.md).

## Outcome

1. The host's buttons are evenly spaced everywhere.
2. A number is typed on a numpad that belongs to the app. The phone's keyboard no longer opens for amounts, counts or stakes.
3. Ending a set is quicker and safer: the players' count fields come first, there is one running total, the main button always does the right next thing, and the app says clearly whether the books balance before money is recorded and before a set is frozen.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new colours, fonts or imagery. No service, model or migration change.

## Decisions for the human

Approving the plan accepts the recommendations unless you say otherwise.

1. **Numpad scope: every typed number,** in this order: the buy-in, rebuy and cash-out sheets; count-up; then the stakes, rake and seats fields on New session, Set settings, presets and New table. Recommended because one way of typing numbers is the cleaner flow you asked for. The alternative is the set page only, leaving the setup forms on the phone's keyboard.
2. **Phones and tablets only.** On a computer the fields stay as they are, typed with the physical keyboard. A numpad there would be in the way.
3. **Twelve keys, always in the same places.** 1 to 9, then one key that depends on the field, 0, and delete. That one key is a decimal point where a decimal is allowed (pesos and the rake percentage) and "00" where it is not (chips, seats), so a chips game cannot be given a decimal. The alternative is a thirteenth key so pesos games get "00" as well; I recommend against it because the quick amounts already cover round buy-ins and an extra key makes every key smaller.
4. **One "Confirm counts" button instead of one per player.** Today each row's button already confirms every row, which is misleading. The single button sits with the running total.
5. **Count-up on a phone leads with the players.** The overview shrinks to the title and the progress line, the players' rows follow at once, and the running total lives in one place, the bottom bar. The second "Confirmed counts" block, the totals list and the balance check move below the rows.
6. **Finalize asks once.** "Finalize results" opens a short sheet that restates the players, the total in, the total out and "the books balance", with one button "Finalize set N". Recommended because a finalized set cannot be reopened in the app. The alternative is to keep the single tap and only move the success message out of its way.
7. **A switch to turn the numpad off.** An environment variable `NUMPAD=False`, like the one for the offline worker, returns every field to the phone's keyboard without a release. Recommended because you try changes on the live site.

## What you will see

### Stage 1: even gaps

Every two neighbouring controls in Host controls are 8px apart, on a phone and on a computer: the main buttons, "More host controls", and the options under it. A label, its field and its button inside an opened option keep their present spacing.

### Stage 2: the numpad in the buy-in and cash-out sheets

| Part | Content |
|---|---|
| Amount | The large amount at the top of the sheet, as today, with the brass caret. Tapping it no longer opens the phone's keyboard. |
| Quick amounts | Min, Default, 2 ×, Max, as today. |
| Numpad | Four rows of three keys, each at least 48px high: 1 to 9, then the decimal point (pesos) or "00" (chips), 0 and delete. Holding delete clears the amount. |
| Action | "Confirm buy-in", "Confirm rebuy" or "Cash out", as today, below the keys. |

The two help lines in the buy-in sheet become one, so the whole sheet fits a small phone without scrolling.

A key that cannot lead to a valid amount does nothing and the amount gives its short sideways nudge: a second decimal point, a third decimal place, or a digit past the largest amount the server accepts.

### Stage 3: count-up

On a phone, top to bottom:

| Part | Content |
|---|---|
| Overview | Table and set, "Counting up", and one line: "1 of 6 players counted or cashed out". Nothing else. |
| Players | One compact row each: chip, name and status on the first line with "Bought in ₱1,000" at the right; the count field on the second. A confirmed count shows in its field in the quieter colour, so the field is never empty beside "Change". The buy-in and time details move into Details. No button on the row. |
| Below the rows | The totals list, the balance check and the instructions, for reference. Rake rows are left out when rake is off. |
| Bottom bar, nothing typed | The running total in one line ("₱1,950 of ₱2,000 bought in"), the verdict under it, and the one main button. |
| Bottom bar, a field tapped | The numpad rises in the bar's place. Its top strip names the player ("Final count · Carlo") and keeps the running total and verdict, labelled "Preview" while counts are unsaved. Beside the keys: **Next**, which moves to the next player still to count and scrolls them clear, and **Done**. |

The main button follows the state, and is the only bone-coloured button on the screen:

| State | Main button |
|---|---|
| Counts typed and not confirmed | "Confirm 3 counts" |
| Counts confirmed, some players not cashed out | "Cash out counted players (3)" |
| Everyone cashed out, books balance | "Finalize results" |
| Everyone cashed out, books off | "See the ₱100 difference", which goes to the red panel |
| No buy-in recorded | No main button; the line that says why |

The verdict carries a tone and an icon: brass with a warning mark for "missing" or "extra", green with a tick for a match, plain while counting is unfinished. With an override it reads "Off by ₱100, covered by an override."

Typed counts survive a visit to the review and back.

On a computer the two columns stay. The row and main-button changes apply; the numpad does not.

### Stage 4: review, finalize and the final page

- **Review.** Directly above "Cash out N players", one plain verdict. Balanced: a green line, "After this batch the books balance." Not balanced and nobody left to count: a brass notice, "After this batch the books are ₱50 short. Recount before recording, or record and fix it after." Players still to count: "After this batch ₱1,000 is still to count." The grey "After this batch" sentence goes. The column heading becomes "Cash-out".
- **Success messages** on a set page sit above the bottom bar, never over it.
- **Finalize** opens the confirming sheet of decision 6.
- **Final results.** The overview leads with the proof for everyone: "6 players · ₱9,500 in · ₱9,500 out · the books balance", then the viewer's own result when they played. The cash-out total is labelled "Total cashed out". Rake rows show only when rake was collected. The "Live" status is not shown on a final set. An even result reads "Even".

### Stage 5: the numpad on the setup forms

On New session, Set settings, presets and New table, tapping a number field raises the same bottom numpad with the field's label in its strip, Next and Done. Text fields (names, locations, notes) keep the phone's keyboard.

### Movement

- The bottom numpad rises with the sheet's spring and leaves in 200ms. In a sheet it is simply part of the sheet.
- Keys sink 3px under the finger and spring back, like every button. A key acts as the finger goes down.
- Figures appear at their value. Nothing counts up or slides in.
- Next scrolls smoothly to the next field.
- The verdict changes tone without movement.
- Reduced motion: everything above happens at once, with no travel.

### Unchanged

Every amount, rule and permission. What counts, cash-outs and finalization record. The discrepancy panel and the override. The player's read-only view, apart from no longer showing host instructions. Everything without JavaScript: all forms work with the phone's keyboard, and "Confirm all counts" stays at the end of the list.

## Implementation

Each stage is a separate set of commits and can be released on its own.

**Stage 1**
1. `static/css/app.css`: the host controls take one gap (`--s-2`) between neighbouring controls at every width; the phone rule that zeroes form margins goes; the list under "More host controls" uses the same gap.
2. `web/tests/browser/dock.mjs`: a check that every pair of neighbouring controls is 8px apart in the draft, open, running and counting states at 320, 390 and 1280px, with "More host controls" closed and open.

**Stage 2**
3. `static/js/numpad.js`, a new module registered with `page.js`. It serves fields marked `data-numpad="pesos|chips|percent|whole"`. It writes through the field's own value and sends an `input` event, so the count preview, live updates and sheet drafts need no change. It sets `inputmode="none"` only after its keys are on the screen and only where the main pointer is a finger. It keeps the field it writes to by its `data-keep` key, so a live update does not lose it.
4. `templates/web/_buy_in_form.html`, `_cash_out_form.html`: the mark on the amount fields, the one help line, and a place for the keys. `templates/base.html`: the script tag and the `NUMPAD` switch. `config/settings.py` and the context: the switch.
5. `static/css/app.css`: the key grid, from existing button and field tokens.
6. `static/js/sheets.js`: the amount is selected on opening, so the first key replaces the default, as typing does today.

**Stage 3**
7. `templates/web/_count_up.html`, `_players_count.html`, `_count_total.html`, `_host_controls.html`, `_balance.html`, `_rake_totals.html`: the new order, the compact row, one total, the state-led main button, tones and icons on the verdict, heading levels in order, host instructions for hosts only.
8. `static/js/counts.js`: the main button's label and target while counts are typed; the "Preview" label on the bar; drafts kept in `sessionStorage` for the visit to the review.
9. `static/js/numpad.js`: the bottom panel with the strip, Next and Done. `static/js/dock.js`: while the numpad is open the dock gives way to it; the keyboard measuring stays for the text fields that still use the phone's keyboard (cancel reason, override note, reversal reason).
10. `web/views.py`: at most a few values the templates need (the count of typed-count players is client-side; the difference text for the main button comes from the existing balance). No new query.

**Stage 4**
11. `templates/ledger/cash_out_counted.html` and its view: the verdict above the button, from figures the view already computes.
12. `static/css/app.css`, `static/js/toasts.js`: messages sit above the bottom bar on set pages.
13. `templates/web/_host_controls.html`, `static/js/sheets.js`: the confirming sheet for Finalize. Without JavaScript the button submits directly, as today.
14. `templates/web/_final_set.html`, `_results.html`, `web/templatetags/money_tags.py`: the proof line, the label, the rake rows, "Even", no Live status on a final set.

**Stage 5**
15. `games/forms.py`, `templates/games/*`: the mark on the stakes, rake and seats fields; the page reserves room for the panel.

**Tests, written first in each stage**
- Django tests: the templates render the new structure in every state (awaiting, ready, cashed out, discrepancy, override, no money, chips, rake on and off), as host and as player; the review's three verdicts; the final page's proof line and labels; the `NUMPAD` switch; every existing test of amounts, permissions and query counts stays.
- New browser check `numpad.mjs` at 320, 390 and 1280px with touch emulated: the phone's keyboard is not requested (`inputmode` is `none`) only once the keys exist; every key at least 48px; keys write the expected value in pesos, chips and percentage fields; refused keys change nothing; hold-to-clear; the quick amounts and the first-key-replaces rule; Next and Done; the value survives a live update from a second host; a physical key still types; with the script blocked or the switch off the field keeps `inputmode="decimal"`; nothing shows at 1280px with a mouse; reduced motion gives no animation; a screen reader's activation (a click without a pointer event) still writes to the right field.
- New fixture `seed_count_flow.py` with **eight** players and browser check `count_flow.mjs`: at 390 × 844 at least three count rows are in the first screen with the bar folded and two with the numpad open; the first count field is in the first screen; one "Confirmed counts" region; exactly one primary button per state; the main button's five states; typed counts survive the review and back; the three review verdicts; a success message never overlaps the bottom bar; Finalize needs two deliberate taps and is cancellable; the final page's first screen holds the proof line; heading levels in order; focus order follows reading order; contrast at least 4.5:1; no horizontal overflow at 320px with the long-name fixture.
- Updated: `dock.mjs`, `flow.mjs`, `motion.mjs`, `inplace.mjs`, `lifetime.mjs`, `navigate.mjs`. `counts.mjs` and `end_set.mjs` are already stale; the parts of them this change touches are replaced by `count_flow.mjs`.

**Verify.** SQLite suite and the build-style run before each commit; PostgreSQL before a release. One round of captures at 320, 390 and 1280px, defects fixed in one batch, one confirming round. A static motion audit of `numpad.js` (transform and opacity only, nothing allocated per frame). The design skill's critique run again on the flow, to compare with 25 of 40.

**Sync docs.** DESIGN.md (numpad, count-up, review, final results, the gap rule), PRODUCT.md addendum, wiki features, the keyboard footgun (what the numpad removes and what remains), deployment page (`NUMPAD`), browser README, TODO phone checks.

## Acceptance criteria

- AC1. Every check listed under Tests passes, and all existing tests and browser checks that pass today still pass.
- AC2. With `NUMPAD=False`, or with the script blocked, every number field works with the phone's keyboard exactly as today.
- AC3. The repeat critique scores higher than 25 of 40, with no P1 issue left from the study's list.
- AC4. **On your phone, after stage 1:** no two host buttons touch, in any set state.
- AC5. **On your phone, after stages 2 and 3:** record a buy-in, a rebuy and a cash-out, then end a set and count six or more players. The phone's keyboard never opens for a number; Next takes you down the table; you can read the running total while typing. Only you can confirm this on an iPhone.
- AC6. **On your phone, after stage 4:** before recording cash-outs you can tell at a glance whether the books will balance, and you cannot finalize by accident.

## Out of scope

- Reopening a finalized set, and any change to what finalizing records.
- Cashing out and finalizing in one step. The critique raised it; it changes the accounting flow and needs its own study.
- The discrepancy panel and the override form, which the critique rated the best part of the flow.
- Reducing the 18 text sizes across the app; that is a type pass for another cycle.
- The session page's three buttons after a set is finalized.
- Sound and vibration.

## Risks

- **`inputmode="none"` on an iPhone.** It is supported from iOS 12.2, but only your phone confirms that no keyboard appears in Safari and in the installed app. The switch of decision 7 is the way back.
- **The buy-in sheet's height** on a small phone with twelve more keys. The help lines are shortened for this, and the check runs at 320 × 568.
- **The dock and the numpad share the bottom of the screen.** The count-up checks cover both, with a live update arriving while the numpad is open.

## Rollback

Each stage reverts on its own. `NUMPAD=False` turns the numpad off without a release. No migration and no data change.


## Progress, verification and rendezvous

2026-10-05: resumed at the human's request after Claude Code's session limit. All five stages were already committed on `ui/host-gaps-numpad-count-up`; wiki updates were committed as `4b814dd`. DESIGN.md, PRODUCT.md and TODO.md were unfinished documentation changes. The human approved two independent review agents for the repeat critique.

Implementation commits: `bd506a3` (gaps), `25f0e90` (sheet numpad), `b1de88c` (count-up, review and finalize), `7ca27b2` (setup forms). No service, model or migration change.

Verification on the completed implementation:

- 677 Django tests pass on SQLite in development settings and in build-style settings (`DEBUG=False`, HTTPS redirect off, a local test key); ten PostgreSQL-only skips.
- All 677 pass on an isolated local PostgreSQL 17 cluster, including the locking/concurrency tests. The existing development and production databases were not used.
- `numpad.mjs`: 87/87. Touch input, amount limits, physical keys, non-pointer activation, live updates, setup forms, reduced motion, blocked script and error recovery.
- `count_flow.mjs`: 89/89. Eight-player phone layout, button states, retained drafts, live updates, review verdicts, toast clearance, cancellable two-step finalization, final proof, chips, desktop, player view and reduced motion.
- Browser regressions: `dock.mjs` 223/223, `flow.mjs` 52/52, `motion.mjs` 34/34, `lifetime.mjs` 22/22, `navigate.mjs` 37/37 and `screens.mjs` 46/46. Each used a fresh temporary database. Temporary copies changed only the server port to 8767, preserving the pre-existing server on 8765.
- An additional browser probe with `NUMPAD=False` and with JavaScript disabled passes 7/7: native input modes, no keys, setup fields, native count confirmation and a separate finalization submit inside a disclosure. Its first draft assumed an explicit off flag; the template correctly omits the flag, and the probe was corrected.
- Static motion audit: the numpad animates `transform` for rise, leave and refusal, through the existing reduced-motion-aware wrapper. It has no frame loop and allocates nothing per animation frame. Money figures update directly.
- One initial capture round was inspected at 320, 390 and 1280px. Independent review found inaccurate help about empty saved-count fields. Corrected to distinguish an uncounted blank from a retained saved count; a confirming capture round at all three widths fits without overflow (6/6 checks). No new layout or styling.
- The action-in-place regression still selected the removed per-player Confirm button. Its selector now targets the shared `data-confirm-typed` button. The corrected check then exposed a real 34px field shift when the accepted status wrapped. `counts.js` now remembers a visible typed field on submit and restores its position after Turbo restores scroll, unless the scroll position changed while waiting. It uses an instant one-time adjustment, not an animation. `inplace.mjs` passes 38/38: the field is 324px from the top before and after, and the other form's reason and open Details survive. See the [footgun](../wiki/footguns/count_status_moves_the_field.md).

Repeat critique: [snapshot](../../.impeccable/critique/2026-10-05T13-47-15Z__templates-web-count-up-html.md), **25 → 32 of 40**, no observed P0 or P1 issue. Assessment A reviewed design without detector findings. Assessment B scanned six templates and inspected rendered pages. Its six black-text advisories are standalone-template false positives; live overlay signals did not establish new defects. No user-visible overlay is left running. Questions were skipped because this is acceptance work within the approved cycle. Remaining P2 ideas are quieter desktop reference totals, a nearby Back to counts link on review, and explanatory rejected-key feedback for assistive technology. They are follow-ups, not release blockers in this plan.

Plan deviations:

1. NUMPAD also accepts an `amount` marker on setup forms, which reads the current Unit choice, so switching pesos/chips changes the offered key without a reload.
2. Without JavaScript, Finalize uses a native disclosure with a separate submit, rather than submitting immediately. This retains the two-step safeguard.
3. Count-up Next places the active row at the top of the free space so the next player is visible. Very narrow phones can still show only one whole row with the keys open; Next remains available.
4. The review uses the number of players still to count rather than an estimated uncounted amount. It includes the accepted override and rake when calculating the post-batch verdict.

Phone acceptance remains open: AC4–AC6 require the human's iPhone, including Safari and the installed app. Automated checks cannot prove that iOS suppresses the native keyboard. `NUMPAD=False` is the fallback. SPEC.md remains human-owned.


Final confirmation, 2026-10-05: the completed tree passes 677 tests on SQLite (ten PostgreSQL-only skips), the build-style run, and all 677 on PostgreSQL 17. After the scroll fix, count-flow passes 89/89 and script lifetime passes 22/22 again. The nine selected browser suites pass 628 checks in total. The additional fallback and wording/layout probes pass 7/7 and 6/6. `git diff --check` is clean.

AC1–AC3 are met for the listed current checks; older scripts already recorded as stale remain outside this cycle. AC4–AC6 remain open for the iPhone. The coordinator completed verification and doc sync, including the original three unfinished files, the repeat critique, browser README and scroll footgun. Local rendezvous uses `main` at `f044805`, an ancestor of the tested branch. There is no migration, push or deployment in this cycle. Release requires an instruction from the human.


Local rendezvous complete, 2026-10-05: final fix/documentation commit `8d5465e`; merge to local `main` as `0dc4c37`, without conflicts. The merge tree equals the tested branch tree. Temporary verification servers and the isolated PostgreSQL cluster are stopped; the pre-existing server on 8765 was preserved. Not pushed or deployed. Phone acceptance and release remain pending.


Production release, 2026-10-05: the human instructed "push and deploy". The exact Vercel-style local run (`VERCEL=1`, versioned static assets) passed 677 tests with ten PostgreSQL-only skips. Pushed `main` at `4a80de9`. Vercel deployment `dpl_C6m2u66yzgQSSXqjCUPog5EtETXu` reached Ready and the production alias points to it. Its build passed 677 tests (ten skips), then reported no migrations to apply. Production URL: https://pokernights-five.vercel.app. The real iPhone checks remain open.

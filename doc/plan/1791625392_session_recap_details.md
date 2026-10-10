# Session recap with more detail: plan

Status: approved 2026-10-10 ("approved."); all five decisions as recommended. Built on `feat/session-recap`. Date: 2026-10-10, Asia/Manila. Study: [Session recap with more detail](../study/1791625335_session_recap_details.md).

## Outcome

When a session closes, everyone at the table opens one sheet that tells the whole night: who came out on top, how each player did, how each set went, a few facts worth saying out loud, and the viewer's own night. It looks and moves like the recap does now.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new colour, font or raster asset. No migration, and no change to accounting, permissions or what any action records. The recap only reads frozen results. Built with the design and motion skills.

## What you will see

The same bottom sheet, opened once by itself and afterwards from "View session recap". It now scrolls, and its heading and Close button stay at the top while it does.

### 1. The night at a glance

- **Top session result**, as today: every player tied at the highest result, each with their chip, name and figure. "Everyone broke even." and "No positive result after rake." stay.
- Six small facts in a two-column grid, in the style of the Stats tiles: **Players**, **Sets**, **Play time**, **Total bought in**, **Buy-ins** (how many), and **Rake collected** when there is any. Play time keeps "Not recorded" and "partial".

### 2. Your night

Only for a viewer who played.

- Your result, large, with its sign and arrow.
- One line: "₱3,000 bought in · ₱4,500 cashed out · 3 buy-ins · 2h 10m at the table".
- Your result in each set you played: "Set 1 +₱2,000 · Set 2 −₱500".
- What you pay or receive, with Paid or Not paid, as on the page.

### 3. Everyone's results

Every player, best result first, losses included.

- Each row: place, chip, name, and a muted line "₱3,000 in · ₱4,500 out · 3 buy-ins · 2h 10m". The result is at the right with its sign and arrow.
- Under each row a thin bar shows the size of the result against the largest of the night: green for a win, red with a hatch for a loss, as in Stats.
- Players with the same result share a place. Your own row is marked "(you)".

### 4. Highlights

Up to three, each left out when it has nothing to say. No highlight names a loss.

| Highlight | Says | Left out when |
|---|---|---|
| Most buy-ins | "Ben · 4 buy-ins" | Every player bought in the same number of times |
| Biggest win in one set | "Hana · +₱2,400 in set 2" | The session had one set, or no set had a winner |
| Longest at the table | "Carlo · 3h 05m" | Fewer than two players have a recorded time, or all are equal |

Ties name everyone tied.

### 5. Set by set

One row per finalized set: "Set 2", then "6 players · ₱18,000 bought in · 1h 20m", then who came out on top in it. The set's name links to the set. Canceled sets are not listed, as today.

### Movement

| Moment | Movement |
|---|---|
| The sheet opens | It rises as now. The sections are uncovered top to bottom, 60ms apart, all in place within 600ms |
| Everyone's results comes into view | The bars grow from the middle line, 12ms apart, once per opening |
| Close, Escape, tap outside | As now |

Money appears at its value on the first frame and never counts. Reduced motion shows everything in place at once. Without JavaScript the recap is on the page as plain sections, with no movement.

## Decisions for you

Approving accepts the recommendations unless you say otherwise.

1. **Order of the sections:** glance, your night, everyone, highlights, set by set. Your own night comes before the full list because it is what each person looks for first. Recommended: this order.
2. **"Most buy-ins" stays a highlight.** It names who rebought most, which is often a player who lost. You chose not to call out losses; this is a fact about play, not a result. Recommended: keep it. Say if you would rather drop it.
3. **No percentages.** No return on buy-in and no share of the pot. The recap has never shown one, and Stats is where rates live. Recommended: none.
4. **No switch for this release.** The set page revamp had one because it is used during a game. The recap only reads results of a session that is already closed, and reverting the commits removes it. Recommended: no switch.
5. **Past sessions get the new recap** when someone opens it from the button. It does not open by itself again for a viewer who has already seen that session's recap. Recommended: yes.

## Implementation

Branch `feat/session-recap` from `main`, two commits. Not merged and not pushed without your word. Each stage ends with both test suites passing.

**Stage 1: the facts.**

1. Tests first, in `settlement/tests/test_recap.py` and `web/tests/test_night_design.py`:
   - totals over several sets; a canceled set counted nowhere;
   - a player in only some sets; a host who did not play has no "Your night";
   - ranking with ties sharing a place; losses listed; nobody named as a loser in highlights;
   - each highlight's rule, its ties and each case where it is left out; no highlights at all;
   - time: none recorded, some recorded, all recorded;
   - rake; a host override in "cashed out"; a chips game with no peso sign and no percent sign;
   - a corrected finalization uses the current rows only;
   - the session page adds no query (the limit of 14 stays).
2. `settlement/services.py`: `result_rows` reads the other frozen fields in its one query; `session_standings` and `settlement_balances` take what they took before.
3. `settlement/queries.py`: `night_recap` returns a read-only `Recap` with its parts (glance, viewer, ranking, highlights, sets). Existing keys the template and tests use keep their meaning.
4. `templates/web/_night_recap.html`, included by `night.html` in place of the five lines, as plain sections with headings. Existing copy stays word for word where a fact stays.

**Stage 2: the look and the movement.**

1. CSS in `app.css`, inside the recap's own classes: the fact grid, the viewer block, ranked rows with bars, highlight rows, set rows, the head that stays in place, and the section stagger by a per-section index in place of the per-line rules.
2. `sheets.js`: grow the bars when the list comes into view, once per opening. Nothing else changes in how sheets open, close, trap focus or return it.
3. Browser check, `night.mjs` extended, at 320 × 568, 390 × 844 and 1280 × 800:
   - every section present for the fixtures, and absent where its rule says so;
   - Close visible after scrolling to the end; focus trapped and returned; Escape and outside tap;
   - no horizontal overflow with a long name, a large peso amount and a large chips amount; each figure whole on one line;
   - text contrast at least 4.5:1; links at least 48px;
   - figures at their value on the first frame; the reveal done within 600ms; bars once per opening; nothing running and no inline style at rest; reduced motion; Motion blocked;
   - opens once by itself, not after Mark paid or Undo; storage refused; no JavaScript.
4. One `/impeccable critique` of the recap, and one fix batch from it.
5. Sync docs: DESIGN.md (an addendum; the superseded lines of "Closing recap" named), PRODUCT.md, wiki features and architecture, the session surface note, the browser README, and TODO with the phone checklist.

## Acceptance criteria

- AC1. A closed session's recap shows the five sections above, each with the facts listed, for the viewer's role.
- AC2. Every figure equals the sum of the frozen current results it describes; canceled sets and superseded finalizations count nowhere.
- AC3. Losses appear in Everyone's results and in Your night, and in no highlight.
- AC4. A highlight or section with nothing to say is absent, not empty.
- AC5. Missing play time reads "Not recorded" or "partial"; it is never shown as zero.
- AC6. On a 390 × 844 phone the sheet opens on the glance and the start of Your night, scrolls to the end, and Close is reachable at every scroll position.
- AC7. The opening reveal completes within 600ms; no figure shows an intermediate value; reduced motion moves nothing.
- AC8. Without JavaScript the whole recap is readable on the page and every form still works.
- AC9. No query is added to the session page; no model, service write or migration changes.
- AC10. Both suites pass; `night.mjs` passes.

## Out of scope

- Sharing the recap outside the app, a link of its own, or an image of it.
- Hand-level facts, percentages and rates, comparisons with earlier sessions.
- The rest of the session page, settle-up, set pages and Stats.
- A recap for an open or an archived session.

## Rollback

Revert the feature commits. No migration and no stored state besides the existing once-per-browser key.

## Cannot be verified from here

On a physical phone: the sheet scrolling under a thumb, the heading staying put on iPhone Safari and in the installed app, and whether the reveal feels brisk. These go on your phone checklist.

## Progress and blockers

2026-10-10: Study and plan written after three questions to the human. Waiting for approval.

2026-10-10: approved ("approved."), all five decisions as recommended. The design skill (impeccable) and the motion skill were loaded for stage 2.

2026-10-10: built on `feat/session-recap`, not merged and not pushed.

- **Stage 1** committed as `ebf7328`. **Stage 2** and the docs follow in the next commit.
- 950 tests pass on SQLite and on PostgreSQL. `night.mjs` passes 68 of 68 on a fresh seed (53 before).
- No query added: `result_rows` returns named rows with the extra frozen fields, kept on `NightOutcome.results`. The session page's limit of 14 holds.
- Measured at 390 × 844 as a player in a two-set session: the sheet is 717px tall and its content 1,743px; it opens on the top result, the facts and Your night.

Differences from the plan as written:

1. **Bars are 40ms apart, not 12ms.** With three to nine rows, 12ms cannot be seen as a sequence. Each bar takes 420ms.
2. **The fact labelled "Sets" reads "Finalized sets"**, since canceled sets are not counted. "Total bought in" carries "Across finalized sets" as its note instead of in its label.
3. **Total bought in and Rake each take a full row**, so a nine-digit amount stays on one line at 320px.
4. **The viewer's set-by-set results appear only with more than one set.** With one set they would repeat the result above them.
5. **A set where nobody won reads "Nobody finished ahead."**
6. **No separate `/impeccable critique` run.** The captures at 320, 390 and 1280px were reviewed in one round and one batch of four fixes was made from them. A formal critique can still be run on request.
7. **A browser fixture was added**: `two-sets` in `seed_night.py`. One existing check now ignores links that are not displayed, because the recap's set links are hidden while its sheet is closed.

Not checked from here: the sheet under a thumb on an iPhone, the sticky head in iPhone Safari and the installed app. Both are on the phone checklist in TODO.md.

2026-10-10: the human said "push". Merged to `main` and pushed as `0c736fb` (previous production commit `e812dfc`). Vercel reported the deployment complete; the live stylesheet and `sheets.js` carry the recap's changes and the login page answers 200. The recap was not opened on the live site from here; that is the phone checklist in TODO.md.

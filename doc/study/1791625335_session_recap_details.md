# Session recap with more detail: study

Date: 2026-10-10, Asia/Manila. Request: "i want the session recap to display more details about the session keep the nice UI design and animations."

No capture was taken for this study. The recap was read from its template, styles, script and tests; the baseline tests (`web.tests.test_night_design`, `web.tests.test_query_counts`, 13 tests) pass on SQLite.

## What the human chose (2026-10-10)

1. **Details to add:** all four offered: everyone's results, set by set, highlights, and your night.
2. **Losses:** shown in the ranked list like any result. No highlight names a biggest loser.
3. **Form:** the same bottom sheet, scrolling, with its staggered reveal.

## Scope

The closing recap of a closed session: the sheet opened from `templates/web/night.html`, its inline form without JavaScript, the query behind it (`settlement.queries.night_recap`) and its styles and movement. The rest of the session page, settle-up, the set pages and Stats are not part of this.

## What is there today

The recap is a bottom sheet on a closed, unarchived session. It opens by itself once per session, signed-in viewer and browser (`rack-recap:<night>:<user>` in localStorage) and again from "View session recap". Without JavaScript the same facts sit inline at the foot of the page.

It shows at most five lines, each a small label over a 22px value:

| Line | Source |
|---|---|
| Recorded play time | Sum of the timers of the finalized sets; "Not recorded" or "partial" where timers are missing |
| Total bought in across finalized sets | Sum of `Finalization.total_buy_in` |
| Rake already collected | Sum of `Finalization.total_rake`; only when above zero |
| Top session result | Every player tied at the highest positive result; otherwise "Everyone broke even." or "No positive result after rake." |
| Your session result | The viewer's result; only when they played |

Movement: the sheet rises with the `sheet` spring; each line is uncovered top to bottom over 360ms, 60ms apart. The delays are written for lines two to four only, so a fifth line (present whenever there is rake) starts with the first. Reduced motion shows everything at once. Money never counts.

Geometry: `.sheet` is 440px wide at most and 85dvh tall at most, and the whole sheet scrolls, its heading and Close button included. Five lines never needed scrolling, so this has not mattered.

## What is recorded and not shown

Every finalized set freezes one `PlayerResult` per player. Of its fields the session page uses only the result, the time and the rake:

| Field | Meaning | Shown on the session page today |
|---|---|---|
| `buy_in_total` | What the player bought in for in that set | No |
| `buy_in_count` | How many buy-ins | No |
| `cash_out` | Cash-outs plus any share of a host override | No |
| `net` | `cash_out − buy_in_total`, after rake | Yes, summed |
| `play_seconds` | Time at the table; empty for old sets | Yes, summed |
| `rake_total` | Rake taken from the player's buy-ins | Only for the viewer |

Each set also freezes `Finalization.total_buy_in`, `total_rake` and `total_cash_out`, and the view already loads every set's number and timer. The settle-up plan and its paid marks are loaded for the page.

So all four chosen sections can be drawn from frozen rows the app already has. Nothing new needs recording, and no model, service or migration is involved.

Group members already see each player's bought-in and cashed-out figures on a set's final results (`_results.html`), so listing them in the recap shows nobody anything new.

## Findings that shape the plan

1. **One read can feed everything.** `settlement.services.result_rows(night)` reads four fields of the session's current results in one query, for the standings and the settle-up balances. Reading the other frozen fields in that same query gives the recap its data with no query added. The session page's query-count test allows 14.
2. **The recap is a dict built in `night_recap`.** Four sections with rules of their own (ties, missing time, a single set) are better as a small read-only object with named parts, tested on its own.
3. **The reveal does not scale.** The stagger is written per line number. More content needs a stagger per section, with the total kept under the 900ms the motion rules allow a once-only moment.
4. **The sheet's head scrolls away.** With a long recap, Close must stay in reach, so the head has to stay at the top of the sheet while its body scrolls.
5. **A chart vocabulary exists.** Stats draws a result as a thin bar from a baseline: Up in green, Down in red with a hatch, growing from the baseline 12ms apart. Using it for the ranked list gives the recap a second movement without animating any figure.
6. **No percentages.** The recap has never shown one, and a test says so for chips games (`test_chips_break_even_recap_has_no_percentage_or_peso`). The plan adds none.
7. **Highlights need rules for when to stay silent.** "Most buy-ins" says nothing if everyone bought in once. "Biggest win in one set" repeats the top result when there was one set. "Longest at the table" needs recorded time from at least two players. A highlight that has nothing to say is left out, and with none left the section is left out.
8. **Old sessions.** Sets finalized before playing time was recorded have no `play_seconds`. Each time fact needs the same honesty as today's "Not recorded" and "partial".
9. **The inline form gets long.** Without JavaScript the whole recap is on the page under Payment records. It repeats part of Session results. This is the fallback only, and it stays readable as plain sections.
10. **Who has seen it.** A viewer who already opened the recap of a past session will not have it open by itself again; the button opens the new one. This matches the once-per-browser rule and needs no change.

## Not verifiable from here

How the longer sheet scrolls under a thumb on an iPhone, and whether the staggered reveal still feels brisk on a real phone. Both go on the phone checklist.

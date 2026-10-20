# End of set: fewer words and a clear next step: study

Date: 2026-10-20, Asia/Manila. Mode: design. Shaped with `/impeccable shape`.

## Why

The human reports two problems after counts are typed and the books balance:

1. The screens use too many words.
2. The choice between the next set and settle-up is not clear.

## Who arrives

The host. It is late. One hand is free. The host has just counted the stacks and wants to know two things: did the books balance, and what now. Players open the same pages to read their result.

Visitor mode: Operate. The visual authority is the built Rack in DESIGN.md. No new colour, font, raster asset or motion preset.

## Evidence

Captures at 390 × 844, host `hana`, synthetic fixture (`seed.py`, `seed_end_set.py`, `seed_night.py`). Files: `/private/tmp/claude-501/-Users-shm-PokerNights/87b8d1ea-c3a8-4a86-81e2-d3741007c998/scratchpad/before/`.

| Screen | Template | What is wrong |
|---|---|---|
| Cash-out review | `templates/ledger/cash_out_counted.html` | Four totals in the panel. Three explanation paragraphs and a table caption. "Still to count 0" and "Nobody…" show when nobody is left. |
| Balanced count-up | `_books.html`, `_host_controls.html`, `_count_total.html` | "The books balance" is said three times: the books panel, the dock ("All counts match buy-ins") and the hint under the button ("Every player is cashed out. Finalizing freezes…"). |
| Finalize sheet | `_host_controls.html` | Facts, verdict, then a sentence on freezing and reopening. Acceptable; small cuts only. |
| Final set page | `_final_set.html`, `_results.html` | The proof line says in and out, then the totals list says them again. "The set is finalized. Results are frozen. Settle up at the end of the session." Then "Payment: at the end of the session…". Then **Next set or settle up**, which only opens another page. Each result row has three fact lines. The toast covers the first result. |
| Session page, open | `night.html` | **The main cause.** Three full-width buttons: **Open set 1** in the primary style although set 1 is final, **Start next set** in the secondary style, and **Close session and settle up** in the primary style. Each has its own paragraph. "Session open" has a hint. "Collected rake across sets ₱0" shows when there is no rake. "Results so far" has two explanation lines. |

Why the choice is unclear: the host taps "Next set or settle up" and lands on a page where the two answers are not side by side. They have different weights, they are 500 px apart, and a third primary button ("Open set 1") is first.

## The human's answers (2026-10-20)

1. **The choice lives on the final set page.** Right after finalizing, the host sees two equal choices: play the next set, or settle up. No page in between.
2. **Cut hard.** Each fact is said once. A button names its result, so it needs no paragraph. An explanation goes, or moves into a closed disclosure.

## What the code already has

- `games.views.next_set` (POST `next_set`) calls `services.start_next_set`. It is allowed when no set of the session is in play. It opens the new set and redirects to it. Repeated taps are stopped by `data-once`.
- `settlement.views.close_night` (POST `night_close`) closes the session with the ticked `carry` transfers and redirects to the session page, which then shows who pays whom.
- `web/views.py` `night` computes `can_start_next_set`, `can_close`, `unfinished_sets` and `carryable`. The final set page computes none of them. It has `later_set`, `can_reopen` and `night`.
- The finalize confirmation is a sheet (`data-sheet-open`, `details.sheet-source`) with a native `details` fallback. Settle-up can use the same pattern, so the carry list and the confirmation stay one tap away on the final page.
- Motion presets in DESIGN.md: `press`, `release`, `sheet`, `arrive`, `leave`, `nudge`, `pulse`. The books-balanced rule plays once per set per browser through `localStorage`. The same rule suits a one-time arrival of the choice.

## Brief

**Job.** After the books balance, tell the host the set is done and offer the two next steps as equals. Tell a player their result and where payment happens, in one line.

**Direction.** Inside the Rack. Restraint: remove text, never add decoration. The focal moment is the choice: two equal cards side by side under the final proof.

**The choice ("What next?").**

- Two cards of equal size and weight, in one row at 390 px and in the 400 px column on desktop. Each is a full button with a 48 px minimum target, a bone title and one muted line.
- **Play set N** · "Same players, new buy-ins." A native POST to `next_set`. No confirmation: a new open set is cheap to cancel.
- **Settle up** · "End the session. See who pays whom." Opens a sheet: "Close the session?", the number of finalized sets, the carry list when there is one, the primary **Close session and settle up**, and a quiet **Not yet**. Without JavaScript, a `details` element holds the same form.
- Hosts only, and only while the session is open and no later set exists. A card whose action the server would refuse is not shown; when settle-up is blocked by another unfinished set, its card is disabled and names the set in one line.
- The same partial serves the session page, so both pages show the same choice.

**Cuts, by screen.**

- **Review.** The panel shows "After this batch" against "Bought in" and the verdict. The three paragraphs go. The caption becomes visually hidden. "Still to count" shows only when somebody is left.
- **Balanced count-up.** The books panel says "The books balance." once. The dock keeps its count line. The hint under **Finalize results** goes while the books balance.
- **Finalize sheet.** One consequence line: "Results freeze. A host can reopen the set."
- **Final page, hero.** Title, Final badge, date and play-ended line with the set time, the proof line ("2 players · ₱2,000 in · ₱2,000 out") and the verdict. The totals list goes because the proof line has the same figures. The frozen sentence and the "Payment:" paragraph go.
- **Final page, result rows.** One muted line under each name: "₱1,000 in (1) · ₱1,000 out · 1 h 20 min", with rake and override added when present. Details stays.
- **Final page, player.** One line: "Who pays whom comes when the host settles up." and a quiet link to the session.
- **Reopen.** "Found a mistake?" and **Reopen set** stay last, with a shorter line.
- **Session page, open.** **Open set N** is shown only while that set is not finished. "Session open" and its hint go. The ₱0 rake row goes. The choice cards replace "Start next set" and the settle-up section. "Results so far" gets a "Not final" badge and loses its two lines.
- **Toast.** "Set 1 is final." The page change and the Final badge carry the rest.

**Motion.** One moment, once per set per browser, on the final page: the two cards rise 8 px and fade in with the `arrive` spring, 60 ms apart, after the page change. Cards press with the existing `press` and `release`. The settle-up sheet uses the existing `sheet` motion. Money does not animate. Reduced motion shows the cards at once.

**States and ranges.** Pesos and chips. Rake and no rake. Override. One to ten players, long names, 13-character amounts. A later set exists. Session closed. Settle-up blocked by another unfinished set. Player viewer. Desktop from 900 px.

**Boundaries.** No model, service, permission or URL change. What finalize, next set and close record is unchanged. Count-up entry, the books-off state and the closed-session settle-up keep their layout. Wording follows ASD-STE100 and Brand Commitments (plain, exact about money).

**Anti-goals.** No explanations moved into tooltips. No default between the two choices. No new colour for either card.

# End of set: fewer words and a clear next step: plan

Status: approved 2026-10-20 ("approved"); the three open questions as recommended. Date: 2026-10-20, Asia/Manila. Study: [End of set: fewer words and a clear next step](../study/1792508023_end_of_set_words_and_next_step.md).

Mode: design. Visual authority: the built Rack in DESIGN.md. No new colour, font, asset, token or motion preset. No migration. No model, service, permission or URL change.

## OPEN QUESTIONS

Approving accepts each recommendation.

1. **Play the next set without a confirmation.** Recommended: yes. One tap opens set N+1 and goes to it. A host who tapped by mistake cancels the empty set from More host controls.
2. **The "does not finalize and marks no payment" line on the review page.** Recommended: remove it. The button says "Cash out 2 players", and the next screen asks before it finalizes.
3. **The toast after finalizing.** Recommended: keep it, shortened to "Set 1 is final." It confirms the tap. Say if you want no toast.

## Outcome

After the books balance, the host reads each fact once. On the final set page, two equal cards ask what next: **Play set 2** or **Settle up**. The session page shows the same two cards and no misleading button. A player reads their result and one line on payment.

## What you will see

**Cash-out review**
- Panel: "After this batch ₱2,000 of ₱2,000 bought in" and the verdict.
- The table of players and amounts, then **Cash out 2 players**.
- "Still to count" only when somebody is left. "Already cashed out" when somebody is.

**Balanced count-up**
- The books: the figures, then "The books balance." once.
- The dock: the count line, then **Finalize results**. No hint under it.
- The sheet: facts, verdict, "Results freeze. A host can reopen the set.", **Finalize set 1**, **Not yet**.

**Final set page, host, session open**
- "Balanced books · Set 1", Final. "Fri, Oct 9 · Play ended 10:49 PM · 1 h 20 min".
- "2 players · ₱2,000 in · ₱2,000 out", "✓ The books balance."
- Your result, when the host played.
- "What next?" and two equal cards: **Play set 2** "Same players, new buy-ins." · **Settle up** "End the session. See who pays whom."
- Results: each row is the name, the signed result, and one line "₱1,000 in · ₱1,000 out · 1 h 20 min". A rebuy adds ", 1 rebuy" after the amount in.
- "Found a mistake?" and **Reopen set**, last.

**Final set page, player**
- The same hero and results. Under the hero: "Who pays whom comes when the host settles up." and a quiet "Go to the session".

**Session page, open**
- **Open set N** only while that set is not finished.
- The two cards, as on the final page.
- "Results so far" with a "Not final" badge.

## Tasks

### 1. The choice partial and its context
- [x] Add `templates/web/_next_step.html`: "What next?", two cards, the settle-up sheet with the carry list, and a native `details` fallback.
- [x] Move the next-step context (`can_start_next_set`, `can_close`, `unfinished_sets`, `carryable`, the next set number, the finalized-set count) into one read-only helper in `web/views.py`. The night view and the final set view both call it.
- [x] Cards share `.btn` so `press` and `release` apply. Two equal columns; 48 px minimum; title in Bone, line in Bone Dim.
- [x] Settle-up blocked by another unfinished set: the card is disabled and says "Finish set 3 first."
- Acceptance: on a final set with an open session and no later set, a host sees both cards. A player sees neither. With a later set, the cards are absent and "Go to set N" stays. With a closed session, "See who pays whom" stays.
- Done when: view tests cover host, player, later set, closed session and blocked settle-up, and both POSTs work from the final page.

### 2. Final set page
- [x] Hero: remove the totals list, the frozen sentence and the rake note; add the set time to the date line.
- [x] Replace the "Payment:" paragraph and **Next set or settle up** with `_next_step.html` for a host, and one line plus a quiet link for a player.
- [x] Result rows: replace the facts list with one muted line. Keep rake and override on that line when present. Omit time when it is not recorded.
- [x] Reopen: shorten the line to "Correct a count, cash-out or buy-in."
- [x] Toast: "Set N is final.".
- Acceptance: at 390 × 844 the host's first screen shows the proof line and both cards without scrolling for a two-player set.
- Done when: tests pass and the 390 and 1280 px captures match "What you will see".

### 3. Session page, open
- [x] Show **Open set N** only while that set is not finalized or canceled.
- [x] Remove "Session open", its hint, and the rake row when the total is 0.
- [x] Replace "Start next set" and the settle-up section with `_next_step.html`.
- [x] "Results so far": a "Not final" badge; remove the two explanation lines and "Over N finalized sets."
- [x] Sets: remove "Each set has its own timer."
- Acceptance: the open session page has at most one primary-style button on the first screen.
- Done when: tests pass and the capture shows one choice.

### 4. Cash-out review
- [x] Panel: "After this batch" against "Bought in", and the verdict. Remove "Total of this batch" and "Recorded cash-outs" from the panel; the table footer keeps the batch total.
- [x] Remove the three explanation paragraphs; make the caption visually hidden.
- [x] "Still to count" only when somebody is left.
- Done when: tests pass and the 390 px capture fits the table and the button on the first screen for two players.

### 5. Balanced count-up and finalize sheet
- [x] Books panel: "The books balance." only.
- [x] Dock: no hint while the books balance.
- [x] Finalize sheet: one consequence line.
- Done when: tests pass; the books-off and override states are unchanged.

### 6. Motion
- [x] The two cards arrive once per set per browser on the final page: 8 px rise and fade with `arrive`, 60 ms apart. Key in `localStorage`, read in `try`.
- [x] Reduced motion, a blocked Motion file and a reload show the cards at once.
- Done when: `review-animations` finds nothing material and a browser check confirms once-only and reduced motion.
- Result: 12 browser checks pass at 390 px, three runs in a row. The rise is two animations, `opacity` and `y`, so a press during the rise takes over `y` and nothing is left inline. Finalizing redraws the set in place, so the module also runs on `live:updated`. `review-animations` is not installed here; the Motion skill's best practices and DESIGN.md's motion principles were the review.

### 7. Rendezvous
- [x] Full SQLite and PostgreSQL suites: 1,328 tests pass on both (15 PostgreSQL-only skips on SQLite).
- [x] Browser check at 390 and 1280 px, and 320 px for the worst case: host and player, pesos, rake, override, nine players with long and accented names, ₱999,999 buy-in, rebuys, later set, closed session, blocked settle-up, no JavaScript. No horizontal overflow. Contrast: card title 12.46:1, card line 6.6:1, result line 8.28:1, proof 14.31:1.
- [x] `/impeccable critique` (single context, see the snapshot `.impeccable/critique/2026-10-20T15-12-53Z__templates-web-final-set-html.md`): 32/40. Fixed: Reopen set competed with the choice on a phone; it now follows the results below 900 px. Detector: 8 advisories, all false positives (bare templates without the stylesheet). `audit` was covered by the same detector run and the contrast and target checks above; `polish` items are in commit `6e2f4e9`.
- [x] `break-ui` with a worst-case set in the fixture database. Fixed: stacked cards at 320 px kept an empty band; a figure split from its word in the proof line and the result rows. Not changed (older behaviour): the session page's results stack token, name and amount at 320 px; initials such as "BI" and "MÁ"; the finalize toast covers a result row for six seconds.
- [x] `code-review` (medium): 10 findings. Fixed: the final page's poll missed other sets and the session closing; the open session page had no sheet mount, so Settle up opened inline and a redraw could reset carry ticks; Open set N disappeared when an earlier set was unfinished; a draft read "Finish set N first"; the arrival's once could be spent with no card drawn. Kept: no `request_id` on next set and close (as before; both services refuse a repeat by state); about three queries more for a host on a final page; `display: contents` on the aside (as the count-up layout); the review page's removed totals (approved in task 4).
- [x] `security-review` not run: no permission, money or user-data rule changed. Both POSTs keep their service checks.
- Done when: each check is recorded in this plan. Frozen 2026-10-20.

### 8. Sync docs
- [ ] DESIGN.md addendum (impeccable `document`), surface brief addendum for `templates-web-end-set`, features.md, spec.md behaviour facts, TODO.md phone checks.
- Done when: no stale text remains about "Next set or settle up", the "Payment:" line or "Start next set".

## Risks

- Many tests assert today's wording. Update each one to the new wording; do not delete a test.
- The final page now renders the carry list. It is a read query on the same rows the session page reads.

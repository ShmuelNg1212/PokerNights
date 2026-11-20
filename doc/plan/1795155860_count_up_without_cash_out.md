# Plan: count-up without a cash-out step

Study: [1795155860_count_up_without_cash_out.md](../study/1795155860_count_up_without_cash_out.md). Mode: mixed.
Skills: `tdd` (tasks 1–2), `/impeccable polish` and `animate` (tasks 3–4), `code-review`, `break-ui`, `review-animations` (rendezvous).

Outcome: on count-up the host types counts and confirms them. Nothing else. One finishing action records the cash-outs and freezes the results.

## OPEN QUESTIONS

Approved 2026-11-20: all four as proposed.

1. **Books off.** When every count is confirmed and the counts do not balance, the host now sees **Find the ₱X difference** straight away, from the counts. No cash-out first. Proposed: yes.
2. **Override.** **Finalize with an override** becomes available as soon as every count is confirmed and the counts are off. One action records the cash-outs, the override and the results, or nothing. Proposed: yes. This changes a settlement rule, so it gets an ADR.
3. **Players who cashed out during play** (left early). Their row keeps "Cashed out ₱X" and a full pip. They need no count. Proposed: keep.
4. **Old link** `/…/cash-out-counted/`. Proposed: it becomes the finish review only (no partial batch). A GET when the set cannot finish redirects to the set page.

## Tasks

- [x] **1. Finish from confirmed counts, with or without an override.** `tests: first`
  - `finish_set` accepts an optional override (note, mode, absorber). In one transaction: batch cash-out of the reviewed counts, then `record_override` when given, then `finalize`. Any refusal records nothing.
  - `finishes_the_set` is true when every player with money has a confirmed count or a cash-out, whatever the difference. The review page shows the verdict: balanced, or off by ₱X with the override form.
  - `ledger.services.cash_out_counted` stays as an internal step of `finish_set`. The view no longer posts a partial batch.
  - Done when: tests show a balanced finish, an override finish, a stale-count refusal and a repeated tap, each with the exact rows written or none.
- [x] **2. Books-off from counts.** `tests: first`
  - The count-up books and the dock read `count_total` (confirmed counts plus earlier cash-outs) for the gap. **Find the difference** appears when every count is in and they are off.
  - Rows show in / counted / net and the suspect mark from counts, as the cashed-out rows do now.
  - Done when: a set with all counts confirmed and off by ₱500 shows the gap action and the override, with no cash-out row in the database.
- [x] **3. Count-up words and dock.** `tests: alongside`
  - Status `ready` reads "Counted", not "Ready to cash out". Progress reads "N of M players counted".
  - Remove **Cash out counted players (N)**. The dock action after confirming is **Review and finish** (balanced) or **Find the ₱X difference** (off).
  - The review page title is "Finish set N" in every case. Remove the "Cash out N players" button and "After this batch" wording.
  - Done when: no count-up screen, page or message says "cash out" except a row for a player who cashed out during play.
- [x] **4. Pips and motion.** `tests: alongside`
  - A confirmed count fills its pip fully (bone). A cash-out during play stays full green. Drop the half-filled state.
  - `pip-fill` and the row tick run on confirm. No second fill step. Reduced motion: none.
  - Done when: a browser probe confirms two counts and sees two full pips animate once; under reduced motion it sees no animation.
- [x] **5. Records.** ADR for question 2. Update spec.md and features.md in sync docs. Phone check in TODO.md.

## Completion

All tasks ticked. SQLite and PostgreSQL suites pass. Count-flow browser probe passes on a balanced set and an off set. Verified branch `feat/count-up-no-cash-out`, not pushed.

## Checks

Rendezvous, 2026-11-20, branch `feat/count-up-no-cash-out`:

- SQLite suite: 1858 tests OK (23 skipped). New `tests: first` cases fail on the old code: an override finish, an override replacing an older one, counts-off text in the books, a GET-only review.
- `code-review` (medium): 3 important and 4 nits. All 7 fixed in the `fix:` commit: the books stated "Finish the set" when the counts were off; Find the difference had no `#books-gap`; an override finish stacked on an older override; a silent redirect; POST to the review; a second copy of the count-up cash-out form; the missing ADR (0016).
- `count_flow.mjs` on a fresh database and a restarted server: 106/108. The two failures (48px panel keys, 320 × 568) are known on main. Three old expectations were updated for the digit grouping released in e553235 ("2,000", "1,500"). New checks: full marks, no cash-out button, counts off leads to the gap and the override finish, Review and finish rises once and rests with no inline style, a later visit is still, review rows 40 ms apart, reduced motion still, Finish set 1 lands on the final set.
- `review-animations` cannot be run by the agent; the human runs `/review-animations`.
- Not run: the PostgreSQL suite (before release). Five other probes still use the old step; listed in TODO.md.

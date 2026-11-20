# Cash out and Reverse apart

Status: approved 2026-11-20. Reconstituted 2026-11-20 from the queued plan [ui_5_cash_out_and_reverse](../roadmap/plan_queue/ui_5_cash_out_and_reverse.md), critique issue 6 (P2) in the [UI critique](../study/1795101392_ui_critique.md). Mode: mixed (design, with a check that the money path stays the same). Skills: `/impeccable harden`, `tdd` for the guard tests; at rendezvous `code-review`, `break-ui`, `/impeccable critique`.

## Goal

A one-handed host cannot reverse a record when they meant to cash out. A correction stays easy to find for the host who needs one.

## What the code does now

- The player sheet in a set in play has, from the top: the bone "Cash out" button (`sheet-swap`), the summary, then each entry with an open reason field and a red "Reverse" button (`templates/web/_player_actions.html`, included from `templates/web/_player_row.html:49`).
- The same entry list is in the count-up sheet (`templates/web/_count_rows.html:55`).
- A copy of the list is in `templates/web/_player_records_body.html`. The closed-set results (`_results.html:17`) and the counted rows (`_players_count.html` through `_player_records.html`) use it.
- The reason is `required`. One stray tap on Reverse cannot reverse a record today. The risk is a tap in the reason field, then a red button next to the thumb, on every entry, close under Cash out.
- The page already has the safe pattern: "Undo" on a paid transfer is a quiet `<details>` summary. The reason field and the red button show only after it opens (`templates/web/night.html:118`).
- "Tap a player to cash out or correct an entry." shows at all widths (`templates/web/_players.html:13`). From 900 px each row has its own Cash out button (`static/css/app.css:1635`).

## OPEN QUESTIONS

1. **Undo after a money write (Monzo style).** After a rebuy or cash-out, a toast says "Rebuy ₱1,000 · Miguel" with Undo for a few seconds. Undo records a reversal with a fixed reason. My recommendation: keep it out of this plan. It adds a new write path (a reversal without a typed reason) and a timer. It is a money rule change, so it needs its own plan and an ADR. **Answer (2026-11-20): out of this plan.**
2. **The confirm step.** The queued plan says "Reverse asks for a confirmation before the reason form". My recommendation: the disclosure is the confirmation. The host taps a quiet "Reverse…" on the entry, and only then sees the reason field and the red "Reverse ₱1,000" button. That is two deliberate steps and a typed reason. A third dialog adds no safety. **Answer (2026-11-20): the disclosure is the confirmation.**

## Tasks

### 1. One entry list, with the reversal behind a disclosure — `tests: alongside`

- [x] Make one partial for a reversal form, `templates/web/_reverse_form.html`. Use it from `_player_actions.html` and `_player_records_body.html`, for buy-ins and cash-outs.
- [x] The partial is a `<details>` with a quiet summary "Reverse…". Inside: one short line ("This adds a reversal. The record stays in the log."), the reason field, and a red button that names the amount: "Reverse ₱1,000".
- [x] Keep the form's action, `data-once`, `data-keep`, the `required` reason and its `maxlength` the same. Do not change `ledger/views.py` or `ledger/services.py`.
- [x] The summary is a 48 px target on a phone. It is the quiet button style, not red.

Acceptance: in the player sheet no red button and no reason field show until the host opens "Reverse…" on one entry. The open state survives a live refresh (`data-key`). A reversal still lands with its reason.

Completion: `ledger/tests/test_buy_ins.py`, `test_cash_outs.py`, `web/tests/test_acceptance.py` and `test_one_trip.py` pass unchanged or with only markup selectors updated. A new view test checks that the player sheet markup has no `btn-danger` outside a closed `<details>`.

### 2. Corrections under a hairline, below the primary action — `tests: alongside`

- [x] In `_player_actions.html` and `_player_records_body.html`, put the entries under a small heading "Records" and the reversal disclosures on the entries. When the viewer can reverse, the heading says "Records and corrections".
- [x] Put a hairline (`--rule`) between the summary block (Cash out, bought in, played) and the records.
- [x] Use existing tokens and the existing `section-label` style. No new colours.

Acceptance: at 320, 390 and 1280 px the sheet reads: Cash out, summary, hairline, heading, records. The first "Reverse…" is at least one hairline and one heading below Cash out.

Completion: a browser probe at 390 px measures the gap between the bottom of Cash out and the top of the first "Reverse…" target and checks it is 48 px or more, and checks no red button is visible on open.

### 3. Hide the tap hint from 900 px — `tests: alongside`

- [x] Hide `.row-hint` from 900 px. Below 900 px it stays, so no row moves at the first cash-out.

Acceptance: at 1280 px the hint is gone and each row shows Cash out. At 390 px the hint shows.

Completion: the browser probe checks both widths.

## Rendezvous checks (to fill in)

- [ ] SQLite suite.
- [ ] Browser probe as host, set in play, 390 px: open a player, no red button; open "Reverse…", type a reason, reverse; the entry shows struck with the reason.
- [ ] Same on the count-up sheet and on a closed set's results.
- [ ] `break-ui`: a long name and a ₱1,000,000.50 amount in the red button at 320 px.
- [ ] `/impeccable critique` of the sheet.

## Phone check (for TODO.md on release)

- Open a player in a set in play: Cash out is at the top, the records are under a line, and no red button shows. Tap "Reverse…" on a rebuy: a reason field and "Reverse ₱1,000" appear. Reverse it: the rebuy is struck through with the reason. On a computer the "Tap a player" line is gone.

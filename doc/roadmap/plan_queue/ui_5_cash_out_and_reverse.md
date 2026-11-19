# Cash out and Reverse apart (queued)

Status: queued 2026-11-19 from the [whole-app UI critique](../../study/1795101392_ui_critique.md). Reconstitute against the current code before approval. Mode: design. Critique issue 6 (P2). Skill: `/impeccable harden`.

## Goal

A one-handed host cannot reverse a record when they meant to cash out.

## Evidence

- In the player sheet, Reverse sits directly under Cash out (`h_s3_playersheet_act.png`).
- "Tap a player to cash out" shows at 1280 px, where each row already has a Cash out button (`templates/web/_players.html:11`).

## Draft tasks

- [ ] Put corrections under a hairline with a "Corrections" heading, below the primary action.
- [ ] Reverse asks for a confirmation before the reason form. `tests: first` (money: the reversal service, its request_id and its reason stay unchanged).
- [ ] Hide the tap hint from 900 px.
- [ ] Optional, needs the human: a Monzo-style confirmation after a money write ("Rebuy ₱1,000 · Miguel") with Undo for a few seconds. Undo records a reversal (append-only). Put it in OPEN QUESTIONS.

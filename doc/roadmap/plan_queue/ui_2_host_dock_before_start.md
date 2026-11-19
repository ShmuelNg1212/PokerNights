# Host dock before Start (queued)

Status: queued 2026-11-19 from the [whole-app UI critique](../../study/1795101392_ui_critique.md). Reconstitute against the current code before approval. Mode: design. Critique issue 2 (P1). Skill: `/impeccable distill`.

## Goal

On a draft or open set, the dock holds one primary action: **Start the set**, with its usual-buy-in checkbox.

## Evidence

- The open set shows about ten controls at once (Draw, the stakes fold, Rebuy, Buy-in, Full set log, Host controls, Join this set, the checkbox, Start the set, More host controls).
- Two disclosures stack: the "Host controls" toggle and heading (`templates/web/_host_controls.html:4-5`) and "More host controls" (`:69`).

## Draft tasks

- [ ] On phones, remove the "Host controls" heading row on draft and open sets. Keep the toggle only where it carries the next step or the count-up figure. Completion: one disclosure in the dock.
- [ ] Move "Join this set" out of the dock. Recommendation: a "+ You" row at the end of the Players list, in the row-card style. Alternative: into More host controls. Completion: the dock has Start the set and its checkbox only.
- [ ] Browser check at 390 x 844: the whole dock fits without scrolling on s21 and s4. `tests: alongside`.

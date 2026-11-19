# Count-up: clear figure, calm mismatch (queued)

Status: queued 2026-11-19 from the [whole-app UI critique](../../study/1795101392_ui_critique.md). Reconstitute against the current code before approval. Mode: design. Critique issues 4 and 5 (P2). Human answer 2026-11-19: a mismatch is a **calm search**, not an alarm. Skills: `/impeccable clarify`, `/impeccable quieter`.

## Goal

The host reads the count-up dock without remembering anything. A mismatch reads as "find ₱100", with the counts first.

## Evidence

- The dock shows "₱3,550 of ₱8,500 bought in" with no label (`templates/web/_host_controls.html:4`).
- "₱4,950 still to account for. 3 still to count." appears in the books, the books summary and the dock (`ledger/queries.py:394`).
- On a mismatch the panel, the dock line and the primary button are all red. "Finalize with an override" sits under the error (s9).

## Draft tasks

- [ ] Label the dock figure "Counted + cashed out". `tests: first` (the text comes from the books query).
- [ ] Show the remaining sentence once, in the dock. The books keep the table and the not-cashed-out names. `tests: first`.
- [ ] Mismatch panel: neutral surface and border; only the amount in Down. The dock line and the button lose the red outline. Keep the sign and the words. `tests: alongside`.
- [ ] In the mismatch state, put Player counts above The books. `tests: alongside`.
- [ ] Move "Finalize with an override" into More host controls. Keep its reason field and its rules unchanged. `tests: first` (the override is a money action: check that the form, the reason and the permission are unchanged).
- [ ] The count-up progress bar: segments differ by more than colour (pattern or a gap), for colour-blind hosts.

# Session page: the money first (queued)

Status: queued 2026-11-19 from the [whole-app UI critique](../../study/1795101392_ui_critique.md). Reconstitute against the current code before approval. Mode: design. Critique issue 3 (P2). Skill: `/impeccable layout`.

## Goal

On a closed session, a person sees what they pay or get before anything else. The recap is there when they want it.

## Evidence

- The recap sheet opens by itself and covers "You pay ₱850" (n12, n1).
- The sheet's x shows a focus ring on load.
- In one capture, ben's page was not at the top after closing the sheet (`b_n1_norecap_act.png`). Not seen for hana. Check on a phone.
- Settle-up ends on "Not paid"; nothing marks the end when all are paid.

## Draft tasks

- [ ] Do not open the recap by itself. Add a "Recap ready" card under the lead that opens it. Recommendation from Apple Wallet and Splitwise: the amount first, history second. Note: the finale stage (`finale.js`) leads into the recap; keep the finale and have it end on the page, not the sheet. Open question for the human at reconstitution.
- [ ] If the sheet stays automatic: focus without the visible ring on load; keep scroll at the top after close.
- [ ] When every transfer is paid, show "Everyone is square" with the hairline rule that the balanced books use. Plays once; reduced motion shows the end state.

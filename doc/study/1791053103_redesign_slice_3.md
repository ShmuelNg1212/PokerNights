# Study: redesign slice 3

Date: 2026-10-04 (Asia/Manila). This is a revalidation addendum to [the original redesign study](1791045491_visual_redesign.md). It preserves that study and its approved Rack direction.

## Intended outcome

Make the session page easy to use after several sets. Show the viewer's result, who pays whom, the amount still unpaid, payment records and a short closing recap. This is parent-plan task 9. Slice 4 remains separate.

## Current state and evidence

Main is clean. Slices 1–2 are complete. Source inspection covers SPEC.md, AGENTS.md, PRODUCT.md, DESIGN.md, the parent plan, slice 2's completion record, web/views.py, templates/web/night.html, settlement/models.py, settlement/services.py, settlement/queries.py and existing web tests. There is no doc/canonical directory. This revalidation is source-based; no new rendered-screen claims are made.

- The session page still uses the earlier narrow card composition. Sets appear before results and payments. It inherits the built font, palette and controls.
- Session standings aggregate current frozen PlayerResult rows in first-join order. Open-session standings include finalized sets only. An active set does not have a result to add.
- Closing requires every set to be finalized or canceled and at least one finalized set. The close service writes the transfer plan once. Closing does not mark transfers paid.
- A transfer has one active payment at most. Undo preserves the payment and writes a reversal. Payment history includes inactive records. Only hosts can record or undo payments.
- The session page does not poll. Native POSTs redirect to accepted server state. Draft sets remain hidden from players.
- Existing session-page time sums known visible set times, including canceled sets. Recap time therefore needs a narrower, explicit definition.
- The once-only recap has not been built. The existing sheet module requires the set's live region and manages forms and drafts; using it unchanged on the session page would not work.
- Slice 2 measured 7,912 bytes of overall added JavaScript against the parent plan's 8,000-byte ceiling. The stylesheet remains below 26 KB against 40 KB. The local font is 103,912 bytes against 150 KB. Recap work must reclaim JavaScript space through a tested shared implementation.

SPEC.md still describes chip conversion. The approved unit implementation, AGENTS.md and PRODUCT.md prohibit it. This known discrepancy remains a human-owned spec item; slice 3 will not change money semantics or SPEC.md.

## Options and tradeoffs

1. Restyle the old cards only. Small change, but it leaves the session's key task below the set list and omits the approved recap.
2. Recompose the session page within the built Rack system. Put the current session task first, distinguish results from payments and reuse native forms. Add a small recap enhancement. This completes task 9 without changing accounting.
3. Add session polling, payment reporting or partial-payment controls. These require new product and service requirements. They are outside this slice.

Recommend option 2. Retain the palette, Archivo, tokens, signed result icons and existing sheet behavior. Do not reopen visual-direction selection.

## Proposed definitions and composition

Closed sessions lead with a slate field: Still to pay, the settlement status, paid transfer count and an amount-based progress indicator. Still to pay is the sum of transfer amounts without an active payment. Paid progress uses paid transfer amounts divided by all transfer amounts, not transfer count or winnings. Show counts separately. Zero transfers show Nobody owes anything and a zero remaining amount without division by zero. Never call an open session settled because its transfer list is empty.

Open sessions lead with Open set / Start next set when allowed, plus the viewer's Results so far over finalized sets. Host close controls state the unfinished-set gate. Closed sessions lead with the viewer's result and relevant pay/receive instructions. Keep the full Who pays whom, Session results, Sets and Payment records sections separately labelled. Use text to explain that results describe the game and transfers describe settlement. Do not imply the app moves money.

Reuse initial tokens with names always visible. Give members a stable session presentation order from their first appearance in the standings, rather than treating a per-set participant ID as a session identity. The token order and colours may differ from an individual set. No stored identity or seat feature is added.

Recap values come from finalized sets only:

- Recorded play time: sum known finalized-set timer durations. If all are unknown, say Not recorded. If some are unknown, identify the total as partial. Never substitute zero for unknown time.
- Total bought in across finalized sets: sum current Finalization.total_buy_in snapshots. This is money recorded through the sets, not money transferred; carried money may be recorded again in another set.
- Top session result: highest positive aggregate result. Name all tied winners. All-zero standings say Everyone broke even.
- Your session result: show only if the viewer has a standing. A non-playing host gets no invented zero result.

Automatically open the recap once per closed session, signed-in viewer and browser. Store the consumed key before opening, so redirects after paid/undo cannot reopen it. Provide View session recap for manual access. If persistent storage is unavailable, skip automatic opening and keep manual access. The rest of the page and native forms work without JavaScript.

Refine original motion M14 for keyboard access: a 48 px Close control, backdrop tap or Escape closes in one action; Tab retains normal modal focus navigation. This replaces the original instruction that any key closes, which would prevent useful keyboard traversal. Return focus to the recap trigger. Use a short stagger within 600 ms, with static reduced-motion rendering and no amount interpolation.

## Inputs, risks and open decisions

No external asset, API or new dependency is needed. Verification can use synthetic sessions in a temporary database and the existing local Chrome/CDP harness. PostgreSQL verification uses the installed local server. Never seed the development database.

The main risk is the JavaScript budget. Reuse shared dialog behavior and remove duplication while preserving set sheets, drafts and polling. Keep the 8,000-byte ceiling; if implementation cannot meet it without behavioral loss, report the concrete problem before changing the constraint. Other risks are uneven-transfer progress, confusing repeat buy-ins with payments, tied winners, hidden drafts, and overflow from two names plus a large amount.

The recap definitions, per-viewer key, manual reopen and accessible dismissal above are proposed refinements for approval in the slice 3 plan. No implementation is authorized by this study. No additional human input is needed to prepare that plan.

# Who pays whom: alignment study

Date: 2026-10-05, Asia/Manila. Base: `main` at `ebb4ad7`. Outcome: readable payer/payee identities and stable amount, payment-state and action alignment in each transfer card.

## Current state and authority

The human reports alignment issues and asks for design skills. Used Impeccable's layout guidance in Operate mode, inside the built Rack. Sources: SPEC.md, PRODUCT.md, DESIGN.md (session settle-up), the session surface brief, wiki features, `templates/web/night.html` and the transfer rules in `static/css/app.css`. No canonical directory is present. The working tree was clean.

Who pays whom is a session-level list. Each card has payer and payee identities around an arrow and "pays", then an exact amount, Paid/Not paid and a host-only Mark paid/Undo action. Payments change the remaining amount, not frozen poker results. The current parties use two equal columns; the financial line uses a wrapping flex row with a 100px minimum status width and a 124px minimum button width. Paid adds a timestamp and "marked by the host".

## Rendered evidence

A fresh temporary SQLite database used the existing `seed.py`, `seed_end_set.py` and `seed_night.py` fixtures. Isolated Chrome inspected unpaid, paid and large-amount/long-name sessions at 320, 390, 768, 900 and 1280px, plus a player view. No production or development game was changed. Measurements and 16 captures are in `/private/tmp/pn-transfer-study-review/`.

1. **Actions jump between lines.** An ordinary unpaid card is 180px tall at 320px versus 129px at 390px. Mark paid wraps independently of the amount and status. Large amounts also push the action down at 390 and 900px.
2. **Paid metadata changes the alignment.** At 390px the unpaid card is 129px tall; the paid card is 167px. Its amount top is 22px below the status top because flex center-aligns the taller status block. The button floats beside the multi-line timestamp instead of sharing a stable action position.
3. **Long names lose a useful identity axis.** At 320px a long payer name has only 64px of width and is 162px tall. Tokens and the direction are vertically centered against these names. They sit several lines below the beginning of the identity. Word fragments are common.
4. **Screen width is not card width.** At 900px the two-column session layout leaves a transfer card only 416px wide. It still has the wrapping problems despite being in the desktop layout. At 1280px the card is 696px wide.

The captures cropped from a tall section can place the fixed header inside the image. That is a capture artifact, not evidence of a broken header. Geometry findings concern the transfer elements themselves.

## Layout assessment

The useful reading path is payer → payee → exact amount → payment state → host action. Keep each transfer as one card and preserve the existing hierarchy. Identity fields belong together; the financial facts and action form the second group. Use the Rack spacing scale, not independent corrective margins.

The existing identity grid is suitable in a wide card. In a narrow card, full-width identity rows give the names useful space. Start-align chips with the first line of each name. A compact written direction joins the identities. Reserve explicit grid positions for amount, state and action; paid metadata grows downward in its own status block. DOM and focus order must continue to follow the reading path. Player cards omit the action without leaving an empty column.

The layout-scoped mechanical detector returned `[]`. It does not measure flex wrapping or identity alignment, so it does not overturn the rendered findings. No new palette, type family, assets or motion is needed.

## Options and recommendation

- **Margin-only repair:** low code churn, but flex wrapping still depends on amount length, paid text and available card width. It leaves long names in cramped half-width columns.
- **Explicit grid with narrow-card adaptation (recommended):** stable positions for money/status/action; stack identities when the actual card is narrow. Use a container-aware rule, because the 900px session detail column is narrow too. Keep side-by-side identities when there is enough room. Retain all names, amounts, units, status text and payment actions.
- **Replace the cards with a table:** stronger desktop columns, but more work and a different phone interaction. Outside this focused alignment repair.

For narrow cards, place the exact amount across the full financial row, then status on the left and the host action on the right. On wide cards, group amount and status at the left with a fixed action column at the right. Long formatted amounts may use an existing smaller figure role; never truncate, abbreviate, convert units or split number digits.

## Boundaries, risks and open questions

Only transfer markup and scoped CSS need implementation changes. Services, totals, permissions, request IDs, CSRF, forms, Turbo updates and money values stay intact. No migration or new dependency. The existing 48px targets and reduced-motion behavior remain requirements.

Risks: stacked identities increase ordinary narrow-card height; container-aware rules must be verified in both phone and narrow desktop columns; large chip figures need explicit coverage; a player view must reclaim the absent action column. Safari/iPhone appearance remains a human check.

No missing external input blocks a plan. The exact defect on the human's phone was not supplied; these are independently reproduced failures. Recommend the grid repair, with a narrow-card breakpoint selected from the measured content fit during execution. Human approval is needed before implementation under AGENTS.md.

# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Hosts who record the bank during a home poker cash game. Players who check their totals and what they owe. Private groups of friends in the Philippines.

## Product Purpose

Record buy-ins and cash-outs, check that the books balance, and calculate who pays whom. PokerNights does not move money.

## Operating Context

The approved brief describes a dim room, late at night, one hand free and short glances between hands. A session contains one or more sets. Each set has its own money records, counts and timer. Settle-up happens at the end of the session.

## Capabilities and Constraints

Django templates, plain CSS and small vanilla JavaScript modules. Integer money only: centavos in pesos games, whole chips in chips games. Chips have no peso value. Server-confirmed figures are authoritative. Count-up also shows an explicitly labelled local preview while the host types, to compare remaining stacks plus cash-outs with buy-ins before recording cash-outs. Accounting and permissions stay unchanged in the redesign. Seating and statistics are future features.

## Brand Commitments

Dark theme. Plain, short words that are exact about money. Pesos display as ₱1,600 or ₱1,600.50. Wins and losses carry signs and icons. No casino imagery or invented claims.

## Evidence on Hand

SPEC.md, the wiki, and the approved visual-redesign study and plan. Mockups contain synthetic demonstration data.

## Product Principles

- Make frequent host actions easy on a phone.
- Keep total bought in separate from money still in play.
- Show success only after server acceptance.
- Preserve typed values during live updates.

## Accessibility & Inclusion

Large touch targets, visible keyboard focus, labelled controls, reduced-motion support and text contrast of at least 4.5:1.

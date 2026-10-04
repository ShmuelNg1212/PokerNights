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

Django templates, plain CSS and small vanilla JavaScript modules. Integer money only: centavos in pesos games, whole chips in chips games. Chips have no peso value. Server-confirmed figures are authoritative. Count-up also shows an explicitly labelled local preview while the host types, to compare remaining stacks plus cash-outs with buy-ins before recording cash-outs. Hosts can add existing roster players or create a no-login roster player from an ongoing set; late buy-ins remain separate. Accounting and permissions stay unchanged in the redesign. Seating and statistics are future features.

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

## 2026-10-04 addendum — per-buy-in rake

Hosts can configure each set with rake Off, a percentage or a flat amount before accepting money. Rake is deducted from every gross buy-in and rebuy, including opening and late-player buy-ins. Percentages use up to two decimal places and round down separately for each buy-in to centavos or whole chips. The deduction must leave a positive playable amount. The rule stays locked while accepted money exists; the next set inherits it. Buy-in limits and the usual buy-in remain gross amounts.

Screens distinguish total bought in, collected rake, available to play and money still in play. Counting compares remaining stacks plus accepted cash-outs plus already-collected rake with gross buy-ins. Final results include the player's rake as a loss; settle-up adds that already-collected contribution back when calculating remaining player payments. Equal losses consisting only of rake therefore require no further transfer. The dedicated group rake account tracks accepted lifetime fees by session and set, with pesos and chips separate and reversed buy-ins excluded. It is not a player, login or transfer recipient. PokerNights records these facts and payments; it does not move money.

## 2026-10-04 addendum — rake setup controls

New session and Game settings share native Off, Flat amount and Percentage of buy-in choices; new sessions default to Off. Both value fields stay visible, but only the selected rule's value validates. Off ignores both; flat requires a positive amount in the session's unit; percentage requires 0.01%–99.99% with up to two decimal places. Refused submissions retain the choice and typed values with local errors. The initial rule is recorded before opening buy-ins, and presets remain stakes-only.

An empty set offers Choose rake before buy-ins beside the start controls. The next set inherits the current rule and can change it before accepting money. Settings explain that recorded buy-ins or cash-outs lock the rule, including default opening buy-ins created by Start the game, and direct the host to choose before starting the next set. Other permitted stake edits preserve the locked rule; a permitted unit change resets it to Off.

## 2026-10-04 addendum — UI evolution

The group page separates Sessions, Stats and Group settings. Screens use Session for the gathering and Set for one round; “Game settings” is now Set settings. Hosts see written Buy-in, Rebuy and Cash out actions on each row. Stats show profit or loss after rake, sessions played and win rate per unit, for all time or one month, from closed sessions only. The product has a chip-and-crescent mark. [Plan](doc/plan/1791098885_ui_evolution.md).

## 2026-10-04 addendum — Your groups home

The first page after sign-in reports each group's state: whether a set is in play, the one action the viewer is needed for, what they owe or are owed, their record and their last result. A set in play is one tap from here. Money still in play is left off this page because it does not refresh by itself. A one-group member still lands here. [Plan](doc/plan/1791102439_your_groups_home.md).

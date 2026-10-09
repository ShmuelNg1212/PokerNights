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

## 2026-10-04 addendum — Archive and delete

Hosts can clear away a session or a group. Archiving hides it and takes a session out of the stats, records, “To settle” and the rake total; a host can restore it. Deleting is permanent and is offered only where no money was ever recorded. Money records are never removed. Any host of the group may do this; a group delete asks for the typed group name.

## 2026-10-05 addendum — Entry flow

An invite link is the way in. A signed-out visitor who opens one creates an account and is in the group at once; a person who already has an account logs in and confirms. Sign up says that friends see the username and that there is no password reset yet; only the site administrator can set a new password. The entry pages state that PokerNights records the game and never moves money.

## 2026-10-05 addendum — Numpad and the end of a set

On a phone, typed numbers use the app's own number keys: amounts, final counts, stakes, rake and seats. The phone's keyboard stays for text. The keys only offer what the field can take, so a chips amount has no decimal point. The environment variable `NUMPAD=False` returns to the phone's keyboard.

Ending a set is arranged around the host's task. The players' count fields come first, one running total is always in view, and one main button names the next step. Before cash-outs are recorded the review says whether the books will balance. Finalizing asks once, because the app cannot reopen a finalized set. The final page opens with what went in, what came out and that the two agree. Accounting, permissions and what each step records are unchanged. [Plan](doc/plan/1791202390_host_gaps_numpad_count_up.md).

## 2026-10-06 addendum — Password reset link

A person who forgot their password asks a host of their group. The host creates a reset link in Group settings and sends it; the person opens it, chooses a new password and is logged in. The link works once, lasts 24 hours and can be cancelled. The app sends nothing itself. A host cannot create one for a site administrator or for a person who hosts another group; those accounts, and a group's only host, still go to the site administrator. A host could use a link to log in as one of their own players; the audit log records who created and who used each link. [Plan](doc/plan/1791263947_host_issued_password_reset.md).

## 2026-10-06 addendum — Players record their own rebuy and count

A player with a login records their own rebuy from their phone; it is accepted at once, as a host's is, and the host can reverse it. After the host ends play, each player types their own final count. That number is a statement: the host confirms it or types another, and only a confirmed count is cashed out or enters a result. Everyone on the set sees both within seconds. A rebuy sent from a screen that does not show the player's latest buy-ins is refused, so the host and the player cannot record one rebuy twice. The first buy-in, cash-outs, corrections, the balance and finalizing stay with the host. [Plan](doc/plan/1791266619_player_rebuys_and_counts.md).

## 2026-10-09 addendum — Roster management

A host keeps the player list in order. Removing a player is asked first, on a page that says what happens and lists what they still owe or are owed; a player at the table of an unfinished set cannot be removed. A removed player can be brought back with their history intact, and their name cannot be added again as a second person. Hosts save a contact note that only hosts see and add up to 30 names at once. Anyone with a login changes their own name in the group; the username stays. Each row says how many sessions the player came to and when they last played, counted as Stats counts. [Plan](doc/plan/1791525658_roster_management.md).

## 2026-10-09 addendum — Claim links

A host gives a roster player a login of their own by sending a claim link. Whoever opens it first becomes that player in the group, with the player's history; the link works once, lasts 7 days and can be cancelled. A newcomer signs up and is in at once; a person with an account confirms on one page. An account that already has games recorded in the group cannot claim, because two records cannot be joined yet. A claim moves no money record and cannot be undone in the app. [Plan](doc/plan/1791527506_claim_links.md).

## 2026-10-09 addendum — Stats board and player pages

Stats opens with the viewer's own profit or loss, rank and last result. The board can be ordered by profit, average, return, per hour or sessions, over all time, this year, the last three months or one month, and a player needs a few sessions before holding a place. Each player has a page with a running profit chart, a bar for each session, figures that explain the result (average, return on buy-ins, per hour, rebuys, rake paid) and their best and worst nights. Every member of a group can open every player's page. All of it is read from closed sessions; nothing new is stored, pesos and chips never mix, and money never animates through other values. [Plan](doc/plan/1791528961_stats_revamp.md).

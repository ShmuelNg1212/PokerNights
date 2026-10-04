# PokerNights UI inspection

Date: 2026-10-04, Asia/Manila. Scope: Step 1 only. No repository edits, dependency additions, or commits. Read AGENTS.md, SPEC.md, PRODUCT.md, DESIGN.md, current journals and code. Applied agentic-workflow and Impeccable assessment guidance. Preserve the existing Rack visual identity.

## Stack and assets

Python 3.14; Django 6.1.1; Django templates; SQLite locally and PostgreSQL for production/concurrency checks. Four pinned requirements: Django, django-environ, dj-database-url and psycopg. No frontend framework, bundler, WebSocket layer or queue.

There are 33 repository templates: 13 page templates, one base, and 19 fragments. One stylesheet, static/css/app.css (33,125 bytes), holds tokens, base rules, utilities, forms, buttons, notices, badges, cards, tables and sheets, followed by feature-specific sections and later overrides. Tokens exist already, but type, spacing and radii still contain repeated literals. Two root blocks and appended overrides make the cascade harder to follow.

Archivo is served locally from static/fonts/archivo.woff2 (103,912 bytes; OFL). It supports variable weight and width. Normal text uses the full width; money uses the condensed width. Lucide icon paths are rendered by web/templatetags/table_tags.py, with an ISC license. There are no logo SVGs or favicon assets.

Eight vanilla JS files, 20,105 bytes total: forms.js (submission guards/drafts), toasts.js, live.js (four-second polling), clock.js, counts.js (BigInt previews), pick.js, sheets.js (native dialog enhancement) and changes.js. Preserve these behaviors and their progressive enhancement.

The active set becomes two columns at 900px. Both 375px and 768px use the single-column presentation and mobile host dock. Wider containers vary by page: roughly 560–1,180px.

## Current visual values

Colors use OKLCH. Ground .17 .012 60; rail .215 .014 60; rail-2 .265 .016 60; bone .93 .025 85; bone-dim .74 .028 80; ink .19 .02 60; line .55 .018 60; rule .33 .018 60; felt .34 .095 265; felt-deep .25 .08 265; felt-ink .86 .04 265; slate .285 .025 265; slate-ink .86 .025 265; brass .82 .13 85; winnings .82 .13 160; losses .76 .14 25. Existing semantic aliases include background, surface, text, muted, accent, good, danger and warning.

Player colors: #9e3038, #285aa8, #267449, #e4bd48, #82409b, #d48d48, #70b9bd, #dd86a1, #b4b1a6, #524b9a.

Body: 16px, weight 500, line-height 1.45. Headings include 16, 18.4 and 24px; page titles 32px; form titles 28px; hero amounts 64px; money inputs 40px; result amounts 22px; transfers 24px; labels roughly 12–14px. Money font width is approximately 70%.

Spacing literals include 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32 and 48px. Radii include 4px progress, 10px fields, 12px rows, 15px buttons, 16px cards, 26px hero/sheets, pill 999px and circle 50%. Buttons have a hard 3px bottom shadow. Existing tap token is 48px. Existing timings: 110, 180, 320 and 600ms; reduced motion support exists.

## Every page template and screen

| Template | Screen / existing path |
|---|---|
| registration/login.html | Login, /accounts/login/ |
| accounts/signup.html | Sign up, /accounts/signup/ |
| groups/invite_accept.html | Accept invite, valid and invalid, /join/<token>/ |
| web/home.html | Groups list, empty groups, inline group creation, / |
| web/group.html | Group sessions and history; tables/add table; presets; roster/add no-login player/rename/roles/removal; invite links/revoke; group rake account and breakdown, /g/<group>/ |
| games/session_form.html | New session, /g/<group>/sessions/new/ |
| games/preset_form.html | New/edit preset, /g/<group>/presets/new/ and /g/<group>/presets/<preset>/ |
| games/settings_form.html | Set settings including rake; editable and locked states, /s/<set>/settings/ |
| games/add_players.html | Add several players before or during play; roster selection and new no-login players, /s/<set>/players/add-several/ |
| web/session.html | Set: setup, open, in play, counting, balanced/discrepant/override, finalized and canceled; host/player variants, /s/<set>/ |
| ledger/cash_out_counted.html | Review batch cash-outs and empty review, /s/<set>/cash-out-counted/ |
| web/session_log.html | Set ledger/audit log including reversals and settings, /s/<set>/log/ |
| web/night.html | Session overview, next-set/close controls, blocked closure, settle-up unpaid/part-paid/settled/no transfers, results, payment records and recap, /n/<session>/ |

Buy-in, rebuy, individual cash-out, participant details, count confirmation, override and host controls are embedded forms or bottom sheets on the set page. Recap is a sheet on the session page. Table creation, roster management, invite creation/revocation and payment marking use POST endpoints and redirects; they are not separate page templates.

## Every shared template

Base: base.html. General fragments: partials/form_fields.html and games/_rake_fields.html.

Web fragments: _balance.html, _buy_in_form.html, _cash_out_form.html, _count_total.html, _count_up.html, _final_set.html, _host_controls.html, _player_actions.html, _player_records.html, _players.html, _players_count.html, _rake_rule.html, _rake_totals.html, _result_icon.html, _results.html, _session_legacy.html and _session_live.html.

Django admin uses generated framework templates. Representative admin index, set list/detail and read-only money detail were reviewed. Not every admin model was visually reviewed. /healthz is text and /s/<set>/state/ is JSON, not a screen.

There is no leaderboard/stats view, dedicated group settings page, password reset/profile page, export screen, hand-play UI or tournament seating UI in this repository.

## Browser evidence

Used an isolated temporary SQLite database with synthetic records and a temporary server on port 8770. The existing port 8000 preview and its data were left intact. Captured 58 screen/state variants at each of 375px and 768px, plus four at 1280px: 120 captures. No horizontal overflow was detected. Reviewed original key screenshots and contact sheets covering all captures. Very long pages were additionally checked through source and rendered text. This is a visual survey, not exhaustive branch coverage, assistive-technology testing or WCAG certification.

Covered populated/empty groups; host/player groups; login/signup; valid/invalid invite; new session; peso/chip presets; empty/locked/percentage/flat settings; add several and late players; batch cash-out normal/empty; logs/reversals; representative admin; setup/open/active/counting/final/canceled sets; pesos/chips; no money, partial counts, balanced, discrepancy, override, large values; host/player variants; open/close-ready sessions; unpaid/part-paid/settled/no-transfer settlement; recap; rebuy/cash-out sheets; expanded group management. Desktop checks: group, active set, counting and settlement.

Evidence: /private/tmp/pn-ui-inspect-results.json; /private/tmp/pn-ui-inspect-review/; /private/tmp/pn-ui-inspect-browser.log. Captures use synthetic records. No credentials belong in the published report.

## Findings and proposed changes

1. Keep the palette, Archivo, compressed figures, chip avatars, quick amounts, green profits, pills and hard button shadows. This is an evolution of Rack.
2. Felt blue currently covers the group session list even when empty and set setup/open heroes. Counting, final results and settlement use slate but retain the diamond texture. Reserve blue plus diamonds for the running set only. Generic notices are usually brass, not blue; ordinary informational notices still need a calm neutral treatment.
3. Sessions are already listed first on the group page, but management remains beside/below them and rake is inside the sessions column. Use Sessions / Stats / Group settings views on the same existing route, with normal links and query parameters. Preserve all POST endpoints and authorization.
4. Rebuy text disappears below 900px, leaving a plus icon. Individual cash-out is buried in player details. Add visible labels with a two-line mobile action layout. Keep 48px targets, exceeding the requested 44px minimum.
5. Secondary text sampled at 6.2:1–8.28:1 already passes AA for normal text. Preserve it. Existing brass focus rings and skip navigation are useful. More host controls is only 38px high on active mobile sets. Increase it and audit focus, small controls and avatar contrast. These sampled ratios do not establish full contrast compliance for gradients or every control.
6. The active set's pool split resembles progress but is a financial ratio, and rake complicates its meaning. Remove it. Count progress and paid-transfer progress have meaningful denominators and can remain with explicit numeric text. Distinguish unfinished counting from fully counted books that do not balance. Put the signed discrepancy amount above the long player list and retain any acknowledged override explanation.
7. Settlement already has payer/payee chip avatars, amounts, status text, 48px Mark paid actions and Still to pay. Refine the hierarchy and neutral hero. Keep the existing paid/unpaid POST actions and host checks. Make recap explicitly opened rather than automatically covering settlement on first visit.
8. No stats exists. Add read-only aggregation of current finalized PlayerResult snapshots. This requires new queries and display tests, not new models or changes to money calculations.
9. Dark mode is the priority. A complete light theme is not cheap because the current CSS has dark-specific treatments. Defer it; verify the logos against both cream and near-black.
10. Add the four requested hand-written SVG assets, header branding and SVG favicon. Test the chip/crescent at 32px. External SVG images do not automatically inherit HTML currentColor or Archivo; prototype the wordmark delivery and choose self-contained vector lettering if needed to avoid a new dependency.

## Vocabulary and proposed stats definitions

Group = GameGroup; Session = GameNight (the whole gathering and settle-up); Set = GameSession (one round of buy-ins/counting/results); Player = roster member or participant; Table = physical table metadata; Preset = reusable set configuration. Replace ambiguous Game settings/Game log/Join this game with Set settings/Set log/Join this set. Use Poker variant for Hold'em/PLO. Keep model and route names unchanged.

Stats proposal: only closed sessions; current finalized results from noncanceled sets. Aggregate each player's sets into one session result before counting sessions or wins. Total profit/loss uses net after rake, not the rake-adjusted settle-up balance. Win rate means profitable sessions divided by sessions played; break-even sessions count as played but not won. Month means the session's game date in Asia/Manila. Show month/all-time and separate pesos/chips selectors. Never sum or convert units. Include no-login players and historical results subject to existing group access rules. Rake account is not a ranked player.

## Verification baseline

DEBUG=True .venv/bin/python manage.py test: 472 tests passed; 10 PostgreSQL-only skips on SQLite. manage.py check: no issues. pip check: no broken requirements. No configured linter was found. Ledger and settlement already have extensive money tests, including rake, buy-ins, cash-outs, balancing, finalization and transfers. This inspection did not run PostgreSQL concurrency tests.

Preview: http://127.0.0.1:8000, health check 200. To start when stopped: .venv/bin/python manage.py runserver. The temporary fixture server is stopped after inspection. No implementation or logo files were created in Step 1.

# Redesign slice 4: remaining screens

Date: 2026-10-04. This is a new Phase 1 cycle. No implementation is approved.

## Intended outcome

Complete the remaining Rack compositions: groups, home, account entry, supporting forms and the set log. Keep the existing tasks, data and access rules. Make sessions the first task on the group page and keep failed form input available for correction.

## Sources and current evidence

Sources: AGENTS.md, SPEC.md, PRODUCT.md, DESIGN.md, the wiki, and task 10 of [the parent plan](../plan/1791046015_visual_redesign.md). Slices 1–3 are complete on clean main at `cd0d6e7`. This study inspects current templates, views, forms, models, services and CSS. It does not claim a fresh browser inspection of slice 4.

The remaining compositions use the shared Rack font, controls and palette, but retain the earlier 560 px card layout. Home lists memberships then a group-creation form. Group lists sessions first, then tables, presets, players and invitations. Host management remains essential. Ordinary players cannot see draft sets or host forms.

`templates/web/group.html` contains a second copy of add-player and invitation markup inside the title block. That block can put form markup in the document title. Remove that duplicate during execution and retain the functional copy in content.

Django-bound preset, session, settings, login and signup forms retain ordinary bound values after errors. Passwords should remain blank on redisplay. The player picker retains selected IDs after a service refusal. In contrast, group creation, roster add, member rename and table creation call `attempt()` and redirect after a refusal; input is lost and the error is only a page message. Styling alone cannot meet task 10's error criterion. A small change to form binding and failure rendering is required. Services remain the source of business validation and writes.

The log already exposes play periods, participants, settings versions, buy-ins, cash-outs, reversals, balance adjustments, final results and audit events. Its sections are record categories, not one global timeline. Do not imply chronological order across categories or hide reversed entries. Payment records belong to the session page.

`Member` orders by display name then ID. Set token colour uses participant join order. Group roster tokens therefore need an explicit presentation rule; roster order is not set join order. Keep alphabetic roster order and derive roster colour from member ID, with visible initials and full names. Do not promise that colours match a particular set. Reuse the existing palette and collision handling.

The canceled set still uses `_session_legacy.html`. Include its header and canceled notice in this final composition pass so this end state is not left behind. Preserve the reason, roster and log access, and show no invented final result.

## Inventory

- Home and group: `web/home.html`, `web/group.html`.
- Account and invitation: `registration/login.html`, `accounts/signup.html`, `groups/invite_accept.html`.
- Forms: `games/session_form.html`, `games/preset_form.html`, `games/settings_form.html`, `games/add_players.html`, `partials/form_fields.html`; inline group/table/roster forms.
- Read-only records: `web/session_log.html`.
- Remaining end state: canceled branch in `web/_session_legacy.html` and its composition entry point.
- Shared base and CSS only as needed. Already redesigned ledger review, live set, count-up, final results and night page are regression targets, not new compositions.

## Options and tradeoffs

1. Style only. Lowest change cost, but keeps lost input and card-heavy management. Does not meet the parent acceptance criterion.
2. Recompose the remaining screens and repair their form failure presentation. Recommended. A coherent finish of the existing Rack world with a limited view/form change.
3. Add a management dashboard, log filters or a new onboarding flow. Broader product work; no recorded requirement. Defer.

## Recommended structure

Operate mode for groups, home, account and forms; Read mode for the log. Keep the approved warm rails, Archivo, bone actions, brass focus and indigo current-session emphasis. No new visual identity or concept tournament.

Group: heading and current sessions with host New session action first; past sessions next; clearly labelled management sections after those. Keep native disclosures for secondary tools, with the failing disclosure open and the one-time invite link visible when returned. At desktop size the session area can sit beside a management rail; phone order remains sessions first.

Home: groups as full-width navigation rows with role labels, then a compact creation section. No statistics or marketing claims. Account entry and supporting forms use a consistent narrow frame, clear return path, labelled fields and one primary submit. The picker keeps its search, selection summary and capacity checks.

Log: compact set header and labelled record sections with readable time/actor/reason metadata. Keep amount columns exact, signs and icons for results, reversal/void labels plus strike-through, and all existing records. Native section navigation may help long logs without adding a filter or new JavaScript.

## Constraints, risks and external inputs

No new assets, packages, migrations or external services are needed. Use synthetic fixtures for browser checks and leave the development database alone. No money service, settlement algorithm or authorization rule changes.

Current CSS is 28,431 bytes. Added redesign JavaScript is 7,771 bytes, leaving 229 bytes under the approved 8,000-byte ceiling. Prefer native forms and disclosures; add no new module. Keep CSS below 40,000 bytes and the existing 103,912-byte font. Recheck cumulative bytes during execution.

Field-level failures must not mislabel a business rule that concerns several fields. Such errors belong beside the failed form, with all editable input retained. Re-resolve membership on every failure render. No passwords or invitation tokens in persistent draft storage. Existing safe-next authentication behavior must remain.

Pre-existing sidecar/surface brief drift and the SPEC chip-conversion conflict remain outside this slice. Do not repair them as a side effect.

## Open questions

None blocking. The plan proposes a narrowly scoped canceled-state finish and input-retention repair as part of the remaining-screen pass. Human approval of that completed plan is required before implementation.

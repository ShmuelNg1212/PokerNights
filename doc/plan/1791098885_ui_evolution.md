# PokerNights UI evolution plan

Status: approved 2026-10-04 with three amendments (see Progress). Date: 2026-10-04, Asia/Manila.

Study: [UI inspection](../study/1791098885_ui_evolution.md). Both documents were written outside the repository during the no-edit inspection step and copied here on approval.

## Outcome and boundaries

Evolve the existing Rack identity into a consistent, accessible mobile UI with SVG branding. Keep the warm dark palette, cream Archivo text, compressed money, chunky shadows, pill badges, chip avatars, quick amounts and green profits. Felt blue plus diamond pattern belongs only to a running set.

Do not change models, migrations, money write services, settlement algorithms, rake accounting, request-id behavior, access rules or URL patterns. Existing route paths and POST endpoints remain. Group tabs may use query parameters on the existing group route; ordinary links and server-rendered content must work without JS. New stats queries are read-only and access-scoped. No new dependencies. Dark theme only; logos must also work on cream.

## Small commit sequence

Each step is a separate Conventional Commit with relevant tests and a full existing SQLite suite plus Django check before committing. No configured linter exists; do not introduce one solely for this task. If a step uncovers an unrelated defect, record it and keep this scope intact.

1. `refactor(ui): consolidate design tokens and shared components`
   - Extract existing colors, typography, spacing, radii, shadows, targets and motion values into tokens, preserving accepted colors and layout initially.
   - Consolidate duplicate declarations deliberately. Standardize button, input, neutral card, list row, badge, avatar, bottom sheet, empty state and hero-stat primitives. Document component roles.
   - Preserve existing form guards, live polling, BigInt count preview, quick amounts, dialogs and reduced motion.
   - Check representative forms, active/counting sets and settlement at 375/768/1280 before broad adoption. Avoid adding JS where HTML/CSS suffices.

2. `feat(ui): add PokerNights SVG branding`
   - Hand-write static/branding/logo-mark.svg, logo-horizontal.svg, app-icon.svg and logo-mono.svg. Use a flat notched chip and restrained crescent cue.
   - Preserve the Archivo wordmark character. Prototype standalone SVG font delivery; use self-contained vector lettering if required for stable rendering without a new dependency. Do not assume external img inherits page font or currentColor.
   - Wire the header and SVG favicon; retain accessible brand text and avoid duplicate screen-reader names.
   - Check mark at 32px, header at 375px, square icon padding, monochrome and cream/near-black backgrounds. No raster imagery.

3. `refactor(ui): separate sessions from group management`
   - Sessions is the default and primary group view. Add Sessions / Stats / Group settings navigation using the same group URL; Stats is an honest placeholder only until step 7 and should not ship as a dead destination.
   - Move tables, presets, roster, invites and rake into settings presentation. Preserve their forms, roles, action URLs, units and rake breakdown.
   - Make group/session empty states neutral with one clear next action; distinguish informative, warning and error notices. Keep management access for appropriate roles.
   - Test direct group URLs, query selections, redirects, host/player visibility, invite acceptance and native no-JS forms. Implement the complete tab navigation atomically; omit Stats tab until its content exists.

4. `fix(ui): clarify set actions and vocabulary`
   - Apply Group / Session / Set / Player / Table / Preset consistently in templates and display labels. Session is GameNight; Set is GameSession. Use Set settings, Set log, Join this set and Poker variant. Do not rename backend identifiers.
   - Show Buy-in or Rebuy according to current participation, plus a visible Cash out action when valid. Use a stacked mobile action arrangement rather than shrinking targets or names.
   - Preserve quick amounts, limits, request IDs, cash-out eligibility and existing sheet/native behavior.
   - Set all interactive targets, including More host controls, to at least 48px. Keep visible focus and written status/signed figures. Verify dock clearance, keyboard focus and long names.

5. `fix(ui): clarify counting and balance states`
   - Reserve felt texture for in-play sets. Setup/open/counting/finalized/canceled, session overview and ordinary notices use neutral surfaces.
   - Remove the decorative pool split bar. Retain count progress only with a nonzero, meaningful denominator and numeric explanation.
   - Place live counted total and balance status where they are visible before cash-out. Incomplete counts say what remains; completed mismatch shows exact signed discrepancy and the next valid action. A host override retains its reason and raw discrepancy.
   - Reuse existing computed values and BigInt logic. Do not alter balance checks, rounding, thresholds or write services.
   - Verify no-money, partial, zero counts, balanced, discrepancy, override, huge amounts, chips/pesos, rake/reversals and player-view cases.

6. `refactor(ui): prioritize session settle-up`
   - Keep Still to pay / Settled as the primary stat on a neutral hero; put Who pays whom first.
   - Each transfer shows payer avatar/name, payee avatar/name, amount, written paid status and a large Mark paid action. Retain existing undo behavior and host authorization; avoid an optimistic checkbox that misrepresents persistence.
   - Keep meaningful paid-amount progress with explicit totals. A zero-transfer session has a clear settled state with no meaningless bar.
   - Make recap manually opened by default, retain results and payment records, and preserve signed profits/green winnings.
   - Verify unpaid/partly paid/settled/no transfers, host/player, large amounts, reloads, no JS and recap keyboard behavior.

7. `feat(ui): add group player statistics`
   - Add read-only, group-scoped aggregation from current finalized PlayerResult snapshots of noncanceled sets in closed sessions. Use existing records only. No migrations, money writes or new routes.
   - Aggregate sets per player/session first, then calculate total actual net profit/loss, distinct sessions played and profitable-session rate. Use net after rake; never substitute settlement balance.
   - Month is game_date's calendar month in Asia/Manila; provide month/all-time selection. Separate pesos/chips with a unit selection. Include no-login players and permitted historical players. The rake account is not a player.
   - Break-even sessions count in played but not won. Explain the metric so nobody reads it as hand win rate. Use a calm no-data state. Reveal the Stats tab only with working content.
   - Add meaningful query tests for multi-set sessions, month boundaries, rake net, break-even, canceled/old snapshots, empty data, mixed units and cross-group access. Check query count to avoid per-player queries.

8. `docs(ui): record UI verification and sync design documentation`
   - Run final review against the user's eight fixes, four SVG deliverables and identity requirements. Review every page at 375/768 and key table/settlement layouts at 1280; confirm no overflow, keyboard focus, 48px targets, status text, reduced motion and native fallbacks.
   - Measure relevant color pairs rather than claiming WCAG from appearance; verify chip initials and small controls as well as text surfaces. Document any unresolved issue honestly.
   - Run the full SQLite suite, Django checks and PostgreSQL suite if available; report unavailable concurrency verification rather than treating SQLite as equivalent.
   - Compare models, migrations, money services and URL patterns to the baseline. Existing tests remain authoritative for buy-ins, rake, balance checks and transfers. New read-only stats tests must pass.
   - Follow Impeccable finish review and documentation roles where its instructions require them. Sync DESIGN.md, applicable .impeccable records, wiki, TODO and plan progress. Never edit SPEC.md.
   - Complete rendezvous within approved scope, retain small commits, no push or deployment. Final response lists changes, vocabulary, remaining uncertainties and local preview command.

## Acceptance criteria

- Same visual identity; blue diamond hero only while a set is running.
- Neutral empty/info cards; one next action; Sessions clearly separate from group management.
- Consistent vocabulary and visible money actions with 48px targets; no inaccessible focus or color-only state.
- Clear count discrepancy with the exact accepted value, without any accounting changes.
- Who pays whom, Still to pay/Settled and persisted Mark paid remain the settlement focus.
- Stats definitions above are visible and tested; pesos/chips are never combined.
- Four SVG assets, header and favicon render legibly with safe icon padding.
- Existing URLs, permission behavior, totals, rake and transfer semantics are unchanged. No dependencies added.
- All existing tests pass after each commit; final browser coverage and material limits are recorded.

## Assumptions and implementation questions

- Existing URL compatibility allows query parameters on the group page, without new route patterns.
- Stats measures closed sessions and profitable-session rate, rather than hands or unfinished play. Month uses the session's game date.
- Full light mode is deferred as outside the cheap-change allowance. Logos still support both backgrounds.
- Standalone SVG wordmark rendering requires a prototype because HTML webfonts/currentColor do not inherit through external images. Resolve it within existing assets and no added dependencies.
- The inspection baseline is 472 passing tests with 10 PostgreSQL-only skips; PostgreSQL was not run in Step 1.

## Approval checkpoint

AGENTS.md requires study => plan, then stop for human approval. agentic-workflow says: "Wait for an explicit human answer before starting Phase 2." This completed plan is the reviewable checkpoint. Approval covers execution, rendezvous and documentation sync for this cycle.

## Progress and blockers

2026-10-04: Human approved this plan with “approved” and three amendments, which override the text above where they differ:

1. **Recap behavior does not change.** The closing recap keeps opening as it does today. Step 6 drops “Make recap manually opened by default”.
2. **Stats ranking.** Stats list every player with at least one closed session. No minimum-session threshold and no seasons; those stay in Stage 3.
3. **Stats tab.** The tab appears only when it has real content: it is added in step 7, not as a placeholder in step 3.

Execution uses branch `feat/ui-evolution`, worktree `/private/tmp/pn-ui-evolution`. Baseline: 472 SQLite tests pass, ten PostgreSQL-only skips.

2026-10-04 execution: seven commits on `feat/ui-evolution`, each after the full SQLite suite and `manage.py check`.

1. `cdeaac7` tokens and shared components. 120 captures matched the baseline except running clocks.
2. `9f833fa` four SVGs, header mark and favicon. The wordmark is Archivo converted to outlines with a throwaway fontTools environment outside the repository; nothing was added to `requirements.txt`.
3. `cc9f5b9` Sessions and Group settings views on the group route. Management POSTs now redirect to `?view=settings#section`; seven tests that read roster, invite, preset or rake content from the group page now ask for the settings view.
4. `61512b8` vocabulary and row actions. Service messages and audit summaries say “set”; only strings changed in `games/services.py` and `ledger/services.py`. “Pesos game” and “chips game” are kept as the unit names used in AGENTS.md.
5. `9f15647` neutral non-play states, split bar removed, discrepancy panel. Two tests that pinned “>2<” and “0 of 0” were updated to the new presentation.
6. `cf474b2` settle-up cards and written Settled state. Recap behavior untouched (amendment 1); `static/js/` has no changes in this cycle.
7. `1d5655c` Stats view: `settlement.queries.group_stats()` and `stat_periods()`, 12 new tests. No minimum-session threshold (amendment 2). The tab shows once a closed session exists (amendment 3).

2026-10-04 verification: 498 SQLite tests pass (ten PostgreSQL-only skips); all 498 pass on a temporary PostgreSQL 17 instance, now stopped. System and migration-drift checks pass. `git diff main` shows no change to models, migrations or URL patterns. Browser: 135 captures over 62 screen states at 375 and 768px plus seven at 1280px on a synthetic fixture database; no horizontal overflow; no link, button or field under 44px outside the skip link; sampled text pairs from 7.33:1; the indigo felt appears only on running sets. CSS is 38,227 bytes; JavaScript is unchanged at 20,105 bytes.

Not verified: a physical phone, a screen reader, contrast of token initials on the ten player colours, and the no-JavaScript paths in a browser (the native forms are covered by server tests only). `.impeccable/design.json` lost its two slate colours; its component previews were not regenerated and one still shows a slate sample. No independent finish review was run in this cycle.

2026-10-04: Documentation synced: DESIGN.md (frontmatter, prose, addendum), PRODUCT.md addendum, five surface addenda, wiki features and architecture, roadmap, TODO.

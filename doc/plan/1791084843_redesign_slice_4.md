# Redesign slice 4: group, home, account, forms and log

Status: **in-progress**. Date: 2026-10-04.

Source: [slice 4 study](../study/1791084725_redesign_slice_4.md). Parent: [visual redesign task 10](1791046015_visual_redesign.md). Sources of truth: AGENTS.md, SPEC.md, PRODUCT.md, DESIGN.md and the wiki. Main was clean at `cd0d6e7`; study commit `efc5f16`. Baseline: 390 tests pass on SQLite.

## OPEN QUESTIONS

None blocking. This plan proposes input-retention repairs for the existing inline forms and the remaining canceled-set composition. They are part of the scope for approval. Approved by the human with “proceed” on 2026-10-04. Implementation, verification, rendezvous and documentation sync are authorized.

## Goal and direction contract

Finish the remaining Rack screens without changing accounting or access rules. The first phone screen on a populated group leads with sessions and the host's New session action. Management follows. A failed editable form keeps non-sensitive input and shows an error at that form. The log remains a complete, readable account of the set.

Keep the established Archivo, warm rails, indigo current-session emphasis, bone actions, brass focus, initial tokens and signed result icons. Operate mode for home, group, account and forms; Read mode for the log. This is the specified final extension of the approved world, not a new identity exercise. No new image assets or motion sequences.

## Scope

| Surface | Files and intended composition |
|---|---|
| Home | `templates/web/home.html`: group navigation rows and role labels first; creation section and meaningful empty state |
| Group | `templates/web/group.html`: current sessions, past sessions, management; native disclosures for secondary tools; alphabetic roster with initial tokens; remove accidental management markup from title block |
| Account entry | `templates/registration/login.html`, `templates/accounts/signup.html`: consistent narrow form frame, correct labels, password-manager attributes and safe next destination preserved |
| Invitation | `templates/groups/invite_accept.html`: join task and invalid/expired state with clear return path; preserve membership and token behavior |
| Supporting forms | `templates/games/session_form.html`, `preset_form.html`, `settings_form.html`, `add_players.html`, `templates/partials/form_fields.html`: shared heading/return/error/help patterns; picker search and selection behavior kept |
| Inline forms | Home creation; group table creation, roster add and member rename. Bound forms and failure rendering in `groups/forms.py` if needed, `groups/views.py`, `games/forms.py`, `games/views.py` and read-only page-context composition in `web/views.py` |
| Log | `templates/web/session_log.html`: labelled record sections, compact metadata, exact amounts, visible reversal/void explanations, signed final results; native section navigation if useful |
| Canceled set | Canceled branch of `templates/web/_session_legacy.html` and its entry point: Rack header, canceled reason, roster and log path; no final result or payment controls |
| Shared presentation | `templates/base.html`, `static/css/app.css`, `web/templatetags/table_tags.py` only as needed; scope selectors to avoid changing completed pages |

Inline form errors: use bound form validation for field shape, then existing services for business rules. Keep every editable field on refusal; show a field error only when it can be assigned accurately, otherwise a form-level error. Prefer immediate rendering of the bound form over persistent drafts. Each failure render must re-resolve current membership and rebuild authorized context. Do not consume or duplicate a one-time invite URL in the process. Keep successful redirects and existing service calls.

Roster token colour is derived from member ID within the existing ten-colour palette; visible roster order stays alphabetic. Initial collision handling uses the roster's members. Set and session token rules stay unchanged. Full names remain visible; colour is not an identity guarantee across views.

## Exclusions and dependencies

No service, model, migration, write/audit contract, permission, unit-conversion, finalization or settlement changes. No new history filters, exports, banker role, leaderboard, seats feature, password reset, deployment or external requests. Already redesigned active/count-up/review/final/night compositions are regression targets.

No changes to human-owned SPEC.md or unrelated sidecar drift. Product purpose and token palette stay fixed. The existing font, icons, pick.js and generic forms.js supply assets and enhancement. Use temporary synthetic browser data, not the development database. Physical-device verification is unavailable here and must be reported.

## Acceptance criteria

| ID | Observable result |
|---|---|
| AC1 | At 390 × 844, a typical populated host group shows its heading, an existing current session link and New session action in the first viewport. Empty/no-table states give the next valid action. Player view still hides draft sets and host tools |
| AC2 | Every remaining route uses the Rack composition described above. No form markup appears in the group document title. Management tools, past sessions and one-time invite link remain reachable |
| AC3 | Invalid group name, duplicate roster name, duplicate rename and invalid table seats retain submitted editable values and show a local error. The failing disclosure is open. Success performs the same service action once and follows the existing redirect |
| AC4 | Preset/session/settings field and service errors preserve bound editable values. Unit guidance and locked-unit behavior remain exact. Picker refusal retains eligible selections. Login/signup retain username and safe next target; passwords remain blank on refusal |
| AC5 | Log displays all prior record categories, exact units, actor/time/reason metadata, reversed and voided rows, and Final results with signs and icons. No grouping claims one global chronology. Payments remain linked to the session page |
| AC6 | At 320, 390 and 1,280 px, long names, error text, invite URLs and accepted maximum money figures fit without page overflow or clipped digits/units. Phone order remains one column; group desktop composition uses a session area beside management from 900 px when useful |
| AC7 | All tasks work with native forms/disclosures when JavaScript is disabled. Keyboard focus is visible, field labels and error/help associations are correct, actions have 48 px targets, and control/text contrast meets the parent 3:1/4.5:1 limits. Reduced motion remains static |
| AC8 | Canceled set shows the reason and retained records, with no invented result, join or money action. Active, count-up, final and session paid/Undo/recap flows remain unchanged |
| AC9 | Full suite passes on SQLite and PostgreSQL 17, including existing accounting assertions. Existing 133 browser checks pass plus the new remaining-screen flows |
| AC10 | No package/build/runtime dependency is added. CSS stays below 40,000 bytes; cumulative added redesign JS below 8,000 bytes; existing font below 150,000 bytes. Current JS baseline 7,771 bytes leaves only 229 bytes: target no added JS |

## Branch strategy and rollback

After approval, record the human answer and mark in-progress. Use an isolated `feat/visual-redesign-slice-4` worktree from current main. Preserve unrelated work. Commit focused units below, run tests before each commit, and merge to main after verification. Rollback by reverting this slice's commits; no database migration or data repair is involved. Do not push or deploy.

## Task board

- [ ] **1. Build remaining compositions and error retention.** Read Impeccable craft-floor immediately before UI edits. Implement the scope as one coherent working change. Reuse existing CSS patterns and native controls. Keep business rule validation in services. Add focused behavior tests for lost-input repair, scoped failure rendering and the malformed title regression; avoid tests that only mirror CSS classes.
  - Commit: `feat(web): recompose the group, forms and log screens`.
  - Done when AC1–AC8 have a working implementation and relevant behavior tests pass.
- [ ] **2. Verify and finish.** Run both database suites. Add a dependency-free browser harness/fixtures for the remaining routes and rerun the existing Rack, accessibility, end-set and night checks. Complete the bounded visual review below. Record criterion evidence, exact budgets and limitations here.
  - Commit: `test(web): verify remaining Rack screens`.
  - Done when AC1–AC10 have recorded results and the required finish handoff is resolved or the human explicitly accepts a remaining finding.
- [ ] **3. Rendezvous and sync docs.** Use the required documenter after the final correction, then update affected living docs. Merge to main, run the suite there, restart the development server if needed and verify it serves the merged CSS/pages.
  - Commit: `docs: sync completed Rack redesign`.
  - Done when main contains the slice, the server answers and docs describe verified behavior. Mark this plan and parent task 10 done only then.

## Verification matrix

- Django tests: SQLite before every commit; PostgreSQL for implementation completion. Preserve accounting assertions. Add behavior coverage for membership/host gates on error renders, editable-value retention, multi-field service errors, one-time invite display, canceled state and log completeness.
- Browser flows: sign in, refused sign in, signup failure/success and invite next destination; empty home → create group; group host/player; add table; create/edit presets in pesos/chips; new session and settings; add-player capacity/refusal; roster add/rename refusal then success; create/revoke/accept/invalid invite; canceled-set access; records including reversed buy-ins/cash-outs, overrides and final results.
- Native fallback: disable scripts and exercise creation, an inline error, picker selection and log navigation. Keyboard through account/group/forms; inspect focus, labels, described errors, disclosure expansion, pending submit state and long text.
- Regression: reset temporary fixtures as needed for the existing 20 Rack, 13 accessibility, 47 end-set and 53 night checks. Do not let mutating runs contaminate each other.
- Visual evidence: one batched capture round at 390 and 1,280 px, plus 320 px overflow edge states. Include home empty/populated, group host/player/empty/error/invite, account error, invitation invalid, representative supporting forms, picker, long/reversed/final log and canceled set. Validate and open every capture before review. Measure contrast for any new token pairing, targets and overflow against requested viewport width.
- Run Impeccable detector once over changed targets. Spawn a fresh finish reviewer with no inherited conversation and a complete packet: request, this plan, direction contract, valid captures, craft-floor and detector findings. Apply all material findings in one batch and use at most one confirmation round, then request the same reviewer's verdict on those fixes. Follow the skill's special recapture/rebuild rules only for those dispositions. Do not resume an independent polish hunt.
- Spawn the Impeccable documenter after final correction with a restricted documentation boundary. Preserve machine tokens unless an approved durable change requires them; report unrelated pre-existing drift.

## Documentation sync

DESIGN.md: add built group, home, account/form and log patterns; remove deferred-composition claim once true. Surface briefs: record these patterns as incumbent, with mode per surface. Update wiki README/journal, features, architecture if the failure-render flow warrants it, roadmap, TODO and parent plan. Add a footgun only for confirmed behavior requiring a remedy. PRODUCT.md and AGENTS.md only if the actual outcome changes their facts; no changes expected. Studies remain immutable.

## Blockers and progress

No blocker. Approved with “proceed”.

Implementation choice: inline errors use one-redirect, form/group-scoped session drafts rather than importing web page composition into groups or games. Only declared non-sensitive fields and validation errors are stored; the destination re-resolves membership, consumes the draft once and opens the failed disclosure. This preserves dependency direction and successful redirects.

| Date | Entry |
|---|---|
| 2026-10-04 | Source study completed and committed. SQLite baseline: 390 tests pass in 13.293 s. This plan awaits approval; no implementation started |

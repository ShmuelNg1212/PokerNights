---
version: 1
slug: "templates-accounts-supporting-forms"
primary_target: "templates/registration/login.html"
related_targets: ["templates/accounts/signup.html", "templates/groups/invite_accept.html", "templates/games/session_form.html", "templates/games/preset_form.html", "templates/games/settings_form.html", "templates/games/add_players.html", "templates/partials/form_fields.html", "static/css/app.css"]
---

# Account, invitation and supporting forms — The Rack

Mode: Operate. Scope: approved slice 4 extension; human approved “proceed” on 2026-10-04. The existing Rack is the visual authority.

## Direction contract

THESIS: Make one native form task clear and keep the person’s editable values when the server refuses it.

OWN-WORLD: Warm ground, Archivo, existing fields, bone confirmation and brass focus. No new hero, imagery or motion.

STORY: Identify the task, enter labelled values, confirm and read local errors or follow the accepted redirect. Return and alternate-entry paths stay reachable.

FIRST VIEWPORT: A compact heading and context precede a narrow form. Login/signup offer alternate entry; invalid invitations show an explanation and a group return path.

FORM: 600px container with 28px top inset and explanatory prose up to 65ch. Return/alternate links have 48px targets. Label, help and error IDs remain associated with controls. Distinct inline forms have separate auto IDs. Native forms, details and checkboxes remain usable without JavaScript.

FINISH: Ordinary anchor targets were one of the reviewer’s two fixes and are cleared by the bounded ship verdict.

## Built behavior

Login/signup preserve username and safe next destination with password-manager attributes; refused password fields are blank. Supporting forms keep bound field and service errors beside retained editable values, including exact unit/locked-unit guidance. Player selection retains eligible refused selections and existing search/capacity behavior; no new picker script is introduced. Server-scoped inline drafts apply to home/group forms only, carry declared non-sensitive fields and errors for one redirect, and never store passwords or invitation tokens. Refusal does not show success.

## Evidence and boundaries

Read AGENTS.md, PRODUCT.md, incumbent DESIGN.md, the document reference, approved plan `doc/plan/1791084843_redesign_slice_4.md`, finished source and the fresh review/confirmation verdict. The first review requested two material fixes: move New session ahead of the long list and enlarge ordinary action anchors to 48px targets. Both are resolved in `/private/tmp/pn4-finish-verdict.md` with disposition ship. That verdict covers those fixes, not a new whole-surface audit. All 45 overwritten captures in `/private/tmp/pn4-review/` were reopened and valid by the reviewer. The documenter inspected the final populated group phone, desktop log and canceled phone captures, and did not perform another polish round.

Coordinator evidence reports 395 tests passing on each of SQLite and PostgreSQL, and 250 passing browser checks including the 133 existing regressions. CSS is 32,201 bytes, cumulative added redesign JavaScript 7,771 bytes and the existing font 103,912 bytes. No new JavaScript, motion sequence, raster asset, token or dependency ships in this extension. Physical-device verification is unavailable; the initial reviewer inspected voided-override and reversed-cash-out branches in source without visual captures for those states.

DESIGN.md machine frontmatter, `.impeccable/design.json`, config, PRODUCT.md and AGENTS.md are preserved. Pre-existing sidecar freshness/narrative drift is not repaired by this prose-only sync. The slice 1 surface contract still states 76px phone total / 27px phone timer and blinds, whereas incumbent DESIGN.md and the finish-reviewed implementation use 64px / 22px (16px chips blinds); that historical drift is preserved. Earlier surface briefs retain their slice-local deferred boundaries as historical scope.

## Dated addendum — 2026-10-04: add a player during play

Mode: Operate. This narrow extension follows the approved `doc/plan/1791091385_add_player_during_play.md` and inherits The Rack. The host’s Add players entry in `templates/web/_players.html` remains available during setup, open and running play even when the roster is exhausted. `templates/games/add_players.html` keeps roster selection and its search enhancement, adding a separate native Player name form. The explanation makes group-roster persistence and separate buy-in explicit. The form uses incumbent fields and bone confirmation; it adds no CSS, JavaScript, tokens, assets or motion.

Names remain bound on refusal with attached error text. Seated duplicates direct the host back to the set; eligible duplicates direct them to the roster picker. Capacity and ended-state explanations keep recovery readable: full tables disable confirmation, ended sets disable the new-name fieldset and omit roster submission, and Back to the set remains available. Accepted late arrivals return to the set with the ordinary manual buy-in action; joining records no money.

The documenter inspected `/private/tmp/pn-late-review/late-picker-390.png`, `late-picker-1280.png` and `late-duplicate-390.png`. Phone and desktop captures show the incumbent narrow task frame, a labelled name field, full-width confirmation and explicit exhausted-roster text. The duplicate capture retains the typed name and displays seated-player recovery in the alert and local field error. `/private/tmp/pn-late-review/late-player.json` reports all 21 dedicated browser checks passing, including no-JavaScript creation, no overflow at both widths, 48px labelled confirmation, independent buy-in, existing roster selection, full/ended recovery, roster persistence and live arrival. Physical-device verification remains unavailable.

The finish reviewer’s sole material fix was duplicate guidance that had sent a seated player toward roster selection. The coordinator reports that fix resolved on recapture with disposition ship; service source now distinguishes seated and eligible identities, and the inspected phone recapture confirms the seated branch. This records the bounded review, not a new whole-product audit. DESIGN.md frontmatter and `.impeccable/design.json` remain unchanged; pre-existing sidecar freshness/narrative and historical slice-token drift described above remain unrepaired. No new drift was found in these three captures.

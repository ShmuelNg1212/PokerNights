---
name: "PokerNights — The Rack"
description: "A warm, tactile system for recording a home poker game at a glance."
colors:
  ground: "oklch(0.17 0.012 60)"
  rail: "oklch(0.215 0.014 60)"
  rail-2: "oklch(0.265 0.016 60)"
  line: "oklch(0.55 0.018 60)"
  rule: "oklch(0.33 0.018 60)"
  bone: "oklch(0.93 0.025 85)"
  bone-dim: "oklch(0.74 0.028 80)"
  ink: "oklch(0.19 0.02 60)"
  felt: "oklch(0.34 0.095 265)"
  felt-deep: "oklch(0.25 0.08 265)"
  felt-ink: "oklch(0.86 0.04 265)"
  brass: "oklch(0.82 0.13 85)"
  up: "oklch(0.82 0.13 160)"
  down: "oklch(0.76 0.14 25)"
  c1: "#9e3038"
  c2: "#285aa8"
  c3: "#267449"
  c4: "#e4bd48"
  c5: "#82409b"
  c6: "#d48d48"
  c7: "#70b9bd"
  c8: "#dd86a1"
  c9: "#b4b1a6"
  c10: "#524b9a"
  danger-bg: "oklch(0.24 0.035 25)"
  warn-bg: "oklch(0.26 0.03 85)"
typography:
  display:
    fontFamily: "Archivo, ArchivoFallback, system-ui, sans-serif"
    fontSize: "4rem"
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: "-.02em"
  headline:
    fontFamily: "Archivo, ArchivoFallback, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 700
    lineHeight: 1.2
  title:
    fontFamily: "Archivo, ArchivoFallback, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 650
  body:
    fontFamily: "Archivo, ArchivoFallback, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 500
    lineHeight: 1.45
  label:
    fontFamily: "Archivo, ArchivoFallback, system-ui, sans-serif"
    fontSize: ".75rem"
    fontWeight: 500
  amount-input:
    fontFamily: "Archivo, ArchivoFallback, system-ui, sans-serif"
    fontSize: "2.5rem"
    fontWeight: 750
rounded:
  surface: "1rem"
  button: "15px"
  field: "10px"
  sheet: "26px"
  pill: "999px"
  circle: "50%"
spacing:
  field-gap: "12px"
  page-inset: "16px"
  desktop-gap: "28px"
components:
  button:
    backgroundColor: "{colors.rail-2}"
    textColor: "{colors.bone}"
    rounded: "{rounded.button}"
    padding: "0 18px"
    height: "48px"
  button-primary:
    backgroundColor: "{colors.bone}"
    textColor: "{colors.ink}"
    rounded: "{rounded.button}"
    padding: "0 18px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "oklch(0.99 0.01 85)"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.bone}"
    rounded: "{rounded.button}"
    padding: "0 18px"
    height: "48px"
  button-danger:
    backgroundColor: "{colors.danger-bg}"
    textColor: "{colors.down}"
    rounded: "{rounded.button}"
    padding: "0 18px"
    height: "48px"
  input:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.bone}"
    rounded: "{rounded.field}"
    padding: "8px 12px"
    height: "48px"
  card:
    backgroundColor: "{colors.rail}"
    textColor: "{colors.bone}"
    rounded: "{rounded.surface}"
    padding: "14px"
  badge:
    textColor: "{colors.bone-dim}"
    rounded: "{rounded.pill}"
    padding: "2px 10px"
  sheet:
    backgroundColor: "{colors.rail}"
    textColor: "{colors.bone}"
    padding: "16px 20px 24px"
    width: "min(100%, 440px)"
---

# Design System: PokerNights

## Overview

**Creative North Star: "The Rack"**

The Rack turns the bank into a legible working surface: warm near-black rails, indigo felt, bone controls and brass attention. Compressed Archivo figures provide a strong numeric hierarchy; circular initial tokens and small chip edges help the host find a player during a short glance.

The system is dark, compact and tactile, suited to a dim room and one-handed use. This record captures the built shared foundation, active set and sheets, end-of-set flow, session settle-up and closing recap, group and home navigation, account and supporting forms, readable set log and canceled set. The approved HTML/CSS study and slice 2–4 plans supply the visual authority. The final extension uses ordinary task lists and management rails for operation, and quieter record sections for reading. The build ships no raster imagery.

**Key Characteristics:**
- Warm dark rails and indigo felt.
- Compressed, tabular figures with right-aligned player amounts.
- Bone pressable controls and visible brass focus.
- Circular initials paired with written player names.
- Compact phone rows, focused sheets and persistent inline count fields.

## Colors

The palette combines warm dark supports with a cool indigo working field and pale tactile controls. Frontmatter preserves the stylesheet's canonical colour formats; CSS aliases resolve to these primitives.

### Primary

- **Bone:** primary actions, strong figures and readable foregrounds.
- **Indigo Felt / Deep Felt / Felt Ink:** the active-set field, its supporting palette and readable secondary labels.
- **Neutral lead panel (Rail with Bone Dim labels):** every state that is not in play: draft and open sets, count-up, cash-out review, final results and the session overview. Indigo felt and its diamond texture mark only a running set.

### Secondary

- **Brass:** attention and focus, including stale data and accepted changes.
- **Up / Down:** positive and negative results, with signs, icons or written status.
- **Warning / Danger backgrounds:** subdued supporting surfaces for messages.

### Tertiary

- **Player colours (c1–c10):** the ten recurring chip identities. Initials and names remain essential; lighter chips use dark ink. These colours do not encode financial status.

### Neutral

- **Ground:** page and field background.
- **Rail / Rail 2:** containers and secondary controls.
- **Rule / Line:** quiet row separators and stronger control boundaries.
- **Bone Dim:** secondary text and stale figures.
- **Ink:** text on light controls.

**The Attention Rule.** Use brass for keyboard focus, stale status and accepted changes; pair status colour with words or another visible cue.

## Typography

**Display and Body Font:** Archivo, with ArchivoFallback, system-ui and sans-serif fallbacks. The local variable face supports weights from 100–900 and widths from 62%–125%.

The same family shifts from ordinary-width reading text to compressed figures. The body role is normative in frontmatter; smaller labels make room for names and amounts without turning the entire interface into display type.

- **Display:** the active “Still in play” figure uses the display role, compressed to 70%. Its implemented size is 64px, including desktop; the earlier study's 76px target is superseded by the finish-reviewed build.
- **Headline:** the felt heading is compressed to 88%; the phone line height is reflected in frontmatter.
- **Title:** player names; section and sheet headings have their own observed contextual sizes rather than a fabricated universal scale.
- **Body:** ordinary-width text and controls.
- **Label:** player metadata. Felt labels, split labels and connection status have contextual smaller sizes.
- **Amount input:** the sheet entry is compressed to 80%, with a minimum height of 72px.

Count-up progress uses a compressed 48px tabular numerator with a 28px denominator. The viewer’s frozen result uses a responsive 32–52px figure at 70% width; result rows use 22px at 85% width, reduced to 18px below 360px. These contextual figures preserve the shared family without introducing another universal display role.

The session’s closed “Still to pay” figure reuses the 64px display role. Its complete formatted value stays on one line: formatted lengths above 10 use 32px, and above 17 use 24px. These session-scoped content adaptations preserve currency, grouping, precision and the chips unit without abbreviation. The session viewer result uses 32px at 80% width; transfer amounts use 28px, with content-length adaptations, and aggregate result rows use 22px. Recap facts use 22px below 14px labels.

The timer and blinds use 70% width, weight 800 and line height 1.2. On phones they are 22px; chips-game blinds are 16px. At desktop they are 27px. They are supporting figures, not a second display role.

**The Figure Rule.** Keep money and timers tabular. Use compressed display figures for the active total and quieter right-aligned amounts in player rows.

## Layout

Shared pages are centred in a 560px container with a 16px inset. The active-set page extends to 1180px. Phone composition stays in one column: felt overview, compact player list and an opaque bottom host dock. Bottom clearance is 128px; the dock accounts for the safe area and can scroll when expanded. An open set with the opening-buy-in option reserves 340px below 900px so the enlarged dock clears the player list.

The overview has a flexible amount column and a 116px supporting column, separated by 8px. Player rows align a 44px identity token, flexible name, right-aligned amount and action. Below 360px, the token becomes 36px and the row gap becomes 6px.

At 900px and above, the active-set layout becomes a 400px left column plus flexible player list, with a 28px gap and 28px page insets. The left column sticks below the header at 90px. The host action returns to the document flow and rebuy controls display their written label.

Count-up, review and final pages inherit the 1180px table container and the 400px-plus-flexible two-column layout from 900px. On phones, count-up orders the neutral overview, all inline player counts, then the balance check; the host dock remains fixed with visible next-step guidance and a 48px “More host controls” target. Count-up reserves 200px bottom clearance, increased to 370px when the host's count-total dock is present; count fields retain 90px top / 200px bottom scroll margins. The confirmed count total stays in the neutral overview while the local preview sits before the dock's next action. At desktop both remain in the left overview/control column. Review and final pages reserve 48px at the bottom and keep actions in document flow. Below 360px each count button stacks at full width beneath its input. End-set and review containers, names and figures wrap anywhere to contain long unbroken names and large amounts.

The session page inherits the 1180px table container and remains one column on phones. From 900px it uses a 400px overview/action column and flexible detail column with a 28px gap. Its document order is task summary, closed-session transfers, aggregate results, sets and payment records. Actions stay in document flow with 48px bottom clearance; detail sections have 32px separation. Transfer cards query their list’s available width. Below 440px, or without container-query support, each identity occupies a full-width row joined by a downward arrow and “pays.” From 440px, two flexible identity columns surround a rightward arrow and “pays.” The 32px tokens and direction start at the first name line. The financial grid places amount above state; narrow host cards give the amount a full row, then state left and action right. Wide host cards reserve a right action column spanning both financial rows. Player and archived cards have no action column. Full names and result rows can wrap while the primary Still to pay value remains intact.

Home navigation uses a 760px container and 76px-minimum group links with role labels; creation follows the list. Group pages lead with sessions on phones, with the host’s New session above the current-session list. Past sessions precede tables, presets, roster and invites. From 900px, the group container expands to 1180px and uses flexible session/management columns in a 1.25:1 ratio, a 48px gap and a management rail with 28px left inset. These actions stay in document flow.

Account, invitation and supporting forms use a 600px container with 28px top inset; explanatory prose is bounded at 65ch. The log uses an 850px container, wrapping section links with 48px targets, 16px vertical record padding and 96px heading scroll clearance. Names and explanations wrap while record amounts retain their full formatted value.

Sheets are at most 440px wide and 85dvh tall, scrolling internally. They sit against the phone's bottom edge and become centred at desktop. Quick amounts occupy four equal columns with an 8px gap. Shared form stacks and field gaps use the spacing values in frontmatter; there is no additional invented spacing scale.

## Elevation & Depth

Depth comes from tonal rails, fine rules and CSS-built felt grain. Buttons have a short solid underside that disappears on press. Sheets and the host action use stronger shadows to separate them from the working surface; ordinary cards remain flat.

The sidecar records the built shadows, timings and easing curves. Sheet entry moves 24px in 320ms; exit takes 200ms. Accepted-change attention uses a 600ms treatment and remains labelled briefly. Chip-edge entry accompanies a confirmed rebuy. Reduced-motion preferences suppress animations, transitions and button displacement.

The balanced-books message uses a green double rule with a 5px band and one-pixel top and bottom strokes. In count-up, only the existing balanced state makes it eligible for a 600ms left-to-right reveal. A localStorage marker records the set per browser, keeping reloads and later polls static; unavailable storage leaves the rule static. Final results use the static rule. Reduced motion suppresses the reveal while keeping its message.

The closing recap reuses the shared sheet. Its fact lines reveal with a 360ms clip, staggered by 60ms, finishing within 540ms for four lines. Reduced motion leaves them static; accepted money appears immediately without a count animation. Automatic opening is consumed once per session and signed-in viewer in each browser, before opening; manual reopening remains available. Storage failure suppresses only automatic opening.

**The Accepted Change Rule.** Recorded figures change only to accepted server values. A separately labelled local count preview may update directly from unsaved input; it never presents that input as recorded money. Highlight accepted changes without interpolating the amount. The count preview adds no movement.

## Shapes

Rounded rails and controls give the surface a tactile character. The normative radii live in frontmatter: surface, button, field, sheet, pill and circle. Sheet corners are rounded only at the top on phones and all around at desktop. Felt uses the same 26px curve, with bottom-only corners on phones. Player rows use 12px corners; the money-split track uses 4px corners.

Identity chips are circles with CSS radial and conic bands. Rebuy count edges are short striped bars, not photographs or exported illustrations. Dividers and control borders are one pixel; invalid fields use a two-pixel negative-colour border.

## Components

### Buttons

Confident, pressable actions. Shared buttons have a minimum 48px target, medium-heavy text, a visible boundary and a short underside. Primary actions use bone on ink; secondary actions use Rail 2; quiet actions are transparent; danger actions pair a subdued danger surface with Down text and border. Hover lightens the control. Press moves it 3px and removes its shadow; reduced motion removes that movement. Disabled controls fade to 55%; busy controls use brass text over Rail 2. Keyboard focus has a three-pixel brass outline with a two-pixel offset.

### Inputs / Fields

Dark fields with clear boundaries and visible brass carets. Shared fields use the field radius, 48px minimum height and the padding in frontmatter. Amount sheets enlarge the entry and retain an explicit unit label. Invalid state uses the Down border and explanatory text. Quick amounts fill the entry and return focus to it.

### Cards / Containers

Rail surfaces with a Line boundary, the shared surface radius and 14px padding. They do not receive a generic floating-card shadow. The indigo felt overview is a signature active-set container with CSS-only grain; it is not a replacement for every shared card.

### Chips

Player identity circles carry initials and are paired with written names. Pale player colours use Ink text, other colours use white. Buy-in counts also have written metadata alongside the small striped edges.

### Navigation

The shared header stays at the top with Rail background, a bottom Line boundary and a strong written brand. The active-set back link and live status share a compact bar. Connection state has a dot and written status; stale values become Bone Dim and status becomes brass.

### Badges

Compact outlined pills mark state. Live state uses bone and ink; warning and positive variants use the corresponding status colours. Confirmed row changes display “Rebuy added” or “Updated” alongside the attention treatment.

### Player rows

Names and metadata form a single 48px-minimum detail target. Amounts form a separate right-aligned column. Buy-in or Rebuy and Cash out are written buttons at every width: side by side under the name on phones, beside the amount from 900px. Cash-out state and departed-player state remain written.

### Start controls

An open set places a checked native option immediately before Start the set. Its 48px-minimum label shows the current usual amount in the session’s unit and says it applies to players without a buy-in; adjacent help says existing buy-ins stay unchanged. Unchecking opts out for that start, and live updates retain the choice. The native form records missing opening buy-ins on accepted start before the timer begins. The control reuses the shared checkbox, focus and primary-action treatment.

### Count-up

A quiet neutral overview shows “N of M players ready or cashed out,” separate awaiting/ready/cashed-out counts, total bought in, recorded cash-outs and the stopped set timer. Only players with buy-ins contribute to N and M; earlier partial cash-outs alone do not complete a player. Inline rows pair player tokens and names with bought-in figures, written state and a labelled final-count input. Every host input and count button belongs to one shared form: a row button confirms every typed count, zero is valid and empty fields are skipped. Confirmed counts remain written above draft fields; no provisional net result appears. Players see read-only state. Corrections and exceptions remain in native details. Polling retains drafts and focus.

The overview's “Confirmed counts” block compares remaining confirmed stacks plus accepted cash-outs against total bought in, with an exact accounted amount and written count coverage. A quiet rule separates it from the overview facts. The host dock repeats this compact equation; entering a draft changes its heading to “Preview · unsaved counts” and immediately updates its tabular figures. Accounted amounts use a supporting figure (18px), beneath a short heading (14px), rather than another display total. Both blocks inherit the shared palette and wrap long amounts; no new card, token or asset is introduced.

Each eligible remaining player contributes a valid draft or, when blank, their confirmed count. Zero counts; earlier partial cash-outs contribute once alongside the remaining stack. Final cash-outs contribute only through accepted cash-outs. Written missing/extra amounts stay beside “still to count” coverage. A complete match requires every required count, valid drafts and eligible records; an empty ledger does not claim a match. Invalid input marks its field and makes the preview unavailable. Overrides are explicitly excluded from this stack check. Read-only and no-JavaScript views retain the confirmed baseline; polling recomputes the host preview after restoring drafts. The preview creates no cash-out or finalization gate.

The dock opens review when confirmed counts are ready, offers finalization when the books balance, and otherwise explains the next step. Count confirmation stays at the form. Pending cash-outs remain ordinary progress; completed discrepancies carry an error explanation and existing override controls.

### Cash-out review

Neutral-panel totals separate “Total of this batch,” “Recorded cash-outs,” prospective “After this batch” and “Total bought in.” A fixed-layout table pairs initial tokens and wrapping names with right-aligned exact confirmed cash-out amounts. The player column occupies 56%; the batch total has a footer row. A drawn back arrow accompanies the written set link. Awaiting and already-cashed-out lists remain separate. Written guidance states that this action records cash-outs without finalizing or marking payment; stale reviews retain an error and fresh values.

### Final results

The neutral overview gives the viewer’s frozen signed result prominence when present. Result rows pair tokens and wrapping names with signed right-aligned amounts and direction icons; a written Final tag marks the section. Facts list buy-in count and total, cumulative cash-outs, any override and recorded time played. Snapshot values supply the results. Override disclosure remains written, and the session link explains where the next set or settle-up belongs. Set-level transfers and payment controls are absent.

### Session overview and settle-up

The open-session neutral overview leads with the current set action and the viewer’s result so far when a standing exists; it explains that transfers follow closing. Close and next-set actions retain their service gates beside that task. A closed session uses slate, an intact Still to pay figure, written settlement status, amount-based progress and a separately labelled paid-transfer count. Remaining and paid sums use exact integer transfers; zero transfers show “Nobody owes anything” without a progress denominator.

Transfer rows pair payer and payee identity tokens with full names, “pays,” an exact amount and Paid / Not paid text. Identities adapt at 440px of actual card width, including the 416px desktop detail column at a 900px viewport. Named grid areas fix amount, state and action positions. Financial rows align at their top edges; timestamps grow below the badge. Figures stay on one line: the base is 28px, formatted lengths above 10 use 22px narrow / 28px wide, and above 17 use 18px narrow / 22px wide. Currency, digits, decimal precision and the chips unit remain complete. Paid includes its recorded time and “marked by the host.” Host Mark paid and Undo are native POST actions. The session identity order follows first appearance in aggregate standings and keys tokens by member; it need not match a set’s colour order. Payment records retain recorder and undone status, with struck text for reversed records.

Aggregate results remain separate from transfers and payments, using frozen finalized-set values, signed figures and direction icons. Closed results carry Final; open results say “Over finalized sets; session still open.” No-finalization state is explicit. A viewer without a standing receives no invented result. Sets retain number, written state and known timer values; the existing “Play time over all sets” line is distinct from the recap’s finalized-only duration.

### Closing recap

A closed session offers “View session recap” and inline facts when dialog enhancement is unavailable. Recorded play time sums known finalized-set durations only, says Not recorded when none are known and labels partial sums. Total bought in explicitly covers current finalization snapshots across finalized sets, independent of transfers. Top session result names every tied highest positive standing; all-zero results say Everyone broke even. Your session result appears only for a viewer with a standing.

The browser key includes session and signed-in viewer. Automatic opening happens once per key and is consumed before opening; storage refusal leaves manual access. Close, Escape and backdrop dismissal preserve native modal keyboard navigation and return focus to the manual trigger. No JavaScript leaves recap facts and every native form in the document. The recap inherits shared focus, target, sheet geometry and reduced-motion behavior.

### Group and home navigation

Home shows one block per group that reports its state (see the home addendum below). A newcomer gets a focused first-group screen with the mark, the create form and a line about invite links. The group’s current sessions are neutral rows; the host’s bone New session action precedes the list. Without tables, the page gives the table-creation prerequisite. Past sessions and management use ordinary rules and rail sections. Native disclosures contain table creation, member management and roster additions; host-only actions retain their gates.

The alphabetic roster pairs full names with initials, Host / No login labels and native management controls. Roster chip colour derives from member primary key within the ten-colour palette; collision handling uses roster peers. Set join order and session standing order retain their own token rules, so colour does not promise identity across those views. The one-time invite URL remains a labelled read-only field.

### Account and supporting forms

A narrow task frame uses an explicit heading, return or alternate-entry path, labelled fields, attached help and local error text. Field errors use the negative boundary; form errors remain at the form. Login and signup preserve username and the safe next destination while refused passwords remain blank. Invitations offer the join task or a written failure with a group return path. Session, preset and settings forms retain bound editable values and exact unit guidance; the native player picker preserves eligible refused selections and existing search enhancement.

The host’s Add players entry remains beside the player-list heading in setup, open and running sets, including when every roster player is seated. The picker pairs a separate native Player name form with the existing roster selection. Its help explains that a new name stays on the group roster and joins this set; buy-in is recorded separately. Refused names remain bound with local errors. A seated duplicate directs the host back to the set; an eligible duplicate directs them to roster selection. A full table explains the unavailable add actions, while an ended set shows its current state, disables adding and retains the return path. This extension inherits the existing field, button, focus and responsive task-frame treatment.

Home creation, table creation, roster addition and member rename retain non-sensitive declared fields and their errors for one redirect, scoped to the destination form and group/member. The destination consumes the draft once, re-resolves membership and opens the failing disclosure. These are server-session drafts, not browser autosave. Inline forms have distinct field IDs. Shared fields associate help and errors with their control, and refused input never produces a success state.

### Set log and canceled set

The reading surface groups play periods, players, settings versions, buy-ins, cash-outs, balance overrides, frozen final results and audit events under written headings. Native section links jump to the principal categories; the page makes no single global chronology claim. Exact amounts remain tabular, actor/time/reason metadata stays visible, reversed entries remain struck with explanations and voided overrides retain their removal information. Final results carry a Final label, revision metadata, signs and direction icons. Payment records and who pays whom are linked to the session page.

A canceled set uses the warm rail vocabulary, written Canceled state, recorded reason, roster and Full set log path. Its copy explains that retained money records remain in the log and that the set has no final result. No join, money or final-result action appears.

### Sheets

Focused buy-in and player-detail tasks use a native modal dialog outside the polling region. The close control, Escape and outside click close it; keyboard focus stays within the dialog and returns to the opener. Typed values persist during updates; refused submissions reopen the matching form with the exact values and an error. Native details and forms provide the fallback when sheets are unavailable.

### 2026-10-04 addendum — rake facts

This approved Operate extension inherits The Rack. Native set settings append labelled Off / Percentage / Flat amount controls, per-buy-in deduction help and local errors inside the existing task form. Accepted money disables the rule fields with a written reason. Buy-in help repeats the agreed rule without adding a client fee calculator.

The active overview places Collected rake and Available to play below the gross/cash-out split in the existing definition-list treatment. Count-up and cash-out review reuse those facts on the neutral panel; the confirmed total and unsaved preview add accepted rake once to their equation. Final results retain gross buy-ins, playable value, frozen rake and signed after-rake results. Session overview and recap use existing fact rows and explanatory prose to distinguish those results from remaining payments; an all-negative rake-only result says No positive result after rake. The group page adds a quiet Group rake account rail after past sessions, with separate peso/chip totals and a native session/set breakdown disclosure. Settings versions, buy-in records and reversals retain rule and exact fee/playable provenance in the existing reading surface.

No shared token, CSS, motion, raster asset or dependency is introduced. The incumbent phone/desktop topology, Archivo hierarchy, exact unit formatting, focus and 48px actions are reused. DESIGN.md frontmatter and `.impeccable/design.json` are preserved. Pre-existing drift remains: the first active-set contract gives 76px phone totals / 27px clock and blinds, while the finish-reviewed build uses 64px / 22px (16px chips blinds); the sidecar narrative still describes the earlier slice-2 scope and predates the labelled local count preview. This extension does not repair those historical records.

### 2026-10-04 addendum — rake setup controls

New session and Game settings now share a native Rake per buy-in fieldset with Off, Flat amount and Percentage of buy-in radios. Off is selected on creation. The existing check-row treatment gives each written radio label a 48px minimum target and the radio a 22px control with the shared accent. The borderless fieldset uses a 16px top inset and 12px value-field gaps within the incumbent narrow task frame. Both flat and percentage text fields remain visible with decimal keyboard hints; adjacent help says only the chosen option applies. Only the selected value can refuse submission, and local error text retains the chosen radio and both typed values. No script or fee calculator is added.

An empty set places Choose rake before buy-ins in the ordinary host-action stack before opening-buy-in and start controls. Accepted money disables the radios and both value fields; written help explicitly includes default opening buy-ins and gives the next-set recovery path. Other stakes and Save settings remain available. This bounded Operate extension reuses The Rack palette, Archivo hierarchy, focus, reduced-motion behavior and phone/desktop topology. CSS only extends the native-control treatment and fieldset spacing; frontmatter tokens and `.impeccable/design.json` remain unchanged. The historical token/sidecar drift recorded above remains unrepaired.

### 2026-10-04 addendum — UI evolution

The Rack identity is kept: warm near-black, bone, Archivo, hard button shadows, pill badges, chip tokens, condensed amounts, quick amounts and green winnings. [Plan](doc/plan/1791098885_ui_evolution.md).

- **Tokens.** One `:root` block holds colours, a spacing scale (`--s-1` 4px to `--s-6` 32px), radii (`--r-bar`, `--r-field`, `--r-row`, `--r-btn`, `--radius`, `--r-sheet`, `--r-pill`), button shadows, the money width and the 48px target. Slate is removed.
- **Felt and hero.** `.felt` alone is the indigo diamond field for a set in play. `.felt.hero` keeps its layout on Rail with a Rule border for every other state.
- **Notices.** `.notice-info` is neutral for information and waiting; the default notice is a brass warning; `.notice-bad` is an error; `.notice-good` is success. A completed mismatch uses `.discrepancy`: a danger panel that leads with the signed amount at 2.5rem.
- **Panel and empty state.** `.panel` is the neutral card. An empty state is a panel with a heading, one sentence and one action.
- **Tabs and pills.** `.tabs` is a segmented control of ordinary links with `aria-current`; `.pills` are filter links. Both keep 48px targets and work without JavaScript.
- **Row actions.** `.player-actions` holds labelled Buy-in/Rebuy and Cash out buttons. Cash out has its own sheet and native fallback.
- **Transfers.** Each transfer is a panel: tokens and names, an arrow with the word “pays”, the amount at 1.75rem, a written state and a Mark paid or Undo button at least 124px wide. A fully paid session shows a green check and “Settled”.
- **Stats.** Rows show rank, token, name, “N sessions · won N · N% win rate” and a signed amount with a direction icon. Definitions sit in a panel under the list.
- **Branding.** The mark is a bone chip with six ink notches and a brass crescent on an ink disc, so it reads on near-black and on cream. `logo-horizontal.svg` adds the outlined Archivo wordmark in bone; `logo-mono.svg` is ink only; `app-icon.svg` centres the mark at 62% on a full square. No raster files.
- **Measured.** 135 captures at 375, 768 and 1280px: no horizontal overflow, no link, button or field under 44px, and sampled text pairs from 7.33:1 upward. Token initials on the ten player colours were not measured.

### 2026-10-04 addendum — Your groups home

Each group on the home page is an unboxed block separated by a Line rule, not a card. [Plan](doc/plan/1791102439_your_groups_home.md).

- **Head.** Group name at 1.75rem, weight 800, width 88%, linking to the group; the role badge; up to six overlapping 36px tokens ringed in Ground, with the player count in words.
- **Status band.** The one surface in the block, radius 26px. A set in play uses `.felt` with an In play badge, “N at the table · timer”, and a bone Open the table button. Every other state uses Rail with a Rule border. The band holds the single action for the viewer; a player in a quiet group gets none. Money still in play is never shown here.
- **To settle.** A brass heading over ruled rows that link to the session: “You owe **Name**” with the amount in Down, “**Name** owes you” in Up. At most three rows, then a count of the rest. Shown only to the person concerned.
- **Facts.** Ruled rows for Your record (per unit, with sessions and wins) and Last session, with signed amounts and direction icons.
- **Links.** Sessions, Stats and Group settings as quiet 48px text links.
- **Create a group** is a closed disclosure under the groups and opens when its form has an error.
- From 900px, two or more groups use two columns; one group keeps a 560px frame.
- **Measured.** 16 captures over four viewers at 320, 375, 768 and 1280px: no horizontal overflow, no target under 48px, new text pairs from 7.58:1, felt present only with a set in play.

### 2026-10-04 addendum — Collapsible host dock

Below 900px a host can fold the host dock to one bar and open it again. [Plan](doc/plan/1791111069_collapsible_host_dock.md).

- **Toggle row.** The first row of the dock is a full-width 48px button. Expanded, it reads “Host controls” at weight 700 with a muted chevron pointing down; the dock content follows unchanged.
- **Collapsed bar.** Only the toggle row is rendered: “Host controls” as a 13px muted label over one 15px status line, with the chevron pointing up. The status line is “Next: Open for players”, “Next: Start the set” or “Next: End play and count up”. In count-up it is the live count verdict (“₱1,000 still to account for. 1 still to count.”), which follows typed counts as the full preview does. The bar is 55px high, or 69px when the verdict wraps to two lines; very large amounts at 320px may wrap further.
- **No action while collapsed.** The primary action, its options and its guidance appear together only when the dock is expanded.
- **State.** The choice is the class `dock-collapsed` on `<html>`, mirrored in `localStorage` as `rack-dock`. It applies to every set and state on that browser, starts expanded, and survives live updates, reloads and state changes. Refused storage keeps the toggle working for the page view.
- **Clearance.** With JavaScript, the set page reserves the measured dock height plus 16px (`--dock-h`, kept current by a `ResizeObserver`), in either state and with “More host controls” open. This replaces the fixed 128/200/340px phone clearances, which remain as the no-JavaScript values. Count fields use the same value for their bottom scroll margin.
- **Motion.** The dock slides between its two heights: 320ms with the ease-out curve when opening, 200ms with the ease-in curve when closing, the same timings as sheets. While closing, the content stays rendered and leaves with the edge. The chevron turns in 180ms. Reduced motion changes the size and the chevron at once. A tap during a slide cancels it and starts the new one.
- **More host controls.** Every option under the disclosure is a full-width 48px button with 8px between them: Set settings, Resume play, and the Cancel this set and Or add one player disclosures, whose summaries are quiet buttons. An open one takes the Rail 2 fill and its form follows directly below.
- **iPhone keyboard (2026-10-05).** An iPhone keyboard covers the bottom of the page instead of resizing it. While it is up, the dock is raised to sit on the keyboard (`--kb`, from `window.visualViewport`) and shows as the bar whatever the saved choice, without the home-indicator padding and without a slide. Typing in one of the dock's own fields keeps it expanded, no taller than the visible area. A tap on the bar puts the keyboard away; it does not change the saved choice. The page reserves the keyboard height as well, so a field near the end scrolls clear of the bar. A zoomed page, or a change under 80px, moves nothing.
- **Count-up bar (2026-10-05).** In count-up the collapsed bar has two lines: the running total (“₱1,900 of ₱2,000 bought in”) in place of the “Host controls” label, then the verdict. Both follow the typed counts.
- **Unchanged.** From 900px there is no toggle and a stored choice has no effect. Without JavaScript there is no toggle and the dock is expanded. Players have no dock. No token, colour or asset is added; the chevron is Lucide `chevron-down`.
- **Scrolling with the iPhone keyboard open (2026-10-05).** The bar stays the bar for as long as the keyboard is open and follows the visible area as the page scrolls; the page's length does not change during the scroll and nothing but the finger scrolls it. A field is moved clear of the bar only when it gains focus. `--kb-h` is the keyboard's height (state and reserved room); `--kb` is the dock's offset (position).
- **Measured.** 178 checks at 320, 390 and 1280px over draft, open, in-play and two count-up sets: no horizontal overflow against the requested width, the last link clears the dock in both states, the toggle is at least 48px with the 3px focus outline, and keyboard focus stays on the toggle across a live update.

### 2026-10-04 addendum — Archive and delete

Management of a session or group is quiet and sits last on its page. [Plan](doc/plan/1791114191_archive_and_delete_groups_and_sessions.md).

- **Manage this session** is a native disclosure with a muted summary under a Line rule, at the end of the session overview. It holds one sentence per action, a neutral Archive session button and, where allowed, a danger Delete session button. When an action is unavailable the sentence says why and no button appears.
- **Manage this group** is the last panel of Group settings, with Archive group and a danger Delete group.
- **Confirmation pages** use the 560px form page: back link, a question as the heading, the name, a short list of consequences, then one primary or danger button and a quiet “Keep” button. The session archive page adds a panel of unpaid transfers with tabular amounts. The group delete page has one labelled field for the typed name, with the name shown as help text; a refused name stays in the field beside its error.
- **Archived notice.** An info notice at the top of an archived session and its set pages: who archived it and when, and for a host a bone Restore session button. The badge reads Archived. The pages show no other action and no host dock.
- **Archived lists.** “Archived sessions (N)” at the end of the Sessions tab and “Archived groups (N)” at the end of Your groups are closed disclosures under a Line rule, hosts only. Session rows reuse the session-link row with an Archived badge. Group rows have a Restore button and a small Delete this group link.
- Long group names wrap anywhere on form pages and in the archived list. No token, colour, asset or motion is added.
- **Measured.** 85 checks at 320, 390 and 1280px: no horizontal overflow against the requested width, every button, link-button, summary and field at least 48px, visible focus on the danger link, and native submission without JavaScript.

### 2026-10-04 addendum — Entry pages

Log in, Sign up, “Sign-up needs an invite” and Join group share one front-door frame. This replaces the earlier description of login and signup under “Account and supporting forms”. [Plan](doc/plan/1791115804_entry_pages.md).

- **Frame.** One centred column, 440px of content, at every width; no panel and no second column on desktop. Signed out, the site header is left out and the page carries the lockup. Join group is seen signed in, so the header stays and the lockup is the 48px mark alone.
- **Lockup.** The mark at 72px, “PokerNights” at 2rem, weight 800, width 88%, then on Log in and “needs an invite” one muted line: “Keeps the books for your home poker game: buy-ins, cash-outs and who pays whom.” Sign up omits the line so the empty form fits a 390 × 844 phone.
- **Heading.** The task as a centred 1.375rem heading: Log in, Create your account, Join {group}, Sign-up needs an invite. Nothing sits above it but the lockup.
- **Invite sentence.** Under the heading, for a usable invite only: “You’re invited to **{group}**.” Join group shows the player count instead.
- **Form.** Left-aligned labels, full-width fields, a full-width bone primary button, then one muted line with the alternate path as a 48px link.
- **Show / Hide.** A text button inside the right edge of the first password field, 68 × 48px, muted, bone when pressed, with `aria-pressed`. On Sign up it reveals both password fields. It exists only when JavaScript runs, and fields return to hidden on submit.
- **Help and errors.** Sign up help is one short line per field. A refused login shows one error notice above the fields. A refused sign-up shows each error under its field with the Down border; a broken password rule appears under Password and a mismatch under Repeat password. The username stays and passwords return empty.
- No colour, token, font, asset or motion is added.
- **Measured.** 81 checks at 320, 390 and 1280px: no horizontal overflow against the requested width with a 60-character unbroken group name, every control at least 48px, new text pairs at 4.5:1 or more, keyboard order username → password → Show → submit → alternate link with the 3px focus ring, and the whole invite flow without a refused step.

### 2026-10-04 addendum — Settle status

A closed session states its settle status wherever it is listed. [Plan](doc/plan/1791120060_session_settled_indicator.md).

- **Badge.** One pill in words: “Settled” in Up with a 14px check, or “Partly settled” / “Unsettled” in Brass. It never relies on colour alone. One partial renders it for the list and the session top bar.
- **Past sessions row.** Table name, then a muted line “date · N sets”, with “· ₱2,650 still to pay” added while money is owed. The status badge sits at the right in place of the former set-count badge.
- **Heading.** “Past sessions” gains a muted, non-wrapping “N not settled” while any are outstanding.
- **Session top bar.** A closed session shows the status badge in place of “Session closed”. Open sessions read “Session open”; archived ones “Archived”.
- No token, colour or asset is added.
- **Measured.** 24 checks at 320, 390 and 1280px: no overflow with ₱199,999,999.98 still to pay, rows at least 48px, badge and count text at 4.5:1 or more, and each row matching its session page.

### 2026-10-04 addendum — Stakes forms and the shared field box

New session, Set settings and the preset form are laid out in titled groups. [Plan](doc/plan/1791121411_session_form.md).

- **One field box, every form.** Text fields, the date field and dropdowns share full width, 48px height, a 12px text inset, 16px text and left-aligned values. Native appearance is switched off so an iPhone draws them the same way. Dropdowns carry the app's chevron (Lucide, Bone dim, 20px) 12px from the right edge. Radios, checkboxes and legends start on the field edge. Disabled controls fade to 60%.
- **Groups.** “When and where” (Table, Date, Location), “Game” (Poker variant, Unit), “Stakes” (blinds, buy-in limits, usual buy-in), “Rake per buy-in”. Each has a 17px title at weight 650 and, after the first, a Rule hairline above with 24px before and 16px after it. Set settings has Game, Stakes and Rake; the preset form has its name field, Game and Stakes.
- **Pairs.** Small blind | Big blind and Minimum | Maximum buy-in sit in two equal columns with a 12px gap from 360px; below that they stack. Poker variant | Unit pair from 480px, so a dropdown value is never cut off on a phone. Inputs of a pair share one top edge; help and errors sit under their own input.
- **Rake** keeps its approved behaviour: three native choices and both value fields visible.
- **Errors.** Each field error sits under its field. The error text carries one id; the earlier wrapper repeated it.
- **Measured in Chrome.** 69 checks at 320, 390 and 1280px on the three forms: equal left edge, right edge and height for every field, aligned pairs including when one is refused, 16px field text, keyboard order matching the visual order, and submission without JavaScript. The iPhone rendering of the date field is not measurable here; see `doc/wiki/footguns/ios_date_input.md`.

### 2026-10-05 addendum — Entry flow after the critique

This supersedes three points of the Entry pages addendum: Sign up now carries the description, the Show button has no pressed state, and field errors no longer each carry an alert role. [Plan](doc/plan/1791134687_entry_flow_critique_fixes.md).

- **Invite link, signed out.** It opens Sign up. Under the heading: “You’re invited to **{group}**.” and, on the next line, “Already have an account? Log in”, before the first field. There is no alternate line under the button on an invited Sign up. The inline link keeps a 48px touch height without stretching the line.
- **Arrival.** An account created from an invite lands on the group page with the success message “Welcome to {group}. You’re in.” The Join page uses the same sentence.
- **Description.** Log in, Sign up and “needs an invite” show: “Keeps the books for your home poker game: buy-ins, cash-outs and who pays whom. It records the game. It never moves money.” It wraps to three lines on a 390px phone (42ch measure).
- **Sign up help.** Username: “Your friends see this name. Letters and numbers, no spaces.” Password: the four rules in one sentence, then a second line with “There is no password reset yet.” in Bone at weight 600 and “Save it in your phone’s password manager.” Help text on entry pages is 14.4px.
- **Refusals.** One error notice at the top of the form (“Check the highlighted field(s).” on Sign up; the login message on Log in). Refused fields have the Down border and their message beneath. Focus goes to the first refused field, or to Password after a refused login. Under a refused login: “Forgot your password? There is no reset yet. Tell your host, who can ask the site administrator to set a new one.”
- **Log in without an invite**, where sign-up needs one: the alternate line reads “No account? Ask a host of your group for an invite link.” with no link.
- **Invalid invite.** Heading “This invite link doesn’t work”, the reason in one error notice, then “Already have an account? Log in” as a quiet line, or Go to your groups when signed in.
- **Show / Hide.** The text and label change (“Show password” / “Hide password”); there is no pressed state. Bone text marks the revealed state.
- **Busy labels.** “Logging in…”, “Creating account…”, “Joining…”.
- **Spacing.** The primary button sits 16px under the last field. From 900px wide and 1000px tall the column starts 12vh down.
- **Skip link.** 48px high when focused.
- **Known limits.** An invited Sign up is 848px tall at 390px wide, four pixels more than an 844px screen; the Create account button ends at 800px. A refused Sign up is taller and its button needs a scroll. Refused sign-ups return empty password fields by design.
- **Measured.** 91 checks at 320, 390 and 1280px, including both invite paths end to end.

### 2026-10-05 addendum — Installable app

The site can be added to a phone's home screen and opens full-screen. [Plan](doc/plan/1791176898_installable_app.md).

- **Raster exception.** The build ships four PNG app icons and nothing else raster: 180px (iPhone), 192px, 512px and a 512px maskable copy, rendered from `static/branding/app-icon.svg` by `web/tests/browser/make_icons.mjs`. The mark sits inside the central 62% of the square, within Android's safe zone, on `#231d17`.
- **Colours.** The manifest background is Ground (`#130e0a`) and its theme, with the page's `theme-color`, is the header surface (`#1e1813`), so the system bar and the header are one colour. The iPhone status bar style is black, opaque: the page does not draw under the clock.
- **Offline notice.** A fixed line at the top of every page while the phone reports no connection: “You’re offline. Changes can’t be saved until you reconnect.” Brass text at 15px, weight 600, on the warning fill with a Brass rule below, centred, one or two lines. The page and the sticky header move down by its measured height. Submitting a form while it shows flashes the line once (600ms) and sends nothing.
- **Offline page.** Self-contained, with literal colours and an inline mark so it needs no other file: the mark at 72px, “You’re offline”, one sentence, a bone **Try again** button and a quiet **Go back** button, in a 440px centred column, vertically centred. It uses the system font, because the app font may not be available.
- **No install prompt** and no splash images.
- **Measured.** 33 checks: Chrome reports no installability error; the worker's cache holds only the offline page; 17 screens each have a way back; notice and offline page fit 320, 390 and 1280px with 48px controls.

### 2026-10-05 addendum — Actions update in place

No visual change. On the set page and the session page an accepted action updates the screen without a reload. [Plan](doc/plan/1791178826_actions_in_place.md).

- The page stays where it was: the tapped control stays under the finger, typed text in other fields stays, opened sections stay open.
- A sheet closes after the server accepts and focus returns to its opener. A refusal keeps the sheet open with the message beside the amount.
- Success messages float as before. After an in-place update an error also floats, as a toast with the alert role and a Dismiss button, for 12 seconds, because the page may be scrolled away from the top.
- A send that fails says “That wasn’t sent. Check your connection and try again.” in the sheet or as a floating error, and changes nothing.
- Nothing on the page changes before the server answers; the button shows its busy state until then.

### 2026-10-05 addendum — Screen changes

Links change the screen without a page load. [Plan](doc/plan/1791181102_screen_changes_without_reload.md).

- **Loading line.** When a screen takes longer than 500ms, a 3px Brass line grows across the top of the viewport. No spinner and no skeleton.
- **Fade.** The existing 180ms cross-fade between screens is kept, now within one page; reduced motion removes it. Direction and shared elements are left for the motion stage.
- **Arrival.** A new screen starts at the top. Its title is announced once to screen readers and focus moves to the start of the content without a visible ring; a page with an auto-focused field keeps focus there.
- **Back.** Returns to a freshly fetched screen at the scroll position it was left at.

### 2026-10-05 addendum — Motion system (stage 1 of the motion overhaul)

Motion ([motion.dev](https://motion.dev), version 14.0.0) drives interactive motion through `static/js/motion.js`. The look does not change.

**Principles.**

1. Motion explains: where did I go, what changed, did my tap work.
2. Never in the way. No control waits for an animation; the next tap interrupts it. Interactions end within 300ms; a signature moment within 900ms, once.
3. Money does not animate its value. A row may move; digits do not count.
4. Reduced motion removes movement and keeps the state change.
5. Springs for things a finger touches, eases for things that arrive or leave.
6. Additive. Without JavaScript, or if Motion does not load, every screen works with the CSS motion described earlier in this document.

**Presets** (`pokerMotion.run(element, keyframes, name)`).

| Name | Shape | Used for |
|---|---|---|
| `press` | spring, stiffness 1200, damping 50 | A button sinking 3px under a finger |
| `release` | spring, 200ms, bounce 0.45 | The button coming back |
| `sheet` | spring, 300ms, bounce 0.14 | A sheet rising its own height; the host dock opening |
| `arrive` | spring, 240ms, bounce 0.3 | A toast arriving or moving up the stack |
| `leave` | 200ms, the ease-in curve | A sheet or toast leaving |
| `nudge` | 300ms ease-out, 6px then 3px sideways | The field or message that explains a refusal |
| `pulse` | 360ms ease-out, scale to 1.04 and back | The control whose action was accepted |

**Components.**

- **Buttons.** A press sinks the button and it springs back on release. The shadow still drops while pressed. Keyboard activation does not move the button.
- **Pending.** A sent control (`aria-busy`) shows a 2px brass line running along its lower edge. Under reduced motion the line is still.
- **Sheets.** Since stage 2 they move by `transform`, which the browser animates off the main thread. Rise from below the edge and leave the same way, faster. A close during the rise turns the sheet around from where it is. The backdrop fades.
- **Toasts.** Arrive from 16px below. A later toast sits lowest and lifts the earlier ones by its height plus 8px; before this they overlapped. Dismissed toasts drop and fade.
- **Host dock.** Opening uses the `sheet` spring through the Web Animations API; closing keeps the 200ms ease-in. The keyboard behaviour is unchanged.
- **`motion-on`** on `<html>` marks that Motion runs. It switches off the CSS animation of each element Motion has taken over, so nothing animates twice.

**Measured.** `motion.mjs`, 34 checks at 390 and 1280px: each item above, an action sent during a sheet's rise leaves within 50ms, Motion animates only `x`, `y`, `scale`, `transform` and `opacity`, reduced motion, a blocked Motion file, and ten screen changes leaving one set of listeners and nothing running.

### 2026-10-05 addendum — Motion on the live set page (stage 2 of the motion overhaul)

The set page shows a change, yours or someone else's, as movement. `static/js/flow.js` moves rows; `static/js/changes.js` marks what changed.

**Presets added.**

| Name | Shape | Used for |
|---|---|---|
| `shift` | spring, 260ms, no bounce | A row arriving, a row sliding to its new place, the "books balance" words |
| `drop` | spring, 220ms, bounce 0.35 | The new edge landing on a buy-in stack |
| `fade` | 180ms ease-out | A new set state fading in |
| `mark` (CSS keyframes `mark-draw`, 320ms ease-out) | a 2px brass line drawn left to right | The underline of "Still in play" |

`pokerMotion.run` takes a fourth argument for one-off options such as a delay. `pokerMotion.settle` removes the inline style two frames after the element's last animation ends.

**Rules.**

1. Rows carry money and move without bounce. Bounce stays on buttons, badges and the buy-in edge.
2. A figure is at its accepted value on the first frame. Rows, edges, badges and rules move; digits do not.
3. Rows only arrive and shift. Nothing reorders or leaves.
4. Motion animates `transform` (as one string) and `opacity`. The separate `x`, `y` and `scale` remain only where movements combine on one element (buttons, toasts), with `will-change: transform` while they run.

**Events.**

| Event | Motion |
|---|---|
| A player is added | The row fades in and rises 12px. Several arrive 40ms apart. |
| A row above grows or shrinks | The rows below slide to their place. |
| A buy-in or rebuy | The new edge drops; "Rebuy added" springs in; the brass mark fades out over its last 400ms. |
| "Still in play" changes | The underline draws, holds and fades. The figure appears at once. |
| A cash-out, a player marked Left | The row's mark; the Left badge springs in; the name dims over 200ms. |
| The set changes state | The new state fades in over 180ms. Rows do not move as well. |
| A count is confirmed | The row's status badge springs; the progress line is marked. |
| The books balance (once per set per browser) | The green rule draws with the `sheet` spring; 240ms later the words rise 8px and fade in. |
| First sight of a set, typing, a hidden tab, reduced motion, no Motion | Nothing moves. |

**Measured.** `flow.mjs`, 52 checks at 390 and 1280px: each row above on its first frame and at rest, a tap on a moving row, both redraw paths, the books balance complete in under 900ms, twenty redraws leaving nothing running and no inline style, reduced motion and a blocked Motion file.

### 2026-10-05 addendum — Motion between screens (stage 3 of the motion overhaul)

A screen change says which way it went. `static/js/turbo-setup.js` decides; the last block of `static/css/app.css` moves.

**Depth.** Each screen states its depth on `<main>` (`data-depth`): Your groups 0, a group 1, a session 2, a set 3, the set log and the forms opened from a set 4; a form opened from a group is 2 and one opened from a session is 3. Log in, Sign up, invites and the offline page have none. A group's tabs are numbered in order (`data-tab`).

**Tokens.** `screen`: 220ms, a 24px shift with a fade (ease-in for the screen leaving, ease-out for the one arriving). `carry`: 260ms ease-out for anything that travels.

| Change | Motion |
|---|---|
| A tapped link to a deeper screen | The old screen moves 24px left and fades; the new one arrives from 24px to the right. |
| A tapped link to a shallower screen | The mirror image. |
| A group's tab | The content shifts towards the side the tab is on; the marker slides under the words to the chosen tab; the words, the back link, the heading and the tab bar stay still. |
| The phone's Back and Forward; screens at the same depth; screens without a depth | The 180ms cross-fade. |
| An action on a set or session page | No screen movement (stage 2 covers it). |

**Carried.**

- **A name.** The group's name travels from its card on Your groups to the group's heading; a session's table name travels from its row (or from the card's "in play" band) to the session's heading and stays in the heading of each set. Going back, it returns to the card or row. The two ends keep their own type size and fade through each other; the name is never stretched. It is carried only when the words match.
- **A player's chip** travels between a session's results and a set's rows when the same player has one chip in each list, with the same colour and letters, and the chip was on screen. At most twelve.
- **The top bar** stays still on every change.

**Rules.**

1. Nothing waits. A movement lasts 260ms at most, and a tap made during it is passed to the control under the finger.
2. Exactly one element holds a carried name on a screen. Two would make the browser cancel the movement.
3. Markers (`data-go` on `<html>`, the temporary names) are removed only when the browser reports the whole change finished. Removed sooner, the old screen's layer restarts its fade and the previous screen flashes.
4. Reduced motion, or a browser without the View Transition API (Safari before 18): screens change at once.

**Measured.** `screens.mjs`, 46 checks at 390 and 1280px.

### 2026-10-05 addendum — Your groups: the group card

Each group on Your groups is one card: the rail surface, a 1px rule edge, the sheet radius (26px), 16px between cards. It replaces the earlier run of text divided by lines. A card has three zones in a fixed order, divided by rules and running edge to edge; nothing inside it is a second card.

- **Who.** The group's name (1.75rem, links to the group). At the top right, the settings button: a round 48px quiet button with a gear icon, named "Group settings for {group}", which opens the Group settings tab. Under the name, up to six player chips, a "+N" counter for the rest, and the role badge at the right. The player count is read out to screen readers and not printed.
- **Now.** A set in play is the felt band, the only felt on the page, with the table name, one facts line and its one action. An open session uses the raised rail colour. Nothing in progress is plain text on the card. Further open sessions are one row: "More open sessions", the number in a pill, a chevron.
- **You.** "To settle" in brass, one row per person: who, the date, and the amount at 1.5rem in green or red. Then the viewer's figures in a two-column grid: a 1rem label, the signed amount at 1.75rem in the money width with its icon, and for a record one small note (sessions and wins). The last session's date sits beside its label. A third figure takes the full width; under 360px the figures are one column. A session sat out reads "Did not play".

After the last card, "New group" is a full-width button with a dashed edge and a plus icon; it opens the form in a panel below it. From 900px, more than one group flows into two columns that pack by height.

Text under 16px on a card is limited to the role and state badges and the note under a record. The fullest test card went from 17 such pieces to 4.

**Measured.** `home.mjs`, 60 checks at 320, 390 and 1280px.

### 2026-10-05 addendum — Numpad, count-up rework and even host controls

This Operate extension inherits The Rack: no new colour, font, radius or imagery. [Plan](doc/plan/1791202390_host_gaps_numpad_count_up.md); the critique that led to it is in the [study](doc/study/1791201933_host_gaps_numpad_count_up.md).

**The Gap Rule.** Neighbouring controls in the host controls are 8px apart (`--s-2`) at every width: the main actions, "More host controls" and the options under it. Spacing between a label, its field and its button inside an opened option is form spacing and is unchanged.

**Numpad.** On a device whose main pointer is a finger, a typed number uses the app's own keys; the phone's keyboard stays closed for that field. The field remains a real text field with the brass caret and focus ring.

- Twelve keys in a three-column grid with an 8px gap, built from the shared secondary button: 22px tabular figures at weight 700, 52px high in a sheet (48px on a screen under 700px high) and 48px in the panel. The order never changes: 1 to 9, one key that depends on the field, 0, delete. That key is a decimal point where a decimal is allowed and "00" where it is not. Delete is a drawn icon named "Delete"; holding it clears the field.
- In a sheet the keys sit between the amount and the action, and a cash-out sheet reads amount, keys, option, action. A sheet that holds the keys may use 96dvh.
- On a page with several number fields the keys are a bottom panel on the ground colour with a rule edge and the dock's shadow. Its strip names the field, repeats the running total during count-up, and holds Next (secondary) and Done (the panel's one bone button). The panel hides the dock while it is open and the page reserves its height.
- A refused key changes nothing; the field's border turns to the negative colour for 260ms and, with motion on, the field makes the existing 300ms nudge by `transform`.
- Movement: the panel rises with the sheet spring and leaves with the 200ms exit, by `transform` only. Keys sink and spring back like every button and act as the finger goes down. A typed figure appears at its value. Moving to the next field scrolls smoothly; in the count list the row being counted goes to the top of the free space, so the next player shows beneath it. Reduced motion: the panel appears and goes at once, nothing travels and scrolling is instant.
- On touch a tapped key returns to its resting colour (no hover remains).

**Count-up.** The earlier Count-up section describes the accounting and the preview, which are unchanged. The composition is now:

- Phone order: the neutral overview (title, state badge, date, one progress line at body size), the player counts, then Set totals and the Balance check. Once every player is cashed out the Balance check sits directly under the overview. From 900px: overview, host controls, Set totals and Balance check in the 400px column, the player counts in the flexible column.
- A count row: the identity token, the name with its state badge and written amounts beneath, the bought-in figure at the right; then one line with the label "Final count (₱)" and a right-aligned field. A confirmed count is the field's placeholder in Bone Dim. No button on the row. Buy-in count and time played are in Details.
- One running total for the host: the dock's bar on a phone, open or folded (an 18px tabular figure "of ₱X bought in", the verdict beneath, "Preview ·" before it while counts are unsaved); the "Confirmed counts" block with the main action from 900px and where the dock cannot fold. A player keeps one read-only block under Set totals.
- One bone action per state: "Confirm N counts", "Cash out counted players (N)", "Finalize results". A discrepancy offers "See the ₱100 difference" in the danger treatment. No disabled stand-in button: when there is nothing to do yet, the hint line says what to do.
- Confirming typed counts preserves the visible field's position when its saved status wraps. The one-time adjustment is instant; a changed scroll position is left alone.
- **The Verdict Rule.** A verdict states severity three ways: its words, its colour and a mark before it. Brass with a warning triangle when every count is in and the total is off, green with a tick when it matches, plain text while counting is unfinished. The marks are CSS masks in the text colour, not images.

**Cash-out review.** One verdict sits directly above the action: a green outlined notice when the batch balances the books, a brass notice when it leaves them short or over, plain text when players are still to count. The column is headed "Cash-out". Rake rows appear only when rake was collected.

**Finalize.** The action opens the shared sheet titled "Finalize set N?", with fact rows (players, total bought in, total cashed out, rake and override when present), the verdict, one sentence that it cannot be undone here, the bone "Finalize set N" and a quiet "Not yet" that takes the focus. Without the sheet the same content is a native disclosure.

**Messages.** On a set page a floating message sits above the dock's measured height, or above the numpad panel, never on them.

**Final results.** The overview leads with the proof line ("6 players · ₱9,500 in · ₱9,500 out") and the verdict, then the viewer's result when they played. The cash-out total is "Total cashed out". Rake rows appear only when rake was collected. A zero result reads "Even". The connection status is not shown on a final set.

### 2026-10-06 addendum — Smoothness on a phone

[Plan](doc/plan/1791214849_phone_performance_and_smoothness.md). This supersedes two earlier points: the host dock no longer animates its height, and a changed row's mark is no longer an outline.

- **Host dock.** The dock slides by `transform`. The layout takes its new height once: when an unfold starts and when a fold ends, and `--dock-h` is written once per slide. Timings and curves are unchanged (the sheet spring to open, 200ms ease-in to close). A page scrolled to its end glides down with a folding dock. One slide costs 3 layouts; animating the height cost 27 to 55.
- **Pressed links.** Session rows, set links, group names, the rows on a group card and back links lighten (`--pressed`, 12% bone) from the first frame of a touch. Nothing moves, so reduced motion keeps it. The tapped link keeps the look (`is-going`) until its screen is drawn. A link that is a button shows the busy line instead, as a sent form does. Tabs take no pressed look (changed the same day, after the phone check): a lit tab reads as chosen before its content has come, and the marker's slide is the tab's own answer.
- **Changed rows.** The brass mark is a 2px box drawn inside the row, 2px from its top and bottom and 8px into the page's side margin, over a 12% brass tint. Marks on neighbouring rows never cross and no mark covers another row. It still fades over its last 400ms. The pot and single figures keep their own marks.
- **"Rebuy added" and "Updated".** The badge sits in the line under the player's name, after the buy-in count. It wraps to its own line when the row is narrow. It is never placed over the amount, the name or a button, and it does not change the row's height where it fits.
- **One-trip actions (2026-10-06).** An action sent in place is answered with its page in one request. Nothing visual changes: the same in-place update, marks, toasts and sheet behaviour, sooner.
- **Measuring.** `?perf=1` on any address shows a readout of each tap for that tab: the wait for the server, drawing, movement, the server's own figures and late frames. `?perf=0` removes it.

### 2026-10-06 addendum — Password reset link

- **Set a new password** (`templates/accounts/reset.html`) uses the entry frame without the description line: mark, name, heading, “Your username is **name**.” in the `.entry-invite` line, New password with the one Show button, Repeat password, and the bone button “Save and log in”. The tab title never names the account.
- **A link that doesn't work** follows the invalid-invite page: heading, one `notice-bad` alert with the reason and the next step, and Log in as a quiet line.
- **Group settings → Players.** The once-only link is a `notice-good` panel at the top of the Players panel with a read-only field, as the invite link is. The action is a small button in the member's Manage block, between the role button and Remove; a live link adds one muted line and “Cancel link”.
- No new token, colour, font or asset.

### 2026-10-06 addendum — Copy button in a link field

A link that is shown once sits in a read-only field with a text button in its right edge, built like the password Show button: transparent, 80 px wide at least, the field's full height (48 px), bone text at 14 px semibold. It reads "Copy", then "Copied" in the success green for two seconds; the word changes, so colour is not the only signal. The address ends in an ellipsis before the button. A refusal adds one 14 px line in the text colour under the field. Template `web/_copy_field.html`; classes `.copy-wrap`, `.copy-button`, `.copy-status`.

### 2026-10-06 addendum — A player's own row

- **Running set.** A player's own row carries the host's Rebuy button and sheet, unchanged. Other rows have no action.
- **Count-up, player.** The own row holds a labelled field "Your count", right-aligned figures in the count style, beside a primary "Send to host" button, with one muted help line. After sending: one line "You entered **₱1,450**. Waiting for the host to confirm." and a "Change" disclosure with the same form.
- **Count-up, everyone.** A row with an entered number shows a neutral badge "Entered" and "₱1,450, not confirmed yet" where "Awaiting count" was. The neutral badge keeps it apart from the amber awaiting and the blue ready states.
- **Count-up, host.** The field stays empty with the entered number as its placeholder, and one muted line under it names the player, the number and the two choices. The dock's label reads "Preview · players' counts" until the host confirms.
- No new token, colour, font or asset. Classes: `.own-count`, `.own-count-state`, `.own-count-change`, `.count-entered`.

### Roster (2026-10-09)

Group settings → Players. [Plan](doc/plan/1791525658_roster_management.md). No new colour, font or asset.

- **A roster row** is the identity token, the name, and beneath it one muted 13px line in tabular figures: "12 sessions · last played Oct 1". Host and No login badges sit at the right.
- **Disclosures in the Players panel** carry a drawn chevron after the summary text (two 2px borders, the summary's colour) that turns when the disclosure opens. No glyph is used.
- **Manage a player** holds one form (Name, Contact, a full-width Save), then the role and reset-link buttons 16px below as full-width 48px buttons 8px apart, then, under a Rule line with 16px above and below, a quiet danger link "Remove from group". The destructive action never sits beside a routine one.
- **The removal page** is a confirmation page: the question as the heading, the consequences, a "Still to pay" panel with the payer, the payee, the date and table beneath, and the exact amount at the right; then the danger "Remove {name}" and the quiet "Keep {name}". A refusal shows the reason in an info notice, a button to the set that blocks it, and no danger button.
- **Removed players (N)** is a closed disclosure under a Line rule, hosts only. Its tokens are dimmed to 55%; names keep full contrast. "No login" is written at the start of the activity line so the row and its Bring back button stay on one line at 390px; below 360px the button wraps.
- **Names box.** A textarea of at least 132px with the field treatment. A muted line under it counts the names from two up and turns to the Down colour with the limit when over 30.
- **Motion.** Rows just added or brought back take the accepted-change mark for 3 seconds and rise 12px with the `shift` spring, 40ms apart, at most eight steps. After a removal the Removed players summary takes the mark and one `pulse`. An opened disclosure fades in over 6px with `fade`; closing is immediate. The chevron turns in the fast duration. Under reduced motion the mark shows and nothing moves. No inline style is left behind.
- **Measured.** `roster.mjs`, 44 checks at 320, 390 and 1280px: no horizontal overflow, every button, link-button, summary and field at least 48px, contrast of the activity line, the summaries and the danger button at least 4.5:1, the mark removed after its hold, reduced motion, and every action present without JavaScript.

### Claim link (2026-10-09)

[Plan](doc/plan/1791527506_claim_links.md). No new colour, font or asset.

- **The page that asks** uses the entry frame and leads with the player's own identity token at 64px, in the colour it has on the roster, in place of the brand mark. Then the heading "Join {group} as {name}", one balanced paragraph, a neutral bordered block naming the account (and, muted, an empty entry that will be replaced), the bone "Claim {name}", a quiet "Not now", and "Not {username}? Log out" as an underlined text button with a 48px target.
- **Refused and dead links** keep the compact brand mark, a heading that says so, one notice with the reason and one button to Your groups.
- **The host's side** repeats the reset-link pattern: a good-coloured notice with the Copy field, shown once; in "Manage", one muted line, then full-width 48px buttons.
- **Motion.** The token springs in once with `arrive` (`[data-pop]`), from a visible default. Nothing else on the page moves.
- **Measured.** `claim.mjs`, 30 checks at 320, 390 and 1280px: no horizontal overflow, 48px targets, contrast of the account line, the muted note and Log out at least 4.5:1, visible focus, no inline style left after the token settles, and the whole flow without JavaScript.

### Stats and charts (2026-10-09)

[Plan](doc/plan/1791528961_stats_revamp.md). The app's first charts. No new colour, font or raster asset.

- **Your summary** is a neutral panel: a Bone Dim label, the viewer's profit or loss as the largest figure on the page (36 to 52px, weight 800, with its sign and direction icon), then Rank and Last result under a Rule line, then one full-width button.
- **Board rows** are links of at least 64px: place, identity token, name with a muted line of sessions and share won, and the figure for the chosen order at the right in Up or Down with its sign and icon. The viewer's own row sits on Rail 2 and says "(you)". A movement mark under the place is Bone Dim, never Up or Down, with a drawn arrow and a number, and words for a screen reader.
- **Period and order** are pill rows. The month list is a native select in the pill shape; it takes the selected treatment while a month is chosen.
- **Stat tiles** are a two-column grid (four from 900px) with hairline Rule gaps: a Bone Dim label, a 20px figure in tabular numerals, and a small note where a figure covers only some sessions.
- **Charts** sit on a neutral panel.
  - Running profit is one Bone line, 2px, with a Line-coloured zero line, the highest and lowest totals and zero written at the left in Bone Dim, and a ringed Bone dot on the latest point. One series, so no legend; the heading names it and the lead figure above states its value.
  - Each session is a thin bar from a Rule baseline, 4px rounded at its far end, with at least 2px between bars. Up bars are Up; Down bars are Down with a diagonal hatch.
  - The two charts share horizontal positions and never an axis. Position is the order of sessions, evenly spaced, with the first and last dates beneath.
  - Text is always Bone or Bone Dim. No gradient, glow or fill under the line.
  - The chosen session is marked in Brass: a hairline through both charts, a dot on the line and a ring on the bar. The line beneath the chart states it in words.
- **Colour check.** The dataviz validator, on Up `#6fdea7` and Down `#fe8b83` against Rail `#1e1813`: contrast with the surface passes; separation for normal vision 25.7; for red-green colour blindness 6.0, which is allowed only with a second cue. A loss is therefore also below the baseline, hatched, and written with its sign. The validator's lightness band is for categorical series and does not apply to these two status colours.
- **Changing period, unit or order** keeps the screen and its scroll position, and replaces the history entry. The chosen pill is a Bone marker behind its words; it slides from the pill chosen before with the `sheet` spring. A new period or unit brings the figures in 32px from the side that was tapped toward, with `shift`. A new order leaves the summary still and moves each row from where it was. No view transition is used, so it is the same in every browser.
- **Motion.** The line is revealed left to right in 600ms and its end dot follows; bars rise from the baseline, 12ms apart, at most thirty steps; rows glide to their new places with `shift` when the order changes. The readout follows the finger with no easing. Money never counts up. Under reduced motion everything is in place at once.
- **Measured.** `stats.mjs`, 75 checks at 320, 390 and 1280px: the page staying where it was scrolled on every change of period, unit and order, no horizontal overflow, 48px targets, contrast of every text style at least 4.5:1, bars meeting the baseline, the end mark inside the chart, the readout by pointer and by keyboard, visible focus on the chart, reduced motion, no JavaScript, and no script error.

### Numpad motion (2026-10-09)

[Plan](doc/plan/1791533332_numpad_motion.md). The app's number keys answer the finger. No new colour, font or asset; only colour, transform and opacity change.

| Moment | Movement |
|---|---|
| The keys enter a sheet | The four rows rise 10px and fade in with `shift`, 30ms apart |
| A key is hit | The key takes a Bone tint at once and loses it over 160ms, on top of the shared press. The field's box is still; see "Numpad digit motion" below |
| Delete is hit | The same light; the deleted digit leaves |
| Delete is held | A Down-tinted fill runs across the key, left to right, linearly, for the 500ms the hold takes. Letting go takes it back at once. A completed clear lets every digit leave together |
| A key is refused | The key shakes with the field and takes the Down border for 260ms |
| Next in the bottom panel | The field's name and note come in from 8px below in 160ms |

- A key acts as the finger goes down; no movement delays it, and a second tap restarts the light.
- The digit shown is always the field's own digit, in its own place. It may fade and rise into that place; no number rolls or counts. (Changed 2026-10-09 from "A digit appears whole and at once".)
- The field's size, caret and focus ring never change.
- Under reduced motion nothing moves and the fill is not shown; the light on a hit key still appears.
- **Measured.** `numpad.mjs`, 105 checks: the keys' first frame in a sheet, a key pressed while rising, ten taps with no pause, the light, the fill at 250ms of a hold, an early release, a completed hold, a refused key, Next, reduced motion, and no inline style or mark left at rest.

### Numpad digit motion (2026-10-09)

[Plan](doc/plan/1791538209_numpad_digit_motion.md). The pulse of the whole field on every key is gone. The box stays still and each digit moves by itself.

| Moment | Movement |
|---|---|
| A digit is typed | It fades in and rises 0.16em into its place in 180ms, `--ease-out`. No bounce |
| Digits already there must make room (a right-aligned field) | They glide to their new place in 180ms, `--ease-out`. A glide cut by the next key carries on from where it is |
| Delete | The digit fades and drops 0.12em in 100ms, `--ease-in`; the rest glide back |
| A digit replaces a selection | What it replaces goes at once, so two values never overlap |
| A key is refused | The drawn digits shake with the field |

- **How.** A text field cannot move one character. While keys are tapped, a drawn copy of the text (`.numpad-figure`, `aria-hidden`) lies over the field, each character where the browser itself sets that text, and the field's own glyphs are hidden with `-webkit-text-fill-color`. The caret stays Brass. 300ms after the last key the copy is removed and the field is a plain field again.
- **Fail safe.** No copy is made when the text is wider than the field, under reduced motion, or without Motion. An update from the server, typing that is not from the keys, another field, and leaving the sheet all remove it at once. An error gives the copy up for the page and the keys keep working.
- **Measured.** `numpad.mjs`, 120 checks. A capture of the field with the copy up and one with the field's own text differ by at most 1 shade in 255 on any pixel, for a left-aligned sheet amount and a right-aligned field: the copy sits exactly on the text.

### Front door (2026-10-09)

[Plan](doc/plan/1791542366_front_door_revamp.md). This supersedes the frame in "Entry pages" and "Entry flow after the critique"; their words, help, errors and Show button stand. No new colour, font or raster asset.

**Frame.** Log in, Sign up, "Sign-up needs an invite", Set a new password, Join group, Claim and their dead-link pages share `templates/entry.html`.

- **Two surfaces.** The hero sits on Ground: the mark and the name. Below it the task sits in a raised sheet: Rail, a Rule edge, the sheet radius (26px), the sheet's shadow. Under 520px the sheet runs edge to edge and to the bottom of the screen, with top corners only. From 520px it is a centred 440px card with 32px padding.
- **The mark is drawn in the page** (`partials/mark.html`), in the tokens Ink, Bone and Brass, so its ring and its crescent are separate parts. Under the ring is a second ring 3 units lower in the primary button's underside colour (`--door-under`): the chip has the thickness the buttons have. It is decoration; the name beside it is text.
- **Hero sizes.** Log in, "needs an invite" and signed-out link pages: the mark at 96px (72px on a screen under 700px high) over "PokerNights" at 2rem. Sign up and Set a new password: one row, the mark at 56px beside the name. Signed in (Join, Claim): the 48px mark alone, or the player's own token on the claim page, under the site header.
- **The description** stays under the name on Log in and "needs an invite". On Sign up it is the sheet's foot, under a Rule line, word for word.
- **An invited Sign up** is headed "Join {group}", then "Create your account to get in." and "Already have an account? Log in" before the first field.
- The return key on a phone keyboard reads Next until the last field, then Go.

**Movement.** The one exception to the 900ms limit for a signature moment: the full arrival may take up to 1.1 seconds, on the front door only, once per browser session.

| Moment | Movement |
|---|---|
| First visit in a browser session (`data-arrival="full"`) | The mark drops 28px from 86% size with the `arrive` spring while its ring turns a third of a turn into place; the crescent rises 140ms later; the name widens from 62% to 88% width as it fades in; the sheet rises 24px with the `sheet` spring and its heading, fields and button follow 40ms apart with `shift`; the description fades in last. 780ms as built |
| Later visits (`data-arrival="short"`) | The hero and the sheet fade in and rise 8px together in 240ms |
| A key or a tap during an arrival | The arrival ends at once. The username field has focus from the first frame |
| A key is typed in any field | The ring and its underside turn 20° (a spring, 300ms, bounce 0.25); a delete turns them back. The crescent is still |
| Show / Hide | The crescent tips 32° and back with `release` |
| A form is sent | The ring spins, one turn in 900ms, until the next page comes. The button keeps its busy line and words |
| A refused page | No arrival. The mark shakes once with `nudge`, as the refused field does |
| Log in ⇄ Sign up | The mark, the name and the sheet are the same things on both screens (`brand-mark`, `door-name`, `door-sheet`): the mark changes size and place, the sheet changes height without stretching its content, the rest cross-fades |
| Getting in, logging out | The mark and the top bar's mark share `brand-mark`, so the browser carries the chip into the top bar and back (420ms). Inside the app the top bar gives the name up (`data-door-done`), so screens there change as before |

**Rules.**

1. The arrival is CSS, not Motion, so it starts on the first paint. Every keyframe runs from a start state to the element's ordinary state: a page where nothing runs is complete. The springs are the app's own, sampled into `linear()` curves (`--spring-sheet`, `--spring-arrive`, `--spring-shift`, `--spring-turn`); a browser without `linear()` gets the ease-out curve.
2. The server chooses the arrival (`config/door.py`) from a cookie that lasts the browser session and holds nothing. A page that answers a POST gets none.
3. Nothing loops while the page is idle.
4. Only transform and opacity move, with one measured exception: the name's width during the full arrival. It added no late frame with the processor slowed four times.
5. Motion (`static/js/door.js`) is used only for what a person causes. A screen with a top bar has two marks, and only the top bar's may hold the carried name.
6. `DOOR_MOTION=False` removes every movement above and the carried names; the frame stays.

**Measured.** `door.mjs`, 134 checks at 320 × 568, 390 × 844 and 1280 × 800: the frame, fit and 48px targets on eight screens, contrast on both surfaces, the first frame of each arrival, the key and the tap that end it, each answer of the chip and its centre of turning, ten changes between Log in and Sign up, the carry in and out, late frames, reduced motion, no JavaScript, Motion blocked and the switch. The empty Sign up ends its button at 620px on a 390 × 844 screen, and the invited one at 675px (800px before).

**Critique.** 29 of 40 (24, then 25 before). Open: where the description belongs, naming who invited, and whether a phone's keyboard hides the chip.

### Arrival into the app (2026-10-09)

[Plan](doc/plan/1791546778_arrival_after_login.md). The last step of the front door: the one page that follows a successful log in, sign up, reset link or claim. No new colour, font, asset or words. Over within 880ms; no exception to the 900ms limit.

| Moment | Movement |
|---|---|
| The chip lands in the top bar | The top bar's mark sinks 2px and returns, once, 380ms in |
| Your groups: the cards | Each card rises 16px and fades in with `shift`, from 100ms, 70ms apart. The fourth card and any after it arrive together |
| The players on a card | The tokens slide 14px into their overlap, from 220ms, 30ms apart; the sixth and the "+N" counter together |
| A set in play | The "In play" badge springs in from 60% at 320ms |
| Money to settle | A 2px Brass line draws under "To settle", holds and fades, once |
| New group | Fades in last |
| A newcomer's first screen | The mark, the heading, the sentence, the form and the note rise in turn, 60ms apart |
| Any other landing page | Only the top bar's mark lands |
| A later visit, a reload, Back | Nothing |

**Rules.**

1. A figure is at its value on the first frame. A card moves with its figures inside it; no digit counts or rolls.
2. Only cards and their parts move, never `<main>`: a transform on it would re-anchor the floating messages and the host dock inside it. This is why a landing page other than Your groups has no rise.
3. The server marks the page (`data-welcome` on `<main>`, `config/door.py`): a login sets a cookie for 30 seconds, and the first page shown to the signed-in person reads and removes it. A page fetched ahead of a tap does not use it up, and a front-door screen seen signed in (Join, Claim) leaves it for the page behind it.
4. It is CSS, as the front door's arrival is. `door.js` ends it on the first key or tap and takes the mark off after 1.2 seconds.
5. `DOOR_MOTION=False` removes it with the rest of the front door's movement.

**Measured.** `welcome.mjs`, 35 checks at 320 × 568, 390 × 844 and 1280 × 800: the first frame, every figure's text on that frame against its text at rest, the order of the cards, the end within 900ms, a tap and a key ending it, a tap on a card's button during it, one card and five, a group page, a newcomer, a reload, Back, a second login, reduced motion, no JavaScript, Motion blocked and the switch. With the processor slowed four times the arrival had one late frame (50ms) where a plain visit had none.

## Do's and Don'ts

### Do:

- **Do** use the built Archivo family, tabular figures and the shared token palette.
- **Do** pair player chip colours with initials and written names.
- **Do** retain visible focus, labelled actions and reduced-motion behaviour.
- **Do** keep typed sheet values through live updates and refused submissions.
- **Do** distinguish still in play, total bought in and cashed out with explicit labels.

### Don't:

- **Don't** add casino imagery or shipping raster decorations.
- **Don't** animate money through intermediate values or show success before server acceptance.
- **Don't** use colour alone to identify a player or communicate wins, losses or updates.

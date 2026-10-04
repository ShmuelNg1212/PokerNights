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

The session’s closed “Still to pay” figure reuses the 64px display role. Its complete formatted value stays on one line: formatted lengths above 10 use 32px, and above 17 use 24px. These session-scoped content adaptations preserve currency, grouping, precision and the chips unit without abbreviation. The session viewer result uses 32px at 80% width; transfer amounts use 24px and aggregate result rows use 22px. Recap facts use 22px below 14px labels.

The timer and blinds use 70% width, weight 800 and line height 1.2. On phones they are 22px; chips-game blinds are 16px. At desktop they are 27px. They are supporting figures, not a second display role.

**The Figure Rule.** Keep money and timers tabular. Use compressed display figures for the active total and quieter right-aligned amounts in player rows.

## Layout

Shared pages are centred in a 560px container with a 16px inset. The active-set page extends to 1180px. Phone composition stays in one column: felt overview, compact player list and an opaque bottom host dock. Bottom clearance is 128px; the dock accounts for the safe area and can scroll when expanded. An open set with the opening-buy-in option reserves 340px below 900px so the enlarged dock clears the player list.

The overview has a flexible amount column and a 116px supporting column, separated by 8px. Player rows align a 44px identity token, flexible name, right-aligned amount and action. Below 360px, the token becomes 36px and the row gap becomes 6px.

At 900px and above, the active-set layout becomes a 400px left column plus flexible player list, with a 28px gap and 28px page insets. The left column sticks below the header at 90px. The host action returns to the document flow and rebuy controls display their written label.

Count-up, review and final pages inherit the 1180px table container and the 400px-plus-flexible two-column layout from 900px. On phones, count-up orders the neutral overview, all inline player counts, then the balance check; the host dock remains fixed with visible next-step guidance and a 48px “More host controls” target. Count-up reserves 200px bottom clearance, increased to 370px when the host's count-total dock is present; count fields retain 90px top / 200px bottom scroll margins. The confirmed count total stays in the neutral overview while the local preview sits before the dock's next action. At desktop both remain in the left overview/control column. Review and final pages reserve 48px at the bottom and keep actions in document flow. Below 360px each count button stacks at full width beneath its input. End-set and review containers, names and figures wrap anywhere to contain long unbroken names and large amounts.

The session page inherits the 1180px table container and remains one column on phones. From 900px it uses a 400px overview/action column and flexible detail column with a 28px gap. Its document order is task summary, closed-session transfers, aggregate results, sets and payment records. Actions stay in document flow with 48px bottom clearance; detail sections have 32px separation. Transfer identities occupy two flexible columns around a written direction, with 32px tokens; amount, status and actions wrap on the next line. Full names and result rows can wrap while the primary Still to pay value remains intact.

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

Transfer rows pair payer and payee identity tokens with full names, “pays,” an exact amount and Paid / Not paid text. Paid includes its recorded time and “marked by the host.” Host Mark paid and Undo are native POST actions. The session identity order follows first appearance in aggregate standings and keys tokens by member; it need not match a set’s colour order. Payment records retain recorder and undone status, with struck text for reversed records.

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
- **Unchanged.** From 900px there is no toggle and a stored choice has no effect. Without JavaScript there is no toggle and the dock is expanded. Players have no dock. No token, colour or asset is added; the chevron is Lucide `chevron-down`.
- **Measured.** 145 checks at 320, 390 and 1280px over draft, open, in-play and two count-up sets: no horizontal overflow against the requested width, the last link clears the dock in both states, the toggle is at least 48px with the 3px focus outline, and keyboard focus stays on the toggle across a live update.

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

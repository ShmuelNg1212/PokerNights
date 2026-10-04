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
  slate: "oklch(0.285 0.025 265)"
  slate-ink: "oklch(0.86 0.025 265)"
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
- **Slate / Slate Ink:** muted end-of-set felt and its readable labels; count-up, cash-out review and final overview share this quieter field.

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

Count-up, review and final pages inherit the 1180px table container and the 400px-plus-flexible two-column layout from 900px. On phones, count-up orders the slate overview, all inline player counts, then the balance check; the host dock remains fixed with visible next-step guidance and a 48px “More host controls” target. Count-up reserves 200px bottom clearance and count fields use 90px top / 200px bottom scroll margins. Review and final pages reserve 48px at the bottom and keep actions in document flow. Below 360px each count button stacks at full width beneath its input. End-set and review containers, names and figures wrap anywhere to contain long unbroken names and large amounts.

The session page inherits the 1180px table container and remains one column on phones. From 900px it uses a 400px overview/action column and flexible detail column with a 28px gap. Its document order is task summary, closed-session transfers, aggregate results, sets and payment records. Actions stay in document flow with 48px bottom clearance; detail sections have 32px separation. Transfer identities occupy two flexible columns around a written direction, with 32px tokens; amount, status and actions wrap on the next line. Full names and result rows can wrap while the primary Still to pay value remains intact.

Home navigation uses a 760px container and 76px-minimum group links with role labels; creation follows the list. Group pages lead with sessions on phones, with the host’s New session above the current-session list. Past sessions precede tables, presets, roster and invites. From 900px, the group container expands to 1180px and uses flexible session/management columns in a 1.25:1 ratio, a 48px gap and a management rail with 28px left inset. These actions stay in document flow.

Account, invitation and supporting forms use a 600px container with 28px top inset; explanatory prose is bounded at 65ch. The log uses an 850px container, wrapping section links with 48px targets, 16px vertical record padding and 96px heading scroll clearance. Names and explanations wrap while record amounts retain their full formatted value.

Sheets are at most 440px wide and 85dvh tall, scrolling internally. They sit against the phone's bottom edge and become centred at desktop. Quick amounts occupy four equal columns with an 8px gap. Shared form stacks and field gaps use the spacing values in frontmatter; there is no additional invented spacing scale.

## Elevation & Depth

Depth comes from tonal rails, fine rules and CSS-built felt grain. Buttons have a short solid underside that disappears on press. Sheets and the host action use stronger shadows to separate them from the working surface; ordinary cards remain flat.

The sidecar records the built shadows, timings and easing curves. Sheet entry moves 24px in 320ms; exit takes 200ms. Accepted-change attention uses a 600ms treatment and remains labelled briefly. Chip-edge entry accompanies a confirmed rebuy. Reduced-motion preferences suppress animations, transitions and button displacement.

The balanced-books message uses a green double rule with a 5px band and one-pixel top and bottom strokes. In count-up, only the existing balanced state makes it eligible for a 600ms left-to-right reveal. A localStorage marker records the set per browser, keeping reloads and later polls static; unavailable storage leaves the rule static. Final results use the static rule. Reduced motion suppresses the reveal while keeping its message.

The closing recap reuses the shared sheet. Its fact lines reveal with a 360ms clip, staggered by 60ms, finishing within 540ms for four lines. Reduced motion leaves them static; accepted money appears immediately without a count animation. Automatic opening is consumed once per session and signed-in viewer in each browser, before opening; manual reopening remains available. Storage failure suppresses only automatic opening.

**The Accepted Change Rule.** Figures change only to accepted server values. Highlight the changed row or total without interpolating the amount.

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

Names and metadata form a single 48px-minimum detail target. Amounts form a separate right-aligned column. Phone rebuy controls are circular with a plus icon and a labelled accessible action; desktop adds visible words. Cash-out state and departed-player state remain written.

### Start controls

An open set places a checked native option immediately before Start the game. Its 48px-minimum label shows the current usual amount in the session’s unit and says it applies to players without a buy-in; adjacent help says existing buy-ins stay unchanged. Unchecking opts out for that start, and live updates retain the choice. The native form records missing opening buy-ins on accepted start before the timer begins. The control reuses the shared checkbox, focus and primary-action treatment.

### Count-up

A quiet slate overview shows “N of M players ready or cashed out,” separate awaiting/ready/cashed-out counts, total bought in, recorded cash-outs and the stopped set timer. Only players with buy-ins contribute to N and M; earlier partial cash-outs alone do not complete a player. Inline rows pair player tokens and names with bought-in figures, written state and a labelled final-count input. Every host input and count button belongs to one shared form: a row button confirms every typed count, zero is valid and empty fields are skipped. Confirmed counts remain written above draft fields; no provisional net result appears. Players see read-only state. Corrections and exceptions remain in native details. Polling retains drafts and focus.

The dock opens review when confirmed counts are ready, offers finalization when the books balance, and otherwise explains the next step. Count confirmation stays at the form. Pending cash-outs remain ordinary progress; completed discrepancies carry an error explanation and existing override controls.

### Cash-out review

Slate totals separate “Total of this batch,” “Recorded cash-outs,” prospective “After this batch” and “Total bought in.” A fixed-layout table pairs initial tokens and wrapping names with right-aligned exact confirmed cash-out amounts. The player column occupies 56%; the batch total has a footer row. A drawn back arrow accompanies the written set link. Awaiting and already-cashed-out lists remain separate. Written guidance states that this action records cash-outs without finalizing or marking payment; stale reviews retain an error and fresh values.

### Final results

The slate overview gives the viewer’s frozen signed result prominence when present. Result rows pair tokens and wrapping names with signed right-aligned amounts and direction icons; a written Final tag marks the section. Facts list buy-in count and total, cumulative cash-outs, any override and recorded time played. Snapshot values supply the results. Override disclosure remains written, and the session link explains where the next set or settle-up belongs. Set-level transfers and payment controls are absent.

### Session overview and settle-up

The open-session indigo overview leads with the current set action and the viewer’s result so far when a standing exists; it explains that transfers follow closing. Close and next-set actions retain their service gates beside that task. A closed session uses slate, an intact Still to pay figure, written settlement status, amount-based progress and a separately labelled paid-transfer count. Remaining and paid sums use exact integer transfers; zero transfers show “Nobody owes anything” without a progress denominator.

Transfer rows pair payer and payee identity tokens with full names, “pays,” an exact amount and Paid / Not paid text. Paid includes its recorded time and “marked by the host.” Host Mark paid and Undo are native POST actions. The session identity order follows first appearance in aggregate standings and keys tokens by member; it need not match a set’s colour order. Payment records retain recorder and undone status, with struck text for reversed records.

Aggregate results remain separate from transfers and payments, using frozen finalized-set values, signed figures and direction icons. Closed results carry Final; open results say “Over finalized sets; session still open.” No-finalization state is explicit. A viewer without a standing receives no invented result. Sets retain number, written state and known timer values; the existing “Play time over all sets” line is distinct from the recap’s finalized-only duration.

### Closing recap

A closed session offers “View session recap” and inline facts when dialog enhancement is unavailable. Recorded play time sums known finalized-set durations only, says Not recorded when none are known and labels partial sums. Total bought in explicitly covers current finalization snapshots across finalized sets, independent of transfers. Top session result names every tied highest positive standing; all-zero results say Everyone broke even. Your session result appears only for a viewer with a standing.

The browser key includes session and signed-in viewer. Automatic opening happens once per key and is consumed before opening; storage refusal leaves manual access. Close, Escape and backdrop dismissal preserve native modal keyboard navigation and return focus to the manual trigger. No JavaScript leaves recap facts and every native form in the document. The recap inherits shared focus, target, sheet geometry and reduced-motion behavior.

### Group and home navigation

Full-width group rows pair written names with membership roles. An empty home explains creation or an invitation. The group’s current sessions reuse indigo with readable Felt Ink labels; the host’s bone New session action precedes the list. Without tables, the page gives the table-creation prerequisite. Past sessions and management use ordinary rules and rail sections. Native disclosures contain table creation, member management and roster additions; host-only actions retain their gates.

The alphabetic roster pairs full names with initials, Host / No login labels and native management controls. Roster chip colour derives from member primary key within the ten-colour palette; collision handling uses roster peers. Set join order and session standing order retain their own token rules, so colour does not promise identity across those views. The one-time invite URL remains a labelled read-only field.

### Account and supporting forms

A narrow task frame uses an explicit heading, return or alternate-entry path, labelled fields, attached help and local error text. Field errors use the negative boundary; form errors remain at the form. Login and signup preserve username and the safe next destination while refused passwords remain blank. Invitations offer the join task or a written failure with a group return path. Session, preset and settings forms retain bound editable values and exact unit guidance; the native player picker preserves eligible refused selections and existing search enhancement.

Home creation, table creation, roster addition and member rename retain non-sensitive declared fields and their errors for one redirect, scoped to the destination form and group/member. The destination consumes the draft once, re-resolves membership and opens the failing disclosure. These are server-session drafts, not browser autosave. Inline forms have distinct field IDs. Shared fields associate help and errors with their control, and refused input never produces a success state.

### Set log and canceled set

The reading surface groups play periods, players, settings versions, buy-ins, cash-outs, balance overrides, frozen final results and audit events under written headings. Native section links jump to the principal categories; the page makes no single global chronology claim. Exact amounts remain tabular, actor/time/reason metadata stays visible, reversed entries remain struck with explanations and voided overrides retain their removal information. Final results carry a Final label, revision metadata, signs and direction icons. Payment records and who pays whom are linked to the session page.

A canceled set uses the warm rail vocabulary, written Canceled state, recorded reason, roster and Full game log path. Its copy explains that retained money records remain in the log and that the set has no final result. No join, money or final-result action appears.

### Sheets

Focused buy-in and player-detail tasks use a native modal dialog outside the polling region. The close control, Escape and outside click close it; keyboard focus stays within the dialog and returns to the opener. Typed values persist during updates; refused submissions reopen the matching form with the exact values and an error. Native details and forms provide the fallback when sheets are unavailable.

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

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

The system is dark, compact and tactile, suited to a dim room and one-handed use. This record captures the built shared foundation and slice 1: the active set, player rows, buy-in sheets and player detail sheets. Later screens inherit shared controls and tokens but retain their existing composition; their layout is not an approved Rack pattern. The approved HTML/CSS study is the visual authority. The build ships no raster imagery.

**Key Characteristics:**
- Warm dark rails and indigo felt.
- Compressed, tabular figures with right-aligned player amounts.
- Bone pressable controls and visible brass focus.
- Circular initials paired with written player names.
- Compact phone rows and focused sheets.

## Colors

The palette combines warm dark supports with a cool indigo working field and pale tactile controls. Frontmatter preserves the stylesheet's canonical colour formats; CSS aliases resolve to these primitives.

### Primary

- **Bone:** primary actions, strong figures and readable foregrounds.
- **Indigo Felt / Deep Felt / Felt Ink:** the active-set field, its supporting palette and readable secondary labels.

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

The timer and blinds use 70% width, weight 800 and line height 1.2. On phones they are 22px; chips-game blinds are 16px. At desktop they are 27px. They are supporting figures, not a second display role.

**The Figure Rule.** Keep money and timers tabular. Use compressed display figures for the active total and quieter right-aligned amounts in player rows.

## Layout

Shared pages are centred in a 560px container with a 16px inset. The active-set page extends to 1180px. Phone composition stays in one column: felt overview, compact player list and an opaque bottom host dock. Bottom clearance is 128px; the dock accounts for the safe area and can scroll when expanded.

The overview has a flexible amount column and a 116px supporting column, separated by 8px. Player rows align a 44px identity token, flexible name, right-aligned amount and action. Below 360px, the token becomes 36px and the row gap becomes 6px.

At 900px and above, the active-set layout becomes a 400px left column plus flexible player list, with a 28px gap and 28px page insets. The left column sticks below the header at 90px. The host action returns to the document flow and rebuy controls display their written label.

Sheets are at most 440px wide and 85dvh tall, scrolling internally. They sit against the phone's bottom edge and become centred at desktop. Quick amounts occupy four equal columns with an 8px gap. Shared form stacks and field gaps use the spacing values in frontmatter; there is no additional invented spacing scale.

## Elevation & Depth

Depth comes from tonal rails, fine rules and CSS-built felt grain. Buttons have a short solid underside that disappears on press. Sheets and the host action use stronger shadows to separate them from the working surface; ordinary cards remain flat.

The sidecar records the built shadows, timings and easing curves. Sheet entry moves 24px in 320ms; exit takes 200ms. Accepted-change attention uses a 600ms treatment and remains labelled briefly. Chip-edge entry accompanies a confirmed rebuy. Reduced-motion preferences suppress animations, transitions and button displacement.

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
- **Don't** treat deferred screen compositions as approved Rack patterns.
- **Don't** use colour alone to identify a player or communicate wins, losses or updates.

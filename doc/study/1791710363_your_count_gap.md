# "Your count" touches the panel above it: study

Date: 2026-10-11, Asia/Manila.

## Report

The human said: "the your count UI awkwardly overlaps the upper part of the UI for non-host participants in the count up pages."

## Reproduced

A player (`ben`) on a set that is counting up, in headless Chrome, with the fixture `seed.py` + `seed_player_entries.py` and play ended.

| Width | Bottom of the overview panel | Top of "Your count" | Gap |
|---|---|---|---|
| 390px | 228 | 228 | 0 |
| 320px | 228 | 228 | 0 |
| 900px | (first column) | 133, level with the overview in the second column | not stacked |
| 1280px | (first column) | 133 | not stacked |

On a phone the "Your count" card starts on the very pixel where the overview panel ends. The overview is full width with 26px rounded lower corners; the card is inset 16px with its own border and 16px corners. With no space between them the card's upper edge sits inside the curve of the overview's corners, so it reads as tucked under, or overlapping, the panel above. From 900px the two are side by side and nothing touches.

## Root cause

`static/css/app.css`, from the count-up revamp of 2026-10-10 (`974779f`):

```css
.own-count-lead { margin: 0 0 var(--s-5); }
```

The top margin is zero. The host's page does not show it, because there the first thing under the overview is the "Player counts" heading, which has its own space above (`.count-v2 .count-workspace > .section-heading { padding: var(--s-2) 0 0; }`). The player's page puts the card first, and the card was given no space of its own. The revamp's browser check looked for the block and its place in the order, not for the distance above it.

The same zero gap applies to every state of the card: empty, "You entered …", "The host confirmed …" and "You are cashed out".

## Fix

Give the card space above it on a phone, where it is stacked under the overview, and none from 900px, where it stands beside it. 16px (`--s-4`), the page's standard gap between a panel and the block after it.

## Risk

Small: one rule, one screen, players only. The count fields and the order of the page do not change.

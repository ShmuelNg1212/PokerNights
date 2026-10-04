# Collapsible host dock: study

Date: 2026-10-04, Asia/Manila.

## Request

The human wants the menu at the bottom of the phone screen to be collapsible, through the whole life of a set: preparation, opening the set, play, cashing out and settlement.

## What the menu is today

The menu is the host dock: `templates/web/_host_controls.html`, a `div.host-controls`. Below 900 px it is fixed to the bottom of the set page (`static/css/app.css`, the `max-width:899px` block). From 900 px it sits in the left column in normal flow.

Only a host sees it, and only on the set page (`/s/<id>/`) in four states:

| Set state | Dock content on a phone | Space reserved under the page |
|---|---|---|
| Draft (`setup`) | Open for players, More host controls | 128 px |
| Open (`open`) | Opening buy-in checkbox and its help, Start the set, Back to draft, More host controls | 340 px |
| In play (`running`) | End play and count up, More host controls | 128 px |
| Counting up (`reconciliation`) | Count preview, next action (Cash out counted players or Finalize results), written guidance, More host controls | 200 px, or 370 px with the count preview |

On a 390 × 844 phone the open and count-up docks cover about 40% of the screen. The player list and the count fields scroll in what is left. That is the cost the request removes.

These pages have no bottom menu, so the request changes nothing on them:

- Cash-out review (`templates/ledger/cash_out_counted.html`): its button is in the page flow.
- Finalized set (`_final_set.html`): its link is in the page flow.
- Session page with settle-up (`night.html`): no fixed element.
- Any page seen by a player who is not a host.

## Constraints found in the code

1. **Polling replaces the dock.** `static/js/live.js` sets `region.innerHTML` every time the set version changes. It restores open `details[data-key]` and typed `data-keep` values, nothing else. A collapsed state stored on an element inside `#live` would be lost on each poll. A state stored outside the region (a class on `<html>`) survives with no restore step.
2. **The primary action is positioned twice.** `.host-controls .next-action` is `position: fixed` on its own, and the dock around it is also fixed. Inside a fixed dock that scrolls (`max-height: 75dvh; overflow: auto`) this works only because the dock has no transform. The collapse must not add a transform or a clip to the dock.
3. **Bottom clearance is hand-set.** Four `padding-bottom` rules (`128px`, `200px`, `340px`, `370px`) use `:has()` to match the dock content. A collapsed dock needs its own, smaller value, or the page keeps a large empty band.
4. **Direct-child selectors.** Rules such as `.table-layout .host-controls > p` and `> form` depend on the dock's children being direct. A wrapper element around the content would break them.
5. **Browser checks depend on the dock.** `web/tests/browser/opening.mjs`, `counts.mjs` and `end_set.mjs` assert that the last row clears the dock and that the dock guidance is visible. Fifteen scripts click `.next-action`. They pass only if the dock starts expanded.
6. **No-JavaScript fallback.** Sheets follow the pattern "markup works without JavaScript; a class on `<html>` turns the enhancement on" (`sheets-enabled`). The dock should follow it: without JavaScript there is no toggle and the dock is expanded.
7. **Storage can be refused.** `changes.js` and `sheets.js` wrap `localStorage` in `try`. A refusal must leave the dock working, only not remembered.
8. **Hidden options carry money.** In the open state the checkbox "Add usual buy-in for players without a buy-in" is checked by default, and Start the set then records buy-ins. In count-up, Finalize results freezes results and its guidance says to check the cash-outs first. If the collapsed dock kept the primary button, a host could start or finalize with the option and the guidance out of sight.
9. **Design rules.** 48 px targets, visible focus, reduced motion disables movement, dark single-column phone layout (AGENTS.md rule 9, DESIGN.md).

No model, service, view or URL is involved. The server renders one more element; the rest is CSS and one small script. Design rules 1 to 8 and 10 to 11 are untouched.

## Options for the collapsed dock

**A. A single bar that names the next step (recommended).** Collapsed, the dock is one 48 px row: "Host controls", the next step in muted text ("Next: Start the set"), and a chevron. Tapping it expands the dock. Every action, option and line of guidance is visible before the host can act. Cost: the main action takes two taps while collapsed.

**B. Keep the primary button, fold the rest.** Collapsed, the dock is the primary button beside a round toggle. One tap to act. The height is about the same as A. Cost: constraint 8. Start the set would submit a hidden, checked opening-buy-in option, and Finalize results would lose its guidance.

**C. Hide the dock while scrolling down, show it on scrolling up.** No control to learn. Cost: it moves on its own, needs scroll handling against the on-screen keyboard during count-up, and conflicts with reduced motion. It also gives the host no way to keep it closed.

A is recommended because this app records money and option 8 is a real way to record buy-ins nobody meant to add.

## Where the state lives

A class `dock-collapsed` on `<html>`, mirrored in `localStorage` under one key for the browser. One preference for all sets and all states: a host who collapses the dock while seating players wants it to stay collapsed when the set starts. The default is expanded, which is today's screen, so nothing changes for a host who never taps the toggle and the existing browser checks stay valid.

## Risks

- **First paint.** `dock.js` is deferred, so it applies the class after parsing. A collapsed dock may show expanded for one frame on a slow phone. Accepted; an inline script in `<head>` would remove it but adds an inline script to every page.
- **Keyboard focus across a poll.** If the toggle has focus when a poll replaces the region, focus falls to the body. The script must put it back on the new toggle.
- **Expanded dock grows by the toggle row.** The four clearance values need re-measuring at 320, 390 and 1280 px (see the footgun on mobile overflow checks: compare against the requested width, and inspect the capture).

## Addendum, 2026-10-04: the human's reason

The human gave the reason after reading the plan: on the pages before results are finalized, the bottom menu with its buttons takes half the screen and the page content is hard to see. That is the count-up state (370 px reserved with the count preview) and, to a lesser degree, the open state (340 px).

Consequence for the design: count-up is the state where the dock will most often be collapsed, and it is also the state where the dock holds something the host reads while typing, the live count preview. Hiding the preview completely would trade one loss for another. The collapsed bar in count-up therefore carries the live verdict line ("₱200 still to account for. 2 still to count.") in place of the "Next:" text. `static/js/counts.js` writes each preview value to one element today (`box.querySelector`); it must also write the status and coverage to the bar.

Options A, B and C and the recommendation are unchanged.

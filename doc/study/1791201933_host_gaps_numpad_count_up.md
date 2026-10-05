# Host control gaps, an in-app numpad, and the count-up to finalize flow: study

Date: 2026-10-05, Asia/Manila. Earlier work this builds on: [collapsible host dock](../plan/1791111069_collapsible_host_dock.md), [dock behind the keyboard](../plan/1791184990_dock_behind_keyboard.md), [live counted total](../plan/1791089905_live_counted_total.md), [motion overhaul](../plan/1791186717_motion_overhaul.md), [redesign slice 2](../plan/1791050738_redesign_slice_2.md).

## The request

The human, 2026-10-05:

1. "the host control buttons dont have a space inbetween them make it so that the space in between is uniform with the rest of the buttons."
2. "For the inputs requiring typed numbers, I want to use a numpad integrated within the webapp instead of the native keyboard inputs. This is to make the overall flow of the app much cleaner."
3. "critique the counting up UI until the finalize UI and suggest improvements."

They asked for the design and motion skills, and allowed the work to be split between agents.

## How this was studied

A fresh temporary database with the synthetic fixtures (`seed.py`, `seed_end_set.py`, `seed_night.py`, `seed_opening.py`, `seed_counts.py`), served locally and driven in headless Chrome at 390, 1280 and, for overflow, 320 and 360px. Nothing in the repository or in production was changed.

The critique followed the design skill's method: two separate passes that did not see each other's work. One was a design review that walked the whole flow as the host on one set (type counts, confirm, review, cash out, finalize). The other ran the skill's detector and measured the pages (sizes, gaps, contrast, overflow, focus order, reduced motion). I checked the main findings of both against their screenshots before using them.

Limits: every count-up fixture has two players, so figures for six to nine players are worked out from measured row heights. Headless Chrome has no on-screen keyboard. Only a real phone confirms keyboard behaviour.

## 1. Host control gaps

### What is wrong

On a phone the host's main buttons touch each other. Measured at 390px:

| Set state | Pair | Gap |
|---|---|---|
| Draft | "Choose rake before buy-ins" and "Open for players" | 0px |
| Open | "Start the set" and "Back to draft" | 0px |
| Any | last main button and "More host controls" | 6px |
| Any | buttons under "More host controls" | 8px |
| Any | a field and its button inside an opened option | 12px |

At 1280px the same main buttons are 12px apart and the ones under "More host controls" are 8px apart, so desktop is uneven too, only less visibly.

### Cause

`.host-controls` is a `.stack`, which puts 12px above each following child. A phone-only rule from the first dock, `.table-layout .host-controls > form { margin: 0; }` (`static/css/app.css`), removes that space from every form, and each main button is inside its own form. The list under "More host controls" has its own rule with 8px.

### Direction

One gap between every two neighbouring controls in the host controls, at every width: 8px, the value the rest of the list already uses. The space between a label, its field and its button inside an opened option stays as it is, because that is form spacing, not button spacing.

## 2. Typed numbers and the native keyboard

### Every field that takes a typed number

| Where | Field | When it is used |
|---|---|---|
| Buy-in or rebuy sheet | Amount, with Min / Default / 2 × / Max | During play, many times a night |
| Cash-out, in a player's sheet | Amount | During play |
| Count-up | One "Final count" per player | End of each set, six to nine in a row |
| Count-up, player Details | Buy-in amount (late buy-in) | Rare |
| New session, Set settings, presets | Small blind, big blind, minimum, maximum and usual buy-in | Before play |
| The same forms | Rake percentage, flat rake | Before play |
| New table | Seats (2 to 12) | Rare |

All of them are ordinary text fields with `inputmode="decimal"`, except Seats, which is a number field. Money is parsed on the server (`ledger/money.py`), pesos with up to two decimal places and chips as whole numbers.

### What the native keyboard costs today

- It covers about 40% of the screen and, on an iPhone, sits on top of the host dock. `static/js/dock.js` spends about a hundred lines measuring the visible frame every animation frame to keep a one-line bar above the keyboard. That code needed three versions and is recorded as a [footgun](../wiki/footguns/ios_keyboard_covers_fixed.md).
- It offers a decimal key in a chips game, where a decimal is always an error.
- It has no "next player" key. During count-up the host taps a field, types, finds the next field under the keyboard, and repeats.
- The page length changes when it opens and closes.

### What an in-app numpad can and cannot do

The field stays a real text field. The script gives it `inputmode="none"`, which tells a phone not to open its keyboard, and the numpad writes into it. That keeps everything that depends on a real field: the form still submits the same value, the count preview and live updates still see typing, a refused value still comes back in the field, a physical keyboard still types into it, and a screen reader still reads it.

It also makes the change fail safe, which matters because changes are tried on the live site: the script switches the native keyboard off only after the numpad is on the screen. If the script does not load or throws, the fields behave exactly as today.

Things it cannot do: paste from another app into the field still works through the phone's own menu, but there is no dictation and no password-manager style autofill. Neither applies to money amounts.

### Two shapes are needed

- **In a sheet (buy-in, cash-out):** the sheet already is the focused task. The numpad is part of the sheet, under the amount and the quick amounts. Nothing rises or falls.
- **On a page with several number fields (count-up, the stakes forms):** a panel fixed to the bottom of the screen that appears when a number field is tapped and names the field it is writing to. It carries Next and Done. During count-up it takes the dock's place and shows the running total, which is what the one-line bar above the keyboard does today.

### Keys

Digits 1 to 9, 0, delete, and one key that depends on the field: a decimal point where the field allows one (pesos, percentage), a double zero where it does not (chips, seats). Keys that cannot produce a valid value do nothing: a second decimal point, a third decimal place, a digit past the largest amount the server accepts.

### Movement

From the motion skill and the built motion system (`static/js/motion.js`, DESIGN.md):

- The panel rises with the existing sheet spring and leaves with the existing 200ms exit. Only `transform` moves, so it runs on the compositor.
- Keys are ordinary buttons, so they already sink 3px under a finger and spring back. A key acts when the finger goes down, not when it lifts, so fast entry never drops a digit.
- A typed figure appears at once. No digit animates in, by the Accepted Change Rule.
- A refused key gives the field the existing short nudge.
- Moving to the next field scrolls the page smoothly so the field clears the panel.
- Reduced motion: the panel appears and disappears at once, keys do not travel, the scroll is instant.

### Where a pointer and a keyboard are present

On a computer the numpad would be in the way. It is offered only where the main pointer is a finger (`pointer: coarse`).

## 3. Critique: count-up to finalize

Method: two separate passes (design review, and detector plus measurements). The flow is four screens: count-up, the cash-out review, count-up again with every player cashed out ("Finalize results"), and the final results.

### Score

| # | Heuristic | Score (0 to 4) | Main issue |
|---|---|---|---|
| 1 | Visibility of system status | 3 | The success message covers the dock's verdict and its button; the one-line bar shows unsaved figures with no "Preview" label |
| 2 | Match with the real world | 2 | "Recorded cash-outs" and "Total cashed out" name one figure; "batch" and "accounted" are ledger words |
| 3 | User control and freedom | 2 | Finalize is one tap with no confirmation and no undo; typed counts are lost on leaving the page |
| 4 | Consistency and standards | 2 | A row's "Confirm count" confirms every row; two or three primary buttons at once; three totals blocks with different labels |
| 5 | Error prevention | 2 | The review does not say when a batch leaves the books off; the dock's main button ignores typed counts |
| 6 | Recognition rather than recall | 3 | A confirmed count is not shown in its field |
| 7 | Flexibility and efficiency | 3 | One form confirms all counts and one batch cashes everyone out, but there is no move to the next field and rows are tall |
| 8 | Aesthetic and minimalist design | 2 | The same equation twice; rake rows at zero; three instruction paragraphs |
| 9 | Error recovery | 3 | The discrepancy panel is very good; the count field's error does not say what the allowed amount is |
| 10 | Help and documentation | 3 | Inline and in context, but too much of it, and host instructions are shown to players |
| | **Total** | **25 of 40** | Acceptable; the money model is strong, the phone layout is not |

Cognitive load: four of eight checks fail (single focus, chunking, visual hierarchy, minimal choices).

### What works

- **The discrepancy panel.** The signed amount at large size, a plain cause, where to look and a next step. The override asks who absorbs the difference and requires a note.
- **The one-line bar while typing.** "₱1,950 of ₱2,000 bought in / ₱50 missing. 0 still to count." updates as the host types. It is the right instrument for the moment.
- **Honest money.** Figures show accepted values only, the preview is labelled, and the review states that it "does not finalize the set and it marks no payment".
- **Measured basics hold.** No text pair is under 4.5:1. No horizontal overflow at 320, 360 or 390px, including the long-name fixture. With reduced motion nothing animates. No console errors.

### Priority issues

**1. The phone screen puts three summaries ahead of the work. (P1)**
At 390 × 844 no player row is in the first screen. The first count field is 1,220px down the page. The expanded dock is 288px, 34% of the screen, and at most one of two rows is fully visible at any scroll position. The "Confirmed counts" block is on the page twice, once in the overview and once in the dock directly below it, with identical figures until the host types; then only the dock's copy changes. "2,000 chips bought in" appears in four blocks. A count row is about 315px tall, so nine players are about 2,800px of scrolling.

**2. The dock's main button ignores typed counts and loses them. (P1)**
With a count typed but not confirmed, the dock shows "Preview · unsaved counts … 0 still to count" directly above "Cash out counted players (1)". Tapping it opens the review without the typed player, and on return the field is empty. The largest button on the screen does the wrong thing at the moment the host is most likely to press it.

**3. The review does not say whether the batch balances the books. (P1)**
With a count ₱50 short, the review shows "After this batch ₱1,950" and "Total bought in ₱2,000" as two ordinary rows and one small grey sentence, and the button reads "Cash out 2 players" exactly as it does when the books balance. This is the last cheap moment to catch a miscount. After it the fix is a reversal with a typed reason, or an override.

**4. The success message covers the next action. (P1)**
After the cash-outs are recorded, the message "2 players cashed out; everyone is cashed out." sits on top of "Finalize results" for six seconds, with "Dismiss" above the button. Finalize has no confirmation and no undo in the app. A tap aimed at Dismiss as the message leaves lands on Finalize.

**5. A discrepancy gets the least signal when it matters most. (P1)**
In the first screen of a set whose books are ₱100 off: "2 of 2 players counted or cashed out" at 48px, "₱100 missing." in ordinary text, and a greyed "Cash out counted players (0)". The red panel is below, behind the dock. With an override, the dock says "₱100 missing" directly above an enabled "Finalize results".

**6. The count row repeats itself and hides the confirmed value. (P2)**
Each row has a label "Final count (₱)", a placeholder "Final count", its own button and three lines of detail. A confirmed row shows "Counted ₱900 at 8:02 PM" beside an empty field. Each row's button submits every row.

**7. The final page buries its proof. (P2)**
A host who did not play sees "The set is finalized." as the headline, and "The books balance" is the last line of the page. The total cashed out is labelled "Available to play". A "Live" status stays on a set that can no longer change.

**8. Smaller points. (P3)**
- The one-line bar does not say "Preview" when it shows unsaved figures.
- "Missing", "extra" and "match" look the same: no colour, no icon.
- Heading order is h1, h3, h2, h2, h3, h2. Keyboard focus reaches the dock's buttons before any count field.
- Rake rows show at ₱0 when rake is off.
- A player sees the host's instructions.
- "Full set log" is a 17px-high link.
- The flow uses 18 distinct text sizes, seven of them between 12 and 14.4px.
- An even result reads "– ₱0".

### Detector

The skill's command-line detector reported ten advisory findings, all the same rule ("colour outside DESIGN.md"), and all false: it renders each template partial alone, without the stylesheet, and sees the browser's default black. In the running page it reported low contrast on player chips (false: it compared the initial with the striped rim, real ratios are 5.7 to 10.3), covered text inside closed disclosures (false), and three true but minor points: the skipped heading level, the wide shadow on the dock's main button, and close heading sizes on the review (16, 18.4 and 22px).

### Who is hurt most

- **The host at 1 a.m. with the table waiting** cannot see the players' fields and the running total together unless the dock is folded, and has nothing on the review to read aloud that says "we are square".
- **A one-handed user** scrolls two screens to the first field, and loses typed counts after a visit to the review.
- **A keyboard or screen-reader user** meets two regions both called "Confirmed counts", one of them out of date, and a verdict whose severity is in the words only.

### How the three requests connect

The numpad and the critique meet on the count-up screen. The numpad gives count-up a "Next player" key, removes the decimal key in a chips game, and removes the need to keep a bar above the phone's keyboard for count fields. The critique's first two issues are about the same bottom area of the same screen. Designing the dock, the numpad and the row together avoids building the numpad around a layout that then changes.

## Constraints that shape the plan

- No service, model or migration change is needed for any of this. Counts, cash-outs and finalization keep their services and rules.
- Fields in the live region keep `data-keep`, and count fields stay in the one counts form ([footgun](../wiki/footguns/one_form_per_row_loses_typing.md)).
- A new script registers with `page.js` and stops when the page is left ([footgun](../wiki/footguns/scripts_run_once_per_tab.md)).
- Without JavaScript every form must still work with the phone's keyboard.
- The user tries changes on the live site, so each stage must fail safe and be releasable on its own.

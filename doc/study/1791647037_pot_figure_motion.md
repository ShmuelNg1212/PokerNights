# Pot figure motion: study

Date: 2026-10-10, Asia/Manila.

## Request

The human said: "can you add animations for the live count when someone buys in." Asked which movement, the human chose "Roll digits + delta": the digits that changed roll to the new value, and the amount added rises beside the figure.

"The live count" is read as the large "Still in play" figure at the top of a set in play. The human was told this reading when asked and did not correct it.

## What happens today

When a buy-in is accepted, by this person or by anyone else, the set page is redrawn within four seconds (`live.js`) or at once for the person who sent it (`turbo-setup.js`). Then:

- The player's row is marked in brass, a new edge drops on their buy-in stack and "Rebuy added" springs in (`changes.js`).
- A brass line draws under "Still in play", holds and fades.
- The figure itself is replaced with the new amount in one frame. Nothing shows how much was added.

So the row says who bought in, and the pot says only that something changed.

## Constraints

1. **The money rule.** DESIGN.md, motion system rule 3: "Money does not animate its value. A row may move; digits do not count." The set page rules repeat it: "Rows, edges, badges and rules move; digits do not." The human's choice changes the second half. What the rule protects stays: no amount other than the accepted one can be read at any moment. See "The rule" below.
2. **The page is redrawn whole.** A poll replaces the live region's HTML; an action sent in place morphs it. Anything added to the figure must be built after the redraw and must not be there at rest.
3. **Transform and opacity only,** as everywhere else on the set page.
4. **Never in the way.** Rebuy and every other control work while the figure moves.
5. **Reduced motion, a hidden tab, no Motion, first sight of a set:** nothing moves.
6. **No preview deployments.** The human tests on the live build on a phone. If anything is off, the figure must be the plain figure it is today.
7. **Amounts are integers** (AGENTS.md rule 1). The amount added is a difference of two integers in the set's unit. No `float`.
8. **A figure can change width** (₱9,500 to ₱10,000) and can switch to its smaller "long" size.

## Options for the figure

**A. Changed digits roll; the rest stay (chosen).** The figure is drawn one character per cell for the length of the movement. A cell whose character changed sends the old one out and brings the new one in, upward for a rise and downward for a fall. Unchanged characters, the peso sign and the separators stay still, or glide if the figure got wider. The new amount is the page's text from the first frame; only the drawing of the changed digits moves.

**B. Count through the values.** ₱4,000, ₱4,100, ₱4,200 … ₱4,500. Shows amounts that were never recorded. Not chosen.

**C. Digits still, only the amount added shown.** Not chosen.

## The amount added

A small "+₱500" beside the figure tells what the redraw cannot: how much. It is the difference between the amount shown before and the amount shown now, so two buy-ins that arrive in one update show their sum.

The browser has to write that amount in the app's format (`₱1,600.50`, `1,600 chips`). The format lives on the server. To avoid a second copy that could drift, the browser's version is checked on every use: it must write the new total exactly as the server did in the figure. If the two differ, the amount added is not shown.

## What else lowers or raises the figure

"Still in play" also falls when someone cashes out, and changes when a buy-in is reversed. The same figure moving for one cause and jumping for another would look broken, so the plan proposes one behaviour for every change, with the direction and the sign following the change. This is a decision for the human.

## The rule

The numpad cycle ([study](1791538181_numpad_digit_motion.md)) already narrowed "a digit appears whole and at once" to "the digit shown is always the true digit; it may fade and rise into place. No number rolls or counts." This cycle goes one step further for one figure: a changed digit of the pot is replaced by a short roll.

What is honest to say about it: for about a quarter of a second, a cell that changed shows the old digit leaving and the new one arriving. The figure never reads as a third amount, never passes through values in between, and the page's text (what a screen reader and a copy would get) is the accepted amount throughout. Counting through values stays forbidden everywhere.

## What stays outside this cycle

- The player's row, the stack edge, "Rebuy added" and the brass underline. They stay as released.
- The "₱X bought in · N buy-ins" line of a set that has not started.
- Count-up totals, results, settle-up and every other figure.
- Sound and vibration.

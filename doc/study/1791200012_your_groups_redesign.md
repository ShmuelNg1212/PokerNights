# Your groups: one settings button and a new layout: study

Date: 2026-10-05, Asia/Manila. Earlier work on this page: [Your groups home](../plan/1791102439_your_groups_home.md).

## The request

The human, 2026-10-05: on the group cards of Your groups, "instead of having three separate buttons (sessions, stats, group settings) i just want one clean button that opens a group settings menu for that group. After that utilize redesign skills to revamp how the 'your groups' page should look like."

Asked three questions, the human answered:

1. **The button** goes to that group's Group settings tab. The group's name still opens the group.
2. **Scope:** a new layout in the same look. The app's dark, warm look, type and colours stay.
3. **What bothers them:** the page "looks plain or unfinished", and there is "too much small text".

## The page today

Captured at 390 and 1280px from the test fixture (one group, a set in play).

- "Your groups" heading, then each group as a run of text separated by a thin line. A group has no surface or edge of its own; only the set-in-play band is a shape.
- In reading order: the group's name with a Host badge; a row of player chips with "14 players"; the band (table name, "8 at the table · timer under 1 min", one button); "11 more open sessions"; a "To settle" list when the viewer owes or is owed; "Your record" and "Last session" as label-and-figure lines; three underlined links (Sessions, Stats, Group settings); and, last on the page, "Create another group" as plain text.
- Small text on one card, counted from the template: the player count, the band's facts line, the more-sessions line, a caption under each "To settle" line, a caption under "Your record", a caption under "Last session", "You did not play", and the three links. Up to ten pieces at 15px or less.
- At 1280px the page is one 760px column; with several groups the cards sit in two columns divided by lines.

## What the page is for

From PRODUCT.md and the earlier plan: after sign-in, tell the viewer each group's state, the one action they are needed for, what they owe or are owed, their record and their last result. A set in play is one tap away. This does not change.

## What the data offers

`web/views.py` already gives each card: the group and the viewer's role; up to six member chips and the member count; the kind of state (a set in play, an open session, or nothing in progress) with its table, set, facts and one action; a count of further open sessions; dues; the viewer's record per unit; the last session and the viewer's result in it; whether the group has stats. No new query is needed for a new layout.

## Findings

1. **Why it looks unfinished.** A group is the main object of the page and has no body. Everything is type on the page's ground, so the eye has one shape (the band) and a column of lines. The rest of the app gives its main objects a surface: the felt overview on a set, the rail panels on a session.
2. **Why there is too much small text.** Figures that matter (record, last result, what is owed) are set as a caption beside a mid-sized number, and each carries a second caption. Counts are written as sentences ("14 players", "11 more open sessions").
3. **The three links repeat** what the group's name already does (it opens the group on Sessions, where Stats and Group settings are one tap away).
4. **"Create another group" reads as a stray line,** not as an action.
5. **Things other work depends on** and must stay: the name link in the card's heading and the band's title are what stage 3 of the motion overhaul carries to the next screen; `navigate.mjs` taps the group link on a card; `test_home.py` asserts the states, figures and privacy rules.

## Options for the button

- **A round button with a gear icon in the card's top corner,** named "Group settings" for screen readers. The cleanest; it uses no line of the card. A gear is widely understood, but it is an icon without a word.
- **A written "Group settings" button across the foot of the card.** Unmissable; it adds a row and a second full-width button under the main action.

## Recommendation

Each group becomes a card with a surface and an edge. Inside, three parts in a fixed order: who (name, chips, the settings button), now (the band with the one action, or the quiet state), and you (what you owe, your record, your last result) with the figures set large and their captions cut to one short line each. Counts become numbers on chips and rows, not sentences. The settings button is the round gear in the top corner. "Create another group" becomes a real button at the end of the list.

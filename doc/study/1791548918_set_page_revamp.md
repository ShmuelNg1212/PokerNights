# Set page revamp, preparing and in play: study

Date: 2026-10-09, Asia/Manila. Request: "lets revamp the UI while a set is being prepared and ongoing."

Skills used: the design skill (impeccable, `shape`) and the motion skill. Captures were taken from a seeded temporary database as a host and as a player, at 390 × 844 and 1280 × 800, for a draft, an open and a running set.

## What the human chose (2026-10-09)

1. **Goal:** all three: faster during play, clearer preparation, a more premium look.
2. **Player rows during play:** Rebuy on the row, the rest behind a tap. This changes the UI evolution decision that both actions are written on every row.
3. **Preparation:** a short checklist in place of the panel of totals.

## Scope

One page, `templates/web/session.html`, in three of its states: `setup` (shown as a draft), `open` and `running`. Count-up, cash-out review, final results, the session page and the set log are not part of this.

The page is built from `_session_live.html` (the lead panel and the layout), `_players.html` (the list, the row actions and the sources of the sheets), `_host_controls.html` (the host's menu, a bottom dock on a phone) and `_player_actions.html` (a player's records inside their sheet).

## What is there today

### Preparing (draft and open)

- The lead panel is the in-play panel on a neutral surface. An empty draft therefore opens with "Still in play ₱0", "Set timer not recorded" and four rows of zeros (total bought in, cashed out, collected rake, available to play), then "Rake is Off." and "Draft · players cannot see this set yet."
- The steps a host actually takes are in three places: **Add players** beside the list heading, **Choose rake before buy-ins** and **Open for players** in the host menu, then, once open, the opening buy-in option and **Start the set** in the same menu. Nothing says which are done.
- The badge reads "Setup"; the text under it and the menu say "draft".
- On a phone the host menu of an open set (option, help line, Start, Back to draft, More) is about 520px tall and covers the player list.

### In play

Measured on the 390 × 844 capture, as a host with eight players:

| Thing | Height |
|---|---|
| Top bar and back link | 117px |
| Felt panel | 351px |
| Players heading, Add players, Join this set | 111px |
| One player's row | 142px |
| Host menu, expanded (the default) | 166px |
| Whole page | 1,758px |

- The first player's Rebuy and Cash out buttons sit under the host menu on the first screen. No row is fully usable without a scroll.
- A row is 142px because two full-width 48px buttons sit under the name. Eight players are 1,136px, about two and a half screens.
- The panel always shows six facts under the main figure. During play a host reads one of them often (still in play) and the rest rarely.
- A host who is not seated sees "Join this set" above every player.
- A player's own row is wherever they joined; in the capture Ben is last of eight, a screen and a half down, and that row holds the only thing he can do (Rebuy).
- From 900px the page is already good: a 400px panel and a list where each row is one line with both buttons.

### What works and should stay

- The felt panel and its large condensed figure are the identity of the app. Felt appears only for a set in play.
- Player tokens with written names; amounts right-aligned in tabular figures.
- Sheets for one task, with the app's own number keys.
- The live behaviour: rows are watched by `data-watch` and `data-value`, updates morph in place, typed values and open sections survive, changed rows are marked. `flow.js`, `changes.js`, `live.js`, `sheets.js`, `dock.js` and `numpad.js` depend on this structure.
- Every action is a native form or a native disclosure first, so the page works without JavaScript.

## Findings

1. **Two different jobs share one layout.** Preparing is a sequence with a clear end (start). Playing is a loop of two actions (rebuy, cash out) on a list. The layout was designed for playing and reused for preparing. They should share the frame and the list, not the lead panel.

2. **The checklist needs no new data.** Each step can be read from what the page already has: the number of players and free seats, the settings version (blinds, buy-in limits, usual buy-in, rake rule), the state, and the totals. Which step is next follows from the state and the player count. No model, service or query changes.

3. **Money facts should appear when there is money.** Before the first buy-in every figure is zero. One line ("₱500 bought in · 1 buy-in") is enough in preparation once there is something to say.

4. **A short row is possible at 390px, and tight at 320px.** One line holds a 40px token, the name with its buy-in line, the amount and one written button of about 96px. Under 360px the amount has to move under the name. The whole row outside the button becomes the target that opens the player's sheet; today only the name is.

5. **Cash out moves into the player's sheet.** Today there are three sheets per player (buy-in or rebuy, cash out, details). With the row opening the player's sheet, that sheet has to lead with Cash out and keep the records and the removal below. Whether one sheet can open another is not known from reading `sheets.js` and is the first thing to try in the build; the fallback is the cash-out form inside the player's sheet.

6. **The panel can shrink without hiding a fact.** The main figure, the timer and the blinds stay. The six facts under them become one summary line with a native disclosure for the rest. Rake rows show only when rake is on, as on the final page. On a phone this takes the panel from about 351px to about 230px. From 900px the left column has the room and can keep the facts open.

7. **The host menu during play is one rare action.** "End play and count up" is pressed once per set, yet the expanded menu covers 166px of the list all night. The fold already exists; the question is only its default while a set is in play.

8. **Rows must not reorder while a set is live.** DESIGN.md, motion stage 2: "Rows only arrive and shift. Nothing reorders or leaves." So players who left are not moved to the end. A viewer's own row can still be placed first, because that is where it is drawn for that viewer from the start, not a move.

9. **Words.** "Setup" and "Running" are the stored names of states. The app elsewhere says "draft" and "In play" (the home card's badge). The page should use one set of words: Draft, Open, In play.

10. **The premium part is finish and one moment.** The system (colours, type, radii) is right and stays. What is missing is a considered composition at phone size and an answer when the set changes state. Starting a set is the one moment of the night that deserves a signature: the neutral panel becomes felt and the timer begins. Everything else uses the presets that exist.

11. **Risk is concentrated in the live page.** Nine browser scripts and several Django tests name this page's classes. It is also the screen a host is on during a real game, and the human tests on the live site. The codebase already has the answer: `_session_legacy.html` and `_group_stats_legacy.html` are earlier layouts kept behind a switch. The same can be done here for one release.

## Constraints

- Design rules 1, 7, 8, 9 and 10 of AGENTS.md: integer amounts in the set's unit, totals are queries, the display formats, 48px targets, single column on a phone and two from 900px, money figures at their accepted value.
- PRODUCT.md: keep total bought in separate from money still in play; show success only after the server accepts; preserve typed values during live updates.
- Motion: money does not animate its value; rows carry money and move without bounce; interactions end within 300ms and a signature moment within 900ms, once.
- No migration and no change to accounting, permissions or what each action records.

## Not studied

Count-up and the end of a set (reworked on 2026-10-05), seating, a tournament clock or blind levels, and any new figure on the page.

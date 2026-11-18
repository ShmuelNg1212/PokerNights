# Study: table moments (blinds change, count-up progress, row press)

Date: 2026-11-18. Mode: design. Skills: `/impeccable shape` (folded into "Shape" below), `animate`, `mobile-native`.

## Question

This is the second batch of the 2026-11-14 improvement list. The first batch (sheet drag and haptics) is released. The list's order for the second batch is: blind levels going up, then count-up progress. Press feedback on rows was in the first group of the list and is not built. Which of these can the app do within spec.md and DESIGN.md, and how?

## What exists

### Blinds

- spec.md says: "Cash games only (no tournaments, no blind timer)". It lists a blind timer under tournament features, out of scope.
- The app has no blind levels. `clock.js` only adds elapsed time to the set timer.
- The blinds are stakes in a `SettingsVersion`. `games.services.update_settings` accepts a change in `SETUP`, `OPEN` and `RUNNING`. A host reaches it during play through **Set settings** in More host controls (`templates/web/_host_controls.html:91`). Each change is a new version, with `audit.record("session.settings_changed")` and `touch(session)`.
- The set page shows the blinds in the felt: `<strong data-fact="blinds">` in `templates/web/_session_live.html:10`. Other phones get the new figure by the live redraw. Nothing marks the change. A player who looks away misses it.
- Consequence: the list's item "blind levels going up" assumes a feature that the spec excludes. The real cash-game event is a host who raises (or lowers) the stakes during the set. That event exists and passes silently today.

### Count-up

- The count-up head already shows progress: "**4 of 7** players counted or cashed out" (`templates/web/_count_v2.html:9`, `count_complete` from `web/views.py:292`). It has `data-watch="count-progress"`, so `changes.js` gives it the Brass mark when it changes.
- Under it, `.count-pips` has one pip per player with a buy-in. A pip that changes to counted or cashed out fills from the left in 360 ms (`app.css:1832`, `pip-fill`).
- The list's claim "count-up has no motion" read only `counts.js`. It is wrong: the progress motion is in `changes.js` and CSS.
- What does not exist: a meter of money, "accounted of bought in", in `templates/web/_count_total.html`. `ledger.queries.CountTotal` has the values (`accounted`, `difference`, `tone`).
- `static/js/counts.js` updates a local preview from typed counts. It has no motion.
- DESIGN.md, the Accepted Change Rule: "Recorded figures change only to accepted server values. … The count preview adds no movement."
- DESIGN.md, motion principle 3: "Money does not animate its value." The pot is the one exception: its changed digits roll.
- The books-balance moment already exists (`changes.js`, once per set per browser, with a haptic).

### Press on rows

- Buttons sink and spring back (`motion.js:67`).
- Rows and cards already show a pressed background: `app.css:667` (table cards), `app.css:1126` (session, set and home rows), `app.css:1302` (roster), `app.css:1624` (player rows on the set page).
- DESIGN.md: "Rows carry money and move without bounce. Bounce stays on buttons, badges and the buy-in edge."

## Shape

### 1. Stakes change in play

- **Moment.** The blinds figure changes on a live redraw while the set is in play.
- **Mark.** The new figure is there on the first frame. A Brass underline draws under it, holds, and fades, as "Still in play" does. A small label "Blinds up" (or "Blinds down", or "Stakes changed" if only the buy-in limits changed) rises beside the "Blinds" label and fades after 3 s.
- **Haptic.** One `done` pattern on the other phones, because the event changes how each player bets. It is a poll, so the iPhone may stay silent (see the first batch's study). Android vibrates.
- **Mechanism.** Reuse `changes.js`: the blinds figure gets `data-watch="stakes"` and `data-value="{small}:{big}:{min}:{max}"`. `changes.js` already compares the value with the one last seen in this tab, adds `just-changed`, holds 3 s and fades. A new branch picks the label from the integers: up when the big blind rises, down when it falls, "Stakes changed" when only the buy-in limits change. No new script.
- **First sight.** A tab that never saw the earlier value shows no mark. A tab that saw it and comes back (reload, Back) shows the mark once. This is the behaviour of every other watched figure.
- **Reduced motion.** The label shows, still. No underline movement.
- **Not shown.** The host who changed the stakes comes back by a full page load. That page shows no mark: the host knows.

### 2. Count-up progress: mostly built already

- The figure, the Brass mark and the pips that fill already give count-up progress. The books-balance moment ends it.
- Only a money meter is left: a bar of confirmed "accounted / bought in" that moves to each accepted value with the `shift` spring and never with typed counts.
- Recommendation: leave it out. It repeats what the pips say, it adds a second progress figure to a crowded page, and it is the money figure that the Accepted Change Rule guards most. The gain does not pay for the rule risk.
- If the human wants it anyway: the server computes the fill as an integer in basis points, capped at 10,000; the bar moves by `transform: scaleX`; above 100 % it uses the warn tone.

### 3. Press on rows

- **Moment.** A finger goes down on a tappable row or card.
- **Motion.** `scale` to 0.98 with the `press` spring, back to 1 with the `shift` spring (no bounce, because rows carry money). The pressed background stays as it is.
- **Cancel.** A scroll fires `pointercancel`; the row goes back.
- **Where.** Touch only (`pointerType` not `mouse`). Not inside an open sheet while a drag can start.

## Risks

1. **A redraw during the stakes mark.** A second poll can arrive within 3 s. The script must compare with the values before each redraw and restart the mark, like `pot.js`.
2. **The mark and the morph.** A poll morph strips inline styles (footgun `poll_morph_strips_inline_styles.md`). The stakes mark must use classes and `changes.js`'s `data-watch` path, which already survives the morph, not inline styles that must last.
3. **Row scale and the view transitions.** A session card that is tapped starts a shared-element transition. A scale that is still running when the snapshot is taken can make the name jump. The press must reset before the transition starts, or the transition must use the element at scale 1.
4. **Row scale and the player-row stack.** Player rows move with `flow.js`. A second transform on the same element breaks the footgun "press interrupts a combined animation". Scale the inner opener, not the row.

## Left out of this batch

- A stats chart that draws in and a rank-change badge: a later batch.
- Sound and a live-connection pulse: not asked for.
- A tournament blind timer: out of scope by spec.md.

# "Your count" touches the panel above it: plan

Status: approved 2026-10-11 ("ok lets fix this gap and add some ui and animation design using skills and plugins for this"). The scope grew at approval: see "Changes at approval". Date: 2026-10-11, Asia/Manila. Study: ["Your count" touches the panel above it](../study/1791710363_your_count_gap.md).

## Outcome

On a phone, a player's "Your count" card on a count-up page sits clear of the overview panel above it, 16px below, in every state of the card. Nothing else on the page moves. From 900px, where the card stands beside the overview, it is unchanged.

## Implementation

Branch `fix/your-count-gap` from `main`.

1. `static/css/app.css`: `.own-count-lead` gets `margin-top: var(--s-4)`; inside the existing `min-width: 900px` rules it is set back to 0.
2. `web/tests/browser/player_entries.mjs`: one more check at 390px, that the card's top is at least 12px under the overview's bottom, so the gap cannot silently go again.
3. Look once at captures of the player's page at 320, 390 and 900px in three states (nothing entered, entered, cashed out), and at the host's page to confirm it did not move.
4. Run `player_entries.mjs` and the Django suite.
5. Documents: the plan's progress note and TODO.md.

## Acceptance

1. At 320 and 390px the card's top is 16px under the overview panel, with the panel's rounded corners clear of it.
2. At 900 and 1280px the card's top is where it is today.
3. The host's count-up page is pixel-for-pixel where it is today.

## Release

Kept local until you say to push. No migration, no server change.

## Changes at approval

2026-10-11. The human approved the gap fix and asked for design and motion work on the card, with the skills.

Read as a polish of the "Your count" card, not a redesign: its words, its field and what each state says stay as they are (tests and the player-entries check pin them). Added:

- **Where the count is.** Three steps across the top of the card: Counted, Confirmed, Cashed out. A finished step has a Bone rule and a tick (the last one Green, as the count marks above use); the step that is waited for has a Brass rule.
- **Motion thesis.** Focal moment: a step completing. When the count moves on (the player sends it, the host confirms it, the host cashes the player out) the finished step's rule draws from the left and its tick draws, on the player's phone, whoever caused it. Feedback: the card takes the page's standard Brass "this changed" mark for three seconds. Waiting: while the next step is the host's, its Brass rule breathes slowly. Budget: transform, opacity and stroke only; nothing on first sight of the page; reduced motion shows the states still.

## Progress

2026-10-11: Built on `fix/your-count-gap` from `main`; kept local.

- The gap: `.own-count-lead` has `margin-top: var(--s-4)` and none from 900px.
- The steps: a `own_count` template tag works out the stage and each step's state; `_count_own.html` draws them and carries `data-watch`, so the page's existing change marking (`changes.js`) drives the motion. No new script.
- The card's sentences, label, field and button are untouched; the existing Django tests of them pass unchanged.

Verification:

- 1020 tests pass on SQLite (15 skipped), 2 of them new (`web/tests/test_own_count.py`). PostgreSQL was not run: no model or query changed.
- A player's page driven through all four stages by the real services, at 390px: gap 16px; on each move the card was marked and the finished step's rule and tick were animating on the first frame; the waiting step breathed; three seconds later nothing was running. Gap 16px at 320px; the card's top unchanged (133px) at 900 and 1280px. Captures of the four states were looked at once.
- `player_entries.mjs`: 28 pass, 1 fails and the script then stops ("the app's number keys open for the field and name it"). It fails and stops at the same place on `main` without this change (26 pass, 1 fail), so the rest of that script did not run on either. Not looked into. Two of the three checks added to it ran and passed; the third sits after the stop.
- Skills: the design skill's polish and animate guidance and the motion skill's rules were read for this change; the motion thesis is recorded under "Changes at approval".

Acceptance: 1 and 2 are met. 3 (the host's page unchanged) rests on the rule touching only `.own-count-lead`, which the host's page does not have; the host's page was not captured.

Not verified: a real phone; a screen reader; the part of `player_entries.mjs` after its stop. A fresh reviewer did not read the branch.

Documentation synced: wiki features, DESIGN.md, TODO.

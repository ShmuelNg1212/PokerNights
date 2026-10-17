# The header: the way back and the account token: plan

Status: asked for and built 2026-10-17 ("proceed" on the navbar review in the session). Date: 2026-10-17, Asia/Manila. No study: the review in that session stands in for one.

## Outcome

A phone shows one bar above the content instead of two. The header's start is the brand on Your groups and the way back on every deeper page, where it used to sit in a second row under the header. The username and Log out give way to the person's own chip, whose panel holds the username and Log out, so a mis-tap at the table no longer logs anyone out.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. Shaped with the design (impeccable) and motion (animate) skills. No migration, no dependency, no new colour, font or asset, no new switch.

## Behaviour

| Where | The header |
|---|---|
| Your groups | The brand, then (on the right) the bell and the account token |
| A group, a player's page | ← Your groups / ← {group} stats |
| A session | ← {group}; the session's status badge (Open, Partly settled, Archived…) moves beside the session's heading |
| A set | ← Session: {table} and the live status (dot and words; the dot alone below 360px). Below 390px "Session: " is for screen readers only |
| Cash out counted players | ← Back to set N |
| The account token | The username's first letter on a chip in a colour that stays with the account. A tap opens a panel: "Logged in as {username}" and **Log out** (48px). Escape, a tap outside it, the token, or going to another screen closes it; a refresh of the same page leaves it open (it is permanent, as the bell is) |
| Forms with a "Back to …" link in the page | Unchanged: the brand in the header, the return path in the page |

## Look

- One row, 69px as before, at 320, 390 and 1280. The way back is Bone at 1rem/650 with a 20px arrow, takes the room left and ends in an ellipsis on one line.
- The token: a 32px chip in a 48px round target; Rail 2 behind it while open (and on hover with a fine pointer). The panel is the bell's panel (Rail, Line edge, surface radius, soft shadow, caret at the token), with a 40px chip, the label in Bone Dim and the name at 1.0625rem/700.
- An empty live status (before the first answer, or without JavaScript) shows no dot.

## Motion

- The panel: opens with `shift` from the caret (scale 0.96 and 4px down to rest), closes with `leave`. A tap during the close turns it back from where it is. Reduced motion: at once.
- The way back's words: on a deeper or back change they leave 8px towards where the old screen goes (140ms) and the new ones come 8px from the other side (220ms), the ease-out token, inside a header that stays still. Back/Forward and tabs: no movement.
- Getting in on a page without the brand (a group after an invite): the token lands as the brand's mark does (`welcome-land`).

## Bugs looked for after the build, and what was done

1. **The seat draw's mark** was copied from `.brand img`, which a set page no longer has. It now comes from the page's icon link (the same file).
2. **The session status** would have crowded the header at 320px; it moved beside the heading.
3. **The set page refreshes itself** (morph): an open panel would close every few seconds. The token is `data-turbo-permanent`, so it stays open.
4. **"Hide the live status on a final set"** was a sibling selector from the old bar; now `body:has(#live[data-state=finalized])`.
5. **The arrival after a login** had no mark to land on a group page; the token lands instead.
6. **A tap during the close** restarted the panel from transparent; it turns back from its current state now.
7. **Without JavaScript** the token is a native `<details>`, so Log out is still two taps; an empty live status no longer shows a dot nobody checked.
8. **Two panels**: the bell's and the token's each close the other.
9. **The tabs' transition** named the old bar (`page-bar`); the rule went with it.
10. **The caret variable** became `--caret`, shared by both panels.

## Verification

- 1,224 tests pass on SQLite and in the build-like run (`VERCEL=1`). New: `web/tests/test_header.py`.
- `header.mjs` 103 of 103 at 320, 390 and 1280; with the alerts fixtures (`PN_BELL=cal`), 3 of 3.
- `screens.mjs` 46/46, `inplace.mjs` all pass, `alerts_bell.mjs` 45/45, `door.mjs` 128/128, `welcome.mjs` 51/51, `seat_draw.mjs` 50/50, `carried_debts.mjs` 32/32, `night.mjs` 86/86, `settled.mjs` pass.
- `navigate.mjs`: the same two failures on unchanged `main` ("after 22 screen changes … one sheet dialog" and "no poll after leaving the set page"); not caused here.

## Verification after release

On the phone, in the installed app: see TODO.md.

## Release (2026-10-17)

Merged and pushed as `a673477` (previous production commit `8ca7972`). Four minutes later: `/healthz` 200, and the login page loads `account.js?v=06c03b32dd`. Rollback: revert `a673477` on `main`; no migration.

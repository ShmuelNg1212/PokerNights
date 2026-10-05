# Your groups: one settings button and a new layout: plan

Status: approved and built on 2026-10-05; merged and pushed as `f044805` (local remote-tracking evidence). Date: 2026-10-05, Asia/Manila. Study: [Your groups: one settings button and a new layout](../study/1791200012_your_groups_redesign.md).

## Outcome

Your groups looks finished: each group is a card you can take in at a glance, with one button for its settings, the set in play one tap away, and your own figures large enough to read without the small print.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new colours, fonts or imagery.

## Decisions for the human

Approving the plan accepts the recommendations unless you say otherwise.

1. **The settings button is a round gear in the card's top corner,** 48px, which opens that group's Group settings tab. Recommended because it is the cleanest and takes no line of the card. The alternative is a written "Group settings" button across the foot of the card; say so if you prefer the word.
2. **Sessions and Stats lose their own links on the card.** The group's name opens the group on Sessions, and Stats is one tap from there.
3. **Wording that goes or shrinks** (the "too much small text" answer):
   - "14 players" becomes a count on the last chip of the row ("+8").
   - "11 more open sessions" becomes one row, "Open sessions", with the number at its end.
   - "Your record" and "Last session" each keep one short caption instead of two.
   - "You did not play" becomes "Did not play" in the figure's place.
   Nothing that states money is removed.
4. **Players see the same card** as hosts, including the gear: the Group settings tab is already open to players, where it shows what a player may see.

## What you will see

On a phone, top to bottom, for each group:

| Part | Content |
|---|---|
| The card | A raised panel with rounded corners and a thin edge on the page's dark ground; 16px between cards. |
| Who | The group's name, large, which opens the group. Under it the player chips with the count on the last one, and the Host or Player badge. In the top right corner, the gear button. |
| Now | A set in play: the blue felt band, as today, with the table name, one facts line and "Open the table". An open session: the same band in the panel's own colour with its one action. Nothing in progress: one quiet line and, for a host, "New session". Further open sessions: one row with the number. |
| You | "To settle" first when there is anything: one row per person, the amount large at the right. Then two figures side by side: your record and your last result, each a large signed amount in green or red with its icon and one short caption. Pesos and chips records stay apart. |
| After the last card | A full-width "New group" button that opens the same form in place. Archived groups stay below it, as today. |

From 900px wide, two cards sit side by side when there is more than one group. A single group stays one column.

Unchanged: what each state shows and to whom, every figure, the order of groups (a set in play first), the first-group screen, archived groups, and where every remaining link leads.

## Implementation

1. **`templates/web/_group_card.html`** restructured into the three parts. The name link in the heading and the band's title keep their place and classes, because the screen movement of stage 3 carries them. The three links are replaced by the gear link (`aria-label="Group settings for {group}"`).
2. **`templates/web/home.html`:** the create form's summary becomes a button-styled "New group".
3. **`web/templatetags/table_tags.py`:** a gear icon from the icon set already in use.
4. **`static/css/app.css`:** the home block is rewritten with the existing tokens (rail surface, rule edge, the money type for figures). No change to other screens' rules.
5. **`web/views.py`:** no new query. At most the count of players beyond the chips shown is passed to the template.
6. **Tests first.**
   - `web/tests/test_home.py`: each card has exactly one link to Group settings with its name; no Sessions or Stats link in a card's foot; the name still links to the group; every existing assertion about states, figures, units, privacy and query count stays.
   - New fixture `seed_home.py` and browser check `home.mjs` at 320, 390 and 1280px: a group with a set in play, one with an open session, one with nothing in progress, one with dues and records in both units, a 60-character group name, six and fourteen players, a player's view, and five groups. Checks: no horizontal overflow; every control at least 48px; text contrast at least 4.5:1; the gear leads to Group settings and the name to the group; figures never wrap mid-number; the count of text pieces under 16px per card is lower than today's; two columns from 900px with more than one group; "New group" opens the form and a refused name keeps it open; keyboard order follows reading order; without JavaScript everything works.
   - `screens.mjs` (the name still travels from the card), `navigate.mjs`, `lifetime.mjs`.
7. **Verify.** SQLite suite and the build-style run; PostgreSQL before release. One round of captures at the three widths inspected, defects fixed in one batch, one confirming round. The design skill's detector run once over the changed files.
8. **Sync docs.** DESIGN.md (the home card), wiki features, browser README, TODO phone check.

## Acceptance criteria

- AC1. Every check in step 6 passes.
- AC2. All existing tests and the listed browser checks pass.
- AC3. **On your phone:** Your groups reads as finished, the gear is where you expect it, and the small print no longer competes with what matters. Only you can judge this.

## Out of scope

- The group page, its tabs and any other screen.
- New information on the card (for example money still in play, which this page leaves out on purpose).
- New colours, fonts, illustrations or a new look for the app.
- Movement beyond what stages 1 to 3 already give the page.

## Rollback

Revert the commits. No migration and no data change.

## Progress and blockers

2026-10-05: Study and plan complete. The human answered three questions before the plan (button target, scope, what bothers them); they are recorded in the study. Waiting for approval.

2026-10-05: approved by the human ("approved, i like your suggestions. utilize ui design and motion skills if needed"). Built on `home-redesign`. Tests were written first and seen to fail.

Changes from the plan:

1. **The three zones run edge to edge inside the card**; the band is no longer a rounded panel of its own. A panel inside a card read as a box in a box.
2. **More wording went than decision 3 listed,** because the first build still had as much small text as before. Beside a due, and beside "Last session", only the date remains; the table's name is gone from both (the row and the label still link to that session). The line under the last result is gone. "Your record in chips" reads "Your record", since the amount says chips; screen readers still hear "in chips".
3. **Two desktop columns pack by height** and read down the first column, then the second. A plain two-column grid left a hole beside a tall card.
4. **Under 360px the figures are one column.**
5. **No new motion.** The card keeps the hooks stage 3 carries: tapping the name, the gear or the band's button still moves the name to the next screen's heading. Buttons press as everywhere.

A measuring mistake, caught: the temporary server caches templates, so the first "before and after" count of small text compared the new page with itself and showed no change. Measured again on restarted servers: the fullest fixture card has 4 pieces of text under 16px, against 17 before.

Verification:

- `home.mjs`: 60 of 60 at 320, 390 and 1280px on the `seed_home.py` fixture. Three checks in its first draft tested nothing and were replaced before this count.
- `screens.mjs` 46, `lifetime.mjs` 22, `navigate.mjs` 37.
- 651 tests pass on SQLite (ten PostgreSQL-only skips), in the build-style run and on local PostgreSQL 17.
- Captures inspected in two rounds at 390 and 1280px; 320px was checked by measurement only. The design skill's detector reported two advisories about black text that come from reading the templates without the stylesheet.

AC1 and AC2 are met. **AC3 is open: only the human can judge it on a phone.** Not verified: a real phone; Safari's rendering of the two packed columns on an iPad or desktop.


2026-10-05 documentation correction: local `main` and `origin/main` record the Your groups merge as `f044805`, after the verification above. The earlier "not pushed" status is stale. Phone acceptance remains open.

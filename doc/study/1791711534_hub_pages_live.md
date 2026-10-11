# An open session does not update on players' screens: study

Date: 2026-10-11, Asia/Manila.

## Report

The human said: "when a session is open, it doesnt update live on the screens of non-host participants."

The report does not name the screen. So each screen a player can have open during an open session was measured.

## Measured

A player (`ben`) in headless Chrome with four pages open, while the host acted through the real services. Fixture: `seed.py` plus a new session with one open set.

| The player's screen | Asks the server by itself? | Host starts the set | Host records a buy-in | Host adds a player |
|---|---|---|---|---|
| The set page | Yes, every 4 seconds | Shown at once | Shown after 3.8 s | Shown after 2.7 s |
| The session page | Yes, every 5 seconds (released today) | Shown after 2.1 s | Not on this page | Not on this page |
| The group page (Sessions) | **No** | **Never, until a reload** | Not on this page | Not on this page |
| Your groups | **No** | **Never, until a reload** | Not on this page | **Never** (the card says "7 at the table") |

So the set page and the session page do update for a player during an open session. The two screens a player starts from do not.

## Root cause

`templates/web/home.html` and `templates/web/group.html` have no live region and no script asks for them. It was never built. In today's session-page plan this was decision 3, "Your groups stays as it is", and was approved; in use it is the gap that shows.

What a player on those screens misses while a session is open:

- a session being created and its set opened for joining: no card or row appears, so the player does not know there is a table to open;
- the set starting, ending, being finalized: the state word stays ("Open" instead of "In play");
- players joining: the count "N at the table" stays;
- the session closing: no "you owe" line appears, and the row stays under Current sessions.

The agent's reading, to be corrected if wrong: this is what the report is about. If the screen meant was the set page or the session page, those were measured as working here, and the fault would be something on the phone or on the live site that this test does not show.

## Constraints

1. The session page's approach fits: a short stamp derived from what the page shows, asked on a timer, and a redraw in place. Nothing stored (rule 7).
2. **Your groups is held to exactly 11 queries** (`web/tests/test_home.py`). The stamp cannot be worked out on the page without raising that number.
3. **Group settings shows links once** (a new invite, claim or reset link is taken from the login session and shown a single time). A redraw would fetch the page again and the link would be gone. The Settings tab must never redraw by itself.
4. Both pages have forms and disclosures (New group, archived lists). A redraw must not close an open one or lose typing.
5. A person may leave Your groups open for hours. The asking must be cheap and must slow down.
6. Access (rule 5): a stamp covers only the requester's own active memberships.

## Options

| Option | For | Against |
|---|---|---|
| A. The same asking as the session page, for Your groups and the Sessions tab of a group | One mechanism, already built and tested; no stored state | Two more small endpoints; a stamp over several groups |
| B. Reload these pages on a timer | Trivial | Flicker, lost scroll, a full page each time for everyone idle on the home page |
| C. Leave as is and add a "Refresh" button | No polling cost | Does not answer the report |

Recommend A.

The page does not carry its stamp (constraint 2). The script asks once as soon as the page starts and takes that answer as its baseline. A change in the fraction of a second between the page being drawn and that first answer would be missed until the next change or the next visit; this is accepted and stated.

## Risks

| Risk | Effect | Answer |
|---|---|---|
| A redraw wipes a link shown once | A host loses an invite link | Only Your groups and the Sessions tab ask; Settings and Stats never do |
| A redraw closes New group or loses typing | Annoyance, lost input | Wait while a field has focus or typing, a sheet is open, or a disclosure without a kept state is open |
| Cost of many idle phones | Free-plan limits | 5 seconds, 20 after two quiet minutes, none while hidden; about five small queries per ask |
| The arrival after login replays on a redraw | A flash of animation | The check covers a redraw during and after the arrival |

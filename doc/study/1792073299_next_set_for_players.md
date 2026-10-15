# The next set, for players: study

Date: 2026-10-15, Asia/Manila. Base: `main` at `7a153e9` (table alerts released as `525495f`).

## Request

"It is not very clear for non-host participants that a new set has started within a session. Let's fix it."

## Understanding

- **Said:** a player who is not the host should notice that the host started the next set.
- **Assumed:** "a new set has started" is the host's **Start next set** on the session page (`games.services.start_next_set`). It creates the next set already Open, with the players still at the table copied in. "Started" here is that moment, not the host's later **Start the set** (play begins), which players see on the set page already.
- **Success:** a player still looking at the previous set, on their phone at the table, sees within a poll that set N has started and gets there in one tap. A player not looking at the app gets the same table alert as for a first set.

## What happens now

| Where the player is | What they see when set 2 starts |
|---|---|
| **Set 1's page** (counting up, or the final results): where players usually are between sets | Nothing. `start_next_set` bumps only the new set's version, so set 1's poll answers "no change". The page's one way on is **Go to the session**, and there **Open set 2** |
| The session page | Refreshes itself (`nightlive.js`): the hero's button becomes **Open set 2** and the Sets list gains a row "Open". Nothing marks either as new |
| Your groups | Refreshes itself: the card's band becomes the new set with **Open set 2**. Nothing says it is new, and "added you" does not appear |
| The phone, app closed | Nothing. Table alerts are sent from `transition("open")` and from `add_participants`. `start_next_set` creates the set already Open and copies the players with `Participant.objects.create`, so it goes through neither |

The last row is a gap in today's release, not a design choice: a player carried into set 2 should hear about it as they did for set 1.

Set 1 can still be counting (Counting up) when set 2 starts. A player may still have to send their own count there, so whatever appears on set 1's page must not push that aside.

## Options

- **A. Tell set 1's page (recommended).** `start_next_set` also bumps the previous set's version, so every phone on it redraws within a poll. The set page then shows a notice at the top of the page: "Set 2 has started", a line saying whether the viewer is at its table, and a primary **Go to set 2**. On the final page the existing main button becomes **Go to set 2**, with the session one step quieter. Counting-up content stays where it is, under the notice.
- **B. Send players to set 2 by themselves.** Set 1's page would load set 2 on its own. It would take away a player's results or their count form mid-glance, and a sheet they had open. Not proposed.
- **C. Only the alert.** Fix the missing notification and leave the pages. A player at the table with set 1 on screen would still see nothing until the phone buzzes, and only if they turned alerts on.

## Design direction (motion and UI skills)

The set page is an Operate surface. The brass attention rule and the reopening notice (`reopen-arrived`: the brass rule draws, then the words rise) already give a "this set changed under you" moment; the next-set notice is the same family, pointing forward instead of back.

- **The notice.** A Rail panel with a 2px brass top edge at the top of set 1's page (above the felt), with "Set 2 has started" (1.125rem, 750), one line under it in Bone Dim, "You're at the table." or "Join from the set.", and a full-width primary **Go to set 2**. 48px. A second later set (set 3) replaces it: the notice always names the latest open or in-play set.
- **Arriving.** Seen first on a redraw: the brass edge draws left to right (`mark-draw`), then the words rise 8px and the button fades in (`shift`, 60ms after). Once per set and browser, like the books balancing. On a first sight, a reload or under reduced motion it is simply there.
- **Said.** The redraw announces "Set 2 has started." through the polite line the set page already has (`#arrival-news`).
- **The final page's button.** "Go to set 2" becomes the primary; "Go to the session" stays as a quiet link under it.
- **Your groups and the session page.** The new set's band and the session page's **Open set 2** already update. A carried player also gets the Your groups line, worded for this case: "ari started set 2".
- **The alert.** "Friday table · set 2 is open", "ari started set 2. You're at the table." Same tag per set, same switches.

## Costs and risks

- **One more query on set pages that can have a later set** (Counting up, Finalized, Canceled): which set of the session is the latest open or in play. A set in play does not ask, so the budget tested on a set in play does not change.
- **A write to the previous set** inside `start_next_set`, which already holds the session lock: its version only, so its phones redraw. No money record changes.
- **A redraw under a sheet or typing** waits as today (`live.js` keeps a snapshot until the person stops typing).
- **Fail-safe.** A switch, `NEXT_SET_NOTICE`, hides the notice and the button change. The alert follows the existing `PUSH_ALERTS` and `TABLE_NOTICES`.

## Conclusions

1. Fix the gap: carried players get the table alert and the Your groups line when the next set starts.
2. Tell set 1's page: bump its version, show a "Set N has started" notice with **Go to set N**, and lead the final page's button to the new set.
3. Do not move anyone to the new set by itself.

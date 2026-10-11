# The session page does not update by itself: study

Date: 2026-10-11, Asia/Manila.

## Report

The human said: "the settlement pages does not update live on the non-host participants after the session."

Read as: after a session is closed, a player who has the session page open (who pays whom, the Paid marks, the results) does not see what the host does until they reload.

## Root cause

It was never built. It is not a fault introduced by a recent change.

- The set page has a live region (`<div id="live" data-url=…>` in `session.html`). `live.js` asks `session_state` every 4 seconds with the set's `version` and redraws the region when it changed.
- The session page (`night.html`) has no such region, no address to ask and no script that asks. Nothing on it changes without a new page load.
- The host's own page changes because their action is sent in place and answered with the redrawn page (`turbo-setup.js`). That answer goes only to the person who acted.
- `mark_paid()` and `mark_unpaid()` write a `Payment` or a reversal and change no version, so even a poll of a set's version would not learn of them.
- The wiki states it under "Limits today": "The session page does not refresh by itself; the set page does." The only help today is `app.js`: a page that does not refresh itself reloads when the app comes back after 30 seconds away.

What a player misses on an open session page:

| The host does | The player's page shows |
|---|---|
| Marks a transfer paid, or unpaid | The old mark, the old "N of M paid" and the old "you still pay" |
| Closes the session | "Session open", no transfer list |
| Reopens the session, or reopens a set | The retired transfer list as if current |
| Starts the next set, finalizes a set | The old list of sets and old "results so far" |

## Constraints

1. Totals are queries (rule 7); nothing new is stored for this.
2. Each view resolves through the requester's membership (rule 5).
3. The session page is held to 14 queries (`web/tests/test_query_counts.py`). A poll must cost far less than a page.
4. The page already declares `turbo-refresh-method: morph` and keeps scroll, open disclosures (`data-key`) and typed fields (`data-keep`) across an in-place update.
5. A sheet may be open on this page (recap, share, reopen). A redraw under an open sheet would tear its content out.
6. Vercel's free plan and Neon: a poll is a function call and a database round trip. Phones left on the settle-up page for an hour should not cost a request every 4 seconds.

## Options

| Option | For | Against |
|---|---|---|
| A. A cheap "has anything changed" address for the session, asked on a timer; on a change the page is fetched and morphed in place | No stored state; cannot be forgotten by a future write; reuses the morph the host's actions already use | A new small endpoint and script |
| B. A `version` on the session row, bumped by every write that touches it | One integer to compare | A migration; a dozen services must each remember to bump it; a missed one is this same fault again |
| C. Bump every set's `version` on a paid mark and poll a set | No new endpoint | Set pages redraw for payments that they do not show; the session page still needs a poll |
| D. Reload on a timer | Trivial | Flicker, lost scroll, full page cost each time |

Recommend A. The "stamp" is derived from what the page shows: the session's status, each set's state, the current transfer list, and the payments. If a future write changes any of those, the stamp changes without anyone remembering to make it.

## Risks

| Risk | Effect | Answer |
|---|---|---|
| A redraw while a sheet is open or a field is being typed in | Lost typing, a broken sheet | Wait: the redraw happens when the sheet closes and the field is left |
| Polling cost | Free-plan limits | 5 seconds while things are changing, slowing to 20 seconds after two quiet minutes; none while the tab is hidden |
| The stamp misses something the page shows | A stale page again | A test per kind of change in the table above |
| The poll fails | Nothing updates | Back off as the set page does; the 30-second return reload stays as it is |

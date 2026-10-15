# Table alerts: study

Date: 2026-10-15, Asia/Manila. Base: `main` at `dabf138`.

## Request

"When a session has been opened for players, I want a notification to be sent to all the added players in a session, include the recommended fixes for the player adding UI flow. Make sure to use motion and UI skills when polishing this feature."

Answered before this study (2026-10-15):

- **Channel:** a phone notification by Web Push, plus a mark in the app for anyone without push.
- **When:** when the host opens the set, everyone already added is told at once; after that, a player the host adds while the set is open or in play is told at that moment. A player who joins by themselves, and the host who acts, are never told.

## Understanding

- **Said:** added players learn that the set is open. The earlier review's fixes for the add-player flow are part of the same work.
- **Assumed:** "opened for players" is the set's `open` action (Draft → Open, "Opened the set for joining", `games.services.transition`). A set is `GameSession`; the notice concerns one set. Only players with a login can be told; a no-login roster player has no phone to reach.
- **Success:** a player whose phone has alerts on gets a lock-screen notification within seconds of the host tapping Open, and a tap opens the set. A player without alerts sees it on Your groups. A player already watching the set sees, plainly, who was just added.

## What happens now

### Players already watching the set

The review of 2026-10-15 found that an added player is hard to notice on another phone:

1. The new row only fades in and rises 12px (`flow.js`). It has no brass mark and no badge, because `changes.js` marks a row only when it has an earlier value to compare.
2. Rows are in join order, so the new row is at the bottom, usually below the fold on a phone with six or more players.
3. The heading's "6 · 2 seats free" changes without any mark.
4. Under reduced motion nothing at all shows the change.
5. Nothing is announced to a screen reader; the only `aria-live` text is "Live · 21:04".
6. The host who added gets the full arrival (`players_arrived`, the brass mark for three seconds, the rise, a scroll into view). Polls never carry it. A rebuy is marked on every phone ("Rebuy added"), so it is more visible than a new player.

### Players not watching

Nothing reaches them. Your groups refreshes every 5 seconds (`nightlive.js`) and the card shows "Open set N", but nothing on the card says that this viewer was added. Push notifications are listed as not built (`doc/wiki/features.md`). There is no email (accounts have usernames only).

### What already exists

- A service worker at `/sw.js` (`config/pwa.py`). It only shows the offline page, and `SERVICE_WORKER=False` serves a worker that removes itself.
- The installed app (manifest, icons, the home-screen suggestion).
- `audit` is a leaf app that stores `group_id` and `session_id` as plain integers; a new leaf can follow it.

## Web Push on the players' phones

| Phone | What works |
|---|---|
| iPhone, app on the Home Screen, iOS 16.4 or later | Push works after the player allows it from a tap inside the app |
| iPhone, Safari tab | No push. The Home Screen suggestion already asks people to install |
| Android, Chrome (tab or installed) | Push works after the player allows it |
| Desktop Chrome, Edge, Firefox, Safari | Push works after the player allows it |

- Permission must be asked from a tap, once per phone. A refusal can only be undone in the phone's settings, so the ask must come with a reason and never on page load.
- The server signs each message with a VAPID key pair. The private key is a secret in Vercel; the public key is sent to the page.
- Sending is an HTTPS request per phone to the phone maker's push service. A dead subscription answers 404 or 410 and is removed.
- **Library:** `pywebpush` 2.5.0 (Python 3.10 or later; it brings `cryptography`, `http-ece`, `py-vapid`, `requests` and `aiohttp`). It resolves for Python 3.14. The alternative, `http-ece` and `py-vapid` with the standard library's `urllib`, saves two dependencies but reimplements what `pywebpush` already tests. Recommended: `pywebpush`.

## Where the sending runs

There is no queue (AGENTS.md: none without a recorded requirement). The send runs after the transaction commits (`transaction.on_commit`), in the host's request, in parallel threads, with a 5-second limit per phone. A typical send to eight phones is well under a second; the worst case adds 5 seconds to the host's tap, during which the button shows its busy state. A failure is logged and never refuses the host's action: the set is open whether or not a phone was reached.

## Options for the in-app mark

- **A. A notice row per player and set (recommended).** Written in the same transaction as the open or the add, so it exists exactly when the set does. Unique per player and set, so opening, closing and opening again tells nobody twice. Your groups reads it; opening the set page marks it seen. It doubles as the record of which phones were sent a push.
- **B. Derive it from `Participant.added_by` and the audit log.** No new table, but "seen" has nowhere to live, and the card would mark the player at every visit until the set ends.

## Design direction (from the motion and UI skills)

The set page is an Operate surface: short glances in a dim room, one hand free. DESIGN.md's attention rule says brass marks accepted changes, paired with words. The motion rules say rows carry money and move without bounce, badges may spring, and reduced motion keeps the state change while it removes the movement. Everything below reuses existing presets (`shift`, `arrive`, `mark-draw`) and existing parts (the change badge, the brass row mark, toasts); nothing new is invented for one moment.

- **A row added by someone else** gets what a rebuy gets: the brass mark for three seconds and a badge, "Joined" ("You're in" on the player's own row). It rises 12px as today; the badge springs in. Under reduced motion the mark and badge show without movement.
- **Below the fold:** one toast, "Ana joined" (or "Ana and Ben joined", or "Ana, Ben and 2 others joined"), with a **Show** button that scrolls to the first new row and marks it again. A row in view gets no toast, so nothing is said twice. Later arrivals replace the toast rather than stack.
- **The count** gets the 2px brass underline that "Still in play" uses, drawn once.
- **Screen readers** hear "Ana joined the set." from a polite live region outside the redrawn area.
- **The host's own action** (a form sent in place) keeps today's success message; the toast and the announcement come only from a poll, so the host is not told twice.
- **Your groups:** a card whose set added this viewer, unseen, gets a line in the band, "Ana added you", led by a brass dot. The set's button becomes the primary button. The line arrives with `shift` when a refresh brings it. It goes away once the set page has been opened.
- **The alerts ask** is a quiet panel at the foot of Your groups, beside the home-screen line: one sentence of reason, "Turn on table alerts" (neutral, not primary) and "Not now". It shows only where push can work. Once alerts are on, a quiet line says so with a Turn off link. If alerts are blocked, a line says where to change it.

## Costs and risks

- **A new dependency and two secrets.** `pywebpush` and its tree; `VAPID_PUBLIC_KEY` and `VAPID_PRIVATE_KEY` in Vercel. Without the keys, push is off and the in-app mark still works.
- **Latency on Open** (above): at most 5 seconds in the worst case, usually less than one.
- **A new leaf app.** AGENTS.md rule 11 names `audit` as the only leaf; this adds `notify`. That is an edit to AGENTS.md, so it needs the human's approval with the plan.
- **A write on a page view.** Opening the set page marks the notice seen. It goes through `notify.services`, as rule 2 requires.
- **Rule 3 (request IDs).** A subscription is an upsert keyed by its unique endpoint, so a repeated tap changes nothing; that unique constraint stands in for a `request_id`.
- **The service worker changes.** Browsers fetch `/sw.js` again on navigation (`no-cache`), so phones pick up the push handler within a visit. `SERVICE_WORKER=False` removes the worker and push with it.
- **No preview deployments** (the human tests on the live build): every part ships behind its own switch and fails to today's behaviour.
- **iPhone only when installed.** Players who use Safari get the in-app mark only.

## Conclusions

1. Send a Web Push notification, and write an in-app notice, to each added player with a login, other than the actor, when the set opens, and to each player a host adds later while the set is open or in play.
2. Store subscriptions and notices in a new leaf app, `notify`; send after commit, in parallel, with a time limit, never failing the host's action.
3. Fix the set page so another phone sees an added player: the brass mark and "Joined" badge with or without motion, a toast when the row is out of view, the count's underline, and a screen-reader line.
4. Mark Your groups for a player who was added and has not looked yet.
5. Ship each part behind its own switch.

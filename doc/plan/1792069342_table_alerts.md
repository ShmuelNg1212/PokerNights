# Table alerts: plan

Status: built 2026-10-15 on `feat/table-alerts`; released 2026-10-15 as `525495f` on the human's word "ok release" (previous production commit `db5fa73`). The VAPID keys were added to Vercel Production before the release. Four minutes after the push the live `/sw.js` carried the push and tap handlers, and `/healthz` answered 200. Approved 2026-10-15 ("approved": `pywebpush`; a new self-contained app `notify`; the contact address defaults to the site's address, `https://pokernights-five.vercel.app`, set in Vercel). Date: 2026-10-15, Asia/Manila. Study: [Table alerts](../study/1792069341_table_alerts.md).

## Outcome

1. When a host opens a set, every player already added who has a login, other than the host who tapped, gets a notification on their phone: "Friday table · set 2 is open". The body is "Ana added you. Tap to see the table.", and a tap opens the set. A player the host adds later, while the set is open or in play, gets one at that moment ("Friday table · you're in set 2", "Ana added you. Play has started." while in play).
2. On Your groups, that player's card says "Ana added you" until they open the set.
3. A player already watching the set sees who was just added: the brass mark and a "Joined" badge on the row, a toast with **Show** when the row is out of view, the count underlined, and a line read out to screen readers.

## Decisions for the human

1. **Library.** Recommended: `pywebpush==2.5.0`. Alternative: `http-ece` and `py-vapid` with the standard library (two fewer dependencies, more code of our own).
2. **The leaf app.** Recommended: a new app `notify`, a leaf like `audit`, with AGENTS.md rule 11 changed to "`audit` and `notify` are leaves".
3. **VAPID contact.** The push services want a contact address in each signature (`VAPID_SUBJECT`, a `mailto:` or `https:` address). Which address should it be? The site's address, `https://pokernights-five.vercel.app`, works if you would rather not use an email.

## Implementation

Branch `feat/table-alerts` from `main`, in three commits that each work alone. The motion and UI skills are loaded again while building parts A and C, and the finished screens get one `impeccable` polish pass and one Motion audit.

### A. Seeing an added player on the set page (front end only)

1. **Arrivals on a redraw.** `changes.js` keeps the set of player rows it saw on the previous redraw (not in storage, so a first sight of the page marks nothing). A row that is new on a later redraw gets `just-changed` and its change badge set to "Joined", or to "You're in" on the viewer's own row. It holds for 3 seconds and fades over the last 400 ms, with or without motion. `flow.js` keeps its 12px `shift` rise and 40 ms stagger; the badge springs with `arrive`. The before-and-after tracking in `flow.js` runs even when motion is off, so the mark does not depend on it.
2. **Out of view.** If no new row is in view above the host dock after the redraw, a toast says who: "Ana joined", "Ana and Ben joined", or "Ana, Ben and 2 others joined" (names from the row, so nothing new comes from the server). It has role `status`, lasts 6 seconds, and has **Show** and Dismiss. Show scrolls to the first new row (`smooth`, or instant under reduced motion) and marks it for another 3 seconds. A second arrival while the toast is up replaces its words rather than stacking another.
3. **Only from a poll.** The toast and the announcement come only from `live.js` redraws. A redraw after the viewer's own action (`turbo-setup.js`) gets the mark but no toast, because the success message already speaks. A host who arrives from Add players keeps today's `players_arrived` arrival.
4. **The count.** "6 · 2 seats free" in the Players heading and the checklist's Players line carry `data-watch`. When the number changes, the 2px brass `mark-draw` underline draws once.
5. **Screen readers.** A visually hidden `aria-live="polite"` element in `session.html`, outside `#live`, gets "Ana joined the set." (or "You were added to this set.").
6. **Words.** DESIGN.md's Badges line gains "Joined" and "You're in". The motion table's "A player is added" row adds the mark, the badge, the toast and the underline.

### B. Notices and Your groups

1. **App `notify`** (leaf; it imports only Django and `accounts`' user model through `settings.AUTH_USER_MODEL`).
   - `Notice`: `user`, `group_id`, `session_id` (plain integers, as in `audit`), `kind` (`open` or `added`), `title`, `body`, `url`, `actor_name`, `created_at`, `seen_at`. Unique on (`user`, `session_id`).
   - `notify.services.tell(users, *, group_id, session_id, kind, title, body, url, actor_name)` creates the notices that do not exist yet (`bulk_create(ignore_conflicts=True)`, then reads back which were new) inside the caller's transaction, and returns them. `notify.services.mark_seen(user, session_id)`.
2. **Who is told** (`games.services`, inside the existing transaction and session lock):
   - `transition(..., "open")`: every `JOINED` participant whose member has a login and is not the actor's user.
   - `add_participant`, `add_participants`, `add_players`, `add_new_player`, while the set is Open or In play, for each added member with a login who is not the actor. A self-join tells nobody. A no-login player is skipped.
   - Each call already writes an audit record and bumps the version; the notice adds no second audit row.
3. **Your groups** (`web/home.py`, `_group_card.html`): one query for the viewer's unseen notices on the cards' current sets. Such a band gets a line above its facts, a 6px brass dot and "Ana added you", and its button becomes primary. When `nightlive.js` brings the line in, it rises 8px with `shift` and the dot springs with `arrive`; on first paint it is part of the arrival; under reduced motion it is simply there.
4. **Seen.** `web.views.session` calls `notify.services.mark_seen` for the viewer and set. A canceled or finished set's notice is not shown.
5. **Migration:** `notify.0001` (two tables, nothing changed in existing ones).

### C. Web Push

1. **Dependency:** `pywebpush==2.5.0` in `requirements.txt`; `pip check` stays clean.
2. **`PushSubscription`** in `notify`: `user`, `endpoint` (unique), `p256dh`, `auth`, `created_at`, `last_sent_at`. Same migration as B if B and C land together; otherwise `notify.0002`.
3. **Endpoints** (login required, JSON, CSRF as the rest of the site): `POST /alerts/subscribe/` upserts by endpoint and moves it to the requester; `POST /alerts/unsubscribe/` deletes the requester's row for that endpoint. A repeated tap changes nothing.
4. **Sending.** `notify.services.tell` registers `transaction.on_commit` for the new notices. The send runs in a pool of up to 8 threads, each push with a 5-second limit, a 6-hour TTL, urgency `high` and the topic `set-{id}`. A 404 or 410 deletes the subscription. Any other failure is logged and dropped. Nothing is sent if the transaction rolls back, and nothing is sent without both VAPID keys.
5. **Payload:** `{title, body, url, tag: "set-{id}"}`. No amounts and no other players' names.
6. **Service worker** (`config/pwa.py` `WORKER`): a `push` handler shows the notification with the app icon (`app-192.png`), the tag and `renotify: false`. A `notificationclick` handler focuses an open window of the app and moves it to the URL, or opens one. The offline behaviour is unchanged, and `REMOVER` stays as it is.
7. **The ask** (`static/js/alerts.js`, `_home_app.html`, at the foot of Your groups beside the home-screen line). It shows only when `PushManager` and `Notification` exist, the keys are set, and the app is installed or the phone is not an iPhone. It never asks on page load. It follows the permission state:
   - Not yet asked: a quiet panel, "Table alerts" with "Get a notification when a host adds you to a set.", a neutral **Turn on table alerts** and a quiet **Not now** (hidden for 30 days, `localStorage`).
   - On: one quiet line, "Table alerts are on for this phone." with **Turn off**.
   - Blocked: "Alerts are blocked for PokerNights in this phone's settings." No button.
   - Turning on: the button shows its busy line, the browser asks, the subscription is sent, and the panel cross-fades (`fade`) to the On line with a tick that springs in (`arrive`). A refusal or failure shows the reason in the panel. 48px targets, focus kept on the panel.

### Switches (all default on)

- `ARRIVAL_MARKS`: part A. Off returns the set page to today.
- `TABLE_NOTICES`: part B. Off writes and shows no notices.
- `PUSH_ALERTS`: part C. Off, or a missing key, hides the ask and sends nothing; subscriptions are kept.

### Tests

- **Django** (`notify/tests/`, `games/tests/`, `web/tests/`): opening tells each added player with a login, and not the actor, a no-login player or a player in another set. Opening, closing and opening again tells nobody twice. A host add while Draft tells nobody until Open; while Open or In play it tells at once; a self-join tells nobody. A rollback sends nothing (`on_commit` with a stubbed sender). A 410 removes the subscription; a timeout keeps it and the host's action still succeeds. Subscribe and unsubscribe need a login, ignore another user's endpoint and are idempotent. Your groups shows the line until the set page is opened, and not for a canceled set. Each switch turns its part off. The worker script contains the push and click handlers and the remover is unchanged.
- **Browser** (new `web/tests/browser/arrivals.mjs`, host and player in two browser contexts, 390 × 844 and 1280 × 800, eight players):
  - An add by the host shows on the player's page within one poll: the mark, "Joined" and the underlined count.
  - The toast with **Show** appears when the row is out of view, and not when it is in view. Show scrolls to the row and marks it.
  - Several adds give one toast. The host's own in-place add gives no toast.
  - The live region text is set.
  - Reduced motion shows the mark with no movement, and a blocked Motion file still shows the mark.
  - Your groups shows "Ana added you" through a refresh, and it clears after the set is opened.
  - The alerts panel goes through its states with `PushManager` stubbed. Real delivery is checked on the phone.
  - `flow.mjs` and `table.mjs` run again.

## Acceptance

1. The Django suite passes on SQLite, on PostgreSQL, and the way the Vercel build runs it.
2. `arrivals.mjs` passes, with its checks failing first on `main`; `flow.mjs` and `table.mjs` still pass.
3. **On your phones, after release:**
   - A player with the app on the Home Screen turns on table alerts. You add them to a set and open it: their locked phone shows the notification within seconds, and a tap opens the set.
   - You add them to a set in play: they get "you're in set N".
   - A second player watching the set sees the added row marked "Joined", or the toast if it is out of view.
   - A player without alerts sees "Ana added you" on Your groups.

## Your steps

1. Answer the three decisions above.
2. Before release: I generate a VAPID key pair locally and give it to you; you add `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY` and `VAPID_SUBJECT` in Vercel → pokernights → Settings → Environment Variables (Production). The private key is never committed. Without these, everything except the phone notification still ships.

## Fail-safe

- A failed send never refuses the host's action.
- Each part has its own switch. Missing keys mean no push and no ask.
- The migration only adds tables.
- Rolling back the release leaves the two tables unused.

## Not covered

- A sentence in the home-screen suggestion saying that installing enables alerts on an iPhone.
- Notifications for anything else, such as play starting, a count to enter, or money to settle.
- Telling no-login players, and email.
- A list of past notices.

## Release

Built and checked locally on `feat/table-alerts`, then held for your word. After a release, one request about four minutes after the push to see the new worker and the panel on the live site.

## Progress

- [x] Approve the plan and answer the three decisions. Approved 2026-10-15.
- [x] Build A, B and C; test; run the browser checks; polish pass and Motion audit. Built 2026-10-15 on `feat/table-alerts`.
- [x] Add the VAPID keys in Vercel; say when to release. Keys added and released 2026-10-15.
- [ ] Phone checks above.

## Verification record (2026-10-15)

- **Django.** 39 new tests: `notify/tests/` (25: who is told and when, once per set, rollback, sending, a forgotten phone, a timeout, a real message encrypted and signed by `pywebpush`, the endpoints with login, CSRF and refusals) and `web/tests/test_table_alerts.py` (14). Three existing tests changed: two query budgets went up by one fixed query each, the unseen-notice read on Your groups and the seen update on the set page, neither growing with players. The script-order list gained `arrivals` and `alerts`. 1,162 pass on SQLite, on PostgreSQL 17, and as the Vercel build runs them (with `web/tests/browser/` moved aside).
- **`arrivals.mjs`:** 41 of 41. Served with all three switches off, its arrival checks fail, as `main` would.
- **Other browser checks:**
  - `flow.mjs` 51 of 52 and `home.mjs` 57 of 60, the same failures as `main` run the same way.
  - `hub_live.mjs` 19 of 19.
  - `table.mjs` stops at the same known place on both.
- **Polish pass** (from the screenshots at 390px):
  - "Turn off" no longer wraps.
  - The panel's sentence wraps without leaving one word alone.
- **Motion audit:**
  - The MotionScore audit needs Motion+, which is not connected.
  - In its place, `arrivals.mjs` checks that every new movement animates only `transform` and `opacity` (toasts keep their `y`, as DESIGN.md allows).
  - Under reduced motion nothing moves and the marks stay.
- **Not checked:** delivery to a real phone, and the time a send adds to the host's Open tap on Vercel. The phone check shows both.

### Rulings made while building

1. **A module of its own.** The arrival marks, the toast and the announcement are `static/js/arrivals.js`, not part of `changes.js` and `flow.js`. `flow.js` keeps the rise and `changes.js` is unchanged; `live.js` now tags a poll's redraw (`detail.poll`), which tells someone else's change from the viewer's own.
2. **A redraw keeps the mark.** A redraw replaces the rows, so a mark still inside its three seconds is put back on the new row. A change of the row's own (a buy-in) takes over with the badge `changes.js` gives it.
3. **A hidden tab announces nothing.** `flow.mjs`'s "hidden tab" check caught a toast and a badge spring in a hidden tab. Polls stop there anyway; now neither is shown.
4. **Notices are the record of who was told.** With `TABLE_NOTICES=False` and push on, notices are still written (so nobody is pushed twice) and only hidden; with both off nothing is written.
5. **One code commit, not three.** The plan said three commits; the switches in `config/settings.py` and the script tags in `base.html` are shared by all three parts, so A, B and C landed together. B and C share one migration (`notify.0001`, both tables). Each part still has its own switch.
6. **The panel stays across redraws** (`data-turbo-permanent`), because Your groups redraws itself by morphing; its buttons are answered once at the document.
7. **The worker's icon** is written into `/sw.js` from `static()`, so it follows the static address.

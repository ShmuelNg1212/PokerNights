# The next set, for players: plan

Status: built 2026-10-15 on `feat/next-set-for-players`; released 2026-10-15 as `2b69354` on the human's word "release" (previous production commit `525495f`). Four minutes after the push the live stylesheet carried the notice's styles and `/healthz` answered 200. Approved 2026-10-15 ("approved", with the recommended answers: the notice and the button change on the previous set's page; shown to every member there, worded for whether they are at the new table). Date: 2026-10-15, Asia/Manila. Study: [The next set, for players](../study/1792073299_next_set_for_players.md).

## Outcome

When a host taps **Start next set**:

1. Every phone on the previous set's page shows, within a poll, a notice at the top: "Set 2 has started", "You're at the table." (or "Join from the set." for a player who was not carried), and **Go to set 2**. On the final results page the main button is **Go to set 2**.
2. Each carried player with a login, other than the host, gets the table alert ("Friday table · set 2 is open", "ari started set 2. You're at the table.") and, on Your groups, "ari started set 2" until they open it.

Nobody is moved to the new set by itself. Counting up on the previous set works as before, under the notice.

## Decisions for the human

1. **On set 1's page.** Recommended: the notice and the button change (study, option A). Alternative: only fix the alert (option C).
2. **Who sees the notice.** Recommended: every member on set 1's page, worded for whether they are at the new table. Alternative: only the carried players.

## Implementation

Branch `feat/next-set-for-players` from `main`.

1. **Service** (`games.services.start_next_set`, inside its existing lock):
   - Bump the previous set's version (`touch(previous)`) as well as the new set's, so the previous set's phones redraw.
   - Tell the carried players through `_tell_added(..., started=True)`: kind `next`, title "{table} · set {N} is open", body "{host} started set {N}. You're at the table.".
   - `notify.Notice.Kind` gains `NEXT`. Its migration only adds a choice.
2. **Set page context** (`web.views.session_context`), only for a set that is Counting up, Finalized or Canceled:
   - `later_set` is the session's latest set after this one that is Open or In play. A draft is never shown to players.
   - `at_later_table` says whether the viewer is seated in it.
   - The snapshot carries both, so the poll's redraw shows the notice.
3. **Template:**
   - A new `_next_set_notice.html` sits at the top of the live region, above the felt, with `data-next-set="{pk}"`.
   - In `_final_set.html`, the main button becomes **Go to set N** when `later_set` exists, and "Go to the session" becomes a quiet link.
4. **Motion** (`static/js/arrivals.js`, the set page's module for things that arrive):
   - On a redraw that brings a `data-next-set` that was not there before, the brass edge draws (`mark-draw`, CSS). The words rise 8px and the button fades in with `shift`, 60ms apart, once per set and browser (`localStorage`).
   - The polite line says "Set N has started.".
   - On a first sight, a reload or under reduced motion it is simply there.
5. **Your groups:** a notice of kind `next` reads "{host} started set {N}" in the band line.
6. **Switch:** `NEXT_SET_NOTICE` (default on) hides the notice and the button change. The alert follows `PUSH_ALERTS` and `TABLE_NOTICES`.
7. **Tests:**
   - **Django:**
     - Starting the next set tells carried players with a login and not the host. It tells nobody twice, and a player who left set 1 is not told.
     - Set 1's version moves.
     - Set 1's page and its snapshot show the notice with the right words for a seated and an unseated player, and the final page's button leads to set 2.
     - A draft later set and a set in play show nothing.
     - The switch turns it off.
     - The query budget for a set in play is unchanged.
   - **Browser** (`arrivals.mjs` gains a section, with a new fixture):
     - A player on set 1's final page sees the notice within one poll.
     - The edge draws and the words rise once.
     - **Go to set 2** opens set 2.
     - A reload plays nothing.
     - Reduced motion shows it at rest.
     - The line is announced.
     - A player counting up on set 1 still has their count form.
     - 390 and 1280px, no overflow, 48px button.
8. **Docs:**
   - DESIGN.md: the notice joins "Table alerts".
   - `doc/wiki/features.md`.
   - TODO.md.

## Acceptance

1. The Django suite passes on SQLite, PostgreSQL and as the Vercel build runs it.
2. `arrivals.mjs` passes, with the new checks failing first on `main`.
3. **On your phones:**
   - With a player looking at set 1's results, tap **Start next set**: their screen shows "Set 2 has started" within a few seconds, and **Go to set 2** takes them there.
   - A player with alerts on and the app closed gets "… set 2 is open".

## Fail-safe

`NEXT_SET_NOTICE=False` returns set pages to today. A failed alert never refuses Start next set. There is no data migration; the new notice kind is only a choice.

## Not covered

- Moving players to the new set by themselves (study, option B).
- Marking the new set on the session page's list.

## Release

Built and checked locally, then held for your word. After a release, one request about four minutes after the push.

## Progress

- [x] Approve the plan and answer the two decisions. Approved 2026-10-15.
- [x] Build, test, browser check. Built 2026-10-15 on `feat/next-set-for-players`.
- [x] Say when to release. Released 2026-10-15.
- [ ] Phone check above.

## Verification record (2026-10-15)

- **Django.** 10 new tests in `web/tests/test_next_set.py`: who is told, a player who left, the Your groups words, the notice for a seated and an unseated player, the poll answering once a later set starts and 204 after, the final page's buttons, a canceled later set, a set in play, the switch. 1,172 pass on SQLite, on PostgreSQL 17, and as the Vercel build runs them (with `web/tests/browser/` moved aside). No query budget changed.
- **`arrivals.mjs`:** 56 of 56 (15 new). Served with `NEXT_SET_NOTICE=False`, the first next-set check fails, as `main` would. `flow.mjs` 51 of 52, the same failure as `main`.
- **Polish pass** (screenshots at 390 and 1280px): the final page had two primary "Go to set 2" buttons on one screen; its own button is now neutral and the notice's is the one primary.
- **Not checked:** a real phone.

### Rulings made while building

1. **No write to the previous set.** The plan said `start_next_set` would bump the previous set's version. `lock_session` locks a set and its session together, and `start_next_set` holds the session, so locking the previous set there could deadlock with a player's count on it. Instead an ended set's live version is "{version}.{later set}": the poll compares it, and it changes when a later set starts or ends. Asked only for an ended set; a set with no later one keeps its plain number.
2. **One primary.** The final page's **Go to set N** is neutral (see the polish pass).
3. **The host sees the notice too**, with "It is open." (or "in play") in place of the player's line.

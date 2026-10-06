# Player rebuys and player-entered counts: study

Date: 2026-10-06, Asia/Manila.

## Request

"Non-host players during a set have the option to rebuy and input their own chip count. Make sure all of these reflect live on all users in the game. Host still has control over finalizing the count."

## What exists today

- **Only a host writes money.** `ledger.services.record_buy_in`, `confirm_count(s)`, `record_cash_out` and the rest start with `require_host`. A player's set page has no action except Join.
- **Buy-ins.** A buy-in or rebuy is accepted the moment it is recorded, within the set's minimum and maximum, while the set is open or in play. Rake is taken from it by the set's rule. A mistake is reversed with a reason; the row stays in the log. `BuyIn.recorded_by` already names who recorded it.
- **Counts exist only after play has ended.** The host taps End play; the set is "counting up". The host types what each player has left and confirms (`FinalCount`: "a host's confirmation", versioned, one current per player). Then the host cashes the counted players out, and finalizes when the books balance. During play nobody's stack is recorded; an early leaver is cashed out by the host with a typed amount.
- **Live.** The set page asks the server every few seconds whether `GameSession.version` changed and redraws the live region. Every write service ends with `games.touch(session)`. So anything a service writes reaches every phone within about 5 seconds, and the sender's own page updates at once.
- **Typed values survive redraws.** The host's count fields are one form; any non-empty field counts as a typed draft, is kept through redraws and is remembered for the tab (`live.js`, `counts.js`, and the footguns on lost typing).

## Reading of the request

1. **Rebuy:** a player records their own rebuy from their own phone, without waiting for the host.
2. **Chip count:** when the host has ended play, each player types what they have left from their own phone, so the host does not type nine numbers.
3. **Host control:** a player's number is a statement, not a confirmed count. It becomes the final count only when the host confirms it. Cash-out, balance and finalize stay with the host.

The phrase "during a set" could also mean a running stack count while play continues. A stack changes every hand, and nothing in the accounting uses it, so this study reads "chip count" as the final count. The plan asks the human to confirm.

## Constraints

1. **Money records are append-only; each write is audited, carries a `request_id`, locks the set row and bumps the version** (AGENTS.md rules 2, 3, 4, 6).
2. **A player's own row only.** The server must decide whose row it is from the login, never from the form. A roster player without a login has no phone; the host acts for them as today.
3. **A rebuy is real money at the table.** If a player records one that the banker never received, the books are wrong by that amount until someone notices. The host must see it at once and be able to reverse it.
4. **Two people, one rebuy.** With two phones able to record the same rebuy, the host and the player can each record it. The two forms have different `request_id`s, so today's duplicate guard does not catch it.
5. **A player's number can change after the host has seen it.** The host must confirm exactly the number on their screen, or nothing (the batch cash-out already works this way: a stale review records nothing).
6. **The host's typing wins.** A player's number must never overwrite what the host has typed, and must not turn into a sticky host draft.
7. **Count-up preview.** The host's running total ("₱1,900 of ₱2,000") should include players' numbers, labelled as not yet confirmed.
8. **No preview deployments.** A switch must turn the feature off without a release.
9. **SQLite hides missing locks.** A player and the host writing at the same moment needs PostgreSQL tests.

## Options

**Player rebuy**

- **A. Recorded at once (recommended).** It is a normal buy-in with the player as recorder. The host's screen marks the row within seconds and the log says who recorded it. The host can reverse it. This is what "have the option to rebuy" asks for, and the request reserves host control for the count only.
- **B. A request the host approves.** Safer, but the host still has to act for every rebuy, which is the work the feature is meant to remove.

**The doubled rebuy (constraint 4)**

Each buy-in form says how many buy-ins that player had when the page was drawn. If the number has changed, nothing is recorded and the sender is told who recorded the other one and when. This covers host and player alike.

**Player count**

- **A. A separate record, "entered by the player", which the host confirms (recommended).** A new table holds the player's statement, versioned like `FinalCount`. The host's row shows "Maria entered ₱1,450"; the main button "Confirm N counts" includes it; typing in the field overrides it. The confirmation names the entry it accepts; if the player has changed it since, nothing is saved and the host sees the new number.
- **B. Write the player's number straight into `FinalCount`.** One table fewer, but it removes the host's control, which the request keeps.
- **C. Pre-fill the host's field with the player's number.** The field machinery would treat it as the host's own typing and keep it after the player corrects it (constraint 6).

**When a player can enter a count**

Only while the set is counting up, for a player with a buy-in who is not cashed out. Before End play there is no final count to enter.

## Size

One migration in `ledger` (a new table, one nullable column on `FinalCount`). Two services gain a player path; one new service. The set page gains a player's Rebuy button and sheet, a player's count field, and the host's "entered" state. No change to cash-out, balance, finalization, settle-up or stats.

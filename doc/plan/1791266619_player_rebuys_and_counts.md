# Player rebuys and player-entered counts: plan

Status: approved 2026-10-06 ("approved", with all seven decisions as recommended). Date: 2026-10-06, Asia/Manila. Study: [Player rebuys and player-entered counts](../study/1791266618_player_rebuys_and_counts.md).

## Outcome

A player with a login records their own rebuy, and at the end of a set types their own final count, from their own phone. Everyone at the table sees both within seconds. The host still confirms every count, cashes players out and finalizes.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new colour, font or asset. One migration (`ledger`: a new table and one nullable column; nothing existing changes).

## Behaviour

### 1. A player's own rebuy

- On their own row, a player who is at the table and already has a buy-in sees **Rebuy**. It opens the same sheet the host uses: amount, Min / Default / 2 × / Max, the allowed range, the rake rule, the number keys, **Confirm rebuy**.
- It is recorded at once as a normal rebuy: same limits, same rake, same place in the totals. The set log says "Maria bought in for ₱1,000" with Maria as the recorder.
- The player's page updates in place. Every other phone on the set shows the new total within about 5 seconds, with the brass mark and "Rebuy added" on the row.
- Only for yourself. Not offered to a player with no buy-in yet, a player who has left or is cashed out, or after play has ended. The host does those, as today.
- The host can reverse it with a reason, as any buy-in. A player cannot reverse.

### 2. No doubled rebuy

A buy-in sheet remembers how many buy-ins that player had when it was drawn. If another one arrived in the meantime, nothing is recorded and the sender reads: "Maria already has a new rebuy (₱1,000, recorded by Maria at 21:40). Nothing was added. Check, then try again if this is another one." This applies to the host's sheet too.

### 3. A player's own final count

After the host taps End play:

- On their own row, a player with a buy-in who is not cashed out sees a field **Your count** with the number keys and **Send to host**. 0 is a valid count.
- After sending, the row reads "You entered ₱1,450. Waiting for the host to confirm." with **Change**.
- Everyone sees, on that player's row, the state **Entered** and "Entered ₱1,450" in place of "Awaiting count".
- For the host, the row's field shows the entered number as its hint, and it is counted in the running total as not yet confirmed. The main button reads **Confirm N counts**, where N includes entered and typed counts. A number the host types for that player replaces the player's number.
- If the player changed their number after the host's screen was drawn, the confirmation saves nothing and says so; the screen then shows the new number.
- Once the host has confirmed, the player's row reads "Confirmed ₱1,450" and the field is gone. If the host confirmed a different number: "The host confirmed ₱1,400. You entered ₱1,450."
- If the host clears a count, or resumes play and ends it again, the player can enter again.

### 4. Unchanged

Confirming counts, clearing them, cash-outs, the balance check, overrides, finalizing and settle-up stay host-only and work as today. A player's entered number is never a cash-out and never enters a result by itself. Players without a login are handled by the host.

### 5. Switch

`PLAYER_ENTRIES=False` in Vercel removes both player actions without a release; entered numbers already sent are then ignored and the host types as before. Default on.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **"Chip count" means the final count after End play.** Recommended. During play nothing in the accounting uses a stack size. Say so if you meant a running stack count while play continues; that is a different feature.
2. **A player's rebuy is recorded at once, without the host's approval.** Recommended, because the request keeps host control for the count only. The risk: a rebuy recorded for money the banker never received stays in the books until the host reverses it. The alternative is a request the host approves with one tap.
3. **Rebuys only, not the first buy-in.** As requested. The host (or "Start the game") still records a player's first buy-in. Say so if a player should also record their own first buy-in.
4. **The host confirms a player's number with the main button**, together with any typed counts, not one by one.
5. **Every member sees a player's entered number.** The request asks for it to show live to all.
6. **No per-group setting** to forbid player rebuys. The switch is for the whole site. Say so if hosts should choose per group.
7. **The words** in sections 1 to 3.

## Implementation

1. **Model (`ledger/models.py`, one migration).** `CountEntry`: `session`, `participant`, `amount` (≥ 0), `version`, `is_current`, `request_id` (unique per set), `entered_by`, `created_at`. Append-only; one current row per player, kept by the service under the set's row lock (the old row is retired before the new one is written). `FinalCount.entry`: nullable link to the entry a confirmation accepted.
2. **Services (`ledger/services.py`).**
   - `record_buy_in`: the actor is a host, or the participant's own member with an accepted buy-in, at the table, not cashed out, and the switch on. New optional `seen_count`; a mismatch raises the message in section 2. Still locks the set, audits and touches.
   - `enter_count(session_id, actor, amount, request_id)` (new): the actor's own participant, set counting up, has money, not cashed out. Writes the next `CountEntry` version, audits `count.entered`, touches.
   - `confirm_counts`: accepts, per player, either a typed amount or an entry id. An entry id that is no longer current raises "Maria changed her count to ₱1,500. Nothing was saved." All or nothing, as today.
   - Clearing a count, voiding counts on resume, and a cash-out leave entries as history; a resume retires current entries with the counts.
3. **Queries.** `PlayerLine.entry` (the current entry when no count is in force) and a fourth status `entered` between `awaiting` and `ready`. `CountTotal` reports entered amounts separately, so the confirmed total is unchanged and the preview can add them.
4. **Views and addresses.** `buy_in_add` drops its host-only gate in favour of the service's rule and passes `seen_count`. New `POST s/<set>/counts/enter/`. `count_confirm` reads `entry_<participant>` fields beside the typed ones. Every object is still resolved through the requester's membership; whose row it is comes from the login.
5. **Templates.** `_players.html`: the Rebuy button and sheet on a player's own row. `_buy_in_form.html`: the `seen_count` field. `_players_count.html`: the player's field and its three states; the host's "Entered" state with a hidden `entry_<participant>` field in the counts form. Without JavaScript each is a plain form.
6. **JavaScript.** `counts.js`: an entered amount counts in the host's preview unless that field holds typing, and in N of the main button. The player's field uses the existing keep-while-typing rule. No new script.
7. **Setting.** `PLAYER_ENTRIES = env.bool("PLAYER_ENTRIES", default=True)`.
8. **Tests first.**
   - Rebuy as a player: recorded with limits and rake, audited with the player as recorder, version bumped; refused for another player's row, with no buy-in yet, when left, when cashed out, outside open/running, for a roster-only member, and with the switch off; the host path unchanged.
   - Doubled rebuy: a stale `seen_count` records nothing and names the other record, for host and player; a repeated `request_id` still returns the same row.
   - Entering a count: versions, 0 accepted, a blank refused, only own row, only while counting up, not when cashed out, audited, version bumped.
   - Confirming: entered only, typed only, both, typed over entered; a stale entry saves nothing; the confirmed count links its entry; clear and resume let the player enter again; the total and the balance ignore entries until confirmed.
   - Pages: what a player sees on their own row and on others' in each state; what the host sees; nothing for a player without the switch; another group's member gets 404.
   - Query counts on the set page and the polling endpoint do not grow with players.
   - PostgreSQL only: host and player record a rebuy for the same player at the same moment with the same `seen_count` (exactly one is recorded); a player changes their entry while the host confirms (the count saved is one the host saw, or nothing).
   - Browser check `player_entries.mjs` with a seed, two browsers: the player's rebuy appears on the host's screen without a reload; the player's count appears on the host's row and in the running total; the host types over it; the host confirms and the player's row turns to Confirmed; typing in either field survives the other's update; numpad, 48 px, contrast, 320 / 390 / 1280 px, no JavaScript.
9. **Verify.** SQLite and PostgreSQL suites. The new browser check, then `count_flow.mjs`, `flow.mjs`, `inplace.mjs`, `numpad.mjs` and `marks.mjs`, which share these screens. Captures inspected.
10. **Sync docs.** Wiki features and architecture, PRODUCT.md (who records what), DESIGN.md addendum, browser README, deployment (the switch), TODO. SPEC.md is the human's; a line in TODO if it should mention this.

## Acceptance criteria

- AC1. A player records a rebuy for themselves, and for nobody else, within the set's limits and rake.
- AC2. A player's rebuy shows on every other phone on the set within 5 seconds without a reload.
- AC3. The same rebuy recorded from two phones at once is recorded once.
- AC4. A player enters and changes their own final count while the set is counting up; everyone sees it within 5 seconds.
- AC5. An entered count is not a confirmed count: it is not cashed out, not in the balance and not in any result until the host confirms it.
- AC6. The host confirms exactly the number shown on their screen, or nothing is saved.
- AC7. A number the host has typed is never replaced by a player's entry.
- AC8. Every write is audited with the person who made it, and the log shows it.
- AC9. `PLAYER_ENTRIES=False` removes both player actions without a release.
- AC10. Cash-out, balance, finalization, settle-up and stats give the same results as before for the same records. Existing tests pass on SQLite and PostgreSQL.

## Out of scope

- A running stack count during play.
- A player's own first buy-in, cash-out, or reversal.
- A request-and-approve flow for rebuys.
- A per-group or per-set setting.
- Notifications beyond the live update on the open page.

## Rollback

Set `PLAYER_ENTRIES=False` in Vercel for an immediate stop. To remove the code, revert the feature commits; the new table and column can stay unused, so no migration needs reversing. Rebuys that players recorded stay as ordinary buy-ins.

## Progress and blockers

2026-10-06: Study and plan complete. Waiting for the human's approval. No code written.

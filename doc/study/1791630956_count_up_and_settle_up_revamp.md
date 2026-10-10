# Count-up and who pays whom, revamp: study

Date: 2026-10-10, Asia/Manila. Request: "conduct a design workflow for the count up page and the who pays whom page. I want to revamp it."

Skills used: the design skill (impeccable, `shape`). Captures were taken from a seeded temporary database as a host and as a player, at 390 × 844 and 1280 × 800. Eight of them are in [the assets folder](1791630956_count_up_and_settle_up_revamp_assets/).

## What the human chose (2026-10-10)

1. **Count-up:** faster counting. One compact line per player with the count field on it, so most of the table fits one phone screen.
2. **Who pays whom:** a person sees their own part first, then the list. A player's headline is what they pay or receive; the host's is the table's total.
3. **Reach:** the whole closed-session page, not only the transfers section.
4. **Boldness:** inside the current look, with one or two authored moments.

## Scope

Two screens.

- **Count-up:** `templates/web/session.html` while a set is in `reconciliation`. It is built from `_count_up.html`, `_players_count.html`, `_count_total.html`, `_balance.html` and `_host_controls.html`, with `counts.js`, `numpad.js` and `dock.js`.
- **The closed session page:** `templates/web/night.html` once a session is closed: the overview, Who pays whom, Session results, Sets and Payment records.

Not in scope: cash-out review, the finalize sheet, final results, the set page in play, the recap released today, the open session page except where it shares a part, Stats.

## Count-up as built

Measured on the 390 × 844 capture, as a host with six players:

| Thing | Height |
|---|---|
| Top bar and back link | 117px |
| Overview panel | 105px |
| "Player counts" heading | 32px |
| One player's row | 111px |
| Host bar, open | 203px |
| Set totals | 165px |
| Balance check | 273px |
| Whole page | 1,973px |

What the captures show:

1. **About three players fit between the heading and the host bar.** The first row starts at 254px and the bar covers the last 203px, leaving about 390px for rows of 111px.
2. **A row spends three lines on one number.** The name line carries a state badge and "Counted ₱450"; the second line is the label "Final count (₱)" and a field whose placeholder is the same ₱450; the third line is "Details". A cashed-out player has no field and still takes 80px.
3. **The state is said in several ways at once.** "Ready to cash out" as a badge, "Counted ₱450" beside it, and 450 in the field.
4. **Details is a line on every row.** It holds the player's records and corrections, which are needed rarely during a count.
5. **The host bar is tall.** Two lines of running total, the main button, a hint and "More host controls". Only the total and the button are needed while counting.
6. **The same totals appear twice below the list.** Set totals lists Total bought in and Recorded cash-outs; Balance check lists Total bought in and Total cashed out directly under it.
7. **The help paragraph sits after the last player.** "Type what each player has left; 0 for an empty stack…" is read once and then scrolled past every time.
8. **A player's own count is one row among the others.** Their field and "Send to host" are wherever they joined in the list.

What works and stays: one form for every typed count, the running total that follows typing, the numpad panel on a phone with Next and Done, the verdict stated by words, colour and mark, one main button per state, and drafts surviving live updates.

## The closed session page as built

Measured on the 390 × 844 captures:

| Thing | Host | Player |
|---|---|---|
| Overview panel | 361px | 539px |
| "View session recap" and "Manage this session" | 145px | 64px |
| Start of the first transfer | 750px | 848px |
| One transfer card | 251px | 227px |
| Page with two transfers | 1,951px | 2,002px |
| Page with five transfers | 3,116px | 3,100px |

What the captures show:

1. **No transfer is on the first screen.** A host sees the first card start at 750px of 844; a player does not see one at all.
2. **A transfer card is a quarter of a screen.** Payer, an arrow with "pays", payee, the amount, the state and the button are stacked. Five transfers take 1,300px.
3. **The headline is the table's figure for everyone.** A player reads "Still to pay ₱600" at 64px; their own "Miguel pays you ₱400 · Not paid" is 14px text at the foot of the panel.
4. **The overview repeats itself.** The settle status is a badge in the top bar and again under the figure; progress is a bar and two lines ("₱0 of ₱600 marked paid", "0 of 2 transfers paid"); "Collected rake across sets ₱0" is shown when there is no rake.
5. **Housekeeping sits above the money.** "View session recap" and "Manage this session" come between the overview and Who pays whom.
6. **Three explanations surround the list.** One sentence above it and two below it say what transfers are and are not.
7. **Payment records are always open** at the foot of the page, repeating what the Paid marks say.

What works and stays: exact figures on one line at every size, Paid and Not paid in words, the host's Mark paid and Undo as native forms, results kept separate from payments, and the page updating in place after a payment.

## Constraints that shape the plan

- **Rows do not reorder.** The app's rule is that live rows keep their place. Emphasis has to come from the row, not from moving it.
- **Money never animates its value** and success shows only after the server accepts. A moment can move a mark or a row, never a figure.
- **Every action works without JavaScript.** The count fields belong to one native form; Mark paid and Undo are native forms.
- **48px targets, one column on phones, two columns from 900px.**
- **No query is added.** The session page is held to 14 queries and the set page to 13 by tests.
- **Count-up is used during a real game.** The set page revamp shipped behind a switch for one release for this reason.
- **Accounting does not change.** What a count, a cash-out, a payment or an undo records stays exactly as it is.

## Existing checks that describe these screens

`end_set.mjs` (47 checks), `night.mjs` (68), `numpad.mjs`, `dock.mjs`, `player_entries.mjs`, and the Django tests `test_end_set.py`, `test_count_flow.py`, `test_count_total.py`, `test_night_design.py`, `test_query_counts.py`. Several name classes and copy that a new layout will move.

## Not verifiable from here

Typing counts with one thumb at a real table, the numpad panel together with shorter rows on an iPhone, and how the paid moment feels on a real phone. These belong on the phone checklist.

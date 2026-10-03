# Study: cash amounts and a unit option

- **Date:** 2026-10-03 23:10 (Asia/Manila), Unix timestamp `1791040240`
- **Request:** "remove the chip count feature. make this app purely for cash games but add an option for the units to become chips."
- **Workflow:** `agentic-workflow`, Phase 1 of a new cycle. No code changes before approval of the plan.

Labels: **FACT** = verified today. **REC** = recommendation. **ASSUMED** = needs confirmation.

## 1. Intended outcome (ASSUMED reading of the request)

1. The host records each cash-out as an **amount**, not as a chip count. With the default unit, the amount is in pesos.
2. The app has no chip-to-peso conversion. There is no "chips per buy-in", no chip rate, and no "chips in play".
3. A game has a **unit** option. The default is pesos (₱). The other choice is chips. With chips, each amount in that game is a chip number, shown as "1,600 chips" and never with ₱.

The request has a second possible reading. Section 4 states it. The plan asks which one is correct (Q1).

## 2. Current state (FACT)

Repository: `/Users/shm/PokerNights`, branch `main`, clean. The dev server runs on port 8000. The dev database holds your test data: 2 groups, 2 sessions, 16 buy-ins, 3 cash-outs, 1 finalized session.

Chip features in the code today:

| Where | What |
|---|---|
| `SettingsPreset`, `SettingsVersion` | `chips_per_buy_in` |
| `GameSession` | `rate_centavos`, `rate_chips`: the chip rate, locked by the first buy-in. The lock also means "this game has money in it" (cancel rule, settings rule) |
| `BuyIn` | `chips` next to `amount_centavos`. A buy-in must buy a whole number of chips |
| `CashOut` | `chips` only. No peso amount |
| `BalanceAdjustment` | `chips_delta` |
| `Finalization`, `PlayerResult` | `chips_issued`, `raw_difference_chips`, the rate, `chips_cashed`, `adjustment_chips` |
| `ledger/money.py` | `reduce_rate`, `chips_for_amount`, `value_floor`, `allocate` (largest-remainder rounding) |
| Balance check | Compares chips cashed out with chips issued |
| Screens | "Chips in play" tile, chips on each player line, cash-out input in chips, chips in the log |

Not affected: accounts, groups, invites, roster, tables, the lifecycle, joining, reversals, the settle-up algorithm, paid marks, live updates, the audit log.

## 3. Conflicts with earlier documents (FACT)

- `SPEC.md`, step 2: "Record a player's final chip count" and "Convert chips to cash using the session's chip values". This request replaces that. The AI does not edit `SPEC.md`. You can update it, or the wiki records the difference.
- The first architecture request: "chips issued per buy-in" and "final chip counts". This request replaces those items.
- Footgun page `adjustments_are_in_chips.md` becomes obsolete.

## 4. Options

| Option | What "units become chips" means | Pros | Cons |
|---|---|---|---|
| **A. One number system with a unit label** | A game is in pesos or in chips. No conversion exists. In a chips game, buy-ins, cash-outs, results and transfers are chip numbers | Simple. Removes all rate and rounding logic. The balance check becomes "cashed out = bought in" in one unit, as `SPEC.md` words it | A chips game settles in chips ("B pays A 3,000 chips"). The group converts to money outside the app |
| B. Pesos by default; chips with a peso rate as an opt-in | A chips game keeps today's behavior: cash-outs in chips, converted to pesos | Settle-up is always in pesos | Keeps the feature that the request removes. Two code paths for money |
| C. Remove chips, no option | — | Smallest | Does not meet the request |

**REC: A.** It matches "remove the chip count feature" and "purely cash", and the option is a label, not a second accounting method.

## 5. Recommended design

### Unit

- `GameSession.unit` and `SettingsPreset.unit`: `php` (default) or `chips`. A session copies the preset's unit. The host can change it until the first accepted buy-in.
- Each amount is one integer in the unit's smallest step: centavos for pesos, whole chips for chips. No `float`.
- `ledger/money.py` parses and formats by unit: `₱1,600` and `₱1,600.50`, or `1,600 chips`. Chip input must be a whole number.
- Blinds and the minimum, maximum and usual buy-in are in the session's unit.

### Records

| Record | Change |
|---|---|
| `BuyIn` | Keeps its amount. `chips` is removed |
| `CashOut` | `chips` becomes an amount in the session unit. Several cash-outs per player stay possible. A cash-out of 0 stays a real record |
| `BalanceAdjustment` | `chips_delta` becomes an amount |
| `Finalization`, `PlayerResult` | Chip columns and the rate are removed. `unit` is added, so later statistics never add pesos to chips |
| `SettingsPreset`, `SettingsVersion` | `chips_per_buy_in` is removed |
| `GameSession` | `rate_centavos` and `rate_chips` are removed |

Money column names change from `…_centavos` to neutral names (for example `amount`, `buy_in_total`, `net`), because a chips game stores chips in them.

### Rules

- **Balance check:** total cashed out + overrides = total bought in. The difference is shown in the unit with its direction: "₱50 more was cashed out than was bought in" or "₱50 is missing".
- **Override:** unchanged in meaning. One named player or an equal share; the equal split gives units that do not divide to players in join order.
- **Finalization:** result = cash-outs + override − buy-ins. No conversion and no rounding rule are needed. The conservation asserts and the database checks stay.
- **Settle-up, paid marks, lifecycle, permissions:** unchanged. Transfers show the unit.
- **"This game has money" rule:** today the chip-rate lock carries it. It moves to a guard that `ledger` registers with `games`, the same pattern as the existing withdraw guard. Cancel and unit change use it.
- **Live view:** the "Chips in play" tile becomes "Still in play" = bought in − cashed out, in the unit.

### Existing data

- Each existing session becomes a pesos session.
- A data migration converts each chip cash-out and override to centavos at that session's locked rate. It uses the current largest-remainder rule once, per session, so the converted amounts sum to the same total and a finalized session still balances.
- `PlayerResult` rows already hold peso values. They keep them.
- The migration cannot be reversed, because chip counts are dropped. The plan backs up `db.sqlite3` first.

### Later stages

- Leaderboards (Stage 3) must be per unit. A pesos board includes only pesos games.

## 6. External inputs

None. No new dependency.

## 7. Risks

| Risk | Mitigation |
|---|---|
| The reading of "units become chips" is wrong | Q1 in the plan. Option B is a different, larger change |
| Data loss in the migration | Backup of the dev database. A migration test with chip data, including a fractional rate. Run on a copy of your database before the real one |
| A wide rename breaks a screen | 213 existing tests are updated, plus the end-to-end test and the browser check |
| A host mixes units between games | The unit is shown on each amount. Statistics are per unit |

## 8. Open questions

1. **Q1.** Does a chips game have no peso value at all (option A), or must it convert chips to pesos (option B)?
2. **Q2.** Keep your current test games and convert them to pesos, or start with an empty database?

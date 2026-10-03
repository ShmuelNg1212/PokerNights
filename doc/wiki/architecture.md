# Architecture

One Django 6.1 project with server-rendered templates, one stylesheet and two small vanilla JavaScript files. SQLite runs locally. PostgreSQL is the target for shared use. This page describes what is built. The full design and its reasons are in the [study](../study/1791037419_poker_home_game_architecture.md).

## Apps

| App | Responsibility | Key files |
|---|---|---|
| `config` | Settings from the environment, root URLs, `/healthz`, database options per engine | `settings.py`, `deploy.py` |
| `accounts` | Custom `User`, sign-up, login, logout. `LoginRequiredMiddleware` protects each page | `views.py`, `forms.py` |
| `audit` | Append-only `AuditEvent` and `record()` | `services.py` |
| `groups` | `GameGroup`, `Member` (roles; roster players without logins), `Invite`, access helpers | `services.py`, `access.py`, `errors.py`, `http.py` |
| `games` | `Table`, `SettingsPreset`, `GameSession`, `SettingsVersion`, `Participant`, the lifecycle | `services.py`, `access.py`, `forms.py` |
| `ledger` | `BuyIn`, `CashOut`, their reversals, `BalanceAdjustment`, the balance check, `Finalization`, `PlayerResult`, money arithmetic | `services.py`, `queries.py`, `money.py` |
| `settlement` | Settle-up algorithm, `finalize()`, `SettlementPlan`, `Transfer`, `Payment`, `PaymentReversal` | `algorithm.py`, `services.py`, `queries.py` |
| `web` | Pages that read from several apps: home, group, session, polling endpoint, game log. No models. It never writes | `views.py` |

Dependencies point one way: `accounts → groups → games → ledger → settlement → web`. `audit` depends only on `accounts`. Two exceptions are deliberate:

- `ledger/money.py` and `settlement/algorithm.py` are pure modules with no project imports. `games` imports `ledger.money` to parse and format pesos.
- `games.services.PARTICIPANT_EXIT_GUARDS` is a list of checks. `ledger` registers one at start-up, so `games` can refuse to withdraw a player who has money without importing `ledger`.

## Rules that the code follows

1. Only `services.py` functions write. Views call services.
2. Each write to a session opens a transaction and locks the session row (`games.services.lock_session`, `select_for_update`). Writes to one session run one at a time.
3. Each write that a form starts carries a `request_id` (a hidden field from the `{% request_id_field %}` tag). A unique constraint and a check under the lock make a repeated submission a no-op.
4. Money records are never updated or deleted. A correction is a reversal row with a reason.
5. Each write records an `AuditEvent` in the same transaction and increments `GameSession.version`.
6. A rule violation raises `groups.errors.RuleError`; the view shows the message. A role violation raises `NotAllowed` (HTTP 403). A requester outside the group gets HTTP 404.

## Data model

```
User ─1:n─ Member ─n:1─ GameGroup ─1:n─ Invite
                           │
                           ├─1:n─ SettingsPreset
                           ├─1:n─ Table
                           └─1:n─ GameSession ─1:n─ SettingsVersion
                                      │
                                      ├─1:n─ Participant ─n:1─ Member
                                      │          ├─1:n─ BuyIn ──0:1─ BuyInReversal
                                      │          ├─1:n─ CashOut ─0:1─ CashOutReversal
                                      │          └─1:n─ BalanceAdjustment
                                      ├─1:n─ Finalization ─1:n─ PlayerResult
                                      │          └─1:1─ SettlementPlan ─1:n─ Transfer
                                      └─1:n─ Payment ─0:1─ PaymentReversal   (Payment → Transfer)
AuditEvent (group_id, session_id as plain integers)
```

- A **table** is reusable and has no date. A **session** is one dated game at one table. A two-table night is two sessions.
- A **Member** is a person in a group's roster. `user` is empty for a player without a login. Results are keyed by member.
- A **SettingsVersion** is never edited. A change adds a version. Each buy-in points to the version in force.
- `PlayerResult` repeats `member`, `group` and `game_date` so that later statistics read one table.

## Money and chips

- Money is integer **centavos**. Chips are integer **chip units**. No `float` is used. `ledger/money.py` is the only place that parses and formats pesos.
- The **chip rate** is two integers in lowest terms, `(rate_centavos, rate_chips)`. ₱1,000 for 10,000 chips is `(10, 1)`.
- The first accepted buy-in locks the rate on the session. Each buy-in must be between the minimum and the maximum and must buy a whole number of chips at that rate. When no accepted buy-in remains, the rate unlocks.
- While the rate is locked, the session has money in it. It cannot be canceled, and a settings change must keep the same rate.
- Totals are calculated on demand in `ledger/queries.py`. Nothing is stored until finalization.

| Figure | Definition |
|---|---|
| Total bought in | Sum of the amounts of accepted buy-ins |
| Chips issued | Sum of the chips of accepted buy-ins |
| Chips in play | Chips issued − chips of accepted cash-outs |
| Rebuys | Accepted buy-ins after a player's first |

## Session lifecycle

```
setup ──open──▶ open ──start──▶ running ──end──▶ reconciliation ──finalize──▶ finalized
  ▲               │                ▲                   │
  └────close──────┘                └──────resume───────┘
setup, open, running, reconciliation ──cancel──▶ canceled   (refused while buy-ins are accepted)
```

| State | Who sees it | Host can | Player can |
|---|---|---|---|
| `setup` | Hosts | Edit settings, add players, open, cancel | — |
| `open` | Members | The same, record and reverse buy-ins, start | Join, withdraw (before a buy-in) |
| `running` | Members | Buy-ins, rebuys, cash-outs, mark a player left, end play | Join late, withdraw (before a buy-in) |
| `reconciliation` | Members | Cash-outs, reversals, override, resume, finalize | — |
| `finalized` | Members | Mark transfers paid or unpaid | — |
| `canceled` | Members | — | — |

"Settled" is not a state. It is derived from the paid marks: `unsettled`, `partly` or `settled`.

## Balance check and override

`ledger.queries.balance()` compares chips cashed out with chips issued.

- Finalization is refused while a player with a buy-in has no cash-out record. A player who lost everything needs a cash-out of 0.
- A difference is shown in chips and pesos with its direction (chips extra or chips missing) and likely causes.
- The app never spreads a difference by itself. A host can record an **override** with a note: one named player absorbs the difference, or all players share it equally (chips that do not divide go one each in join order). The override is stored as `BalanceAdjustment` rows **in chips**, so the centavo rule below still conserves the total.

## Finalization

`settlement.services.finalize()` runs one transaction with the session locked:

1. The balance check must pass.
2. Each player's cash-out value comes from `money.allocate()` (largest-remainder rule): each value is rounded down, and the centavos left over go one each to the largest fractional parts, ties to the earlier join order. The values sum to the total bought in exactly.
3. It asserts that cash-outs equal buy-ins and that results sum to zero. A failure raises `LedgerInvariantError` and rolls back.
4. It writes `Finalization` and one `PlayerResult` per player with a buy-in.
5. It calculates transfers and asserts that they clear each balance.
6. It writes `SettlementPlan` and `Transfer` rows, sets the state, and records an audit event.

Database check constraints repeat the main invariants: `total_buy_in = total_cash_out` on `Finalization`, and `net = cash_out − buy_ins` on `PlayerResult`.

## Settle-up

`settlement/algorithm.py`:

- `balances(nets, payments)`: what each party is still owed. A payer is owed more by the amount paid; a payee less. With no payments, the balance equals the result. Stage 1 passes no payments, because none can be recorded before finalization.
- `settle(parties)`: splits the parties into the largest number of groups that each sum to zero (dynamic programming over subsets), then settles each group with one transfer fewer than its size. The result is the minimum number of transfers; the proof is in the module docstring. Ties follow join order, so the output is deterministic. Above 16 parties (more than a table seats) it falls back to one group and the plan is marked `proven_minimal = False`.

## Live updates

- `static/js/live.js` polls `GET /s/<id>/state/?v=<version>` each 4 seconds while the tab is visible.
- The endpoint returns HTTP 204 when the version is unchanged. Otherwise it returns the new version and the rendered live region, which the script swaps in.
- Each response is a full snapshot. A missed poll needs no replay.
- A hidden tab stops polling. It polls at once when it becomes visible or the browser comes back online.
- After two failures the page shows "Reconnecting… last updated …" and backs off to 8, 16, then 30 seconds.
- An update waits while the user types in a field of the live region, and applies when the field loses focus.
- `static/js/forms.js` disables a form's buttons after the first submit. The server-side `request_id` check is the real protection.

## Front end

- `templates/base.html` is the shell. `templates/web/` holds the pages and the partials of the session screen (`_session_live.html`, `_players.html`, `_balance.html`, `_results.html`, `_host_controls.html`).
- `static/css/app.css` is the one stylesheet: tokens first, dark by default, one column, 48 px controls.
- No build step and no front-end framework.

## Security

- Each page needs a login except sign-up, login and `/healthz`.
- Each lookup goes through `groups.access.member_for` or `games.access.session_for`.
- Invite tokens are stored as SHA-256 hashes. A link is shown once.
- `manage.py check --deploy` is clean with `DEBUG=False`, a real `SECRET_KEY` and `HTTPS_ONLY=True`.

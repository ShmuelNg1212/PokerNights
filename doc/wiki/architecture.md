# Architecture

One Django 6.1 project with server-rendered templates, one stylesheet and small vanilla JavaScript modules. SQLite runs locally. PostgreSQL is the target for shared use. This page describes what is built. The full design and its reasons are in the [study](../study/1791037419_poker_home_game_architecture.md).

## Apps

| App | Responsibility | Key files |
|---|---|---|
| `config` | Settings from the environment, root URLs, `/healthz`, database options per engine | `settings.py`, `deploy.py` |
| `accounts` | Custom `User`, sign-up, login, logout. `LoginRequiredMiddleware` protects each page | `views.py`, `forms.py` |
| `audit` | Append-only `AuditEvent` and `record()` | `services.py` |
| `groups` | `GameGroup`, `GroupRakeAccount`, `Member` (roles; roster players without logins), `Invite`, access helpers | `services.py`, `access.py`, `errors.py`, `http.py` |
| `games` | `Table`, `SettingsPreset`, `GameNight` (session), `GameSession` (set), `SettingsVersion`, `Participant`, `ParticipantBatch`, `PlayPeriod`, `PlayInterval`, the lifecycle, the clock | `services.py`, `access.py`, `forms.py` |
| `ledger` | `BuyIn`, `RakeEntry`, `FinalCount`, `CashOut`, `CashOutBatch`, reversals, `BalanceAdjustment`, the balance check, `Finalization`, `PlayerResult`, amount parsing and formatting | `services.py`, `queries.py`, `money.py` |
| `settlement` | Settle-up algorithm, `finalize()` for a set, `close_night()` for a session, `SettlementPlan`, `Transfer`, `Payment`, `PaymentReversal` | `algorithm.py`, `services.py`, `queries.py` |
| `web` | Pages that read from several apps: home, group, session, set, polling endpoint, set log. No models. It never writes | `views.py` |

Dependencies point one way: `accounts → groups → games → ledger → settlement → web`. `audit` depends only on `accounts`. These integration boundaries are deliberate:

- `ledger/money.py` and `settlement/algorithm.py` are pure modules with no project imports. `games` imports `ledger.money` to parse and format amounts.
- `games.services.START_HOOKS` runs ledger-owned opening-buy-in creation while the set is open, under its lock and transaction, before clock creation. Each joined participant without an unreversed buy-in receives the current default through `ledger.services.record_buy_in()`. Child UUIDs derive from the start request and participant ID. `GameSession.start_request_id` is nullable and unique; successful same-request retries return without repeating records or timers, including empty starts. Existing sets remain null without backfill. The native start option defaults checked, supports opt-out and retains its state through live redraws.
- `games.services.PARTICIPANT_EXIT_GUARDS` and `SESSION_MONEY_CHECKS` are lists of checks. `ledger` registers one in each at start-up, so `games` can refuse to withdraw a player with money, to cancel a game with money, or to change its unit, without importing `ledger`.

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

## Sessions and sets

- **Naming:** the screen word "session" is the `GameNight` model. The screen word "set" is the `GameSession` model, which existed first. See [footguns/session_means_set_in_the_code.md](footguns/session_means_set_in_the_code.md).
- `GameNight` holds table, date, location, game type, unit and status (`open`, `closed`). `GameSession.night` and `set_number` place a set in it.
- **One set in play:** a partial unique constraint allows one set per session in `setup`, `open` or `running`. `games.services.start_next_set()` checks the same under a lock on the session row, copies seats and the latest settings, and carries over participants with status `joined`. It copies no money.
- **Resume:** a set cannot resume once a later set of its session exists.
- **Settle-up:** `settlement.services.finalize()` freezes one set's results and writes no transfers. `close_night()` requires every set to be finalized or canceled, sums each member's results over the finalized sets, runs the settle-up algorithm, and writes one `SettlementPlan` for the session. `Transfer` and `Payment` name members, because a player has one participant row per set.

## Timers

- `PlayPeriod(session, started_at, ended_at)`: a stretch of play of one set. One open period per set (database constraint). The set's timer is the sum of its periods.
- `PlayInterval(session, participant, started_at, ended_at)`: a stretch during which a player was at the table while the set was in play. One open interval per participant.
- `games/clock.py` opens and closes them. The lifecycle services call it with one `now`: start and resume open; end and cancel close everything of that set at one timestamp and set `GameSession.ended_at`; join, return, leave and withdraw touch one player.
- Opening is a no-op if one is open; closing touches only open rows. A repeated request changes nothing.
- `clock.SKIP_ON_RESUME` lets `ledger` keep a cashed-out player out of a resumed set.
- Pages show the server's figure. `static/js/clock.js` only advances the shown minutes of a running timer between page updates.
- `PlayerResult.play_seconds` stores the player's time when the set is finalized. Play has ended by then, so the figure is the time up to the end of play.

`games.services.add_new_player(session_id, actor, name, request_id)` locks the set, checks a completed ParticipantBatch request before state refusal, and validates state/capacity before calling group roster creation. It composes `groups.services.add_roster_player()` and the existing participant batch addition in one outer transaction. The existing group lock protects normalized active-name uniqueness, while the set lock protects seats, the join interval and request retry. Games depends on groups; groups never acquires a set lock, so this path introduces no opposite lock order. An error rolls back the identity, join, timer and audit records together. The picker uses distinct native new-name and existing-selection forms with independent request IDs. An ended-set refusal preserves the name on a disabled recovery form.

## End of a set: counts and batch

`ledger.queries.count_total()` derives remaining confirmed stacks plus accepted cash-outs and collected rake from the existing summary. It excludes final-cashed-out players from remaining stacks and reports count coverage, stray cash-outs and the raw difference from buy-ins. It neither stores a total nor changes Balance/finalization. The shared `_count_total.html` renders a confirmed baseline and host dock preview. `counts.js` uses BigInt to replace saved amounts with valid drafts, parse ordinary native amount syntax and format exact values. Invalid or unsupported input makes the preview unavailable. No write or extra request occurs.


- `FinalCount`: a host's confirmation of a player's final amount, in the session's unit. Append-only, with a `version` per participant; `is_current` marks the one in force. Zero is a count. No row means "not counted".
- `CashOut.kind`: `partial` (the player played on) or `final`. A cash-out with "Leaving the game", any cash-out while counting, and each batch cash-out are final. A player has at most one accepted final cash-out. If the player returns or buys in again, it becomes partial again (logged).
- The count fields of a set belong to one form (`counts-form`, through the `form` attribute). `ledger.services.confirm_counts()` confirms every typed count in one transaction and skips empty or unchanged ones. A refused submit stores the typed text in the login session and the page shows it again once.
- Status of a player while counting: `cashed_out` (has a final cash-out), `ready` (has a current count), `awaiting`.
- `ledger.services.cash_out_counted(session_id, actor, count_ids, request_id)`: under the set lock, each submitted count must still be current and its player not cashed out; otherwise nothing is recorded. It writes one `CashOutBatch`, one final `CashOut` per count (linked to the count and the batch), audit events and one version increment. A known `request_id` returns the first batch.
- Reversing a batch cash-out voids its count. Resuming play voids counts that are not cashed out.
- The finalization gate: each player with a buy-in needs a final cash-out, and the totals must match or be overridden.

## Adding players

- **One player:** `games.services.add_participant()`. A player joins for themselves, or a host adds one member. The unique `(session, member)` constraint makes a repeat a no-op.
- **Several players:** `games.services.add_participants(session_id, actor, member_ids, request_id)`. Host only, in `setup`, `open` or `running`. Under the session lock it checks that each id is an active member of the group, that none is at the table, and that the count fits the free seats. Any failure raises `RuleError` and adds nobody. Success writes the participants, one audit event each, one `ParticipantBatch` and one version increment.
- `ParticipantBatch` stores the form's `request_id` with a unique constraint per session. A repeated submission returns the players of the first call.
- Neither function touches `ledger` or `settlement`. Joining takes one unit of capacity and gives no seat number.
- The picker page (`games.views.participants_add`, `templates/games/add_players.html`, `static/js/pick.js`) is separate from the live game page, so polling cannot clear the ticks. Search hides rows in the browser; the checkboxes stay in the form.

## Amounts and units

- A game has a **unit**: `php` (pesos, the default) or `chips`. Presets and sessions carry it. A session copies it from the form or the preset.
- Each amount is one integer in the unit's smallest step: **centavos** in a pesos game, **whole chips** in a chips game. No `float` is used.
- A chips game has **no peso value**. Nothing in the code converts chips to pesos. There is no chip rate and no "chips per buy-in".
- `ledger/money.py` is the only place that parses and formats: `parse_amount(text, unit)` and `format_amount(value, unit)` give `₱1,600` or `1,600 chips`. Chip input must be a whole number. Templates use `{{ value|amount:unit }}`.
- A buy-in must be between the minimum and the maximum of the settings in force.
- The unit can change only while the game has no accepted buy-in or cash-out. `games.services.has_money()` asks the checks in `SESSION_MONEY_CHECKS`; `ledger` registers one at start-up. The same check blocks cancel.
- `Finalization` and `PlayerResult` store the unit, so later statistics never add pesos to chips.
- Totals are calculated on demand in `ledger/queries.py`. Nothing is stored until finalization.

| Figure | Definition |
|---|---|
| Total bought in | Sum of the amounts of accepted buy-ins |
| Total cashed out | Sum of the amounts of accepted cash-outs |
| Collected rake | Accepted buy-ins’ linked fees; reversals excluded |
| Available to play | Gross buy-ins − collected rake |
| Still in play | Available to play − total cashed out (shown while the game is open or running) |
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
| `open` | Members | The same, record and reverse buy-ins, start. Change the unit before the first buy-in | Join, withdraw (before a buy-in) |
| `running` | Members | Buy-ins, rebuys, cash-outs, mark a player left, end play | Join late, withdraw (before a buy-in) |
| `reconciliation` | Members | Cash-outs, reversals, override, resume, finalize | — |
| `finalized` | Members | Mark transfers paid or unpaid | — |
| `canceled` | Members | — | — |

"Settled" is not a state. It is derived from the paid marks: `unsettled`, `partly` or `settled`.

## Balance check and override

`ledger.queries.balance()` compares cash-outs plus collected rake with gross buy-ins, in the game's unit. Overrides cover the remaining discrepancy. Count preview adds remaining stacks, earlier cash-outs and recorded rake, excluding overrides.

- Finalization is refused while a player with a buy-in has no cash-out record. A player who lost everything needs a cash-out of 0.
- A difference is shown as an amount with its direction ("₱50 too much" or "₱50 is missing") and likely causes.
- The app never spreads a difference by itself. A host can record an **override** with a note: one named player absorbs the difference, or all players share it equally (units that do not divide go one each in join order). The override is stored as `BalanceAdjustment` rows.

## Finalization

`settlement.services.finalize()` runs one transaction with the session locked:

1. The balance check must pass.
2. Each player's result is cash-outs plus any override, minus buy-ins. No conversion or rounding takes place.
3. It asserts that cash-outs plus overrides plus rake equal gross buy-ins, and that player results plus rake sum to zero. A failure raises `LedgerInvariantError` and rolls back.
4. It writes `Finalization.total_rake` and each `PlayerResult.rake_total` with the other frozen facts.
5. It marks the set finalized, increments its version and records an audit event. It writes no transfers. Session closure handles those.

Database check constraints repeat the main invariants: `total_buy_in = total_cash_out + total_rake` on `Finalization`; `net = cash_out − buy_in_total` and `cash_out = cashed_out + adjustment` on `PlayerResult`.

## Set rake and group account

Each group has one `GroupRakeAccount`, created by group services or the metadata migration. It is not a Member or settlement party and has no mutable money counter. `ledger.queries.group_rake()` derives accepted lifetime totals and a per-session/set breakdown. Web composes this on the membership-protected group page. Pesos and chips stay separate; live and finalized sets contribute, payment marks do not.

`SessionForm` and `SettingsForm` share native rake choices and active-only value parsing. Session creation validates stakes and rake before writing and stores the rule in its first settings version. Inactive text inputs have no browser number constraints.

`SettingsVersion` holds `rake_mode` (Off, Percentage, Flat), integer `rake_basis_points` and `rake_flat`. Host settings use a per-set unique request ID; accepted retries return their version before state refusal. Explicit settings submissions create audited versions, even when values are unchanged, to persist the request identity. Stakes-only service calls without a request retain their prior no-op behavior.

Percentage accepts two decimals (0.01%–99.99%); 5% is 500 basis points. Each fee is `gross * basis_points // 10000`, rounded down per entry. Flat is a positive native amount. Off normalizes both parameters to zero. Rake must leave a positive playable amount. Gross buy-in limits and default amounts remain gross. The rule is locked while accepted buy-ins or cash-outs exist; unchanged-rule stakes edits remain allowed. Next sets inherit the rule. A permitted unit change resets it to Off. Presets remain stakes-only.

`record_buy_in()` validates the fee before any timer/money/audit write, then writes BuyIn and one immutable linked RakeEntry in the same locked transaction. Opening, rebuy and late-player paths all use it. The linked unique buy-in request prevents duplicate fees. Entry facts include amount, unit and rule provenance; zero fees are explicit for new Off/rounded-zero buy-ins. Historical buy-ins without entries mean zero fee. Reversing a buy-in excludes its fee without deleting either row; the log retains its recorded unit. There is no independent fee edit or historical charge backfill.

The migration adds zero snapshot defaults and changes only finalization conservation. Existing money, results, transfers and payments retain their exact original values. Once rake records exist, preserve the schema and use forward fixes; an old conservation rule cannot represent those records safely.

## Settle-up

`settlement.services.session_standings()` keeps actual after-rake results. `settlement_balances()` separately sums `net + rake_total` in first-join order for closure. These remaining balances sum to zero because rake was already collected at each buy-in. Closure passes them to the unchanged algorithm and verifies exact clearance. No transfer or payment targets the group rake account. For two ₱1,000 buy-ins at 5% and ₱950 cash-outs, results are −₱50 each, group rake is ₱100, and no further transfer is owed.

`settlement/algorithm.py`:

- `balances(nets, payments)`: what each party is still owed. A payer is owed more by the amount paid; a payee less. With no payments, the balance equals the result. Stage 1 passes no payments, because none can be recorded before finalization.
- `settle(parties)`: splits the parties into the largest number of groups that each sum to zero (dynamic programming over subsets), then settles each group with one transfer fewer than its size. The result is the minimum number of transfers; the proof is in the module docstring. Ties follow join order, so the output is deterministic. Above 16 parties (more than a table seats) it falls back to one group and the plan is marked `proven_minimal = False`.

## Live updates

- `static/js/live.js` polls `GET /s/<id>/state/?v=<version>` each 4 seconds while the tab is visible.
- The endpoint returns HTTP 204 when the version is unchanged. Otherwise it returns the new version and the rendered live region, which the script swaps in.
- Each response is a full snapshot. A missed poll needs no replay.
- A hidden tab stops polling. It polls at once when it becomes visible or the browser comes back online.
- After two failures the page shows "Reconnecting… last updated …", marks the figures as stale, and backs off to 8, 16, then 30 seconds.
- An update waits while the user types in a field of the live region, and applies when the field loses focus.
- A refresh replaces the whole region. Fields with a `data-keep` key keep their typed, unsaved value across it: the script reads them before the swap and puts them back after it. Nonblank count inputs are also retained when their value equals the rendered default, because refused submissions render unsaved drafts as defaults. `live:updated` fires after typed values and open details are restored, so derived previews read the restored fields.
- `static/js/forms.js` disables a form's buttons after the first submit. The server-side `request_id` check is the real protection.

## Front end

- `templates/base.html` is the shared shell. One locally hosted Archivo variable font is preloaded with `font-display: swap`. Font and icon licenses live in `static/fonts/` and `static/icons/`.
- `static/css/app.css` holds tokens, base elements and components. The Rack is dark, single-column on phones, with 48 px action controls. Active sets, count-up, batch review, final results and session settle-up use a 400 px overview column beside the working list from 900 px. Group uses a sessions-first column beside management from 900 px. Home uses group navigation rows, supporting forms use a narrow frame and the log uses a reading column.
- `_session_live.html` selects the compact active composition for setup, open and running, `_count_up.html` for reconciliation and `_final_set.html` for frozen results. `_session_legacy.html` provides the canceled-set reason, retained roster and log link. `_players_count.html` retains the single inline count form. `_player_records.html` shares the existing records, corrections and reconciliation exceptions. The batch review remains a separate host page with exact count IDs.
- `web/templatetags/table_tags.py` is presentation only: initial tokens, join-order set colours, member-ID roster colours, decorative buy-in edges, input amounts, split-bar percentage and licensed Lucide SVG paths. Formatting calls the existing integer-money module.
- `static/js/sheets.js` serves both set forms and the session recap. It moves the row's native form content into one `<dialog>` outside `#live`. Polling can replace rows without replacing that form or its focused field. Closing restores the content to the current row, and returns focus. Native expandable forms remain usable without JavaScript.
- A sheet POST stores typed `data-keep` values in `sessionStorage`. An error banner after redirect reopens the matching form and restores the values. Success clears that temporary draft. These drafts are local to the browser tab; they do not write money.
- `static/js/changes.js` watches explicit server-value keys and compares them with this tab's earlier values. Only a changed value highlights a row or total. A server-gated `data-balance` marker draws the double rule once per set per browser, with a `localStorage` flag; the static message remains on later visits. Amounts themselves never interpolate. `toasts.js` shows dismissible success notices; errors stay visible. `forms.js` marks pending submissions as Sending… and disables repeat buttons through `form.elements`, including external count buttons; back/forward-cache restoration re-enables those controls.
- Reduced motion disables CSS animations, transitions, view transitions and press movement. Dialog focus handling uses the native modal and explicit Tab wrapping.
- `settlement.queries.NightOutcome` derives total to pay, paid amount and still to pay from the frozen transfer plan and current active payments. Session tokens reuse standings in first-join order with member identity. `night_recap()` reads current finalization buy-in snapshots and known finalized-set timer durations, exposes unknown/partial time and preserves tied top results. These helpers write no records.
- The closed `web/night.html` page uses the shared sheet module with `.night-layout` as its source region. `rack-recap:<night>:<user>` in localStorage suppresses repeat automatic opening; storage refusal leaves manual access. The inline source remains available without JavaScript. There is no session polling endpoint added.
- [DESIGN.md](../../DESIGN.md) and `.impeccable/design.json` describe the built visual system. The [parent redesign plan](../plan/1791046015_visual_redesign.md), [slice 2 plan](../plan/1791050738_redesign_slice_2.md), [slice 3 plan](../plan/1791053204_redesign_slice_3.md) and [slice 4 plan](../plan/1791084843_redesign_slice_4.md) record measured checks.
- Inline group/home failures use bound forms and existing services. `groups.http.keep_form()` stores only declared non-sensitive values and errors in a form/group-scoped request-session draft. `take_form()` consumes it once on the redirected page. The destination rechecks membership and supplies host forms only to hosts. This preserves the one-way app dependency; neither groups nor games imports web composition. Business records remain service-only writes.
- No build step, front-end framework, added package or external runtime request.

## Security

- Each page needs a login except sign-up, login and `/healthz`.
- Each lookup goes through `groups.access.member_for` or `games.access.session_for`.
- Invite tokens are stored as SHA-256 hashes. A link is shown once.
- `manage.py check --deploy` is clean with `DEBUG=False`, a real `SECRET_KEY` and `HTTPS_ONLY=True`.

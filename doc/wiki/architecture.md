# Architecture

One Django 6.1 project with server-rendered templates, one stylesheet and small vanilla JavaScript modules. SQLite runs locally. PostgreSQL is the target for shared use. This page describes what is built. The full design and its reasons are in the [study](../study/1791037419_poker_home_game_architecture.md).

## Apps

| App | Responsibility | Key files |
|---|---|---|
| `config` | Settings from the environment, root URLs, `/healthz`, database options per engine | `settings.py`, `deploy.py` |
| `accounts` | Custom `User`, sign-up, login, logout, and `PasswordResetLink` (a hashed one-use token; `services.py` is its only writer). `LoginRequiredMiddleware` protects each page | `views.py`, `forms.py`, `services.py` |
| `audit` | Append-only `AuditEvent` and `record()` | `services.py` |
| `notify` | Table alerts (2026-10-15): `Notice` (a player was put in a set by someone else; one per player and set) and `PushSubscription` (a phone that takes notifications). Sends Web Push after the commit | `services.py`, `push.py`, `views.py` |
| `groups` | `GameGroup`, `GroupRakeAccount`, `Member` (roles; roster players without logins), `Invite`, access helpers | `services.py`, `access.py`, `errors.py`, `http.py` |
| `games` | `Table`, `SettingsPreset`, `ChipPreset`, `GameNight` (session), `GameSession` (set), `SettingsVersion`, `Participant`, `ParticipantBatch`, `PlayPeriod`, `PlayInterval`, session chip values, the lifecycle, the clock | `services.py`, `access.py`, `forms.py`, `chips.py` |
| `ledger` | `BuyIn`, `RakeEntry`, `CountEntry` (a player's own statement of their final count, never a count), `FinalCount`, `CashOut`, `CashOutBatch`, reversals, `BalanceAdjustment`, the balance check, `Finalization`, `PlayerResult`, amount parsing and formatting | `services.py`, `queries.py`, `money.py` |
| `settlement` | Settle-up algorithm, `finalize()` for a set, `close_night()` for a session, `SettlementPlan`, `Transfer`, `Payment`, `PaymentReversal` | `algorithm.py`, `services.py`, `queries.py` |
| `web` | Pages that read from several apps: home, group, session, set, polling endpoint, set log. No models. Its one write is through another app's service: opening a set marks the viewer's notice seen (`notify.services.mark_seen`) | `views.py` |

Dependencies point one way: `accounts → groups → games → ledger → settlement → web`. `audit` and `notify` depend only on `accounts`; `games` calls `notify.services.tell`. These integration boundaries are deliberate:

- `ledger/money.py` and `settlement/algorithm.py` are pure modules with no project imports. `games` imports `ledger.money` to parse and format amounts.
- `games.services.START_HOOKS` runs ledger-owned opening-buy-in creation while the set is open, under its lock and transaction, before clock creation. Each joined participant without an unreversed buy-in receives the current default through `ledger.services.record_buy_in()`. Child UUIDs derive from the start request and participant ID. `GameSession.start_request_id` is nullable and unique; successful same-request retries return without repeating records or timers, including empty starts. Existing sets remain null without backfill. The native start option defaults checked, supports opt-out and retains its state through live redraws.
- `games.services.PARTICIPANT_EXIT_GUARDS` and `SESSION_MONEY_CHECKS` are lists of checks. `ledger` registers one in each at start-up, so `games` can refuse to withdraw a player with money, to cancel a game with money, or to change its unit, without importing `ledger`.

## Rules that the code follows

1. Only `services.py` functions write. Views call services.
2. Each session write opens a transaction. A set write uses `games.services.lock_session()`: lock its parent `GameNight` first, then its `GameSession` row with `select_for_update`. Session-wide writes use `lock_night()` first. This lock order prevents an assignment edit and a count submission from taking the same locks in opposite orders. Writes in one session run one at a time.
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
                                      │          └─1:n─ SettlementPlan ─1:n─ Transfer
                                      └─1:n─ Payment ─0:1─ PaymentReversal   (Payment → Transfer)
AuditEvent (group_id, session_id as plain integers)
```

- A **table** is reusable and has no date. A **session** is one dated game at one table. A two-table night is two sessions.
- A **Member** is a person in a group's roster. `user` is empty for a player without a login. Results are keyed by member.
- A **SettingsVersion** is never edited. A change adds a version. Each buy-in points to the version in force.
- `PlayerResult` repeats `member`, `group` and `game_date` so that later statistics read one table.

## Sessions and sets

- **Naming:** the screen word "session" is the `GameNight` model. The screen word "set" is the `GameSession` model, which existed first. See [footguns/session_means_set_in_the_code.md](footguns/session_means_set_in_the_code.md).
- `GameNight` holds table, date, location, game type, unit, chip values and status (`open`, `closed`). `GameSession.night` and `set_number` place a set in it.
- **One set in play:** a partial unique constraint allows one set per session in `setup`, `open` or `running`. `games.services.start_next_set()` checks the same under a lock on the session row, copies seats and the latest settings, and carries over participants with status `joined`. It copies no money.
- **Resume:** a set cannot resume once a later set of its session exists.
- **Settle-up:** `settlement.services.finalize()` freezes one set's results and writes no transfers. `close_night()` requires every set to be finalized or canceled, sums each member's results over the finalized sets, runs the settle-up algorithm, and writes one `SettlementPlan` for the session. `Transfer` and `Payment` name members, because a player has one participant row per set.
- **Payments at the table** ([ADR 0002](../adr/0002-payments-at-the-table.md)): a `Payment` with no transfer. `record_table_payment()` and `reverse_table_payment()` write it while the session is open; the check constraint `payment_at_table_names_two_players` requires both players and that they differ. `payable_seats()` is the one rule for who can be named: an accepted buy-in in a set that is not canceled. Results never read payments; only the balances at close do.

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
- The count fields of a set belong to one form (`counts-form`, through the `form` attribute). `ledger.services.confirm_counts()` confirms every typed count in one transaction and skips empty or unchanged ones. A refused submit stores the typed text in the login session and the page shows it again once. Since 2026-10-06 the same call takes `entries`: for a player whose field is empty, the id of that player's own `CountEntry` that the page showed. An entry is accepted only while it is still current, never over a typed amount and never over a count already in force.
- Two writes are open to a player, for their own participant only, resolved from the login: a rebuy through `record_buy_in` and a statement through `enter_count`. Both lock the set row, audit and bump the version, so the polling page of every member shows them. Every buy-in form carries `seen_count`; `record_buy_in` refuses when the player's accepted buy-ins no longer number that, which stops one rebuy being recorded from two phones.
- Status of a player while counting: `cashed_out` (has a final cash-out), `ready` (has a current count), `awaiting`.
- `ledger.services.cash_out_counted(session_id, actor, count_ids, request_id)`: under the set lock, each submitted count must still be current and its player not cashed out; otherwise nothing is recorded. It writes one `CashOutBatch`, one final `CashOut` per count (linked to the count and the batch), audit events and one version increment. A known `request_id` returns the first batch.
- Reversing a batch cash-out voids its count. Resuming play voids counts that are not cashed out.
- The finalization gate: each player with a buy-in needs a final cash-out, and the totals must match or be overridden.

### Session chip values

`GameNight.chip_values` holds one optional denomination table for all its sets. Each row has a fixed colour ID, an optional label and a positive integer value in the session unit. A new session starts without assignments. Colours have no assumed value. This is an input method for stack values, not an exchange rate.

`games.services.set_chip_values()` replaces the table under the session lock. It checks the posted `chip_values_revision`. Each successful save increments that revision and creates a `ChipValueChange` row. Unique constraints on the session and request ID make prior saves safe to repeat. The service audits the save and increments every set's live version. The session page's stamp includes the revision and lock state.

`ledger.services.enter_count()` and `confirm_count()` accept denomination IDs and whole quantities as an alternative to an amount. Both use `games.chips.calculate()` under the same parent-first lock. The server checks the revision and calculates the total with integer arithmetic. It rejects unknown or repeated IDs, fractions, negative quantities and totals above the amount limit. Blank quantities mean zero only inside an explicitly submitted chip form. An untouched form needs the separate Empty stack action.

A successful chip-based submission sets `GameNight.chip_values_locked_at`, including a player's unconfirmed entry. A refused submission does not lock the table. Clearing counts or reopening the session does not unlock it. This prevents later edits from changing the meaning of another player's count. A configured table also blocks a unit change.

`CountEntry.chip_breakdown` and `FinalCount.chip_breakdown` retain the denominations, quantities and subtotals used for that record. Corrections create new count versions. Accepting a player's entry copies its breakdown. A direct amount replacement has no unrelated chip breakdown. Host confirmation, cash-out and balance checks use the existing count workflow.

`ChipPreset` holds a group's reusable chip values with a unit. `games.services.save_chip_preset()` and `archive_chip_preset()` lock the group row and validate with `games.chips.denominations()`. Each write creates a `ChipPresetChange` row with a unique request ID, so a repeated or late request writes nothing. A session never references a preset: the Chip values page fills its form from one, and `set_chip_values()` saves a copy.

`games/chip_views.py` adapts the setup and preset forms. `ledger/chip_views.py` adapts the chip-count forms. Both keep their writes in services. The native pages work without JavaScript. `static/js/denominations.js` adds exact BigInt previews and saves each draft's revision with its quantities across live redraws. A stale draft shows Recount needed and disables submission until the person loads current values and recounts. The server checks the revision again when the form is sent.

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
- The unit can change only while the game has no accepted buy-in or cash-out and the session has no configured chip values. `games.services.has_money()` asks the money checks in `SESSION_MONEY_CHECKS`; `ledger` registers one at start-up. The money check also blocks cancel.
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

- `balances(nets, payments)`: what each party is still owed. A payer is owed more by the amount paid; a payee less. With no payments, the balance equals the result. `close_night()` passes the session's standing table payments, after any carried transfers.
- `settle(parties)`: splits the parties into the largest number of groups that each sum to zero (dynamic programming over subsets), then settles each group with one transfer fewer than its size. The result is the minimum number of transfers; the proof is in the module docstring. Ties follow join order, so the output is deterministic. Above 16 parties (more than a table seats) it falls back to one group and the plan is marked `proven_minimal = False`.

## Archive and delete

`GameNight` and `GameGroup` carry `archived_at` and `archived_by`. Nothing else marks an archive.

- **Session services** are in `games/services.py`: `archive_night`, `restore_night`, `delete_night`. They lock the session row with `lock_night(..., allow_archived=True)`, write an audit event and bump the version of every set.
- **One gate for writes.** `lock_night` and `lock_session` raise `RuleError` for an archived session. `lock_session` joins the session row, so its `select_for_update` locks that row too and an archive waits for a write in progress. No write service needs its own check.
- **Money check without imports.** `games.NIGHT_RECORD_CHECKS` holds one check from `ledger` and one from `settlement`, registered in each app's `ready()`, like `SESSION_MONEY_CHECKS`. Any ledger row, plan or payment makes a session undeletable. The database also refuses through `PROTECT`.
- **Totals.** Archived sessions are filtered in `settlement.queries.counted_results` and `unpaid_transfers`, `ledger.queries.group_rake`, `web.views.visible_nights` and `web.home.home_cards`.
- **Pages of an archived session** render with `games.access.read_only(member)`, a copy of the membership with the player role, so no host control appears. The session page gets the real role only for Restore.
- **Group services.** `groups.services.archive_group` and `restore_group`; `lock_group` refuses an archived group and is called by `create_session` and `create_invite`. `groups.ARCHIVE_GUARDS` lets `games` refuse while a set is unfinished. `games.services.delete_group` deletes in the order the `PROTECT` links require: sets, sessions, tables, the rake account, then the group.
- **Access.** `groups.access.member_for` returns 404 for an archived group. Only the restore and delete views pass `archived=True`.
- **Known gap.** A write on a finished set that was started just before the group was archived can still land, because set writes do not lock the group row. It is visible after restore and breaks no money rule.
- **Request ids.** These actions carry none; a repeat is a no-op, as for `close_night`.

## Screen changes

Links change the screen without unloading the page (Turbo navigation). Forms do so only when marked `data-turbo="true"`; every other form posts natively and loads a page.

- **Script lifetime.** Every script loads once from the head and registers a start and a stop with `static/js/page.js`. `turbo-setup.js` calls stop before a page is swapped out and start after the next one is in. See the footgun [scripts run once per tab](footguns/scripts_run_once_per_tab.md). This is a rule for every future script.
- **No page cache.** `turbo-cache-control: no-cache` on every page. Back and Forward fetch the page again; scroll position is still restored.
- **Prefetch.** A link is fetched when the pointer or finger reaches it. `config.prefetch.PrefetchLeavesOneTimeState` makes such a request render without flash messages and leave the session's one-time values (`inline_forms`, `new_invite_url`, `count_drafts`) untouched, so a page that is never shown consumes nothing. A new one-time session value must be added to its list. Turbo itself waits 100 ms after a hover before it sends; `turbo-setup.js` passes a touch on with no delay, so the request leaves as the finger lands and a tap asks once.
- **Server timing.** `config.timing.ServerTiming` is the first middleware. Every response carries `Server-Timing: app;dur=…, db;dur=…;desc="N queries", connect;dur=…`: the whole request, the wait for queries with their count, and the time to open a database connection. It reads no request data and writes nothing. `static/js/perf.js` shows these figures on the phone when asked with `?perf=1` (see [features](features.md)).
- **Query counts.** `web/tests/test_query_counts.py` holds the busiest pages to a number: the session page 14 whatever its number of sets, the set page and a redrawing poll 13, and no write of the login session on a plain page view. Figures over several sets come from one query each: `ledger.queries.rake_total`, `games.clock.timers`, `settlement.services.result_rows`. `games.clock.player_clocks` reads a set's intervals once.
- **One-trip actions.** `config.inplace.AnswerInPlace` sits after the session, login, message and prefetch middleware. A form that Turbo sends in place carries `X-Answer-In-Place: <the page's path>` (`turbo-setup.js`). When the view answers with a redirect to exactly that path, the middleware draws the page as a plain GET in the same request (the same login session, user and queued messages) and returns it with status 200, `X-In-Place-Location` and `no-store`. `turbo-setup.js` stops Turbo's own handling of that answer and hands the HTML to Turbo as a finished visit, so the page is updated as after a redirect. Views still answer with redirects; without the header nothing changes. A page that fails to draw falls back to the redirect. `ANSWER_IN_PLACE=False` switches it off.
- **A failed screen change** falls back to an ordinary navigation, so the service worker's offline page appears.
- **Accessibility.** After a swap the new title is written to a polite live region and focus moves to `<main>`, unless the page has an `autofocus` field.
- **A release.** Script and stylesheet tags are tracked; the first screen change after a release is a full page load.

## In-place updates

Two things now replace content on the set page without a reload: the 4-second poll (`live.js`, replaces `#live`) and a background form send (Turbo morph refresh of the whole body). They share rules: `data-keep` fields keep typed text, `data-key` disclosures stay open, `data-focus-key` controls keep focus, and every page module reacts to `live:updated`. `turbo-setup.js` raises `inplace:updated` first so `live.js` can adopt the new version and skip a redundant poll. The sheet container and the offline notice are `data-turbo-permanent`, so a morph leaves them alone. See [features](features.md#actions-update-in-place).

## Motion

- **Screen changes start their own view transition.** `base.html` no longer carries Turbo's `view-transition` meta tag. Turbo starts its transition before it announces the new screen, and the browser photographs the old screen at that moment, too early to mark what is carried. `turbo-setup.js` therefore pauses the render in `turbo:before-render` (`preventDefault`), sets `data-go` and the temporary `view-transition-name`s from the old and new `<main>`, calls `document.startViewTransition`, and resumes Turbo's render inside it; `turbo:render` tells the transition the screen is in place (with a 2s fallback). `pokerPage.stop()` runs inside the transition, after the photograph, so the leaving screen is photographed as the person saw it. In-place updates (morph) go through the same transition with no direction, as they did under Turbo's.
- **Clean up on the transition's own `finished` promise, nothing earlier.** The first version removed `data-go` when the layers' animations ended. The layers are still on screen for a moment after that; without `data-go` the old screen's layer falls back to the default fade and plays it again, which showed the previous screen for a split second on an iPhone.
- **A tab's marker is its own element** (`.tab-marker` inside the current tab). In a tab change it is one layer, each word is another layer above it, and the tab bar a third below. Naming the whole tab made its word travel with the marker.
- A direction needs a depth on both screens (`data-depth` on `<main>`, set by each template's `screen` block) and a tapped link: a history visit (`turbo:visit` with action `restore`) gets none. A new screen template must set its depth or it only cross-fades.
- During a view transition Chrome sends a tap to `<html>` and `elementFromPoint` returns `<html>`, even with `pointer-events: none` on `::view-transition`. `turbo-setup.js` finds the control by its rectangle and clicks it when exactly one control is there.

- `static/js/vendor/motion-14.0.0.js` defines `Motion`. `static/js/motion.js` loads after it and before the other page scripts, and exposes `window.pokerMotion`: `on()`, `run(element, keyframes, preset, extra)`, `after(controls, done)`, `settle(element, controls, properties)` and `timing(preset)` (a spring as a duration and an easing for the Web Animations API).
- `on()` is false under reduced motion or when `Motion` is missing. `run` then returns `null`, and each caller keeps its plain path. The class `motion-on` on `<html>` tells the CSS which of the two is in use.
- `motion.js` registers with `window.pokerPage`. On stop it cancels every animation it started. Its document listeners (press, release, `inplace:updated`, `inplace:failed`) are added once per tab.
- Callers: `toasts.js` (arrive, stack, leave), `sheets.js` (rise, leave), `dock.js` (the opening spring), `flow.js` (rows and state on the set page), `changes.js` (edge, badges, books balance). The presets and their uses are in DESIGN.md, "Motion system".
- **The set page has a before-event.** `live:updating` is dispatched on `#live` before either kind of redraw: by `live.js` before it replaces the HTML, and by `turbo-setup.js` before a morph render. `live:updated` follows the redraw as before. `flow.js` reads each keyed row's position (`li[data-watch]`) and the set's state (`#live[data-state]`, also `state` in the poll's JSON) on the first event and compares on the second. A redraw with no before-event, such as a first load or a screen change, moves nothing.
- **Motion writes the final style once more on the frame after it reports the end.** Clearing an inline style in the `finished` callback is undone. Use `pokerMotion.settle`, which waits two frames.
- Motion starts an animation on the frame after `run` is called, before that frame is painted. A check that reads the first frame must read it in `requestAnimationFrame`.
- Motion animates `transform` and `opacity` only: `transform` as one string where a single movement is enough (sheets, rows), the separate `x`, `y` and `scale` where movements combine (buttons, toasts), with `will-change: transform` set by `run` while they play. The dock's height stays on the Web Animations API.

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
- `static/css/app.css` holds tokens, base elements and components. The Rack is dark, single-column on phones, with 48 px action controls. Active sets, count-up, batch review, final results and session settle-up use a 400 px overview column beside the working list from 900 px. Group has Sessions, Stats and Group settings views on one route; settings use two columns from 900 px. Home uses group navigation rows, supporting forms use a narrow frame and the log uses a reading column.
- `_session_live.html` selects the compact active composition for setup, open and running, `_count_v2.html` for reconciliation and `_final_set.html` for frozen results. `_session_legacy.html` provides the canceled-set reason, retained roster and log link. `_players_count.html` retains the single inline count form. `_player_records.html` shares the existing records, corrections and reconciliation exceptions. The batch review remains a separate host page with exact count IDs.
- `web/templatetags/table_tags.py` is presentation only: initial tokens, join-order set colours, member-ID roster colours, decorative buy-in edges, input amounts and licensed Lucide SVG paths. Formatting calls the existing integer-money module.
- `static/js/sheets.js` serves both set forms and the session recap. It moves the row's native form content into one `<dialog>` outside `#live`. Polling can replace rows without replacing that form or its focused field. Closing restores the content to the current row, and returns focus. Native expandable forms remain usable without JavaScript.
- A sheet POST stores typed `data-keep` values in `sessionStorage`. An error banner after redirect reopens the matching form and restores the values. Success clears that temporary draft. These drafts are local to the browser tab; they do not write money.
- `static/js/changes.js` watches explicit server-value keys and compares them with this tab's earlier values. Only a changed value highlights a row or total. A server-gated `data-balance` marker draws the double rule once per set per browser, with a `localStorage` flag; the static message remains on later visits. Amounts themselves never interpolate. `toasts.js` shows dismissible success notices; errors stay visible. `forms.js` marks pending submissions as Sending… and disables repeat buttons through `form.elements`, including external count buttons; back/forward-cache restoration re-enables those controls.
- Reduced motion disables CSS animations, transitions, view transitions and press movement. Dialog focus handling uses the native modal and explicit Tab wrapping.
- `settlement.queries.NightOutcome` derives total to pay, paid amount and still to pay from the frozen transfer plan and current active payments. Session tokens reuse standings in first-join order with member identity. `night_recap()` reads current finalization buy-in snapshots and known finalized-set timer durations, exposes unknown/partial time and preserves tied top results. It returns a `Recap` with a ranked `RecapLine` per player, a `RecapSet` per finalized set and the `Highlight`s that have something to say. Its per-player figures come from `settlement.services.result_rows()`, the one read of the session's current `PlayerResult` rows, which returns named rows and is kept on `NightOutcome.results`, so the recap adds no query to the session page. `NightOutcome.part_for(member_id)` returns a `ViewerPart`: the member's transfers and what of them is still unpaid to pay or to receive, for the session page's headline. These helpers write no records.
- The closed `web/night.html` page uses the shared sheet module with `.night-layout` as its source region. `rack-recap:<night>:<user>` in localStorage suppresses repeat automatic opening; storage refusal leaves manual access. The inline source remains available without JavaScript. There is no session polling endpoint added. The recap's markup is `web/_night_recap.html`; `sheets.js` marks its result list before the sheet shows and lets the bars grow when an IntersectionObserver first sees the list, clearing the marks when the sheet closes.
- [DESIGN.md](../../DESIGN.md) and `.impeccable/design.json` describe the built visual system. The [parent redesign plan](../plan/1791046015_visual_redesign.md), [slice 2 plan](../plan/1791050738_redesign_slice_2.md), [slice 3 plan](../plan/1791053204_redesign_slice_3.md) and [slice 4 plan](../plan/1791084843_redesign_slice_4.md) record measured checks.
- Inline group/home failures use bound forms and existing services. `groups.http.keep_form()` stores only declared non-sensitive values and errors in a form/group-scoped request-session draft. `take_form()` consumes it once on the redirected page. The destination rechecks membership and supplies host forms only to hosts. This preserves the one-way app dependency; neither groups nor games imports web composition. Business records remain service-only writes.
- `web.views.group` chooses the view from `?view=`. Kept form drafts and the one-time invite link are taken only in the settings view, so opening another tab does not use them up. `groups.http.group_settings()` redirects management POSTs to `?view=settings#section`.
- `settlement.queries.group_stats()` reads `PlayerResult` rows that are current, belong to a finalized set and a closed session, in one unit. One grouped query adds each member's sets per session; Python then counts sessions and profitable sessions. `stat_periods()` lists the units and months that have data and decides whether the Stats tab shows. Both are read-only: two queries for a ranking, whatever the number of players.
- `.felt` is the in-play field; `.felt.hero` is the same panel on a neutral surface for every other state. `.panel`, `.notice-info`, `.tabs`, `.pills` and `.player-actions` are shared components listed at the top of `app.css`.
- `static/branding/` holds four hand-written SVGs. The wordmark is Archivo converted to outlines, so the files need no font.
- `web/home.py` builds the Your groups page. `home_cards(user)` returns one `Card` per active membership from eleven batched queries, whatever the number of groups or players: memberships, members, tables, open sessions with their sets, timers and seated counts for sets in play, `settlement.queries.member_records()`, `unpaid_transfers()`, the latest closed session per group and `session_nets()`. `_choose_status()` picks the one status and action for the viewer. `games.clock.seconds_by_set()` reads several timers in one query. All read-only.
- No build step, front-end framework, added package or external runtime request.

## Security

- Each page needs a login except sign-up, login and `/healthz`.
- Each lookup goes through `groups.access.member_for` or `games.access.session_for`.
- Invite tokens are stored as SHA-256 hashes. A link is shown once.
- `manage.py check --deploy` is clean with `DEBUG=False`, a real `SECRET_KEY` and `HTTPS_ONLY=True`.

## Roster management

- **Removal guard.** `groups.services.REMOVE_GUARDS` holds `guard(member)` functions that raise `RuleError`, as `ARCHIVE_GUARDS` does for a group. `games` registers `guard_member_removal` in `GamesConfig.ready()`: it refuses a member who is `joined` in a set in `UNFINISHED_STATES`. `groups` imports neither `games` nor `settlement`.
- **Lock order.** Seating a member (`add_participant`, `add_participants`, and `set_left(..., left=False)`) reads the member row with `select_for_update()` after the set lock. `remove_member` and `restore_member` lock the group, then the member row, and never a set. Every path is set → group → member, so a removal and a seating of the same member cannot both succeed. `web.tests.test_concurrency.ConcurrentRosterTests` covers it on PostgreSQL.
- **Restore** keeps the `Member` row. `_free_name` settles a taken name under the group lock before the status turns active, because `member_active_name_unique` is a partial constraint and cannot be deferred.
- **The removal page** is `settlement.views.member_remove` (GET asks, POST removes), because it reads seats and unpaid transfers. `groups.services.removal_refusal` gives the reason without writing.
- **Group writes carry no `request_id`.** Each is safe to repeat: a second remove or restore changes nothing and writes no audit event, and a second add of the same names is refused by the name rule.
- **Roster activity** is one query over `counted_results()` for active and removed members together, so the settings tab's query count does not grow with the roster.
- **Marks after a redirect.** The add and restore views put the new member ids in the login session (`roster_arrived`), the removal view puts `roster_left`; the settings page takes them once and `roster.js` marks those rows.

## Claim links

- **`ClaimLink`** (`groups`, migration `0005`): the member, the token's SHA-256 hash, expiry, used time and account, cancelled time, creator. The token is never stored. One live link per member is kept by the service under the group lock, not by a constraint.
- **A claim** (`claim_member`) locks the link row, the group, then the member row, and checks everything again. It sets `Member.user`. Nothing else about the member or its records changes.
- **An account's own entry in the group** is deleted first when it is empty, because `member_one_per_user_per_group` is not deferrable. "Empty" is asked of the database: Django's deletion `Collector` is run on the row without deleting, and a `ProtectedError` (a seat, a result, a transfer or a payment points at it) means it has records. `groups` imports none of the apps above it.
- **Sign-up** uses the three hook lists in `accounts/signup.py`: `claim_vouches` opens sign-up where it needs an invite, `claim_group_name` names the group on the entry pages, `claim_after_signup` makes the new account the player and returns the group's address.
- **The page** `claim/<token>/` is exempt from the login requirement, `never_cache`, and sends `Referrer-Policy: same-origin`. GET never writes.
- **`[data-pop]`** (`motion.js`): an element with this attribute springs in once when its page starts. The claim page uses it for the player's token. Without Motion, or under reduced motion, the element is simply there.

## Stats

- **One query, then arithmetic.** `settlement.stats.fetch(group, unit)` reads every counted result once and folds a player's sets into one `SessionResult` per session. `members_of` is the second query. Periods, the board, ranks, movement and a player's record are plain Python over that list (`Period`, `PlayerRecord`, `board`). The Stats tab and a player page take a fixed number of queries whatever the number of players and sessions.
- **Integers.** Every amount is an integer; `toward_zero` does each division. Chart positions are floats, because they place marks on a screen.
- **Nothing is stored.** No table, no migration, no write, no audit event.
- **Charts** are positions worked out in `web/charts.py` as percentages of a box. The template draws the line as one SVG path stretched to the box (`preserveAspectRatio="none"`, `vector-effect: non-scaling-stroke`) and the labels, end mark and bars as positioned HTML, so text and round ends never distort. `stats.js` adds the readout; without it the chart and the list are complete.
- **A stats filter is the same screen.** `main` carries `data-stats`; when a visit goes from one stats screen to the same kind, `turbo-setup.js` starts no view transition. `stats.js` holds, from the tap until the new screen is in, the scroll position, which pill was chosen and where, and each row's place. It marks Turbo's visit as already scrolled (`Turbo.navigator.currentVisit.scrolled`, an internal of the vendored 8.0.23) and sets the position again on `turbo:load`; then it slides the pill marker, brings in `[data-stat-body]`, or moves the rows. The links and the Month form use `data-turbo-action="replace"`; the form needs `data-turbo="true"` because forms are opt-in here.
- **A person across groups.** `stats.fetch_for_user(user, unit)` is `fetch` for one person's memberships in unarchived groups; each `SessionResult` then carries `group_id` and `group`. `units_for_user` lists their units. `web/profile.py` builds the profile from these: one query for the units and one per unit, whatever the number of groups. Pesos rows go into one `PlayerRecord`; chips rows make one record per group, never one total ([ADR 0001](../adr/0001-chips-never-add-across-groups.md)).
- **Older stats code stays:** `queries.member_records` serves Your groups. `queries.group_stats` served the single ranked list removed on 2026-10-12; no page calls it now, and the tests keep it as a second sum to check the board against.

## Profile settings

- **Name in all groups.** `groups.services.rename_everywhere(user, name)` locks each group of the person's active memberships in id order (so two such calls never wait on each other), skips a group archived since the ids were read, and uses `_rename` in each. A taken name skips that group. It is idempotent by state, as `rename_self` is, so it has no `request_id`. The view lives in `groups` and returns to `/me/`.
- **Password change.** `accounts.services.change_password(user, current, new)`. The limit counts `password.change_refused` audit events of the last 15 minutes, because there is no shared cache and a memory count on Vercel resets for each instance. The refusal is written in its own transaction, before the error is raised, so it stays. A change sent twice is recognised by state (the new password already works) and succeeds without a refusal. The view keeps only the errors for one redirect, in `request.session["profile_password_errors"]`; `keep_form` is not used, because it keeps every field's data.
- **The panel row** in `_account.html` has no current-page mark: the panel is `data-turbo-permanent`, so it is not drawn again on each screen.

## Reopening

Two more transitions, both in `settlement.services`, host only, with a required reason, idempotent by state like finalize and close. [Plan](../plan/1791699815_reopen_set_and_session.md).

- `reopen_set()`: `finalized → reconciliation`. Refused while the session is closed. `ledger.services.void_results()` marks the current `Finalization` and its `PlayerResult` rows not current and fills `voided_at`, `voided_by`, `void_reason`; `games.services.mark_reopened()` changes the state and clears `finalized_at`. `ended_at` and the play periods are untouched. `write_results()` then writes revision `n + 1`.
- `reopen_night()`: `closed → open`. Refused while the current plan has an active paid mark (a `Payment` with a transfer). Table payments do not block it. The plan is marked not current with the same three void fields; `close_night()` writes a new one.
- **A session has several plans, one current.** `SettlementPlan.night` is a plain link (`night.plans`) with the partial unique rule `plan_one_current`. Every reader of transfers filters `plan__is_current=True`: `night_outcome()` (which also returns `replaced`), `settle_states()`, `unpaid_transfers()`, `unpaid_in()`, `services._transfer()`. A new reader must do the same, or a retired transfer shows as owed.
- `ledger.services.is_reopened(session)` is true while a set with an earlier finalization is counting up. Only then does `record_buy_in()` accept a host's buy-in outside open and running; it does not reclassify the player's final cash-out.
- Stats need no change: they read current results of finalized sets in closed sessions.
- Audit actions: `session.reopened` (with the retired nets) and `night.reopened`.
- Screens: `_reopen_set.html`, `_correction.html` (the reason line), the session's manage disclosure. The arrival of the reason line is in `changes.js` (`[data-reopened]`, once per reopening and browser, as the books' rule).

## Share results

Read-only and client-drawn. [Plan](../plan/1791701751_share_results.md).

- `web/share.py` `card(night, outcome, recap)` builds a plain structure from what the session view already loaded (no query): title, lines, ranked rows, transfers, foot, the text and a file name. Every amount is formatted there with `ledger.money`. The view adds it on a closed, unarchived session with a current plan; `_share.html` writes it with `json_script` (`#share-card`).
- `web/templatetags/table_tags.py` `token()` is the chip label rule, shared by the `player_token` tag and the card.
- `static/js/share.js` draws on a canvas when the share sheet shows (`sheet:shown`, dispatched by `sheets.js` on open and swap): it confirms Archivo with `document.fonts.load`, reads the palette from the page's custom properties (each colour painted once and read back, so an unread colour stops the card), lays the card out in a dry pass for its height, draws, checks the result is not blank and keeps a PNG `File`. The share call is made directly in the tap with that file; nothing is awaited first. Any failure leaves the text and Copy.
- No service, model, migration or audit event.

## Home screen suggestion

Browser-side, with one signal from the server. [Plan](../plan/1791703670_install_prompt.md).

- `config/door.py`: `door.came_in` is true on the one page shown after a login, read from the same 30-second `arrived` cookie as `door.welcome` and not consumed by a prefetch. It does not depend on `DOOR_MOTION`; the cookie is now set when either switch is on. `base.html` writes `data-came-in` on `<main>` inside the `welcome` block, so entry pages (which empty that block) pass it on with the arrival.
- `templates/_install.html` is a `<dialog class="sheet">` in `base.html` for signed-in pages. `templates/web/_home_app.html` on Your groups holds the button that reopens it and the installed app's link field; both start hidden.
- `static/js/install.js`: keeps `beforeinstallprompt` for the tab and prevents the browser's own bar; picks a part (`inapp`, `install`, `ios`, `menu`) from the user agent and the kept event; notes a login in `sessionStorage` (`rack-install-due`) and opens on the first page that is not an entry page and has no open dialog; remembers only "done" in `localStorage` (`rack-install`). Inside the installed app (`display-mode: standalone` or `navigator.standalone`) it shows the link field instead and sends a pasted same-origin `/join/`, `/claim/` or `/reset/` path to `location.assign`.
- `static/manifest.webmanifest` states `launch_handler` (reuse the open app) and `handle_links`. Android's installed web apps take in-scope links through the system; iOS has no way for a home-screen web app to receive a link.
- No model, service, migration or audit event.

## Live updates of the session page

[Plan](../plan/1791706983_session_page_live.md). The set page polls a stored `version`; the session page polls a derived stamp, because the writes that change it (paid marks, close, reopen, set transitions) have no single row to bump.

- `settlement.queries.night_stamp(night)`: a 16-character hash of the session's status and archive mark, each set's id, state and `finalized_at`, the current plan's id, the number of retired plans, and how many payments exist and how many stand (table payments before closing, paid marks after). Three queries. Never stored.
- `settlement.queries.stamp_from(...)` is the same rule over rows the caller holds. The session view uses it with what it has already read, so the page carries its stamp (`data-stamp` and `data-state-url` on `.night-layout`) at no cost in queries. `web/tests/test_night_live.py` checks at every kind of change that the page's stamp equals the queried one; if they ever differed the page would redraw on every poll, and `nightlive.js` also refuses to redraw twice for one stamp.
- `web.views.night_state` (`n/<id>/state/?v=`): 204 when unchanged, else `{"stamp": …}`. Membership as on the page.
- `static/js/nightlive.js`: on a new stamp it asks Turbo to visit the same address with `replace`, which the page's `turbo-refresh-method: morph` turns into a redraw in place. After a morph it calls `pokerPage.start()`, because a morph restarts no script: the sheet, the recap that opens once and "Settled" must read the new page. It raises `night:refreshed` with the paid marks as they were, which `settle.js` uses to settle a row marked by someone else.
- Something a future change makes the session page show must enter the stamp, or other people's pages will not learn of it.

## RSVP

[ADR 0003](../adr/0003-rsvp-with-a-waitlist.md); [plan](../plan/1793109970_rsvp_waitlist.md).

- An RSVP belongs to the session (`GameNight`), not to a set. `GameNight` has `announced_at`, `start_time` and `seat_limit`; `games.Rsvp` is one row per member and session, with `status` (`confirmed`, `waitlisted`, `out`) and `queued_at` for the line order.
- The writes are in `games/services.py`: `announce_night`, `answer_rsvp`, `set_seat_limit`, `seat_from_waitlist`. Each locks the session row (`lock_night`), writes an audit event with set 1's id, and bumps every set's version. Moving up happens inside the write that frees the seat.
- `games/rsvp.py` only reads: `answering_open()` (announced, open, not archived, set 1 Draft or Open), `answering_nights()`, and `boards()`, which builds who is coming for any number of sessions in a constant number of queries.
- Players see an announced draft through `games.access.night_for`. `session_for` still hides the set while it is a draft.
- Removing a member: `groups.services.REMOVE_LOCKS` locks their answering sessions before the member row, then `REMOVED_HOOKS` turns their answers Out. Adding players locks the session, then the member, so the two never wait on each other.
- The night stamp and the hub stamp include the answers of sessions that still take answers, so open pages redraw.



[Plan](../plan/1791711535_hub_pages_live.md). The same script and redraw as the session page, with a stamp over groups.

- `settlement.queries.hub_stamp(group_ids)`: a hash, over those groups, of each set's id, state and `finalized_at` with its session's id, status and archive mark; the count of players at the table of each unfinished set; the count of active members per group; each plan's id and whether it is current; how many payments exist and stand; and the seat limit, start time and answers of each session still taking answers (`games.rsvp.answering_nights`). Six queries however many groups, seven when a session takes answers.
- `web.views.home_state` (`state/`) covers the requester's active memberships in unarchived groups; `group_state` (`g/<id>/state/`) one group through `member_for`. Both share `_stamp_answer` with `night_state`.
- `home.html` and the Sessions view of `group.html` declare `turbo-refresh-method: morph` and hold a hidden element with `data-state-url`. They carry **no stamp**: `home_cards` is held to 11 queries. `nightlive.js` therefore asks at once on such a page and takes the answer as its baseline.
- `nightlive.js` now serves every page with `data-state-url`. It does not start on a page that answered a form (`data-method` other than GET) and treats an open disclosure with a form and no `data-key` as in use.
- With the morph setting, a tap on a link to the very page one is on (the brand mark on Your groups) is also a redraw in place.
- A hub page that starts showing something new must add it to `hub_stamp`.

## Sessions tab

- `web/sessions_tab.py` builds the tab: `visible_nights(me)` (drafts for hosts only), `coming_cards(me, nights)` (announced sessions still taking answers, with their `boards()`), `current_cards(me, nights)` (it leaves out an announced draft) and `past_years(me, nights)`. The group view calls `sessions_context(me)`.
- The intent: the tab answers "where is my table?" first. So the card order is by band (in play and mine, in play, open and mine, open, drafts), not by date.
- Reads are batched: the seated players of every card in one query, the clocks in one, and the viewer's nets (`session_nets`) and unpaid transfers (`unpaid_transfers`) in one each. The query count does not grow with the number of sessions (a test holds it).
- `destination(night, latest_set)` is the one rule for where an open session leads and what its button says. The Sessions tab and the group card on Your groups (`web/home.py`) both use it.
- The tab redraws by the hub stamp (below). The stamp counts the seats of each unfinished set, not who sits, so a swap of one player for another between two polls does not redraw the chips. See [footguns/hub_stamp_counts_seats.md](footguns/hub_stamp_counts_seats.md).

## Seat draw

- **Records** (`games/models.py`): `SeatDraw` (one current per set by constraint; `stale`; the dealer's seat, empty until chosen) and `SeatPlace` (a participant's `rank`, rising clockwise from the dealer at 0). Drawn ranks are 1024 apart, so a late player takes the midpoint between two and no row is rewritten. Drawing again turns `is_current` off on the earlier draw. One migration, `games/0013_seat_draw`, adds the two tables.
- **Writes** (`games/services.py`): `draw_seats`, `choose_seat`, `seat_late_player`. Each locks the set, carries a `request_id`, records to the audit log and raises the set's version, which is how the phones learn of it. `add_participant`, `add_participants` and `withdraw_participant` mark the current draw stale before the start; `transition("start")` seats an unchosen dealer at seat 0.
- **Read** (`games/seats.py`): `seating()` builds the seats in one query from the participants the page already holds. A seat's place on the table is `(dealer_seat + distance) mod count`; position names come from the number of drawn players and are not stored. Where that place is drawn comes from `edge()`: a racetrack walked by distance along its edge, giving x, y and the way the seat faces. `seats.js` holds the same rule for the stage, whose proportions differ; a browser check compares the two. `session_for` carries "has a draw" on its own query, so a set without a draw pays no query for it.
- **The page** (`templates/web/_seat_table.html`): the still table, placed by percentages worked out on the server, and the list `seats.js` reads the draw from.
- **The stage** (`static/js/seats.js`): a dialog inside `#table-sheets`, which Turbo keeps across a form answered in place. It is outside the live region, which `live.js` replaces. Each part ends in a picture a "still" function can draw, so a skip, reduced motion and a resize all end in the same place. The seat is sent with `fetch` and the seating plays only after the server accepts it.
- **Polling** (`static/js/live.js`): 1.5 seconds while the region holds `data-poll-fast`, else 4.

## Carried transfers

- **Record** (`settlement/models.py`): `CarriedTransfer(transfer, plan)`. It is in force while `plan` is its session's current list. Nothing marks it ended: `reopen_night` retires the plan, and the transfer is unpaid again. Migration `settlement/0008_carried_transfer` adds the table.
- **Write** (`settlement/services.py`): `close_night(night_id, actor, carry_ids)`. It locks the session being closed, then the sessions of the named transfers in id order, takes `queries.carryable()` again under those locks, and refuses the whole close if a named transfer is not in it. The carried amounts are added to `settlement_balances()` before `algorithm.settle()`; both invariant checks run on the result. `mark_paid` refuses a transfer in force; `reopen_night` refuses while one of the list's transfers is in force elsewhere.
- **Read** (`settlement/queries.py`): `paid_ids()` and `carried_ids()` are the two subqueries every "unpaid" uses (`unpaid_transfers`, `unpaid_in`, `settle_states`, the viewer's part). `night_outcome()` sets `transfer.carried` and `carried_in` from one query, made only when the plan's own read says a carry touches it (`has_carry`), so a session without one pays no query. `night_stamp()` counts the carries in force on the plan's read; `stamp_from()` adds the count only when it is not zero, so earlier stamps hold.
- **Page**: `static/js/carry.js` (the count under the list, the entrance of the carried rows and of the make-up, an earlier row turning Carried after a redraw).

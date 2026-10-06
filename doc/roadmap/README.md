# Roadmap

Each stage needs its own study, plan and approval. The design for all stages is in the [architecture study](../study/1791037419_poker_home_game_architecture.md) and its review addendum. Product intent is in [SPEC.md](../../SPEC.md).

| Stage | Outcome | `SPEC.md` step | Status |
|---|---|---|---|
| 1. Game night | Buy-ins and rebuys, cash-outs with balance check, settle-up with paid marks | 1, 2, 3 | Done, 2026-10-03 |
| 2. Roster, history, banker, corrections | Roster management, history list with filters, optional banker for the night, payments recorded before finalization (early leavers), reopen a finalized game as a new revision | 4 | Next |
| 3. Leaderboard and stats | Seasons; month, season, year and all-time filters; profit/loss, sessions, average result, win rate, ROI | 5 | Partly built 2026-10-04: profit/loss, sessions and win rate by month or all time. Seasons, year filter, average, ROI and a ranking threshold remain |
| 4. Seating | Manual seats and random draws with history | First request, item 10 | Planned |
| 5. Shared use | Deployment, password reset, claim links for roster players | — | Deployed 2026-10-04 at https://pokernights-five.vercel.app (Vercel and Neon, invite-only sign-up). Password reset by a host-issued link built 2026-10-06. Claim links remain |

## Visual redesign pulled forward

The Rack slices 1–4 are built: shared foundation, active set and action sheets, count-up, cash-out review, finalized and canceled sets, session settle-up and closing recap, home, group, accounts, invitations, supporting forms and log. [Parent plan](../plan/1791046015_visual_redesign.md); [slice 2 plan](../plan/1791050738_redesign_slice_2.md). [Slice 3 plan](../plan/1791053204_redesign_slice_3.md). [Slice 4 plan](../plan/1791084843_redesign_slice_4.md) records the final extension and input-retention fixes. Seating remains a separate feature cycle. The [UI evolution](../plan/1791098885_ui_evolution.md) added the Sessions / Stats / Group settings tabs, the branding SVGs and a first Stats view.

## What Stage 1 already prepares

- `PlayerResult` carries `member`, `group` and `game_date`, with indexes for leaderboard queries.
- `Finalization` has `revision` and `is_current`, and `write_results()` already retires an older revision. Reopening needs a lifecycle action and a rule for payments made under the old revision.
- `Payment` has optional `payer`, `payee` and `transfer`, so a banker and a payment before finalization fit the same table. `algorithm.balances()` already accepts payments, and its tests cover the prior-payment and banker cases.

## Decisions that changed the design

- **2026-10-03, cash amounts and units.** Chip counts and the chip-to-peso rate were removed. A game counts in pesos or in chips, and a chips game has no peso value. This replaces `SPEC.md` step 2 ("final chip count", "convert chips to cash") and the "chips per buy-in" item of the first request. `SPEC.md` itself is unchanged; its owner can update it.
- **2026-10-04, sessions with sets.** A session holds several sets. Settle-up is once per session. Results and playing time are stored per set.
- **2026-10-04, stats.** A "session played" is a closed session, not a set; the win rate is profitable sessions over sessions played; profit is after rake; no minimum-session threshold yet.
- **2026-10-04, archive and delete.** A session or group with any money record can be archived and never deleted. An archived session is out of the totals until restored. An archived group is hidden from every member. Single sets are not archived.
- **Consequence for Stage 3:** leaderboards must state whether a "session played" is a set or a session, and can use `PlayerResult.play_seconds` for hourly figures.
- **Consequence for Stage 3:** leaderboards and statistics are per unit. A pesos board includes only pesos games. `PlayerResult.unit` supports this.
- The "chip denominations" item under "Later" no longer applies to pesos games.

## Open product decisions

These used the plan's defaults in Stage 1. They can still change.

| Decision | Default in use |
|---|---|
| Settlement model | Direct settle-up. Banker optional in Stage 2 |
| Balance override | A note, and one named player or an equal share |
| Tables per session | One. A two-table night is two sessions |
| Audience | Private groups. On the public address sign-up needs an invite link; a superuser adds first hosts |
| Seating | Stays in the roadmap as Stage 4 |
| Whole-peso rounding | None. Exact centavos |
| Win rate | Percentage of finalized sessions with profit; the same measure as "cash rate" |
| Ranking threshold | None in the built Stats view. 3 sessions per group stays the Stage 3 proposal |

## Possible follow-ups

- **Breaks.** A player steps away and comes back without leaving the set. Today "Left" does this, and a host brings the player back.
- **Correcting a set's end time.** The end time is the moment the host taps "End play". A late tap adds playing time for everyone. No edit exists.
- **A live session page.** The session page shows changes on reload only.
- **Reopening a finalized set or a closed session** (already Stage 2).

- **New names in the player picker.** Type several new names (one per line) on "Add players"; each becomes a roster player without a login and joins the game in the same all-or-nothing action. Not built. It needs name-clash rules and its own plan. It uses the existing roster model, not a new guest-account system.

## Later (from `SPEC.md`, not planned)

RSVP with a waitlist, recurring games, reminders, IOUs across sessions, rake and tips, session timer, session notes, CSV or image export, chip denominations, bankroll graph.

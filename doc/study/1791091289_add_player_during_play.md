# Add a player during play

Date: 2026-10-04. Request: provide an option to add a player in the middle of an ongoing set.

## Outcome and evidence

The host should add a late arrival without leaving the set workflow. Main is clean at `e133a1a`. Sources: AGENTS.md, SPEC.md (players can join late), PRODUCT.md, DESIGN.md, wiki features/architecture, games services/views/tests and the active player-list/picker templates. Baseline: 423 SQLite tests pass; three PostgreSQL-only tests skip.

Existing behavior already supports roster members joining during play. `HOST_ADD_STATES` includes running. The active page links to the multi-player picker, and the service enforces host role, membership and seat capacity under the set lock. The new player's timer starts on joining; no buy-in is recorded. Batch requests have a unique request ID and retry protection.

The discoverability gap is concrete: `_players.html` hides Add players when `addable_members` is empty. The picker also has no new-name entry. A newcomer not already on the group roster requires leaving the set for the group page, creating a roster player, returning and adding them. Thus the app can appear to have no late-add option when all roster members are already seated.

`groups.services.add_roster_player()` already validates names, checks active case-insensitive uniqueness and locks the group. `games.services.add_participants()` already performs set eligibility, capacity, participant creation, running timer, audit, version and request tracking. A games service can compose these lower-level services in one transaction without importing games into groups or adding a ledger dependency.

## Options and recommendation

1. Explain the existing roster picker. This satisfies adding an existing member but leaves the newcomer gap.
2. Keep the set's Add players link visible and extend its existing page with a new-name form. Create the roster member and current-set participant atomically, then return to the set. Recommended.
3. Add a new sheet and automatically buy in the newcomer. This introduces a separate interaction and changes the approved rule that late arrivals buy in manually. It is outside this request.

Reuse the established picker page. Place a labelled Player name field and Add new player button alongside the roster-selection task as a separate native form. Explain that the name is saved to the group roster and that adding does not record a buy-in. Keep this path available when no roster member remains eligible. A full table shows why adding is unavailable; the service rechecks capacity on submission.

The new operation should lock the set first, check retry/state/capacity, then call the existing group creation and participant batch services inside the same outer transaction. Reuse ParticipantBatch request tracking if it can cleanly represent this single-player action. Failure must leave neither an orphan roster member nor a participant, timer, audit event or version change. Duplicate names should direct the host to the existing roster selection rather than invent a second identity or silently join an existing player.

## Assumptions, risks and inputs

An optional clarification offered two interpretations: enter a new name or make the existing picker easier to find. No answer was available when this study was prepared. The recommendation assumes a new-name entry is desired; the completed plan must explicitly present this behavior for approval.

Preserve setup/open/running availability and refuse new additions during count-up, finalization or cancellation. Keep late buy-ins separate, the ongoing set running and existing clocks/money unchanged. The group roster persists beyond this set. No login/account is created for the new name.

Set-then-group locking must be checked against other combined operations to avoid opposite lock order. Test two different sets adding the same name concurrently, same-request retries and a race for the last seat on PostgreSQL. A roster duplicate or ended set must keep the typed name and show a local error. No new front-end code, schema, token or asset should be needed.

Local Django, SQLite/PostgreSQL and synthetic browser fixtures supply verification inputs. No external service, credentials or real game mutation is needed. Physical-phone verification is unavailable. The proposed interpretation is the only product question; approval of the plan settles it.

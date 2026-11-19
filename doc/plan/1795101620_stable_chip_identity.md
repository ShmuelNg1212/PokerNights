# Plan: one chip per person in a group

Study: [1795101392_ui_critique.md](../study/1795101392_ui_critique.md), priority issue 1. Mode: design (with a small technical part). Skills: `domain-modeling` for the ADR; `tdd` (execute); `/impeccable polish`, `break-ui`, `code-review` (rendezvous).

Branch: `feat/stable-chips`, from `docs/ui-critique` (unreleased, docs only). The other critique items wait in `doc/roadmap/plan_queue/` (`ui_*.md`).

## OPEN QUESTIONS

Answered 2026-11-19: approved, all four recommendations.

1. **Reverse a recorded decision.** DESIGN.md (the roster section, line 337) says: "Set join order and session standing order retain their own token rules, so colour does not promise identity across those views." This plan makes colour and label a promise of identity in a group. Recommendation: **yes**. The critique found the same person in three colours and three labels. A host finds a player by chip first. If no, delete this plan; keep the queue.
2. **Derived or stored colour.** Recommendation: **derived** from `Member.pk`, as the roster and Stats already do. No migration, no new write path. A stored colour (a host picks it) can come later. If stored: add a migration, a service, an audit record and a roster control, and this plan grows past one slice.
3. **More than ten members.** Ten colours repeat in a group of 11 or more. Recommendation: accept the repeat. The two-letter label tells the people apart, and the name is always next to the chip. Do not add new colour tokens.
4. **Label scope.** Recommendation: compute the label against the group's **whole roster**, including removed members, ordered by `pk`. So Ben is "BE" on every screen when the group also has a Bea, even in a set where Bea does not play. The label then never changes when someone joins a set. A new member can still change an old member's label only if it creates a new collision. To stop that: the earlier member (lower `pk`) keeps the short form and the later member gets two letters. See task 1.

## Outcome

- In one group, a person has the same colour and the same label on every screen: set rows, count rows, the cash-out review, results, seats, the session recap, transfers, the ledger, the share image, home, the roster, Stats, RSVP, debts and claim.
- The header account chip is unchanged. It belongs to the account, not to a group.

## Non-goals

- No new colour token. No change to chip shape, size or motion.
- No model, migration or service change.
- No change to money, permissions or what any action records.

## Tasks

- [x] **1. One token rule for a member in a group.** `tests: first`.
  - Add `group_token(member) -> (label, colour)` in `web/templatetags/table_tags.py`. Colour: `(member.pk - 1) % 10 + 1`. Label: the first initial. When the first initial collides with another member of the same group (all members, removed ones too), the member with the lowest `pk` keeps one letter and each later one takes two letters, by the existing rule (first and last word, then the first two letters, then a free letter, then letter plus number).
  - Cache the group's roster labels once per request (for example on the group object or in a context-scoped dict), so a page with 12 chips makes one query, not twelve.
  - Acceptance: tests show (a) the same member gets the same label and colour from a set's participant list, a session's standings and the roster; (b) adding a later member "Bea" does not change "Ben" if Ben joined first; (c) a removed member keeps a label; (d) one query per page for the roster labels (`assertNumQueries` on a set page).
  - Completion: the new tests pass and fail on the old code.
- [x] **2. Every token uses the rule.** `tests: first` for the views, then the templates.
  - `player_token` and `member_token` call `group_token`. Their second argument becomes unused; remove it from the call sites listed by `grep -rn "player_token\|member_token" templates`.
  - `web/share.py:18` uses the same rule, so the share image matches the page.
  - Acceptance: a test renders set 3, session 1 and Stats for the seeded Ben and finds the same `kN` class and the same label on each.
  - Completion: SQLite suite passes.
  - Done 2026-11-19. Deviation: the second argument stays. It is the fallback for objects outside a group (unit tests that use plain namespaces). Templates are unchanged. Three query budgets rose by one: the roster read, once per request (`web/tests/test_query_counts.py`). The share card reuses the page's read. SQLite 1814 OK.
- [x] **3. Update the design record.** Docs.
  - DESIGN.md: replace the sentence at line 337 and extend "Player colours (c1–c10)" at line 196. Colour and label belong to the member in the group.
  - ADR `doc/adr/0015-one-chip-per-member.md` (via `domain-modeling`): context, decision, the >10 rule, and the label rule.
  - Completion: both written; no other DESIGN.md text promises per-set colours (`grep -n "join order" DESIGN.md`).
  - Done 2026-11-19. DESIGN.md lines 196, 323 and 337; `doc/wiki/architecture.md` and `features.md` lost their per-set colour text. The ADR was written in the format of 0014; the `domain-modeling` skill was not run, because the decision was already settled in the plan.
- [x] **4. Browser check.** `tests: alongside`.
  - On the review seed (`seed.py`, `seed_end_set.py`, `seed_night.py`, `seed_opening.py`, `seed_home.py`), read the chip class and label for Ben and Miguel on /s/3/, /s/2/, /n/1/, /n/12/, /g/1/ (Stats and Players) and / as ben.
  - The check must fail on main: on main, Ben is k-pink on /s/3/ and another colour on Stats.
  - `break-ui`: a group of 14 with three names that start with "B", and a 60-character name.
  - Completion: the probe passes; captures at 390 px and 1280 px look right.
  - Done 2026-11-19: `web/tests/browser/stable_chips.mjs`, eleven pages and 1280 px, including seed_home's 14-player and 60-character-name groups. main: 11/13, with Ben drawn four ways (`k8 BN`, `k6 B`, `k1 B`, `k2 BE`). Branch: 13/13, 42 members, each drawn one way. Captures were checked by eye: set 3 at 390 px, the 14-player roster.

## Rendezvous checks

- SQLite suite; PostgreSQL suite before release.
- `code-review` on the branch.
- The browser check of task 4, run against main first (must fail) and then the branch (must pass).
- `/impeccable polish` on the changed screens.

## Phone checks for TODO.md

- Open a set in play, then the session, then Stats. Ben has the same colour and letters on all three.

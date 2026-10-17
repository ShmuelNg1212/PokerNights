# PokerNights: agent workflow

PokerNights is a web app for home poker cash games. It records buy-ins and cash-outs, checks that the books balance, and calculates who pays whom. It does not move money.

The human makes strategic decisions: outcomes, priorities, acceptance criteria. The agent makes tactical decisions, implements, verifies, and records decisions outside the code. The agent does not ask the human to write code or to review a diff.

## The spine

`study → plan → approval → execute → rendezvous → sync docs`

This spine is the only workflow. Skill suites (superpowers, claude-mem make-plan/do, issue-driven flows) supply tools for its stages; their own workflows do not run.

**Size gate.** Work that fits one Conventional Commit goes straight to execute. Larger work runs the full spine and stops after the plan for human approval. If the scope grows past one commit during execution, stop and ask.

**Mode.** Start each task with one line naming the mode: technical, design, or mixed. Mixed runs the technical part first, then the design pass, before rendezvous. The human corrects the mode if wrong.

### Stages

- **study**: write `doc/study/{date +%s}_{topic}.md`. Get the timestamp with `date +%s`. Write only the study doc. A study is not rewritten later; it gets a dated addendum. Commit as `docs:`.
- **plan**: write `doc/plan/{date +%s}_{topic}.md` as the editable task board for another session: checkboxes, acceptance criteria, and a completion criterion per task. Put an **OPEN QUESTIONS** section near the top when human input is needed. Commit as `docs:`.
- **approval**: present the plan and wait. "Fold the answers in" or "reconstitute the plan" means update the plan, then wait again.
- **execute**: make a feature branch, stacked on the last unreleased one. Tick tasks in the plan doc as they finish. Continue until done or blocked.
- **rendezvous**: run the tests, review, record checks in the plan, and leave a verified feature branch. The plan is frozen after this. Merge to main only on "ship" (see Release).
- **sync docs**: make `doc/wiki/` match the code. Delete stale text as well as adding new text.

Other commands: **collect-commit** commits uncommitted work as one or more Conventional Commits. Plans conceived as a batch wait in `doc/roadmap/plan_queue/`; take one at a time and reconstitute it against the current code before approval.

### Skills per stage

| Stage | Technical | Design (impeccable) |
|---|---|---|
| study | `grilling`, then `domain-modeling` (same as `/grill-with-docs`); `research` for primary sources; `prototype` to test logic before planning | `/impeccable shape [feature]` |
| plan | `codebase-design` | the shape brief's decisions as plan tasks |
| execute | `tdd`; `diagnosing-bugs` for failures; `wizard` for steps only the human can do | `/impeccable [feature]` or a refine command; `animate` for motion; `mobile-native`; stay inside DESIGN.md's tokens and motion presets |
| rendezvous | `code-review`; `verification-before-completion`; `security-review` when auth, money, or user data change | `/impeccable critique` and `audit`, then `polish`; `review-animations`; `break-ui` |
| sync docs | `writing-for-agents` when editing AGENTS.md, skills, or wiki | same |
| any | `handoff` when a session gets long | same |

Human-run health checks: `/improve-codebase-architecture`, `/retro`.

**Codex fallbacks.** Codex has no claude-mem and no impeccable. There, read `doc/adr/`, the latest plans and `git log` for history, and use taste-skill `design-taste-frontend` with DESIGN.md as the reference. Say the fallback in one line at the start of the task.

### Subagents

Spawn subagents only during execute, and only when the approved plan has 3 or more tasks in separate files or areas. Code-writing subagents use git worktrees. During study, read-only explore agents may run wide searches. Pass this file's rules into every subagent prompt that explores code.

## Knowledge homes

Each kind of knowledge has one home. Look there first; write there only.

| Kind | Home |
|---|---|
| History of past work | claude-mem: search with `mem_search` before re-deriving past work. Do not write the auto-memory folder. |
| Code structure | graphify, when `graphify-out/graph.json` exists: run `graphify query "<question>"` before the first grep or source read; `graphify path "<A>" "<B>"` for relationships; `graphify explain "<concept>"` for one concept. Read raw files only for lines the graph located. Run `graphify update .` after code changes. |
| Decisions | `doc/adr/` and `GLOSSARY.md`, written by `domain-modeling`; domain rules in [docs/agents/domain.md](docs/agents/domain.md) |
| Current state | `doc/wiki/`: [spec.md](doc/wiki/spec.md), [architecture.md](doc/wiki/architecture.md), [setup.md](doc/wiki/setup.md), [deployment.md](doc/wiki/deployment.md), [features.md](doc/wiki/features.md), [footguns/](doc/wiki/footguns/) |
| Design sources | [PRODUCT.md](PRODUCT.md) and [DESIGN.md](DESIGN.md), owned by impeccable |
| Active work | [TODO.md](TODO.md): active and next items only, 40 lines at most |
| Frozen records | `doc/study/`, `doc/plan/`, [doc/roadmap/](doc/roadmap/README.md) |
| Human-vetted | `doc/canonical/` (if present): read only; report conflicts to the human |

- **spec.md** is living. Update behaviour facts freely during sync docs. Changes to intent (product rules, scope, money or settlement logic) go into the plan's OPEN QUESTIONS; edit spec.md only after approval, and add an ADR.
- **architecture.md** holds the intent behind the structure, not the structure itself.
- **footguns/**: record each noteworthy or unintuitive behaviour as one file.
- Add a wiki page only when a sync finds content that fits none of the existing pages.
- graphify files are local only, listed in `.git/info/exclude`: `graphify-out/`, `.graphifyignore`, `CLAUDE.md`, `.gitattributes`. Keep them out of commits. Rebuild with `graphify extract . --code-only`.

## Git

- One Conventional Commit per change (`feat:`, `fix:`, `docs:`, `chore:`, `build:`, `refactor:`, `test:`). State how you scoped the work. Run the tests before each commit.
- Push only when the human says "ship" or "push"; then run the push yourself. Never force-push.

## Release

- A push to `main` is a production release on Vercel: the build runs the tests, then the migrations. See [doc/wiki/deployment.md](doc/wiki/deployment.md).
- Batch features: build each on its own local branch, stacked on the last unreleased one. Keep TODO.md's phone checks current for everything unreleased. On "ship", merge the stack to main and push.
- Run the PostgreSQL suite locally before a release; the Vercel build skips the PostgreSQL-only tests.
- The human tests on the live build on their phone. Do not offer a preview deployment. Design a risky change to fail safe: fail at build time, or degrade to current behaviour.
- After a push, wait about four minutes, then make one or two requests to the live site. Never poll. On a 403 Vercel challenge, stop and ask the human to check in their browser.
- After a release, list what the human should check on their phone.

## Writing

Write docs and plans in ASD-STE100: short sentences, one instruction per sentence, approved vocabulary. Deviate only when critical nuance would otherwise be lost. Replies to the human use the same style, less strictly.

## Project facts

Stack: Python 3.14, Django 6.1, Django templates, plain CSS, small vanilla JavaScript modules, PostgreSQL (SQLite for simple local development). No front-end framework, queue, cache server or WebSocket layer without a recorded requirement.

```sh
.venv/bin/python manage.py runserver        # http://127.0.0.1:8000
DEBUG=True .venv/bin/python manage.py test  # SQLite; DEBUG=True when SECRET_KEY is unset
DATABASE_URL=postgres://localhost:5432/pokernights .venv/bin/python manage.py test   # PostgreSQL
```

Design rules:

1. Each amount is an integer in the game's unit: centavos in a pesos game, whole chips in a chips game. No `float`. Nothing converts chips to pesos.
2. Only `services.py` functions write. Each write to a session runs in `transaction.atomic()` and locks the session row with `select_for_update()` first.
3. Each write that a person starts carries a `request_id` with a unique constraint.
4. Money records are append-only. A correction is a reversal or a new row with a reason.
5. Each view resolves objects through the requester's active membership. A miss returns 404. Host actions check the role in the service.
6. Each write service calls `audit.record()` and increments `GameSession.version`.
7. Totals are queries. Only finalization writes snapshots.
8. Dates use Asia/Manila. Amounts display as `₱1,600` or `₱1,600.50` in a pesos game and as `1,600 chips` in a chips game.
9. Screens are dark by default, single-column on phones, with 48 px action targets. The active set uses two columns from 900 px. Follow DESIGN.md. Money figures appear at their accepted value; reduced motion disables movement.
10. A session is `GameNight`; a set is `GameSession`. Money, counts, timers and results belong to a set. Settle-up, transfers, payments and the unit belong to a session.
11. App dependencies point one way: `accounts → groups → games → ledger → settlement → web`. `audit` and `notify` are leaves.

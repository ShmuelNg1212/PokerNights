# AGENTS.md: PokerNights working agreement

PokerNights is a web app for home poker cash games. It records buy-ins and cash-outs, checks that the books balance, and calculates who pays whom. It does not move money.

## Sources of truth

1. [SPEC.md](SPEC.md): the product spec. Human-written. Agents do not edit it.
2. `doc/canonical/` (if present): human-vetted rules.
3. [PRODUCT.md](PRODUCT.md) and [DESIGN.md](DESIGN.md): approved product context and the built visual system.
4. [doc/wiki/](doc/wiki/README.md): the current state of the code.
5. `doc/study/` and `doc/plan/`: the journal of decisions. A study is not rewritten. It gets a dated addendum.
6. [TODO.md](TODO.md): short active items.

## Workflow

Each change uses two phases:

1. `study => plan`, then **stop for human approval** of the completed plan.
2. `execute plan => rendezvous => sync docs`.

No implementation starts before the human approves the plan for that cycle. File names use a shell-derived Unix timestamp and underscores: `doc/study/{timestamp}_{topic}.md`.

The human owns outcomes, priorities and acceptance criteria. The agent owns implementation and verification. The agent does not ask the human to write code or to review a diff.

## Stack

Python 3.14, Django 6.1, Django templates, plain CSS, small vanilla JavaScript modules, PostgreSQL (SQLite for simple local development). No front-end framework, queue, cache server or WebSocket layer without a recorded requirement.

## Commands

```sh
.venv/bin/python manage.py runserver        # http://127.0.0.1:8000
.venv/bin/python manage.py test             # SQLite
DATABASE_URL=postgres://localhost:5432/pokernights .venv/bin/python manage.py test   # PostgreSQL
```

Run the tests before each commit. Use Conventional Commits. Do not push or deploy without an instruction.

## Design rules

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
11. App dependencies point one way: `accounts → groups → games → ledger → settlement → web`. `audit` is a leaf.

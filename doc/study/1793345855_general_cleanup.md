# General cleanup: study

Date: 2026-10-30, Asia/Manila. Request: "commence general cleanup". No cleanup item was in TODO.md or the plan queue, so this study finds the scope.

## Method

1. `ruff check --select F,B,UP,SIM,PIE,RET` over the repo (run through `uvx`; not a project dependency).
2. `vulture` over the apps, without migrations and tests. Each function, method, property and class it named was searched with `grep` in Python, templates and scripts. Django names that the framework reads (settings, `urlpatterns`, admin classes, `Meta`, `clean_*`) were set aside.
3. Each template name and each file in `static/js` and `static/css` was searched for a reference.
4. Each class selector in `static/css/app.css` was searched for in templates, scripts and Python.
5. Each file path in `doc/wiki/`, `DESIGN.md`, `AGENTS.md`, `TODO.md` and `docs/agents/` was checked for existence.
6. `git status`, `git branch --merged main`, and the files in the repo root.

## Findings

### Dead application code (no reference anywhere)

| Name | Place |
|---|---|
| `SettingsForm.general_fields` | [games/forms.py:101](../../games/forms.py#L101) |
| `playable_total` | [ledger/queries.py:53](../../ledger/queries.py#L53) |
| `session_results` | [settlement/services.py:126](../../settlement/services.py#L126) |
| import `NameForm` | [games/views.py:18](../../games/views.py#L18) |

### Dead CSS (class used in no template, script or Python)

`.discrepancy-label`, `.hub-list`, `.hub-link` (three rules), `.night-action` (two rules), `.stat-value`, `.stat-wide`, all in `static/css/app.css`.

The `denomination-*` and `k1`–`k10` classes look unused to a plain search, but templates and `web/templatetags/table_tags.py` build them from a value. They stay.

### Tests

18 unused imports and 5 unused local variables in test files (ruff F401, F841). Ruff also reports B023 (closures in a loop) in `web/tests/test_concurrency.py`, B905 (`zip` without `strict`) and UP031 (`%` format). The closures run inside the same loop pass, so B023 is not a fault here. These three rule groups are style only and are not in scope.

### Repository hygiene

- `.obsidian/` is tracked. `.obsidian/workspace.json` changes each time the vault opens, so `git status` is never clean. The other four `.obsidian` files are settings and do not change.
- The repo root has 20 leftover `test_db_N.sqlite3-wal` and `-shm` files from parallel test runs. Git ignores them; they are local clutter only.
- Four local branches are merged into `main`: `feat/past-filters-and-end-time`, `feat/table-rake-and-multi-host-live`, `fix/preset-fill-busy`, `fix/rake-rule-labels`.

### Checked and kept

- `registration/login.html`: Django's login view loads it by its default name.
- `clock.is_running` and `clock.running_participant_ids` are used only by `games/tests/test_clock.py`. The tests use them as the reference that the batched `clock.timers` and `clock.player_clocks` must match. They stay.
- `CashOutLine.initial_buy_in` is used only by a test. It is a small read property; it stays.
- All file paths in the docs exist (template paths are relative to `templates/`).
- The 20 feature switches in `config/settings.py` all default to on. The [switch cleanup plan](../plan/1791788388_switch_cleanup.md) decided on 2026-10-12 that switches which turn a feature off stay. This study does not change that; the plan asks the human again.

## Addendum, 2026-10-30

`general_fields` was defined on `RakeForm`, not on `SettingsForm`. `SettingsForm` inherits it. The finding is otherwise the same.

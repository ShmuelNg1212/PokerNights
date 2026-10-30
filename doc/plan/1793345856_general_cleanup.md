# General cleanup: plan

Date: 2026-10-30, Asia/Manila. [Study](../study/1793345855_general_cleanup.md).

Status: **approved 2026-10-30** ("approved"), with the default answers to all three questions.

## Outcome

Dead code, dead styles and unused test imports are gone. `git status` is clean after Obsidian opens. Nothing a person sees on the live site changes.

## OPEN QUESTIONS

1. **Merged branches.** Delete the four local branches that are merged into `main` (`git branch -d`, which refuses an unmerged branch)? Default: yes.
2. **Obsidian.** Stop tracking `.obsidian/workspace.json` only, and keep the four settings files tracked? Default: yes. The other choice is to stop tracking all of `.obsidian/`.
3. **Feature switches.** The 20 switches all default to on. On 2026-10-12 you decided the switches stay. Do you want a separate study to remove the switches of features you accept? Default: no, they stay. This plan does not touch them.

## Tasks

One branch, `chore/general-cleanup`, from `main`. One commit per task.

### 1. Remove dead application code — `refactor:` — tests: alongside

- [x] Delete `RakeForm.general_fields` (`SettingsForm` inherits it) ([games/forms.py:101](../../games/forms.py#L101)).
- [x] Delete `playable_total` ([ledger/queries.py:53](../../ledger/queries.py#L53)).
- [x] Delete `session_results` ([settlement/services.py:126](../../settlement/services.py#L126)).
- [x] Remove the unused `NameForm` import from [games/views.py:18](../../games/views.py#L18).

Done when: `grep -rw` finds none of the three names outside `doc/`; ruff F finds nothing outside tests; the full test suite passes with the same test count.

### 2. Remove dead CSS rules — `refactor:` — tests: alongside

- [x] Remove the rules for `.discrepancy-label`, `.hub-list`, `.hub-link`, `.night-action`, `.stat-value` and `.stat-wide` from `static/css/app.css`.
- [x] Before each removal, search again in templates, scripts, Python and browser tests.

Done when: the six class names occur nowhere in the repo outside `doc/`; the suite passes; `collectstatic` succeeds.

### 3. Clean unused imports and variables in tests — `test:` — tests: alongside

- [x] Run `uvx ruff check --select F401 --fix` on test files only. (Done: 17 imports. The five F841 sites were edited by hand, because each right-hand side has a side effect.)
- [x] Read each F841 change. Where the right-hand side has a side effect the test needs (for example it creates a row), keep the call and drop only the name.

Done when: ruff F401 and F841 report nothing; the suite passes with the same test count.

### 4. Repository hygiene — `chore:` — no tests

- [x] Add `.obsidian/workspace.json` to `.gitignore` and run `git rm --cached` on it (as answered in question 2).
- [x] Delete the local `test_db_*.sqlite3-wal` and `-shm` files in the repo root. Not a commit; git ignores them.
- [x] Delete the merged branches (as answered in question 1). Not a commit.

Done when: `git status` is clean after Obsidian opens the vault; `ls test_db_*` finds nothing.

## Rendezvous

- [x] SQLite suite passes; PostgreSQL suite passes before any release. (2026-10-30: 1519 tests pass on both.)
- [x] `/code-review` on the branch diff. (No bugs. Three small findings: a stray blank line in `web/tests/test_roster.py`, fixed; the wrong class name for `general_fields`, fixed here and in a study addendum; a possible gap in the seat-draw test after `other` went, not a gap, because `test_a_player_who_is_not_the_dealer_is_refused` checks it.)
- [x] Task 2 changed no template, so the HTML cannot change. The check that could fail instead: each of the six class names occurs nowhere outside `app.css` and `doc/` (templates, scripts, Python, browser tests), and `git diff` of `app.css` holds only the ten removed lines.
- [x] `uvx ruff check --select F` passes on the whole repo.

Verified feature branch: `chore/general-cleanup`. The plan is frozen.

## Release

No migration. No phone check: nothing a person sees changes. The way back is `git revert` of the task's commit.

## Not in this plan

- Ruff B023, B905 and UP031 in tests (style only).
- The feature switches (question 3).
- Test-only clock functions and `initial_buy_in` (the study says why they stay).

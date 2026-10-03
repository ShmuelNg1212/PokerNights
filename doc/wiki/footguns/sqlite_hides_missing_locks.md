# SQLite hides a missing row lock

- **Trigger:** A service that writes to a session without `games.services.lock_session()`, or a change that removes `select_for_update()` from it.
- **Observed behavior:** `select_for_update()` does nothing on SQLite. The settings use `transaction_mode=IMMEDIATE`, so each transaction takes the database write lock at its start and writers still wait. The tests pass on SQLite.
- **Impact:** On PostgreSQL the same code races. Two joins take the last seat. One `request_id` creates two buy-ins. Two finalizations write two result sets.
- **Evidence:** 2026-10-03. With `select_for_update()` removed, 8 of the 9 tests in `web/tests/test_concurrency.py` failed on PostgreSQL 17.
- **Remedy:** Start each session write with `lock_session()`. Run `web.tests.test_concurrency` on PostgreSQL before a release (see [setup.md](../setup.md)).

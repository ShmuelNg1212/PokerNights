# A file copy of the SQLite database can miss recent data

- **Trigger:** Copying `db.sqlite3` as a backup while the app has used it, or deleting it with a shell command that also names a pattern.
- **Observed behavior:** The settings turn on write-ahead logging. Recent writes are in `db.sqlite3-wal` until a checkpoint. On 2026-10-03 the main file was 0.6 MB and the log 1.3 MB.
- **Impact:** A plain `cp db.sqlite3 backup` gives a backup without the latest games.
- **Evidence:** 2026-10-03, before the cash-units migration. The first backup was a plain copy and was discarded.
- **Remedy:** Use the SQLite backup API (see [setup.md](../setup.md)).

## Related: a failed `rm` left test data in the dev database

- **Trigger:** `rm -f db.sqlite3 db.sqlite3-wal db.sqlite3-shm test_db.sqlite3*` in zsh when no `test_db.sqlite3*` file exists.
- **Observed behavior:** zsh stops with "no matches found" and runs nothing. The database was not deleted.
- **Impact:** At the Stage 1 rendezvous the AI reported an empty dev database. It still held the accounts `hana` and `ben` and the group "Browser Check" from the browser check.
- **Remedy:** Do not put an unmatched pattern in a destructive command. Check the result with a query, not with the command's exit.

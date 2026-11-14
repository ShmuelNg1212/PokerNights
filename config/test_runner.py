"""The test runner. It only differs from Django's when the suite runs with ``--parallel`` on SQLite.

Django gives each parallel worker a copy of the test database. Where worker processes are
spawned (macOS, and Linux from Python 3.14), that copy is an in-memory database in SQLite's
shared-cache mode. Two threads on one shared cache lock whole tables and do not wait, so the
tests that race threads fail with "database table is locked". Each worker's copy also exists
as a file; this runner points the worker at the file, which locks as development does.
"""

import glob
import os

from django.db import connections
from django.test import runner


def _init_worker(counter, initial_settings=None, *args, **kwargs):
    runner._init_worker(counter, initial_settings, *args, **kwargs)
    for alias, initial in (initial_settings or {}).items():
        connection = connections[alias]
        name = str(initial["NAME"])
        if connection.vendor != "sqlite" or "mode=memory" not in str(connection.settings_dict["NAME"]):
            continue
        if connection.creation.is_in_memory_db(name):
            continue  # there is no file to use
        root, ext = os.path.splitext(name)
        connection.close()
        connection.settings_dict["NAME"] = f"{root}_{runner._worker_id}{ext}"


class FileBackedParallelSuite(runner.ParallelTestSuite):
    init_worker = _init_worker


class Runner(runner.DiscoverRunner):
    parallel_test_suite = FileBackedParallelSuite

    def teardown_databases(self, old_config, **kwargs):
        names = [str(connection.settings_dict["NAME"]) for connection, _, _ in old_config if connection.vendor == "sqlite"]
        super().teardown_databases(old_config, **kwargs)
        # Django removes each worker's database file but not SQLite's two side files.
        for name in names:
            root, ext = os.path.splitext(name)
            for left in glob.glob(f"{glob.escape(root)}_*{ext}-wal") + glob.glob(f"{glob.escape(root)}_*{ext}-shm"):
                os.remove(left)

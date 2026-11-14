# Static addresses by content: plan

Date: 2026-11-14, Asia/Manila. Study: [optimize and clean up](../study/1794651801_optimize_and_clean_up.md), finding 2. Mode: technical. Branch: `feat/static-addresses-by-content`, stacked on `test/parallel-suite`.

## Goal

A stylesheet or script that did not change in a release keeps its address. A phone then keeps it in its cache and does not download it again. Today each release changes all 46 addresses (about 560 KB before compression).

## OPEN QUESTIONS

Both answered by the human on 2026-11-14: "recommendations approved". Minified Turbo is dropped. The tag is in the query string.

1. **Minified Turbo is dropped from this plan. Agree?** The study said that a published minified build exists. That was wrong: the package `@hotwired/turbo@8.0.23` publishes only `turbo.es2017-umd.js` (the vendored file, same SHA-256) and an ESM build. A smaller file must be made by us with a minifier, and its checksum then matches no published file. The gain is small: the vendored file already keeps one address for a year, so a phone downloads it once (46 KB compressed).
2. **Query string or file name?** This plan keeps the query string (`app.css?v=<hash of the file>`). Django's `ManifestStaticFilesStorage` puts the hash in the file name instead. That is the stricter design, but if its manifest file is not in the Vercel function, every page fails. The query string fails safe (task 2). Recommended: query string.

## Design

- `VersionedStaticStorage.url(name)` appends `?v=<tag>`, where the tag is the first 10 hex characters of the SHA-256 of the file's bytes. The file is read once for each process and the tag is kept in memory.
- The file is found through the staticfiles finders, so the source in `static/` is used and `collectstatic` is not necessary.
- The rule for which files get a tag does not change: `.css` and `.js` outside `vendor/`, and only when `STATIC_VERSION` is set (on Vercel). Local pages and tests keep plain addresses.
- **Fail safe.** If the file cannot be found or read, the address gets the release tag, as it does today.
- `STATIC_VERSION` and `config.deploy.static_version` stay. They are the on-switch and the fallback. The rule that the app refuses to start on Vercel without a tag stays.
- Turbo reloads a page when a tracked address changes (`data-turbo-track="reload"`). After this change, a release that changes no script and no style does not cause that reload. A release that changes one file does.

## Risk

A phone can hold a page from before a release and ask for a script after it. It then stores the new file under the old address. This is the same today and does no harm, because the new page uses a new address. With content tags there is one new case: if a later release returns a file to its exact old bytes, that phone can use the wrong stored copy. The window is the few seconds of a release, and it needs an exact revert. Accepted; record it as a footgun (task 4).

## Tasks

- [x] **1. Tag by content.** `tests: first`. In `config/tests.py`: two files get different tags; the tag of a file is the same under two different `STATIC_VERSION` values; a changed file gets a changed tag; vendored files and fonts get no tag; with `STATIC_VERSION` empty, addresses are plain. Then change `config/storage.py`.
  - Acceptance: the new tests pass. `web/tests/test_inplace.py` and the other address tests pass after they are changed to expect the content tag.
  - Done when: the full suite passes on SQLite, and in the build-style run from [deployment.md](../wiki/deployment.md).
- [x] **2. Fail safe.** `tests: first`. A name that no finder knows gets `?v=<release tag>` and raises nothing.
  - Done when: the test passes.
- [x] **3. Rendezvous.** Run the suite three ways: SQLite `--parallel`, build-style, PostgreSQL. Run `code-review`. Then, with `VERCEL=1` and `DEBUG=False` locally, load the log-in page and check that two scripts have different tags and that each address returns 200 after `collectstatic`.
  - Done when: the checks are recorded here.
- [x] **4. Sync docs.** Update "Static files and caching" in `doc/wiki/deployment.md`. Add `doc/wiki/footguns/static_tag_follows_the_file.md` for the risk above. Add a phone check to `TODO.md`.
  - Done when: the wiki says what the code does.

## After release

Two live requests: the log-in page shows different tags on two scripts, and one script address returns 200. Phone check: after the next release that changes no script, the installed app opens without the short full reload.

## Checks (rendezvous, 2026-11-14)

- Tests first: the eight new tests in `config.tests.ContentTagTests` and the changed page test failed before the change to `config/storage.py` (8 errors, 1 failure) and pass after it.
- SQLite `--parallel`: 1,783 tests pass, 23 skips. Build-style run (`VERCEL=1`, one process): 1,783 pass, 23 skips. PostgreSQL `--parallel`: 1,783 pass.
- Build-like page: with `VERCEL=1`, `DEBUG=False` and a fresh `collectstatic`, the log-in page returned 200 with 46 tagged addresses and 46 different tags. Each tag matched the SHA-256 of the collected file. The release tag was nowhere in the page. The two vendored libraries had no tag.
- Review by the main agent: the edit to `config/tests.py` first removed `ServerTimingTests` by mistake (the count showed 1,778, not 1,783). The class was restored from git and the count checked per file (18 to 26).
- Not checked before release: that the Vercel function can read `static/` at run time. If it cannot, each address falls back to the release tag. The first live request after release shows which.

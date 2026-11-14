# A static address follows the file, not the release

On Vercel, `app.css?v=<tag>` and each script address take their tag from the file's own bytes (`config/storage.py`). A release that does not change a file does not change its address.

What this means:

- **A phone does not get a "new" file unless its bytes changed.** To make every phone download a file again, change the file.
- **Turbo reloads a page only when a tracked address changed.** A docs-only release causes no reload.
- **The tag is read once for each process.** Locally and in tests there is no tag (`STATIC_VERSION` is empty), so this code path runs only on Vercel and in the build's test run.
- **If every address on the live site has the same tag,** the function could not read the files in `static/` and each address fell back to the release tag. Pages work, but each release downloads everything again. Check with one request to the log-in page.
- **An exact revert can meet a wrong stored copy.** A phone that holds a page from before a release, and asks for a script in the seconds after it, stores the new file under the old address. If a later release returns that file to its exact old bytes, that phone uses the wrong copy for up to a year. The fix is to change the file by one byte (a comment) in the release that reverts it.

Do not test for the release tag in a page. Test for `?v=[0-9a-f]{10}`.

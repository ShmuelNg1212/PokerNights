# A page change on a busy machine logs an uncaught view transition error

- **Trigger:** A browser script checks for runtime errors while the machine is under load. Page changes then run late.
- **Observed behavior:** Now and then a run reports one error: `Uncaught (in promise) InvalidStateError: Transition was aborted because of invalid state. ViewTransition opt-in disabled`. The page's address is the one being left. The browser's own transition promise rejects, so no script of ours can catch it.
- **Impact:** The check "no runtime errors" fails in `night.mjs` or `counts.mjs`. Every other check in the run passes, and no record changes. The page change itself still completes, without its movement. Whether a phone ever shows a visible effect is not known.
- **Evidence:** On 2026-11-01, `counts.mjs` ran 3 times with every CPU core busy, on a Slice C branch and on a clean `main`. Each failed once, with the message above. With an idle machine, it passed 16 of 16 runs, 8 on each.
- **Remedy:** Rerun the script on an idle machine before you read this error as a regression. `night.mjs` and `counts.mjs` print the full message, so compare the words. Any other message is a real failure.
- **Not changed:** The page-change code in `static/js/turbo-setup.js`. Its own transition promises are already handled.

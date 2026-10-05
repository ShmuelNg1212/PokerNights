# Fewer queries and one-trip actions: study

Date: 2026-10-06, Asia/Manila. Base: `main` at `fedaeb0`. This continues [phone performance and smoothness](1791214796_phone_performance_and_smoothness.md): its addendum proposed five changes, and the human chose A and B now, then a plan for C, then D.

## Request

- **C.** Fewer database queries on the screens that make the most.
- **D.** An action sent in place (a rebuy, a count, a paid mark) should cost one trip to the server, not two.

## What the phone measured

From the addendum, on the human's iPhone: a query costs about 2.5 ms; every request spends 110 to 170 ms outside our server; an action waits about 400 ms, a link about 200.

## C. Where the queries go

Counted on a fresh temporary database (`seed.py`, `seed_end_set.py`, `seed_night.py`, `seed_home.py`), by listing every statement of one page.

**Every page: 2.** The login session and the user.

**Session page: 23 with one set, about 8 more for each further set.**

| Queries | What | Needed |
|---|---|---|
| 5 per set | The whole ledger summary of each set (players, buy-ins, cash-outs, counts, adjustments), read only to add up the rake | One query for all sets |
| 3 per set | The set's play periods, read twice, plus "is one open" | One query for all sets; `clock.seconds_by_set` already exists |
| 2 | The session's sets, read twice in two orders | 1 |
| 2 | Current player results, read twice | 1 |
| 2 | Payments, by transfer and by session | 1 |

A session with one set can come down from 23 to about 13, and stops growing by 8 per set.

**Set page and its changed poll: 15.** Play intervals are read twice (totals, then who is running) and play periods twice (total, then is one open); each pair is one read. Active members are read twice. About 12.

**Your groups: 14 reads and 1 write.** `groups.http.take_form` puts `inline_forms` back into the login session on every page view, also when it took nothing out, so Django writes the session row each time. The same helper runs on Group settings and the forms pages. The write goes when the helper only writes after taking something.

**Expected gain** at 2.5 ms a query: 25 ms on a one-set session and about 45 ms with three sets; 7 ms on the set page and on each poll that redraws; 3 to 5 ms and one row write less on Your groups and Group settings. Small beside the 110 to 170 ms of the trip itself, and worth having because the Session page grows with every set.

Constraint: totals stay queries (design rule 7). Nothing is cached or stored; the same figures are read in fewer statements. `ledger.queries.summary` keeps its meaning; the Session page gets a rake total of its own.

## D. Why an action takes two trips

A form marked `data-turbo="true"` is posted by Turbo. The view writes through a service and answers with a redirect to the page the form came from. The browser follows the redirect and fetches that page; Turbo then makes the page on screen match it (a "morph"). Two requests, each paying the 110 to 170 ms trip, the login session and user queries, and a database connection.

The redirect exists for a browser without JavaScript, where it prevents a double submit on reload. Turbo also insists on it: a form answered with a plain page is treated as an error.

### Options

1. **Answer the post with the page, when the form asks for it (recommended).** `turbo-setup.js` adds a header to in-place forms. A middleware sees a post with that header whose view answered with a redirect back to the page it came from. It runs that page's view in the same process and returns its HTML with status 200 and the page's address in a header. In the browser, `turbo-setup.js` already steps in on every form answer (`turbo:before-fetch-response`); for this answer it hands the HTML to Turbo as a finished visit (`Turbo.visit(address, {action: "replace", response: {...}})`), which is the path Turbo itself takes after a redirect. The morph, the kept typing, the kept scroll and the `inplace:updated` event stay as they are.
   - No view changes. No form changes. Without the header (no JavaScript, or any other client) the redirect is answered exactly as today.
   - Flash messages added by the post are shown by the page rendered in the same request, as they are today after the redirect.
   - Gain: one trip, about 150 to 200 ms per action.
2. **Turbo Streams.** Each view answers with fragments to replace. Every one of about 30 in-place forms needs its own fragment answer, in apps that must not import `web`. Rejected: much more code, and the page modules listen for a page render, which streams do not send.
3. **Leave it.** Actions stay at about 400 ms of wait.

### What must be proven before building (a spike, thrown away)

- That stopping Turbo's own handling of the answer and starting a visit with the given HTML leaves the form submission finished: the button enabled again, the busy mark gone, a second submit possible.
- That such a visit to the same address morphs (as a redirect back does today) and does not replace the page.
- That a page rendered inside the post's request sees the post's flash messages and fresh `request_id` values, and reports `GET` as its method to `base.html`.

If the first or second cannot be shown in the vendored Turbo 8.0.23 without touching the vendored file, option 1 is dropped and D ends with that finding.

### Risks

- **Money rules.** The write is committed by the service before the page is rendered, as today; the page is rendered from the database after the commit. Nothing is shown before the server accepts it.
- **A page rendered from a post.** The inner request must be a clean GET: no form data, the CSRF check not repeated, `request.method` reading `GET`. A mistake here could re-run a write. The middleware never calls a view for anything but GET and only for a redirect whose path equals the page the form was sent from.
- **Failure inside the page render.** The write has happened. The middleware falls back to the redirect, so the browser fetches the page the ordinary way.
- **The readout.** `perf.js` reports the last answer's server figures; with one trip it reports the only one, which then covers the write and the page.

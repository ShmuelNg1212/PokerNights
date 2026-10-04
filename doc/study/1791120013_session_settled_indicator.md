# Session settled indicator: study

Date: 2026-10-04, Asia/Manila.

## Request

The human said there is no indicator yet of whether a session has been fully settled, and asked for a study and plan.

## What exists today

A closed session has a settle-up plan: a list of transfers. A host marks each transfer paid. The status is derived, never stored (`settlement.queries.NightOutcome.status`):

- **settled**: every transfer has an active payment, or the plan has no transfer;
- **partly**: some do;
- **unsettled**: none do.

Where the status is visible:

| Place | What it shows |
|---|---|
| Session page, overview | "Still to pay ₱2,650" with a "Partly settled" or "Unsettled" badge and a progress bar, or a large "Settled" |
| Session page, top bar | A badge "Session closed". It does not say whether the session is settled |
| Group → Sessions → Past sessions | Table name, date and a badge "N sets". **No settle status** |
| Group → Sessions → Archived sessions | An "Archived" badge only |
| Your groups | "To settle": transfers the viewer personally owes or is owed. "Last session": the viewer's result. Nothing about the session as a whole |

So the only way to learn whether a past session is settled is to open it. With several past sessions, a host cannot see which ones still have money owed. This is the gap.

## Constraints

1. **Totals are queries** (AGENTS.md rule 7). The status stays derived from payments; no stored flag.
2. **Cost.** `night_outcome` runs several queries per session. Calling it for every row of the list would grow with the number of sessions. The list needs one batched read for all its sessions. The home page has a fixed budget of 11 queries (`web/tests/test_home.py`).
3. **Counting paid transfers.** A transfer can have several payment rows over time: one active, earlier ones reversed. A single aggregate that joins payments would count a transfer once per payment row. Paid transfers must be counted from active payments only.
4. **One rule.** The list and the session page must agree. The rule should live in one function that both use.
5. **Units.** The amount still to pay is in the session's unit, shown as `₱1,600` or `1,600 chips`.
6. **Colour is not the only signal** (PRODUCT.md, accessibility). The badge needs words, and the settled state an icon, as the session page already does.
7. **Who sees it.** Results and transfers of a session are visible to every member of the group on the session page today, so showing the status in the list reveals nothing new.
8. **Open sessions have no plan.** The indicator applies to closed sessions only. Archived sessions are out of the totals; their row keeps the "Archived" badge.
9. **A closed session with no transfer** (everyone even, or rake-only results) is settled. The session page says "Nobody owes anything".

## Options for the list row

- **A. Status badge plus the amount (recommended).** The badge reads "Settled" with a check in green, or "Partly settled" / "Unsettled" in the warning colour, replacing "N sets". The second line carries the date, the set count and, when money is owed, "₱2,650 still to pay".
- **B. Badge only.** Smaller, but a host cannot tell ₱50 outstanding from ₱5,000.
- **C. A separate "Not settled" section above the settled sessions.** Strong, but it reorders history by status instead of date and needs an empty state.

A is recommended. A count in the section heading ("2 not settled") gives most of the benefit of C without reordering.

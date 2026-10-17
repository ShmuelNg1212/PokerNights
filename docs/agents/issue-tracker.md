# Issue tracker: GitHub

Issues and feature specs live in GitHub Issues for `ShmuelNg1212/PokerNights`.

Use authenticated GitHub tools or gh. Verify that the chosen tool supports the operation. If access is unavailable, report the missing capability and preserve the work locally without claiming it was published.

With gh, pass `--repo ShmuelNg1212/PokerNights`. Read with `gh issue view NUMBER --json number,title,body,labels,comments`; list with `gh issue list --state open --json number,title,body,labels`. Create with `gh issue create --title TITLE --body-file PATH`. Use body files for multiline descriptions and comments.

When a skill says publish to the issue tracker, create a GitHub issue within the user's authorized task. When it says fetch the relevant ticket, read the referenced GitHub issue. Do not publish comments or send messages without explicit authorization for that communication.

PRs as a request surface: no.

Keep SPEC.md human-owned. Feature specifications in issues supplement the product spec. Studies and plans remain under doc/study/ and doc/plan/; TODO.md remains the short active list and links to plans or issues rather than duplicating ticket bodies. Do not migrate historical work during setup.

Tickets are vertical slices with explicit acceptance criteria and blockers. Use native GitHub sub-issues and dependencies when supported. Otherwise place `Part of #NUMBER` and `Blocked by: #NUMBER` at the top of the ticket and link children from the parent. A ticket is unblocked only when all its blockers are resolved. Resolve labels through triage-labels.md.

For wayfinder, use one map issue and linked child issues with research, prototype, grilling, or task types. Record decisions on the map with links to their source tickets. Claim a ticket before starting it. Read each blocker before selecting the next ready ticket.

Issue readiness does not authorize implementation. Follow AGENTS.md: study, plan, human approval, execution, rendezvous, then sync docs. Follow its separate release restrictions.

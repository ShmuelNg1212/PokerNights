# Matt Pocock workflow setup: plan

Status: awaiting-approval.

## Goal and sources

Make the installed Matt Pocock skills usable in PokerNights with GitHub Issues, default triage labels, and a single domain context. Follow [AGENTS.md](../../AGENTS.md), the installed setup skill, and [the study](../study/1792229459_matt_pocock_workflow.md). Preserve SPEC.md and the existing sources of truth.

The user selected GitHub Issues and default labels on 2026-10-17. These choices approve the configuration preferences, not execution of this completed plan.

## Acceptance criteria

- Skills can discover the issue tracker, triage mapping, and domain rules through tracked AGENTS.md and local CLAUDE.md.
- All five labels exist on `ShmuelNg1212/PokerNights`, verified through authenticated access.
- Future specs are GitHub issues; SPEC.md remains human-owned. A ready issue still requires an approved project plan before implementation.
- Existing workflow, application behavior, graphify instructions, and unrelated working changes remain intact.

## Scope and execution

Use branch `chore/matt-pocock-workflow`. One implementation commit: `chore: configure Matt Pocock engineering workflow`. No plugin reinstall, app changes, issue creation, migration, push, or deployment. Add only missing GitHub labels. Leave existing labels unchanged. Revert the configuration commit to undo local setup; do not automatically delete remote labels that may have been used.

- [ ] Record explicit approval of this completed plan.
- [ ] Verify GitHub access and a supported route for reading and creating repository labels. `gh` is currently absent; use available tools or an authenticated CLI route. Report any remaining access limitation accurately.
- [ ] Write the three configuration files and entry points using the exact drafts below. Preserve surrounding instructions. Completion: both entry points resolve to tracked configuration.
- [ ] Read existing GitHub labels and create missing configured labels. Completion: all five names are verified on the repository.
- [ ] Verify links, inspect the intended diff, and run the project test suite before committing. No new tests are needed for prose configuration.
- [ ] Rendezvous: merge the verified branch locally to main, preserve unrelated files, and sync the wiki index with a short link to the workflow configuration. Record checks, commit, and any limitations here. Do not push.

## Draft: entry points

Append the following section to the existing local CLAUDE.md and tracked AGENTS.md. This deliberate shared pointer makes the configuration discoverable in Codex and in the existing Claude setup; CLAUDE.md stays ignored.

```markdown
## Agent skills

Before using Matt Pocock's engineering workflow, read `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, and `docs/agents/domain.md`.

Follow this repository's two-phase workflow. A ready ticket is input to a plan; execution requires human approval of that completed plan.
```

## Draft: docs/agents/issue-tracker.md

```markdown
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
```

## Draft: docs/agents/triage-labels.md

```markdown
# Triage labels

| Role | GitHub label | Meaning |
| --- | --- | --- |
| needs-triage | needs-triage | Maintainer evaluation needed |
| needs-info | needs-info | Reporter information needed |
| ready-for-agent | ready-for-agent | Specified work suitable for an agent |
| ready-for-human | ready-for-human | Human implementation needed |
| wontfix | wontfix | Work will not be actioned |

Use this mapping when a skill names a triage role. Preserve existing repository labels and create only missing configured labels. ready-for-agent does not replace approval of the completed project plan.
```

## Draft: docs/agents/domain.md

```markdown
# Domain docs

PokerNights uses one domain context. Before domain exploration, read the root GLOSSARY.md if present and relevant decisions under doc/adr/ if present. If absent, proceed; create them lazily when domain-modeling resolves a term or decision.

Follow the source order in AGENTS.md. Use the glossary's vocabulary in tickets, code, tests, and explanations. A session is GameNight; a set is GameSession. Keep money, units, and settlement meanings consistent with the approved product rules.

Flag contradictions with existing decisions and higher-authority documents. Record new decisions in doc/adr/; preserve historical studies and append dated addenda when findings change. A new decision does not authorize editing SPEC.md.

Run domain-modeling during terminology discussions or architectural decisions. Use grilling to resolve unclear outcomes during study and planning; tdd for behavioral implementation; diagnosing-bugs for difficult failures; and code-review against the approved plan and repository standards before completing implementation. Use each skill at its applicable stage inside the existing approval workflow.
```

## Verification and progress

- 2026-10-17: inspected the installed setup skill, templates, writing-for-agents guidance, working agreement, local entry points, and repository state.
- Initial default test command stopped because SECRET_KEY was unset. `DEBUG=True .venv/bin/python manage.py test` passed: 1,254 tests, 15 skipped, no system-check issues.
- No configuration or remote changes have been made. Existing Obsidian and critique changes are outside scope.

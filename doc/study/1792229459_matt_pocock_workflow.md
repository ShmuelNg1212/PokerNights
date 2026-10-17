# Matt Pocock workflow setup

Date: 2026-10-17 (Asia/Manila).

## Outcome

Configure the installed Matt Pocock engineering skills for PokerNights. Preserve the existing two-phase approval workflow and product sources of truth.

## Evidence and current state

- The installed `mattpocock-skills` 1.3.1 package includes `setup-matt-pocock-skills`. Its local README directs users to run that skill once per repository. Source: `/Users/shm/.codex/plugins/cache/mattpocock/mattpocock-skills/1.3.1/`.
- Setup configures an issue tracker, five triage roles, and domain-document consumer rules. It requires a reviewable draft before writing configuration.
- `origin` is `https://github.com/ShmuelNg1212/PokerNights.git`.
- The user explicitly selected GitHub Issues and the five default triage labels in this session.
- `AGENTS.md` is tracked. `CLAUDE.md` exists but is ignored. Both contain graphify instructions; neither has an Agent skills section.
- No existing tracked tracker configuration, root glossary, or glossary map was found. The project uses `doc/`, studies, plans, and a short `TODO.md`.
- `gh` is not on PATH. GitHub connector tools are available for some issue operations, but their presence does not establish permission to this repository or support for repository-label creation.
- Existing unrelated changes: `.obsidian/workspace.json` and two untracked critique reports. Preserve them.

## Options and recommendation

Use the installed skills; do not install a second copy. Put their expected configuration in `docs/agents/` so upstream skills can find it. Keep actual project documents under `doc/`. Use one root `GLOSSARY.md` and lazy ADR creation under `doc/adr/`.

The setup skill normally edits CLAUDE.md when it exists. Update that local file and add a small tracked pointer in AGENTS.md so Codex and fresh clones also discover the configuration. Keep the existing workflow authoritative: issue readiness does not approve execution, ticket specs do not replace the human-owned SPEC.md, and implementation still follows an explicitly approved plan.

## External inputs and risks

GitHub access and label creation need verification during approved execution. Prefer available connected tools; if they cannot manage labels, provision an authenticated gh route without exposing credentials. Do not claim GitHub setup complete until labels are verified. Preserve existing labels and add only missing configured labels. No issue creation, comments, push, or deployment is needed for setup.

Glossary and ADR files should be created only when a later domain discussion resolves terms or decisions. The configuration must retain the existing definition of session (`GameNight`) and set (`GameSession`).

## Open questions

Tracker and label choices are resolved. The completed plan and exact configuration drafts still need human approval, as required by AGENTS.md and the setup skill.

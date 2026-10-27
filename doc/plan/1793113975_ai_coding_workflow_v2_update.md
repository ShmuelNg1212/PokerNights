# Plan: update AGENTS.md to ai-coding-master-workflow v2

Mode: technical. Branch: `docs/ai-workflow-v2`, from `main` (nothing is unreleased). This plan changes docs only. No code, no release.

## Version

- AGENTS.md has no version marker. It counts as v1.
- Current template version: v2.
- `doc/workflow/skills-per-stage.md` does not exist. The update creates it.
- CLAUDE.md already imports `@AGENTS.md`. It is local only (listed in `.git/info/exclude`). No change.

## What changed from v1 to v2

- Subagents may run in execute, rendezvous, and sync docs. They never merge, push, or tick plan tasks.
- Execute subagents need 3 or more tasks and no two tasks that edit the same file.
- The size gate has a tiebreaker: one area, one clear done condition.
- Rendezvous stops and asks after two fix-and-recheck rounds.
- The skills table moves to `doc/workflow/skills-per-stage.md`.
- The fallbacks have their own heading. Long bullets are split into short sentences.
- A version marker is added to AGENTS.md and skills-per-stage.md.
- A GEMINI.md template exists for Gemini CLI.

## OPEN QUESTIONS

Each REC is my recommendation. The project's own rules win where they differ.

1. **Plan test marks.** The template asks for `tests: first` or `tests: alongside` on each plan task, and "write tests before code" for `tests: first`. PokerNights plans do not use these marks. REC: adopt them. The money and settlement rules suit `tests: first`. Alternative: keep plans as they are.
2. **Mode line.** The template asks for the skills to be named with the mode on each task. PokerNights asks for the mode only. REC: adopt the template wording, and keep "The human corrects the mode if wrong."
3. **Subagent prompts.** The template says to pass only the Git and Writing rules to a subagent. PokerNights passes this whole file to subagents that explore code. REC: keep the PokerNights rule, because the design rules matter to code explorers.
4. **GEMINI.md.** Add a GEMINI.md that imports `@AGENTS.md`? REC: yes, only if you use Gemini CLI here. It would be local only, like CLAUDE.md: add it to `.git/info/exclude`.
5. **Rendezvous merge rule.** The template merges to main locally at rendezvous. PokerNights merges only on "ship". REC: keep "ship". No change to the Release section.

## Existing rules: kept, moved, changed, or dropped

| Existing rule | Decision | Reason |
|---|---|---|
| Title, product summary, human/agent split | kept | Project text. |
| Spine with a separate **approval** stage | kept | The template folds approval into plan. PokerNights keeps it as its own stage. |
| "Spine is the only workflow" paragraph | kept | Same as template. |
| Size gate | changed | Add: "Work fits one commit when it stays in one area and has one clear done condition." |
| Mode | changed | See OPEN QUESTION 2. |
| Stages: study (with dated addendum rule) | kept | Project rule. |
| Stages: plan | changed if Q1 is yes | Add the test marks. Split the long sentences. |
| Stages: approval | kept | |
| Stages: execute (stacked branches) | changed if Q1 is yes | Add "Write the tests before the code for `tests: first` tasks." Keep the stacking rule. |
| Stages: rendezvous | changed | Add: exercise the first thing the user will do with the change. Add: allow two fix-and-recheck rounds, then stop and ask. Keep "Merge to main only on ship". |
| Stages: sync docs | kept | |
| collect-commit and `plan_queue` paragraph | kept | Project rule. |
| Skills per stage: table | moved | Goes to `doc/workflow/skills-per-stage.md`. The impeccable design column stays. AGENTS.md keeps a two-sentence pointer. |
| Human-run health checks line | moved | Goes with the table. |
| Codex fallbacks | moved | Goes under a new "Fallbacks" heading. Text stays. |
| Subagents | changed | Replaced by the v2 per-stage rules. Keep the worktree rule and the project's prompt rule (see Q3). |
| Knowledge homes table | kept, one change | Add a row: Skills table, `doc/workflow/skills-per-stage.md`. |
| Knowledge homes bullets (spec, architecture, footguns, graphify local files) | kept | Project rules. |
| Git | kept | Project rules. |
| Release (Vercel, batching, phone checks) | kept | Project rules. Copied word for word. |
| Writing | kept | |
| Project facts and design rules 1 to 11 | kept | Project rules. |
| Version marker | added | `<!-- ai-coding-master-workflow v2 -->` as line 1. Add it last. |

Nothing is dropped.

## Tasks

- [x] **T1. Create `doc/workflow/skills-per-stage.md`.** Start from `templates/skills-per-stage.md`. Use the current PokerNights table rows (including `verification-before-completion`, `handoff`, and the impeccable design column). Add the v2 marker on line 1.
  - Done when: the file has a table with Technical and Design (impeccable) columns, no `{{` placeholder, and the same skills as today.
- [x] **T2. Edit AGENTS.md: size gate, mode, stages.** Apply the rows above, following the answers to Q1 and Q2.
  - Done when: each changed bullet is short sentences, and the project rules in the table above are still present.
- [x] **T3. Edit AGENTS.md: skills pointer and Fallbacks.** Replace the table with a pointer to T1's file. Add the "Fallbacks" heading with the Codex text.
  - Done when: no table remains in AGENTS.md and the Codex text is unchanged.
- [x] **T4. Edit AGENTS.md: subagents.** Replace the section with the v2 per-stage rules. Keep the project's prompt rule.
  - Done when: the section names execute, rendezvous, sync docs, and study, and says subagents never merge, push, or tick tasks.
- [x] **T5. Edit AGENTS.md: knowledge homes and marker.** Add the Skills table row. Add the v2 marker as line 1.
  - Done when: line 1 is the marker and the table has the new row.
- [x] **T6. Optional GEMINI.md** (only if Q4 is yes). Write `GEMINI.md` with `@AGENTS.md`. Add it to `.git/info/exclude`.
  - Done when: `git status` does not list GEMINI.md.
- [x] **T7. Verify.** Run `grep -n '{{' AGENTS.md doc/workflow/skills-per-stage.md`. Check each link in AGENTS.md resolves. Compare Git, Release, Writing, and Project facts with `main`: they must be unchanged.
  - Done when: grep finds nothing, all links resolve, and `git diff main -- AGENTS.md` shows no change inside those four sections.
- [x] **T8. Commit.** Commit as `docs: update the agent workflow to v2`. Record the checks in this plan. Do not merge or push. Merge only on "ship".

## Not in scope

- The Release section, the design rules, and the stack.
- Any code, template, or static file.
- The uncommitted `.obsidian/` and `.impeccable/` files in the working tree.

## Answers (2026-10-27)

All five RECs accepted: Q1 test marks adopted, Q2 mode line adopted, Q3 subagent prompt rule kept, Q4 GEMINI.md added (local only), Q5 "ship" rule kept.

## Checks (rendezvous)

- `grep '{{'` over AGENTS.md and `doc/workflow/skills-per-stage.md`: no hits.
- Every link in AGENTS.md resolves.
- Git, Release, Writing, and Project facts sections: identical to `main`.
- `GEMINI.md` is git-ignored through `.git/info/exclude`. CLAUDE.md is unchanged.
- Not run: the test suite. This change touches docs only.

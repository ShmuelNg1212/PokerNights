# Fold features.md into spec.md (queued)

Status: queued 2026-10-17 by the [workflow setup plan](../../plan/1792233420_ai_coding_master_workflow.md), decision 1. Reconstitute against the current code before approval.

## Goal

One living page for product intent and current behaviour: `doc/wiki/spec.md`. Delete `doc/wiki/features.md`.

## Why

`features.md` is 658 lines of dated build notes ("slice 2", "rework of 2026-10-05"). It overlaps spec.md and grows with each cycle. History already lives in `doc/plan/`, git and claude-mem.

## Draft tasks

- [ ] Map each features.md section to a spec.md feature heading (1–6, or a new heading). Completion: every features.md section has a target or a reason to drop.
- [ ] Write the behaviour facts into spec.md in present tense, with no dates, slice names or plan links. Completion: each fact appears once.
- [ ] Move design-only content (motion, slices, layout) to DESIGN.md if it is not there already, or drop it if DESIGN.md covers it.
- [ ] Keep "Limits today" as a spec.md section.
- [ ] Keep product intent unchanged. Any intent conflict goes to OPEN QUESTIONS.
- [ ] Delete features.md. Update links in AGENTS.md, the wiki README, and other live docs. Frozen records keep their links.
- [ ] Commit as `docs: fold features into the living spec`.

# 0015: One chip per member in a group

Date: 2026-11-19. Status: accepted. Plan: [One chip per person in a group](../plan/1795101620_stable_chip_identity.md). Study: [whole-app UI critique](../study/1795101392_ui_critique.md), issue 1.

## Context

A chip (a coloured token with initials) stands for a player. Before this decision, a set took a chip's colour from the player's join order in that set. A session took it from first appearance in its standings. The roster, Stats and home took it from the member's ID. Initials were worked out against the other names on the page. The same person therefore had up to three colours and three labels. DESIGN.md said so on purpose: "colour does not promise identity across those views." The critique found that hosts find a player by chip first, so the promise is worth making.

## Decision

- A member's chip colour is `(member.pk - 1) % 10 + 1`, on every screen of their group. The colour is derived, not stored.
- A member's label is worked out against the group's whole roster, removed members included, in member ID order. The earliest member with an initial keeps that one letter. Each later namesake takes two letters (first and last word, the first two letters, or a free letter). A new member never changes an earlier member's label.
- A group of more than ten members repeats colours. The label and the written name tell the members apart. No colour token is added.
- The header's account chip is not part of this rule. It belongs to the account, not to a group.

## Consequences

- Each page reads the group roster once for its chips (one query per request). The share card reuses that read.
- A member's label can change only when that member's own name changes.
- A stored, host-chosen colour remains possible later. It would need a migration, a service and an audit record.

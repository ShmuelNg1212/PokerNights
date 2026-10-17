# 0001: Chips never add across groups

Date: 2026-10-17. Status: accepted. Plan: [profile page](../plan/1792238274_profile_page.md).

## Context

The profile page shows a person's results from all their groups. A group can play in pesos or in chips, set by set. The spec already says that pesos and chips never mix. It did not say what happens to chips from two different groups.

## Decision

A person's profile adds pesos across their groups. Chips are shown per group and never added across groups.

## Reasons

- A peso has the same value in every group. A chip does not: each group sets its own stakes, and nothing converts chips to pesos (design rule 1).
- A total of chips from two groups would be a number with no meaning.

## Consequences

- The profile has one pesos total, chart and tiles. Each chips group is its own row with its own figure.
- Any later cross-group view (seasons, a share card) must follow the same rule.

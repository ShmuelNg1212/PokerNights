# 0011: Show Stats before the first closed session

Date: 2026-11-01. Status: accepted. Plan: [UI revamp](../plan/1793431937_ui_revamp.md), Slice F.

## Context

The Stats tab was hidden until a group had a closed session. A new member could not find it. A direct link could already open the empty board. The human chose to show the tab and explain why it has no stats.

## Decision

Show Sessions, Players, Stats and Settings to each active group member. With no closed session, Stats says, "Players appear here once a session closes." Its action is Go to sessions.

Keep the existing rules for the figures. Only eligible closed sessions count. Keep the existing unit and period filters. Explain an empty filtered result in the page. Keep the active-membership access check.

## Consequences

A new group has four stable tab positions. The tab no longer appears as a side effect of closing the first session. The change writes no money record and adds no query.

The human also confirmed two existing choices: earlier unpaid transfers start selected when closing a session, and Not started describes a session with no set begun. This slice keeps both.

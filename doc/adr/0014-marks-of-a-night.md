# 0014: The recap says what a night meant in a player's history

Date: 2026-11-13. Status: accepted. Plan: [Streaks and records](../plan/1794561295_streaks_and_records.md).

## Context

The recap of a closed session said facts of that session only. Stats knew each player's history, but the recap did not use it. The human asked for streaks and records as flair. On 2026-11-10 the human said that a streak can be a winning run or a losing run. The recap's Highlights have an older rule: no highlight names a loss.

## Decision

The recap's Highlights add four marks. Each is worked out when the page is read, from the group's counted sessions in the session's unit, up to and including that session. Nothing is stored.

- **Winning run**: the player finished ahead in this session and in the 2 or more counted sessions they played before it. A break-even session ends a run. A session the player did not play does not.
- **Personal best**: the result is positive and higher than each earlier one, and the player has 3 or more counted sessions. A tie is not a best.
- **First win**: the player's first positive result, when it is not their first counted session. A first win is not also called a personal best.
- **Round number**: the player's 10th, 25th, 50th or 100th counted session, or each 50th after that.

The recap names no loss, no losing run and no last place. The question was put to the human twice with this default, and the plan was approved without another answer. A losing run stays on the player's own page ("Lost 3 in a row"), where it was.

## Consequences

The closed session page makes one more query: the one that Stats makes. A later correction to an earlier session can change the marks of a later one, as it changes Stats. Pesos and chips never mix. An archived session does not count. The marks are not on the share picture and send no notice.

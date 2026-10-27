# 0004: Session chip values are an amount input method

Date: 2026-10-28. Status: accepted. Plan: [session chip values](../plan/1793117581_session_chip_values.md).

## Context

Counting an ending stack and calculating its value take too much effort. Different sessions can use different values for the same physical chip colour. The human approved a session-owned denomination table and a count calculator.

## Decision

- A session (`GameNight`) owns one optional table of 1 to 12 chip colours and values. Every set in it uses this table. A new session starts without assignments.
- A value is an integer amount in the session unit. In a pesos session it is centavos. In a chips session it is whole chip units. This is not an exchange rate between those units.
- A host edits assignments until the first successful chip-based count submission. This includes a player's unconfirmed entry. After that, the table stays locked, including after a count is cleared or a set is reopened.
- A configured session cannot change its unit. Its saved values must keep their meaning.
- The server calculates each count from whole quantities and saved values. The browser shows a preview. A blank form is not an empty stack; zero needs a quantity or the explicit Empty stack action.
- Each chip-based count stores its denomination and quantity breakdown. Accepting a player's entry copies that evidence to the confirmed count. A manual replacement does not inherit it.
- Direct amount entry, host confirmation, cash-out and balance checks continue to use the existing ledger rules.

## Reasons

The gathering sets chip values, not the table or one round. A permanent first-use lock avoids changing denominations while other phones count. Saved breakdowns explain a count without changing append-only money records.

## Consequences

Assignment edits and count writes lock the parent session before a set. Stale revisions are refused. Browser drafts retain their original revision and require a recount after values change. Presets, automatic reuse, stack shortcuts and camera recognition are outside this scope.

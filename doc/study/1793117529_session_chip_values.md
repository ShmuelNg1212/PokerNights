# Session chip values: study

Date: 2026-10-28. Mode: mixed.

## Request

Counting the ending stack and calculating its value take too much effort. The human wants a chip calculator. Colour-to-value assignments must belong to each session.

## Evidence

- `GameNight` is the session. It owns the unit and contains all sets (`games/models.py:110`). Put chip assignments here, not on the table, group or set.
- `FinalCount` stores a confirmed integer amount. A correction adds a version (`ledger/models.py:111`).
- `enter_count`, `confirm_count` and `confirm_counts` already enforce count permissions, state, repeated requests and confirmation (`ledger/services.py`).
- Count-up has host rows and a separate player's own count form (`templates/web/_count_rows.html`, `templates/web/_count_own.html`). Both need the same calculator.
- `lock_session` locks the set and joins its session. `lock_night` locks the session (`games/services.py:139`). Assignment edits and count submissions must use the same session lock to serialize them.
- The spec currently says cash-outs have no chip count or rate (`doc/wiki/spec.md:52`). An approved denomination-entry option needs a spec update and an ADR.
- A chips-unit session has no peso value. Denominations must use the session unit. This does not create a chips-to-pesos rate.

## Proposed shape

One optional denomination table belongs to one session. Every set uses it. The host assigns each chip a colour, a written name and a positive value in the session unit. No values are assumed from colours.

The host and each player can count by denomination. The server calculates the submitted amount. The browser shows a labelled preview. The existing confirmation and cash-out steps remain authoritative.

Keep a snapshot of the denominations and quantities with each chip-based count. A later correction must not change that evidence. Lock the assignment table after its first successful chip-based submission. Manual amount entry remains available.

## Design brief

Use DESIGN.md and the existing Rack forms. The taste skill excludes app screens, so its landing-page workflow does not apply.

On the session page, show a Chip values section. The host can add or remove rows before the table locks. Each row has a colour selector with a written colour name, an optional chip label and a value field. All members can read the saved table.

At count-up, offer Count by chips beside amount entry when assignments exist. Open a focused sheet for one player. Show the chip name, value, whole-number quantity and subtotal. Show the total and a button that states the existing action: send a player count or confirm a host count. An empty form is not a zero stack. Provide an explicit Empty stack action.

Use 48 px controls, numeric keyboards and written labels. Physical chip colours are data swatches, not financial status or player identities. Preserve drafts through live updates and validation errors. Provide a working server-rendered form without JavaScript.

## Risks and scope

- Two hosts can edit or submit at once. Reject stale assignments and serialize writes.
- Do not trust a total sent by the browser. Use integer arithmetic on the server.
- A bad setup can produce a balanced but wrong count. Show denominations before submission and retain the breakdown.
- Existing sessions have no assignments after migration. Existing amount entry must keep working.
- Stack-of-20 shortcuts, saved group presets, camera recognition and mid-session denomination changes are outside this first scope.

## History used

Read the current spec, the session and count implementations, ADR 0001, the latest RSVP study and the recent Git log. The code and current documents provide the evidence for this new feature.

# Collapsible host dock: plan

Status: approved 2026-10-04, executed 2026-10-04. Date: 2026-10-04, Asia/Manila. Study: [Collapsible host dock](../study/1791111003_collapsible_host_dock.md).

## Outcome

On a phone, a host can collapse the bottom menu of the set page to one 48 px bar and expand it again. This works in every state that has the menu: draft, open, in play and counting up. The choice is remembered on that phone and survives live updates, reloads and the move from one state to the next.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. No new token, colour, asset or dependency.

**Why.** On the pages before results are finalized, the menu takes about half of a phone screen (370 px in count-up, 340 px in an open set) and the players and count fields are hard to see. Count-up is the main case.

## Decisions for the human

Each has a recommended answer. Approving the plan accepts the recommendations unless you say otherwise.

1. **What the collapsed menu shows.** Recommended: one bar reading "Host controls · Next: Start the set" with a chevron. The action buttons are hidden until you expand. The alternative keeps the main button visible while collapsed; it saves one tap, but Start the set would then add the usual buy-ins with that checkbox out of sight, and Finalize results would lose its "check the cash-outs first" line.
2. **How it starts.** Recommended: expanded, as today. It stays collapsed only after you collapse it.
3. **How far the choice reaches.** Recommended: one choice per phone, for every set and state.
4. **Pages without a bottom menu.** The cash-out review, the finalized set and the session page with settle-up have no bottom menu today; their buttons are in the page. Recommended: leave them alone. Say so if you meant a menu on those pages too.
5. **Desktop.** Recommended: no toggle from 900 px. The controls are in the left column there and cover nothing.

## Behaviour

**Collapsed (below 900 px).** The dock is one row, 48 px high plus the safe area: "Host controls" in the usual weight, the next step in muted text, a chevron pointing up. Nothing else from the dock is on screen. The page reserves about 72 px at the bottom instead of 128 to 370 px.

**Expanded.** The same row sits at the top of the dock with the chevron pointing down, followed by today's content unchanged.

**The next step text**, chosen by the server:

| State | Text |
|---|---|
| Draft | Next: Open for players |
| Open | Next: Start the set |
| In play | Next: End play and count up |
| Counting up | The live count verdict, for example "₱200 still to account for. 2 still to count." or "All counts match buy-ins." |

In count-up the bar shows the verdict instead of a next step, because the host reads it while typing counts. It updates on each keystroke, as the full preview does. The bar may wrap to two lines there (about 68 px).

**Unchanged.** What each control does, who sees the dock, the count preview, the sheets, the toasts, every page other than the set page.

**Without JavaScript.** No toggle; the dock is expanded.

**Storage refused.** The toggle works for the page view and is not remembered.

**Motion.** None. The dock changes size at once, so reduced motion needs no special case.

## Implementation

1. **`templates/web/_host_controls.html`.** Add as the first child, before the heading:
   `<button type="button" class="dock-toggle" hidden aria-expanded="true">` containing "Host controls", `<span class="dock-next muted small">Next: …</span>` and a chevron icon. No wrapper around the existing children (study, constraint 4).
2. **`web/templatetags/table_tags.py`.** Add `chevron-down` to `ICONS`. The collapsed state rotates it in CSS.
3. **`static/js/dock.js`** (new, about 30 lines, same style as `changes.js`).
   - Return unless `#live` exists.
   - Add `dock-enabled` to `<html>`. Read `localStorage["rack-dock"]` in `try`; if it is `"collapsed"`, add `dock-collapsed` to `<html>`.
   - `sync()`: find `.dock-toggle`, remove `hidden`, set `aria-expanded` from the class. If the toggle had focus before a live update, focus the new one.
   - Delegated click on `.dock-toggle`: flip the class, write or remove the key in `try`, call `sync()`.
   - Run `sync()` at load and on `live:updated`.
   - Load it from `templates/web/session.html` with the other set-page scripts.
   - **`static/js/counts.js`.** `put()` also writes the status and coverage text to the matching `data-count-*` spans in the toggle row. The server renders the same text there first, so the bar is right without JavaScript-driven updates.
4. **`static/css/app.css`**, one new block at the end.
   - `.dock-toggle`: full width, `min-height: var(--tap)`, transparent, text left, chevron right, the shared focus outline. Hidden unless `.dock-enabled` and below 900 px.
   - Below 900 px, `.dock-collapsed .table-layout .host-controls > :not(.dock-toggle) { display: none; }`. This also hides the separately fixed `.next-action`.
   - Below 900 px, `.dock-collapsed .table-page` gets the small bottom clearance, written to outrank the four `:has()` rules.
   - Raise the four expanded clearances by the height of the toggle row, only under `.dock-enabled`, so the no-JavaScript layout keeps today's values. Final numbers come from measurement in step 6.
   - Move the `.next-action` fixed offset so it does not sit on the toggle row; the dock's top padding drops to keep the growth small.
5. **Tests, written first.**
   - `web/tests/test_table.py`: a host sees one `dock-toggle` with the right "Next:" text in draft, open and in play, and with the confirmed count verdict in count-up; a player sees none; the finalized set has none.
   - `web/tests/browser/dock.mjs` (new), on a fresh temporary database with the existing seeds, at 320, 390 and 1280 px:
     - the toggle is a 48 px target with visible focus and a correct `aria-expanded`;
     - collapsed, the dock is at most 48 px plus padding and safe area, and no other dock control is rendered;
     - collapsed and expanded, the last player row and the last count button clear the dock, in all four states;
     - in count-up, typing a count changes the verdict in the collapsed bar, and an invalid count shows the "Preview unavailable" text there;
     - the collapsed state survives a live update made by a second session, a reload, and Open → Start → End play;
     - a focused toggle keeps focus across a live update;
     - no horizontal overflow against the requested width, with long names (set 11);
     - at 1280 px there is no toggle and a stored "collapsed" changes nothing;
     - with JavaScript disabled there is no toggle and the dock is expanded;
     - with `localStorage` blocked the toggle still works.
6. **Verify.** Run the SQLite and PostgreSQL suites. Run `dock.mjs`, then `rack.mjs`, `rack_accessibility.mjs`, `opening.mjs`, `counts.mjs` and `end_set.mjs`, each on a fresh temporary database, restarting the server after the template edit. Inspect the 320 and 390 px captures for both dock states in all four set states.
7. **Sync docs.** DESIGN.md: a dated addendum on the dock toggle and the new clearances. `doc/wiki/features.md`: the collapse behaviour. `web/tests/browser/README.md`: the new script. TODO.md: mark done and add a "try it on your phone" item. Record the rendezvous in this plan.

## Acceptance criteria

- A host on a phone can collapse and expand the menu in draft, open, in play and counting up, and it stays as left across live updates, reloads and state changes.
- In count-up with the menu collapsed, the count fields fill the screen above one bar, and that bar still tells the host whether the counts match as they type.
- Collapsed, the menu covers one bar; the player list and the count fields use the rest of the screen, and the last row is reachable above the bar.
- No action can be taken from the collapsed menu. Expanding shows every control that exists today, behaving as today.
- Players, desktop widths and browsers without JavaScript see the screens they see today.
- All existing tests and browser checks pass.

## Out of scope

- A bottom menu on the cash-out review, finalized set or session page.
- Hiding the dock on scroll, swipe gestures and animation.
- Any change to services, models, views or URLs.

## Progress and blockers

2026-10-04: Study and plan complete. The human gave the reason (the menu covers half the screen before results are finalized); recorded as a study addendum, and the count-up bar gained the live verdict.

2026-10-04: The human approved with “approved”. The five decisions stand as recommended.

2026-10-04 execution, on `feat/collapsible-host-dock`. Tests were written first and seen to fail.

Changes from the plan:

1. **Clearance is measured, not hand-set.** `dock.js` writes the dock height to `--dock-h` and keeps it current with a `ResizeObserver`; the page reserves that plus 16px. Reason: the first browser run showed that the existing fixed values were already wrong. On unmodified `main` the count-up dock covers the last count action (`end_set.mjs` and `counts.mjs` both fail that check), because the 370px rule loses to the 200px rule on specificity. The fixed values remain for the no-JavaScript layout.
2. **Focus is restored in `live.js`, not `dock.js`.** A redrawn control that carries `data-focus-key` gets focus back after `live:updated`. The toggle is rendered `hidden` until `dock.js` shows it, so the focus call has to follow the event.
3. **The status line shows only when collapsed.** Expanded, it repeated the button or the preview directly below it.
4. **The collapsed bar stacks a small label over the status line** instead of putting them side by side, so a normal verdict fits one line at 390px.
5. **The "Next:" text in count-up is the verdict in every case**, as the revised plan says; there is no separate text per count-up case.

2026-10-04 verification:

- 522 tests pass on SQLite (ten PostgreSQL-only skips) and all 522 pass on local PostgreSQL 17, started for the run and stopped after.
- `dock.mjs`: 137 of 137 checks pass on a fresh temporary database. Captures of both states at 320 and 390px were inspected for all four set states, with long names and ₱199,999,999.98.
- Older browser scripts were run on fresh databases on this branch and on unmodified `main`. They are stale on `main` (failures and crashes unrelated to the dock, listed in the browser README). Results on the branch are the same, except that the two dock-clearance checks now pass. `rack_accessibility.mjs` passes 13 of 13 on both.

Not verified: a physical phone, a screen reader, the on-screen keyboard over the count fields, and the one-frame expanded flash on a slow phone named in the study.

Acceptance criteria: all met, with one qualification. "All existing browser checks pass" holds only relative to `main`, where several already fail.

Documentation synced: DESIGN.md addendum, wiki features, browser README, TODO.

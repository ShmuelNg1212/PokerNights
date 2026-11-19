# The dock's fold choice applies to every set

The host's fold choice is the class `dock-collapsed` on `<html>`, kept in `localStorage` as `rack-dock`. It applies to every set on that browser, in every state.

Since 2026-11-20 a dock before the start has no toggle. A CSS rule that hides the dock's children under `.dock-collapsed` must therefore apply only to a dock with a toggle: `.host-controls:has(> .dock-toggle)`. Without that scope, a host who folds the dock in play sees an empty dock on the next draft or open set, with no way to open it.

The same applies to `.kb-bar`. And `dock.js` must observe and measure the dock with or without a toggle, or the page keeps the 128px default clearance and the last row sits under the dock.

Checks: `dock_before_start.mjs` ("after a fold in play, a joining set still shows Start the set", "the page reserves the measured dock height").

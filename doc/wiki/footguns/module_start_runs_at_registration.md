# A module's start runs when it registers

`page.js` starts the page as soon as it loads. Every script is deferred, so the document is already parsed and `readyState` is not `loading`. Each later module's `start` then runs at the moment that module calls `pokerPage.register`, during its own script.

**The trap.** A `start` function that calls another module at once (`window.pokerFinale.play(...)` from `sheets.js`) finds that module only if its script comes earlier in `templates/base.html`. A module that comes later is `undefined` on the first page load. On a later screen change every module is defined, so the fault shows only on a fresh load.

**How it showed.** 2026-11-10: `finale.js` was loaded after `sheets.js`. The recap opened with no finale on a fresh load, and the finale played after a replayed `pokerPage.start()`.

**The rule.** Load a module before each module whose `start` calls it. A call made later, from an event (`table.js` calls `pokerOverture` on `live:updated`), does not need the order. `web/tests/test_inplace.py` fixes the order of the scripts.

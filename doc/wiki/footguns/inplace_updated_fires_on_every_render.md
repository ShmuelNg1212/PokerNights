# `inplace:updated` fires on every Turbo render, not only after a write

- **Trigger:** A listener for `inplace:updated` that acts as if this phone's write was accepted: a vibration, a sound, a "Saved" mark.
- **Observed behavior:** `turbo-setup.js` sends `inplace:updated` on every `turbo:render`. A tapped link to another screen sends it. The session page's own redraw for someone else's change (`nightlive.js`, a `Turbo.visit` with `action: "replace"`) sends it. In those cases `event.detail.form` is `null`. Only an answer to a form this phone sent carries that form.
- **Impact:** Found on 2026-11-18 in review, before release. The first build vibrated "done" on every screen change and on each session-page redraw for another player's buy-in. The set page did not show it, because it redraws by a morph from `live.js`, which does not send the event.
- **Evidence:** `haptics.mjs` checks "a screen change: no vibration" and "the session page's own redraw: no vibration". Both failed against the first build with `[[10,50,14]]` and pass now.
- **Remedy:** Act on an accepted write only when `event.detail.form` is set. `motion.js` `answered(failed, form)` does this. A refusal shown again by a page (`.message-error`) can still nudge, but vibrates only for a form this phone sent.
- **Not changed:** `turbo-setup.js` still sends the event on every render, because the page modules use it to refresh after any render.

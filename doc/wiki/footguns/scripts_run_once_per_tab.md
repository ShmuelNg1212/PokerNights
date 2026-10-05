# A script that starts once per page load keeps running after the screen changes

## Trigger

Write a page script the ordinary way: an immediately invoked function that finds its elements, starts a timer or adds a listener to `document`, and never stops. Then let links change the screen without unloading the page (Turbo navigation, on since 2026-10-05).

## Observed behaviour and impact

In the stage 4 trial, link navigation was switched on with the scripts as they were. After visiting a set page four times, the page made **9 poll requests in 8.5 seconds instead of 2**, because every visit had started another poll loop and none had stopped. After leaving the set, the group page still polled it. Tapping a sheet button raised `showModal` errors from handlers bound to dialogs that were no longer in the page. A host moving around during a game would have multiplied the load on the server.

## Rule

Every page script registers with `static/js/page.js`:

```js
window.pokerPage.register(function start() {
  var region = document.getElementById("live");
  if (!region) return;                       // do nothing where the elements are absent
  var life = new AbortController();
  window.addEventListener("online", refresh, { signal: life.signal });
  var timer = setInterval(refresh, 4000);
  return function stop() { clearInterval(timer); life.abort(); };
});
```

- Scripts load once, from the `<head>` in `base.html`, on every page. None is in the body.
- A listener meant for the whole tab is added outside `start`, once, and checks whether its page is present.
- `start` runs when a page arrives; the returned `stop` runs when it leaves. An in-place update of the same page restarts nothing.
- Script and stylesheet tags carry `data-turbo-track="reload"`, so the first screen change after a release loads the page afresh with the new files.

## Evidence and checks

`web/tests/browser/lifetime.mjs` restarts every script ten times on one page and counts poll loops, dialogs and listeners. `navigate.mjs` makes 22 screen changes and requires exactly one poll loop on a set page, none after leaving, and no script error. `probe_leak.mjs` is the trial's original probe. See the [stage 4 plan](../../plan/1791181102_screen_changes_without_reload.md).

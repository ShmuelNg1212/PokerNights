// Keeps a page fresh that carries data-state-url: the session page, Your groups and a group's
// Sessions tab. It asks whether anything the page shows has changed (a short stamp, see
// settlement.queries.night_stamp and hub_stamp) and, when it has, fetches the page and lets Turbo
// redraw it in place, as it does for the host's own actions. Nothing is redrawn under an open
// sheet, an open form or typing. Asking stops while the tab is hidden and slows down when nothing
// happens. The session page carries its stamp; the other two ask once at the start and take the
// answer as their starting point.
(function () {
  "use strict";
  var BASE_MS = 5000, QUIET_MS = 20000, QUIET_AFTER_MS = 120000, MAX_MS = 30000, WAIT_MS = 1000;
  var mine = null; // the redraw this script asked for: {paid: {transfer id: "0" | "1"}}

  // After our redraw the page's scripts start again: the sheet, the recap that opens once, the
  // "Settled" arrival and this script all read the page as it is now.
  document.addEventListener("turbo:render", function (event) {
    if (!mine) return;
    var before = mine; mine = null;
    // A redraw in place restarts nothing by itself (turbo-setup.js); a swapped page already has.
    // Starting twice would close the recap that the first start opened.
    if (event.detail.renderMethod === "morph") window.pokerPage.start();
    document.dispatchEvent(new CustomEvent("night:refreshed", { detail: before }));
  });

  window.pokerPage.register(function () {
    var region = document.querySelector("[data-state-url]");
    if (!region || !window.Turbo) return;
    // A page that answered a form is not fetched again: that would lose what the answer says.
    if (document.body.dataset.method && document.body.dataset.method !== "GET") return;
    var life = new AbortController(), stopped = false, timer = null;
    var stamp = region.dataset.stamp || "", starting = !stamp;
    var refused = null, failures = 0, due = false, changedAt = Date.now();

    function busy() {
      if (document.querySelector("dialog[open]")) return true;
      var active = document.activeElement;
      if (active && /^(INPUT|SELECT|TEXTAREA)$/.test(active.tagName) && active.type !== "hidden") return true;
      // An open form whose state a redraw would not keep (New group): it is in use.
      if (document.querySelector("main details[open]:not([data-key]) form")) return true;
      return Array.from(document.querySelectorAll("main input[type=text], main textarea")).some(function (el) { return el.value !== el.defaultValue; });
    }
    function delay() {
      if (due) return WAIT_MS;
      if (failures) return Math.min(MAX_MS, BASE_MS * Math.pow(2, failures));
      return Date.now() - changedAt > QUIET_AFTER_MS ? QUIET_MS : BASE_MS;
    }
    function schedule() {
      clearTimeout(timer);
      if (!stopped && !document.hidden) timer = setTimeout(tick, delay());
    }
    function redraw() {
      if (busy()) { due = true; return; }
      due = false;
      var paid = {};
      document.querySelectorAll("[data-transfer]").forEach(function (row) { paid[row.dataset.transfer] = row.dataset.paid; });
      mine = { paid: paid };
      // Our stop runs when the page's scripts restart; until then no second request is sent.
      stopped = true; clearTimeout(timer);
      window.Turbo.visit(location.pathname + location.search, { action: "replace" });
      // A redraw that never arrives must not end the asking.
      setTimeout(function () { if (mine && !life.signal.aborted) { mine = null; stopped = false; schedule(); } }, 10000);
    }
    function tick() {
      if (stopped) return;
      if (due) { redraw(); schedule(); return; }
      fetch(region.dataset.stateUrl + "?v=" + encodeURIComponent(stamp), {
        credentials: "same-origin", headers: { "X-Requested-With": "fetch" }, cache: "no-store", signal: life.signal
      }).then(function (answer) {
        if (answer.status === 204) { failures = 0; return null; }
        if (!answer.ok) throw new Error("status " + answer.status);
        return answer.json();
      }).then(function (found) {
        if (stopped || !found) return;
        failures = 0;
        if (starting) { starting = false; stamp = found.stamp; return; }
        // A stamp the page was already redrawn for and still does not carry: do not loop on it.
        if (found.stamp === refused) return;
        refused = found.stamp; changedAt = Date.now();
        redraw();
      }).catch(function () { if (!life.signal.aborted) failures += 1; }).then(schedule);
    }
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) clearTimeout(timer); else if (!stopped) { clearTimeout(timer); timer = setTimeout(tick, 0); }
    }, { signal: life.signal });
    if (starting && !document.hidden) timer = setTimeout(tick, 0); else schedule();
    return function () { stopped = true; clearTimeout(timer); life.abort(); };
  });
})();

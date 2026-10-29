// Keeps the session screen fresh by polling. The server is the only source of
// truth: each response is a full snapshot of the live region, so a missed poll
// needs no replay. Polling stops while the tab is hidden.
//
// The snapshot is morphed into the region, so a field being typed in keeps its node, its
// value and its focus, and another host's change lands while this host types.
(function () {
  "use strict";

  window.pokerPage.register(function () {
  var region = document.getElementById("live");
  if (!region || !region.dataset.url) return;
  // Everything this page starts ends with it: the poll timer, a request in flight and
  // the listeners on document and window.
  var life = new AbortController(), stopped = false;

  var statusLine = document.getElementById("live-status");
  var BASE_MS = 4000;
  // In play, while counting up and just after a set ends, hosts and players act at once: ask every 2 seconds, back to
  // 4 after a minute with no change. Each unchanged answer is a 204 (deployment.md, "Limits to know").
  var BUSY_MS = 2000;
  var QUIET_AFTER_MS = 60000;
  var BUSY_STATES = { running: true, reconciliation: true, finalized: true };
  var FAST_MS = 1500;
  var MAX_MS = 30000;
  var version = region.dataset.version;
  var delay = BASE_MS;
  var failures = 0;
  var timer = null;
  var lastOk = new Date();
  var lastChange = Date.now();

  function clock(date) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
  }

  function showStatus() {
    if (!statusLine) return;
    var stale = failures >= 2;
    statusLine.classList.toggle("stale", stale);
    region.classList.toggle("is-stale", stale);
    statusLine.textContent = (stale ? "Reconnecting… last updated " : "Live · ") + clock(lastOk);
  }

  // Typed values that are not saved yet. A refresh replaces the whole region,
  // so they are read before it and put back after it. Without this, a change
  // made by someone else would clear what this person was typing.
  function typedValues() {
    var typed = {};
    region.querySelectorAll("input[data-keep], textarea[data-keep]").forEach(function (el) {
      var box = el.type === "checkbox";
      if ((el.hasAttribute("data-count-input") && el.value.trim()) || (box ? el.checked !== el.defaultChecked : el.value !== el.defaultValue)) typed[el.dataset.keep] = box ? el.checked : el.value;
    });
    return typed;
  }

  function restore(typed) {
    Object.keys(typed).forEach(function (key) {
      var el = region.querySelector('[data-keep="' + key + '"]');
      if (el) el[el.type === "checkbox" ? "checked" : "value"] = typed[key];
    });
  }

  function apply(snapshot) {
    var open = [];
    var typed = typedValues();
    var active = document.activeElement;
    var focusKey = active && region.contains(active) ? active.dataset.focusKey : null;
    region.querySelectorAll("details[open][data-key]").forEach(function (el) { open.push(el.dataset.key); });
    // Before and after: flow.js compares the two to show what moved.
    var hadNext = !!region.querySelector("[data-next-set]");
    region.dispatchEvent(new Event("live:updating", {bubbles: true}));
    if (window.Turbo && Turbo.morphChildren) {
      var next = document.createElement("div");
      next.innerHTML = snapshot.html;
      // turbo-setup.js keeps typed fields and open disclosures; the focused field keeps its value.
      Turbo.morphChildren(region, next, { ignoreActiveValue: true });
    } else {
      region.innerHTML = snapshot.html;
    }
    if (snapshot.state) region.dataset.state = snapshot.state;
    restore(typed);
    version = String(snapshot.version);
    region.dataset.version = version;
    open.forEach(function (key) {
      var el = region.querySelector('details[data-key="' + key + '"]');
      if (el) el.open = true;
    });
    // A poll says so: someone else's change, which arrivals.js may announce.
    region.dispatchEvent(new CustomEvent("live:updated", {bubbles: true, detail: {poll: true}}));
    // A focused control that the redraw replaced gets keyboard focus again, once listeners have shown it.
    var again = focusKey && !region.contains(active) && region.querySelector('[data-focus-key="' + focusKey + '"]');
    if (again) again.focus();
    goToNextSet(hadNext);
  }

  // Another host started the next set after this set ended: a host goes there; a player keeps the notice.
  function goToNextSet(hadNext) {
    var notice = region.querySelector("[data-next-set][data-host-go]");
    if (hadNext || !notice || !/^(finalized|canceled)$/.test(region.dataset.state || "")) return;
    if (document.querySelector("dialog[open]")) return;
    var link = notice.querySelector("a[href]");
    if (!link) return;
    if (window.Turbo && Turbo.visit) Turbo.visit(link.href); else window.location.assign(link.href);
  }

  function pace() {
    if (!BUSY_STATES[region.dataset.state] || Date.now() - lastChange > QUIET_AFTER_MS) return BASE_MS;
    return BUSY_MS;
  }

  function schedule() {
    clearTimeout(timer);
    // While a seat draw waits for the dealer's seat the page asks more often, so every phone seats together.
    var soon = delay === BASE_MS && region.querySelector("[data-poll-fast]");
    var wait = soon ? FAST_MS : delay === BASE_MS ? pace() : delay;
    if (!stopped && !document.hidden) timer = setTimeout(poll, wait);
  }

  function poll() {
    clearTimeout(timer);
    fetch(region.dataset.url + "?v=" + encodeURIComponent(version), {
      credentials: "same-origin",
      headers: { "X-Requested-With": "fetch" },
      cache: "no-store",
      signal: life.signal
    })
      .then(function (response) {
        if (response.status === 204) return null;
        if (response.status === 404 || response.redirected) {
          // The game is gone for this user, or the login expired: load the real page.
          window.location.reload();
          return null;
        }
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.json();
      })
      .then(function (snapshot) {
        if (stopped) return;
        failures = 0;
        delay = BASE_MS;
        lastOk = new Date();
        if (snapshot) {
          lastChange = Date.now();
          apply(snapshot);
        }
      })
      .catch(function () {
        if (stopped) return;
        failures += 1;
        if (failures >= 2) delay = Math.min(delay * 2, MAX_MS);
      })
      .then(function () {
        if (stopped) return;
        showStatus();
        schedule();
      });
  }

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) clearTimeout(timer); else poll();
  }, { signal: life.signal });
  window.addEventListener("online", poll, { signal: life.signal });

  // A form sent in the background has already brought this page up to date (turbo-setup.js).
  document.addEventListener("inplace:updated", function () {
    version = region.dataset.version;
    lastOk = new Date();
    lastChange = Date.now();
    showStatus();
  }, { signal: life.signal });

  showStatus();
  schedule();
  return function () {
    stopped = true;
    clearTimeout(timer);
    life.abort();
  };
  });
})();

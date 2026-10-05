// Keeps the session screen fresh by polling. The server is the only source of
// truth: each response is a full snapshot of the live region, so a missed poll
// needs no replay. Polling stops while the tab is hidden.
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
  var MAX_MS = 30000;
  var version = region.dataset.version;
  var delay = BASE_MS;
  var failures = 0;
  var timer = null;
  var lastOk = new Date();
  var pending = null; // a snapshot that waits until the user stops typing

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

  function userIsTyping() {
    var active = document.activeElement;
    return !!active && region.contains(active) && /^(INPUT|SELECT|TEXTAREA)$/.test(active.tagName);
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
    region.dispatchEvent(new Event("live:updating", {bubbles: true}));
    region.innerHTML = snapshot.html;
    if (snapshot.state) region.dataset.state = snapshot.state;
    restore(typed);
    version = String(snapshot.version);
    region.dataset.version = version;
    open.forEach(function (key) {
      var el = region.querySelector('details[data-key="' + key + '"]');
      if (el) el.open = true;
    });
    region.dispatchEvent(new Event("live:updated", {bubbles: true}));
    // A focused control that the redraw replaced gets keyboard focus again, once listeners have shown it.
    var again = focusKey && region.querySelector('[data-focus-key="' + focusKey + '"]');
    if (again) again.focus();
  }

  function schedule() {
    clearTimeout(timer);
    if (!stopped && !document.hidden) timer = setTimeout(poll, delay);
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
          if (userIsTyping()) pending = snapshot; else apply(snapshot);
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

  region.addEventListener("focusout", function () {
    setTimeout(function () {
      if (pending && !userIsTyping()) {
        apply(pending);
        pending = null;
      }
    }, 0);
  });

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) clearTimeout(timer); else poll();
  }, { signal: life.signal });
  window.addEventListener("online", poll, { signal: life.signal });

  // A form sent in the background has already brought this page up to date (turbo-setup.js).
  document.addEventListener("inplace:updated", function () {
    version = region.dataset.version;
    pending = null;
    lastOk = new Date();
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

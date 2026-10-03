// Keeps the session screen fresh by polling. The server is the only source of
// truth: each response is a full snapshot of the live region, so a missed poll
// needs no replay. Polling stops while the tab is hidden.
(function () {
  "use strict";

  var region = document.getElementById("live");
  if (!region || !region.dataset.url) return;

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
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  function showStatus() {
    if (!statusLine) return;
    var stale = failures >= 2;
    statusLine.classList.toggle("stale", stale);
    region.classList.toggle("is-stale", stale);
    statusLine.textContent = (stale ? "Reconnecting… last updated " : "Live · updated ") + clock(lastOk);
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
      if (el.value !== el.defaultValue) typed[el.dataset.keep] = el.value;
    });
    return typed;
  }

  function restore(typed) {
    Object.keys(typed).forEach(function (key) {
      var el = region.querySelector('[data-keep="' + key + '"]');
      if (el) el.value = typed[key];
    });
  }

  function apply(snapshot) {
    var open = [];
    var typed = typedValues();
    region.querySelectorAll("details[open][data-key]").forEach(function (el) { open.push(el.dataset.key); });
    region.innerHTML = snapshot.html;
    region.dispatchEvent(new Event("live:updated", {bubbles: true}));
    restore(typed);
    version = String(snapshot.version);
    region.dataset.version = version;
    open.forEach(function (key) {
      var el = region.querySelector('details[data-key="' + key + '"]');
      if (el) el.open = true;
    });
  }

  function schedule() {
    clearTimeout(timer);
    if (!document.hidden) timer = setTimeout(poll, delay);
  }

  function poll() {
    clearTimeout(timer);
    fetch(region.dataset.url + "?v=" + encodeURIComponent(version), {
      credentials: "same-origin",
      headers: { "X-Requested-With": "fetch" },
      cache: "no-store"
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
        failures = 0;
        delay = BASE_MS;
        lastOk = new Date();
        if (snapshot) {
          if (userIsTyping()) pending = snapshot; else apply(snapshot);
        }
      })
      .catch(function () {
        failures += 1;
        if (failures >= 2) delay = Math.min(delay * 2, MAX_MS);
      })
      .then(function () {
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
  });
  window.addEventListener("online", poll);

  showStatus();
  schedule();
})();

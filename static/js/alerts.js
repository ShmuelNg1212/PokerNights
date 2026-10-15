// Your groups: table alerts for this phone, and the "added you" line on a card.
//
// The panel (#alerts, permanent across redraws) shows only where this phone can take a push:
// a service worker, PushManager and Notification, which an iPhone has only in the installed
// app. It never asks on its own; the browser's question comes from the tap on "Turn on table
// alerts". Its states: ask (with Not now, which hides it for 30 days), on (with Turn off) and
// blocked (changed in the phone's settings only). A phone that is on tells the server its
// subscription once per window, so a phone that changed hands follows the new login.
//
// A card whose set added this viewer carries data-added. When a refresh brings one that was
// not on the page before, it rises 8px and its dot springs in; on a first sight it is simply
// there (the arrival into the app plays over it), and under reduced motion nothing moves.
(function () {
  "use strict";
  var LATER_KEY = "pn-alerts-later", LATER_MS = 30 * 24 * 60 * 60 * 1000, SYNC_KEY = "pn-alerts-synced";
  var registration = null, addedSeen = null;

  // The first keyframe is written before Motion starts (doc/wiki/footguns/motion_starts_a_frame_late.md).
  function enter(el, keyframes, preset) {
    var M = window.pokerMotion;
    if (!el || !M || !M.on() || document.hidden) return;
    Object.keys(keyframes).forEach(function (name) { el.style[name] = keyframes[name][0]; });
    M.settle(el, M.run(el, keyframes, preset), Object.keys(keyframes));
  }

  function supported(panel) {
    return !!panel.dataset.key && "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
  }
  function serverKey(base64) {
    var padded = (base64 + "===".slice((base64.length + 3) % 4)).replace(/-/g, "+").replace(/_/g, "/");
    var raw = atob(padded), out = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
    return out;
  }
  function deferred() {
    try { return Date.now() - Number(localStorage.getItem(LATER_KEY) || 0) < LATER_MS; } catch (_) { return false; }
  }
  function remember(key, value) { try { if (value === null) localStorage.removeItem(key); else localStorage.setItem(key, value); } catch (_) {} }
  function post(panel, url, body) {
    return fetch(url, {
      method: "POST", credentials: "same-origin", cache: "no-store",
      headers: { "Content-Type": "application/json", "X-Requested-With": "fetch",
                 "X-CSRFToken": panel.querySelector("[name=csrfmiddlewaretoken]").value },
      body: JSON.stringify(body)
    }).then(function (answer) { if (!answer.ok) throw new Error("HTTP " + answer.status); });
  }

  // One state shown at a time; a change the person made cross-fades, and "on" brings its tick.
  function show(panel, name, moved) {
    var before = panel.querySelector("[data-alerts-state]:not([hidden])");
    panel.querySelectorAll("[data-alerts-state]").forEach(function (el) { el.hidden = el.dataset.alertsState !== name; });
    panel.hidden = !name;
    var now = name && panel.querySelector('[data-alerts-state="' + name + '"]');
    if (!moved || !now || now === before) return now;
    enter(now, { opacity: [0, 1] }, "fade");
    if (name === "on") enter(now.querySelector(".alerts-tick"), { opacity: [0, 1], transform: ["scale(0.6)", "scale(1)"] }, "arrive");
    return now;
  }

  function sync(panel, subscription) {
    var mark = null;
    try { mark = sessionStorage.getItem(SYNC_KEY); } catch (_) {}
    if (mark === subscription.endpoint) return;
    post(panel, panel.dataset.subscribe, subscription.toJSON()).then(function () {
      try { sessionStorage.setItem(SYNC_KEY, subscription.endpoint); } catch (_) {}
    }).catch(function () {});
  }

  function resolve(panel) {
    if (!supported(panel)) { show(panel, null); return; }
    if (Notification.permission === "denied") { show(panel, "blocked"); return; }
    navigator.serviceWorker.ready.then(function (ready) {
      registration = ready;
      return ready.pushManager.getSubscription();
    }).then(function (subscription) {
      if (subscription) { sync(panel, subscription); show(panel, "on"); }
      else show(panel, deferred() ? null : "ask");
    }).catch(function () { show(panel, null); });
  }

  function failed(panel, words) {
    var error = panel.querySelector("[data-alerts-error]");
    error.textContent = words; error.hidden = false;
    var M = window.pokerMotion;
    if (M) M.settle(error, M.run(error, { transform: ["translateX(0px)", "translateX(-6px)", "translateX(6px)", "translateX(-3px)", "translateX(0px)"] }, "nudge"), ["transform"]);
  }

  function turnOn(panel, button) {
    if (!registration) return;
    var error = panel.querySelector("[data-alerts-error]");
    error.hidden = true;
    button.setAttribute("aria-busy", "true");
    // Straight from the tap: the browser asks only while the tap is still the reason.
    registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: serverKey(panel.dataset.key) })
      .then(function (subscription) {
        return post(panel, panel.dataset.subscribe, subscription.toJSON()).then(function () { return subscription; });
      })
      .then(function (subscription) {
        try { sessionStorage.setItem(SYNC_KEY, subscription.endpoint); } catch (_) {}
        remember(LATER_KEY, null);
        var line = show(panel, "on", true);
        var off = line && line.querySelector("[data-alerts-off]");
        if (off) off.focus({ preventScroll: true });
      })
      .catch(function () {
        if (Notification.permission === "denied") { show(panel, "blocked", true); return; }
        if (Notification.permission === "default") return; // the question was closed without an answer
        failed(panel, "That wasn’t turned on. Check your connection and try again.");
      })
      .then(function () { button.removeAttribute("aria-busy"); });
  }

  function turnOff(panel) {
    if (!registration) return;
    registration.pushManager.getSubscription().then(function (subscription) {
      if (!subscription) return null;
      return post(panel, panel.dataset.unsubscribe, { endpoint: subscription.endpoint }).catch(function () {})
        .then(function () { return subscription.unsubscribe(); });
    }).catch(function () {}).then(function () {
      try { sessionStorage.removeItem(SYNC_KEY); } catch (_) {}
      var ask = show(panel, "ask", true);
      var on = ask && ask.querySelector("[data-alerts-on]");
      if (on) on.focus({ preventScroll: true });
    });
  }

  function notNow(panel) {
    remember(LATER_KEY, String(Date.now()));
    var M = window.pokerMotion, leaving = M ? M.run(panel, { opacity: [1, 0], transform: ["translateY(0px)", "translateY(8px)"] }, "leave") : null;
    function gone() { show(panel, null); panel.style.opacity = ""; panel.style.transform = ""; }
    if (leaving) M.after(leaving, gone); else gone();
  }

  // The panel survives redraws, so its buttons are answered here, once, for every page.
  document.addEventListener("click", function (event) {
    var panel = event.target.closest && event.target.closest("#alerts");
    if (!panel) return;
    var on = event.target.closest("[data-alerts-on]");
    if (on && !on.hasAttribute("aria-busy")) turnOn(panel, on);
    else if (event.target.closest("[data-alerts-off]")) turnOff(panel);
    else if (event.target.closest("[data-alerts-later]")) notNow(panel);
  });

  function addedLines() {
    if (!document.querySelector(".home-groups")) return;
    var lines = Array.prototype.slice.call(document.querySelectorAll("[data-added]")), now = {};
    lines.forEach(function (line) {
      now[line.dataset.added] = true;
      if (!addedSeen || addedSeen[line.dataset.added]) return;
      enter(line, { opacity: [0, 1], transform: ["translateY(8px)", "translateY(0px)"] }, "shift");
      enter(line.querySelector(".added-dot"), { opacity: [0, 1], transform: ["scale(0.6)", "scale(1)"] }, "arrive");
    });
    addedSeen = now;
  }

  window.pokerPage.register(function () {
    var panel = document.getElementById("alerts");
    if (panel) resolve(panel);
    addedLines();
  });
})();

// Table alerts for this phone, in the header; and the "added you" line on a card of Your groups.
//
// The bell (#alerts, permanent across screen changes) shows only where this phone can take a push:
// a service worker, PushManager and Notification, which an iPhone has only in the installed app.
// In an iPhone's browser it shows too, and its panel offers the home-screen sheet (install.js).
// Its shape says the state: ask (outline), on (filled), blocked (slashed), install (outline).
// A tap opens a small panel under it; Escape, a tap outside or the bell again closes it. The
// browser's question comes only from the tap on Turn on.
//
// The reminder: once per window, on Your groups (data-alerts-remind), the panel opens by itself
// in the ask state with Not now, after the arrival, and the bell swings once. It gives way to any
// open dialog (the home-screen sheet goes first) and tries again at the next start. A phone that
// is on tells the server its subscription once per window, so a phone that changed hands follows
// the new login.
//
// A card whose set added this viewer carries data-added. When a refresh brings one that was
// not on the page before, it rises 8px and its dot springs in; on a first sight it is simply
// there (the arrival into the app plays over it), and under reduced motion nothing moves.
(function () {
  "use strict";
  var REMINDED_KEY = "pn-alerts-reminded", SYNC_KEY = "pn-alerts-synced", OLD_LATER_KEY = "pn-alerts-later";
  var WORDS = { ask: "off", install: "off", on: "on", blocked: "blocked" };
  var registration = null, addedSeen = null, state = null;
  var ua = navigator.userAgent || "";

  // The first keyframe is written before Motion starts (doc/wiki/footguns/motion_starts_a_frame_late.md).
  function enter(el, keyframes, preset) {
    var M = window.pokerMotion;
    if (!el || !M || !M.on() || document.hidden) return null;
    Object.keys(keyframes).forEach(function (name) { el.style[name] = keyframes[name][0]; });
    var controls = M.run(el, keyframes, preset);
    M.settle(el, controls, Object.keys(keyframes));
    return controls;
  }

  function read(store, key) { try { return store.getItem(key); } catch (_) { return null; } }
  function write(store, key, value) { try { if (value === null) store.removeItem(key); else store.setItem(key, value); return true; } catch (_) { return false; } }
  function standalone() { return navigator.standalone === true || matchMedia("(display-mode: standalone)").matches; }
  function apple() { return /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1); }

  function supported(box) {
    return !!box.dataset.key && "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
  }
  // An iPhone's browser has no push; the app on its Home Screen has. The sheet that explains how is on the page.
  function installable() { return apple() && !standalone() && !!document.getElementById("install-sheet"); }
  function serverKey(base64) {
    var padded = (base64 + "===".slice((base64.length + 3) % 4)).replace(/-/g, "+").replace(/_/g, "/");
    var raw = atob(padded), out = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
    return out;
  }
  function post(box, url, body) {
    return fetch(url, {
      method: "POST", credentials: "same-origin", cache: "no-store",
      headers: { "Content-Type": "application/json", "X-Requested-With": "fetch",
                 "X-CSRFToken": box.querySelector("[name=csrfmiddlewaretoken]").value },
      body: JSON.stringify(body)
    }).then(function (answer) { if (!answer.ok) throw new Error("HTTP " + answer.status); });
  }
  function bell(box) { return box.querySelector("[data-alerts-bell]"); }
  function panel(box) { return box.querySelector(".alerts-panel"); }
  function isOpen(box) { return !panel(box).hidden; }

  // One state at a time. The bell's glyph follows by CSS (a short cross-fade); in an open panel a
  // change the person made cross-fades its lines and "on" brings its tick.
  function show(box, name, moved) {
    var before = box.querySelector("[data-alerts-state]:not([hidden])");
    state = name;
    box.querySelectorAll("[data-alerts-state]").forEach(function (el) { el.hidden = el.dataset.alertsState !== name; });
    box.dataset.state = name || "";
    box.hidden = !name;
    if (!name) { close(box, true); return null; }
    bell(box).setAttribute("aria-label", "Table alerts, " + WORDS[name]);
    var now = box.querySelector('[data-alerts-state="' + name + '"]');
    if (!moved || !now || now === before) return now;
    enter(now, { opacity: [0, 1] }, "fade");
    if (name === "on") enter(now.querySelector(".alerts-tick"), { opacity: [0, 1], transform: ["scale(0.6)", "scale(1)"] }, "arrive");
    return now;
  }

  // The panel comes from the bell: it grows from the caret and drops 4px; it leaves faster, upward.
  function open(box, remind) {
    var sheet = panel(box);
    box.querySelector("[data-alerts-later]").hidden = !remind;
    box.querySelector("[data-alerts-error]").hidden = true;
    if (!sheet.hidden) return;
    sheet.hidden = false;
    // The caret sits under the bell's middle, measured from the panel's right edge.
    var from = sheet.getBoundingClientRect().right, at = bell(box).getBoundingClientRect();
    sheet.style.setProperty("--alerts-caret", Math.max(16, Math.round(from - (at.left + at.width / 2))) + "px");
    box.classList.add("is-open");
    bell(box).setAttribute("aria-expanded", "true");
    enter(sheet, { opacity: [0, 1], transform: ["translateY(-4px) scale(0.96)", "translateY(0px) scale(1)"] }, "shift");
    if (remind && window.pokerMotion && window.pokerMotion.on() && !document.hidden) {
      var glyphs = box.querySelector(".alerts-glyphs");
      glyphs.classList.remove("is-swinging"); void glyphs.offsetWidth;
      glyphs.classList.add("is-swinging");
      glyphs.addEventListener("animationend", function () { glyphs.classList.remove("is-swinging"); }, { once: true });
    }
  }
  function close(box, instant, restore) {
    var sheet = panel(box);
    if (sheet.hidden) return;
    box.classList.remove("is-open");
    bell(box).setAttribute("aria-expanded", "false");
    function gone() { sheet.hidden = true; sheet.style.opacity = ""; sheet.style.transform = ""; }
    var M = window.pokerMotion, leaving = !instant && M ? M.run(sheet, { opacity: 0, transform: "translateY(-4px) scale(0.98)" }, "leave") : null;
    if (leaving) M.after(leaving, function () { if (!box.classList.contains("is-open")) gone(); }); else gone();
    if (restore) bell(box).focus({ preventScroll: true });
  }
  function first(box) {
    var found = box.querySelector(".alerts-panel [data-alerts-state]:not([hidden]) button:not([hidden])");
    if (found) found.focus({ preventScroll: true });
  }

  function sync(box, subscription) {
    if (read(sessionStorage, SYNC_KEY) === subscription.endpoint) return;
    post(box, box.dataset.subscribe, subscription.toJSON()).then(function () {
      write(sessionStorage, SYNC_KEY, subscription.endpoint);
    }).catch(function () {});
  }

  function resolve(box, then) {
    if (!supported(box)) { show(box, installable() ? "install" : null); return; }
    if (Notification.permission === "denied") { show(box, "blocked"); return; }
    navigator.serviceWorker.ready.then(function (ready) {
      registration = ready;
      return ready.pushManager.getSubscription();
    }).then(function (subscription) {
      if (subscription) { sync(box, subscription); show(box, "on"); }
      else { show(box, "ask"); then(); }
    }).catch(function () { show(box, null); });
  }

  function failed(box, words) {
    var error = box.querySelector("[data-alerts-error]");
    // The bell is on every page, so the alert role comes only with a message: an empty alert would sit in each header.
    error.setAttribute("role", "alert"); error.textContent = words; error.hidden = false;
    var M = window.pokerMotion;
    if (M) M.settle(error, M.run(error, { transform: ["translateX(0px)", "translateX(-6px)", "translateX(6px)", "translateX(-3px)", "translateX(0px)"] }, "nudge"), ["transform"]);
  }

  function turnOn(box, button) {
    if (!registration) return;
    box.querySelector("[data-alerts-error]").hidden = true;
    button.setAttribute("aria-busy", "true");
    // Straight from the tap: the browser asks only while the tap is still the reason.
    registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: serverKey(box.dataset.key) })
      .then(function (subscription) {
        return post(box, box.dataset.subscribe, subscription.toJSON()).then(function () { return subscription; });
      })
      .then(function (subscription) {
        write(sessionStorage, SYNC_KEY, subscription.endpoint);
        var line = show(box, "on", true);
        var off = line && line.querySelector("[data-alerts-off]");
        if (off && isOpen(box)) off.focus({ preventScroll: true });
      })
      .catch(function () {
        if (Notification.permission === "denied") { show(box, "blocked", true); return; }
        if (Notification.permission === "default") return; // the question was closed without an answer
        failed(box, "That wasn’t turned on. Check your connection and try again.");
      })
      .then(function () { button.removeAttribute("aria-busy"); });
  }

  function turnOff(box) {
    if (!registration) return;
    registration.pushManager.getSubscription().then(function (subscription) {
      if (!subscription) return null;
      return post(box, box.dataset.unsubscribe, { endpoint: subscription.endpoint }).catch(function () {})
        .then(function () { return subscription.unsubscribe(); });
    }).catch(function () {}).then(function () {
      write(sessionStorage, SYNC_KEY, null);
      box.querySelector("[data-alerts-later]").hidden = true;
      var ask = show(box, "ask", true);
      var on = ask && ask.querySelector("[data-alerts-on]");
      if (on && isOpen(box)) on.focus({ preventScroll: true });
    });
  }

  // The bell survives screen changes, so its controls are answered here, once, for every page.
  document.addEventListener("click", function (event) {
    var box = document.getElementById("alerts");
    if (!box || box.hidden) return;
    if (!box.contains(event.target)) { close(box); return; }
    if (event.target.closest("[data-alerts-bell]")) {
      if (isOpen(box)) close(box, false, true); else { open(box, false); first(box); }
      return;
    }
    var on = event.target.closest("[data-alerts-on]");
    if (on && !on.hasAttribute("aria-busy")) turnOn(box, on);
    else if (event.target.closest("[data-alerts-off]")) turnOff(box);
    else if (event.target.closest("[data-alerts-later]")) close(box, false, true);
    else if (event.target.closest("[data-alerts-install]")) {
      close(box, true);
      document.dispatchEvent(new CustomEvent("install:open", { detail: { from: bell(box) } }));
    }
  });
  // Going to another screen closes it at once. A refresh of the same page (Your groups every few
  // seconds, nightlive.js) is a visit to the same path, and leaves it open: the bell is permanent.
  document.addEventListener("turbo:visit", function (event) {
    var box = document.getElementById("alerts");
    if (box && isOpen(box) && new URL(event.detail.url, location.href).pathname !== location.pathname) close(box, true);
  });
  document.addEventListener("keydown", function (event) {
    var box = document.getElementById("alerts");
    if (event.key === "Escape" && box && !box.hidden && isOpen(box)) { event.preventDefault(); close(box, false, true); }
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

  write(localStorage, OLD_LATER_KEY, null); // the 30-day "Not now" of the foot panel, replaced by once per window

  window.pokerPage.register(function () {
    var box = document.getElementById("alerts"), main = document.getElementById("main"), timer = null;
    addedLines();
    if (!box) return;
    // Once per window, on Your groups, after the arrival and after the home-screen sheet (install.js).
    function remind() {
      if (!main || !main.hasAttribute("data-alerts-remind") || read(sessionStorage, REMINDED_KEY)) return;
      timer = setTimeout(function () {
        if (state !== "ask" || isOpen(box) || document.hidden || document.querySelector("dialog[open]")) return;
        if (!write(sessionStorage, REMINDED_KEY, "1")) return; // without storage it could repeat: no reminder
        open(box, true);
        var news = document.getElementById("route-announcer");
        if (news) news.textContent = "Table alerts are off. Get a notification when a host adds you to a set.";
      }, main.hasAttribute("data-welcome") ? 1400 : 800);
    }
    resolve(box, remind);
    // A refresh of the same page restarts the scripts too; the panel stays open through it.
    return function () { clearTimeout(timer); };
  });
})();

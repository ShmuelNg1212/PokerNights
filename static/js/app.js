// What makes the site behave when it is installed on a phone: the offline notice, a
// refresh when the app returns to the foreground, and the service worker registration.
// Each part works alone if the browser lacks another.
(function () {
  "use strict";
  var root = document.documentElement;
  function noticeEl() { return document.getElementById("offline-notice"); }

  // The service worker shows an offline page when a navigation fails. See config/pwa.py.
  if ("serviceWorker" in navigator) {
    if (root.dataset.sw === "on") navigator.serviceWorker.register("/sw.js").catch(function () {});
    else {
      // Switched off on the server: remove any worker and cache an earlier visit left on this phone.
      navigator.serviceWorker.getRegistrations().then(function (all) { all.forEach(function (one) { one.unregister(); }); }).catch(function () {});
      if (window.caches) caches.keys().then(function (keys) { keys.forEach(function (key) { if (key.indexOf("pokernights-") === 0) caches.delete(key); }); }).catch(function () {});
    }
  }

  // navigator.onLine is a hint, not proof. The notice is advice; the server decides what is saved.
  function showConnection() {
    var offline = navigator.onLine === false, notice = noticeEl();
    root.classList.toggle("is-offline", offline);
    if (notice) {
      notice.hidden = !offline;
      // The page and the sticky header move down by the notice's real height, one line or two.
      if (offline) root.style.setProperty("--offline-h", notice.offsetHeight + "px");
    }
  }
  window.addEventListener("offline", showConnection);
  window.addEventListener("online", showConnection);
  window.pokerPage.register(showConnection);

  // A form sent with no connection fails, and must not look as if it worked. Typed values stay.
  document.addEventListener("submit", function (event) {
    if (navigator.onLine !== false) return;
    event.preventDefault();
    event.stopPropagation();
    var notice = noticeEl();
    if (notice) { notice.classList.remove("nudge"); void notice.offsetWidth; notice.classList.add("nudge"); }
  }, true);

  // Full-screen mode has no reload button. A page that does not refresh itself reloads when
  // the app comes back after a while, unless that would throw away something typed or open.
  var AWAY_MS = 30000, hiddenAt = null;
  function hasUnsavedWork() {
    if (document.querySelector("dialog[open]")) return true;
    return Array.from(document.querySelectorAll("main input, main textarea, main select")).some(function (el) {
      if (el.type === "hidden" || el.disabled) return false;
      if (el.type === "checkbox" || el.type === "radio") return el.checked !== el.defaultChecked;
      if (el.tagName === "SELECT") {
        // A single select with no marked default starts on its first option.
        var options = Array.from(el.options), marked = options.some(function (o) { return o.defaultSelected; });
        if (!marked && !el.multiple) return el.selectedIndex > 0;
        return options.some(function (o) { return o.selected !== o.defaultSelected; });
      }
      return el.value !== el.defaultValue;
    });
  }
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) { hiddenAt = Date.now(); return; }
    var away = hiddenAt === null ? 0 : Date.now() - hiddenAt;
    hiddenAt = null;
    if (away < AWAY_MS) return;
    if (document.getElementById("live")) return;            // the set page refreshes itself
    if (document.body.dataset.method !== "GET") return;     // a reload would send the form again
    if (navigator.onLine === false || hasUnsavedWork()) return;
    window.location.reload();
  });
  window.pokerNights = { awayMs: function (ms) { AWAY_MS = ms; } };   // for the browser checks
})();

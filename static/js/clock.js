// Keeps shown playing times moving between page updates. The server sends
// each figure in seconds; this script only adds the time since the page (or
// the last live update) arrived. A reload or another tab gets the same figure
// from the server.
(function () {
  "use strict";

  function text(seconds) {
    var minutes = Math.floor(seconds / 60);
    if (minutes < 1) return "under 1 min";
    var hours = Math.floor(minutes / 60);
    var rest = minutes % 60;
    return hours ? hours + " h " + (rest < 10 ? "0" : "") + rest + " min" : rest + " min";
  }

  function tick() {
    var now = Date.now();
    document.querySelectorAll("[data-clock][data-running]").forEach(function (el) {
      if (!el.dataset.since) el.dataset.since = String(now);  // first sight of this server figure
      var elapsed = Math.floor((now - Number(el.dataset.since)) / 1000);
      el.textContent = text(Number(el.dataset.seconds) + elapsed);
    });
  }

  // One interval for the whole tab; each page gets its figures at once when it arrives.
  setInterval(tick, 5000);
  window.pokerPage.register(tick);
})();

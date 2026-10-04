// Collapses the host dock to one bar on phones. The choice is a class on <html>,
// outside the live region, so a poll that redraws the dock keeps it.
(function () {
  "use strict";
  var region = document.getElementById("live");
  if (!region) return;
  var root = document.documentElement, KEY = "rack-dock";
  // The page reserves the measured dock height, so the last row clears the dock in either state.
  var watcher = window.ResizeObserver ? new ResizeObserver(measure) : null;
  root.classList.add("dock-enabled");
  try { if (localStorage.getItem(KEY) === "collapsed") root.classList.add("dock-collapsed"); } catch (_) {}

  function measure() {
    var dock = region.querySelector(".host-controls");
    if (dock) root.style.setProperty("--dock-h", Math.ceil(dock.getBoundingClientRect().height) + "px");
  }

  function sync() {
    var toggle = region.querySelector(".dock-toggle");
    if (!toggle) return;
    toggle.hidden = false;
    toggle.setAttribute("aria-expanded", String(!root.classList.contains("dock-collapsed")));
    if (watcher) { watcher.disconnect(); watcher.observe(toggle.parentElement); }
    measure();
  }

  region.addEventListener("click", function (event) {
    if (!event.target.closest(".dock-toggle")) return;
    var collapsed = root.classList.toggle("dock-collapsed");
    try { if (collapsed) localStorage.setItem(KEY, "collapsed"); else localStorage.removeItem(KEY); } catch (_) {}
    sync();
  });
  document.addEventListener("live:updated", sync);
  sync();
})();

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
    // A live update replaces a dock that was still closing.
    if (!toggle.parentElement.getAnimations || !toggle.parentElement.getAnimations().length) root.classList.remove("dock-closing");
    if (watcher) { watcher.disconnect(); watcher.observe(toggle.parentElement); }
    measure();
  }

  // The dock slides between its two heights. While it closes, "dock-closing" keeps the
  // content rendered so it leaves with the edge. Reduced motion changes the size at once.
  function slide(dock, from, closing) {
    var to = dock.offsetHeight;
    if (!dock.animate || from === to || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (closing) root.classList.add("dock-closing");
    dock.style.overflow = "hidden";
    var done = function () { dock.style.overflow = ""; root.classList.remove("dock-closing"); };
    var motion = dock.animate([{ height: from + "px" }, { height: to + "px" }],
      closing ? { duration: 200, easing: "cubic-bezier(0.4,0,1,1)" } : { duration: 320, easing: "cubic-bezier(0.16,1,0.3,1)" });
    motion.onfinish = motion.oncancel = done;
  }

  region.addEventListener("click", function (event) {
    var toggle = event.target.closest(".dock-toggle");
    if (!toggle) return;
    var dock = toggle.parentElement, from = dock.offsetHeight;
    dock.getAnimations().forEach(function (motion) { motion.cancel(); });
    var collapsed = root.classList.toggle("dock-collapsed");
    slide(dock, from, collapsed);
    try { if (collapsed) localStorage.setItem(KEY, "collapsed"); else localStorage.removeItem(KEY); } catch (_) {}
    sync();
  });
  document.addEventListener("live:updated", sync);
  sync();
})();

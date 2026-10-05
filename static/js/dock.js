// Collapses the host dock to one bar on phones. The choice is a class on <html>,
// outside the live region, so a poll that redraws the dock keeps it.
(function () {
  "use strict";
  var region = null, watcher = null; // set while a set page is shown
  var root = document.documentElement, KEY = "rack-dock";
  var view = window.visualViewport, lifted = 0; // px the dock is raised above the page's bottom edge

  // The page reserves the measured dock height, so the last row clears the dock in either state.
  function measure() {
    var dock = region && region.querySelector(".host-controls");
    if (dock) root.style.setProperty("--dock-h", Math.ceil(dock.getBoundingClientRect().height) + "px");
  }

  function sync() {
    var toggle = region && region.querySelector(".dock-toggle");
    if (!toggle) return;
    toggle.hidden = false;
    toggle.setAttribute("aria-expanded", String(!root.classList.contains("dock-collapsed") && !root.classList.contains("kb-bar")));
    // A live update replaces a dock that was still closing.
    if (!toggle.parentElement.getAnimations || !toggle.parentElement.getAnimations().length) root.classList.remove("dock-closing");
    if (watcher) { watcher.disconnect(); watcher.observe(toggle.parentElement); }
    measure();
  }

  // An iPhone keyboard covers the bottom of the page instead of resizing it, and a fixed dock
  // stays under it. The visual viewport says how much is covered; the dock is raised by that
  // much and shown as its bar, unless the typing is in one of the dock's own fields.
  function keyboard() {
    var dock = region && region.querySelector(".host-controls");
    if (!dock || !view) return;
    var covered = 0, active = document.activeElement;
    if (getComputedStyle(dock).position === "fixed" && Math.abs(view.scale - 1) < 0.01)
      covered = Math.round(dock.getBoundingClientRect().bottom + lifted - view.offsetTop - view.height);
    if (covered < 80) covered = 0; // a browser toolbar, not a keyboard
    var bar = covered > 0 && !(dock.contains(active) && !active.matches(".dock-toggle"));
    if (covered !== lifted || bar !== root.classList.contains("kb-bar")) {
      lifted = covered;
      if (covered) root.style.setProperty("--kb", covered + "px"); else root.style.removeProperty("--kb");
      root.classList.toggle("kb-open", covered > 0);
      root.classList.toggle("kb-bar", bar);
      dock.getAnimations().forEach(function (motion) { motion.cancel(); });
      sync();
    }
    // The browser scrolls a focused field clear of the keyboard, not of the bar above it.
    if (bar && region.contains(active)) {
      var under = active.getBoundingClientRect().bottom + 12 - dock.getBoundingClientRect().top;
      if (under > 0) window.scrollBy(0, under);
    }
  }
  function settle() { setTimeout(keyboard, 0); } // the focus has moved by then

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

  document.addEventListener("click", function (event) {
    var toggle = region && event.target.closest(".dock-toggle");
    if (!toggle || !region.contains(toggle)) return;
    // Above the keyboard the bar is not a choice to save: a tap puts the keyboard away.
    if (root.classList.contains("kb-bar")) { if (document.activeElement) document.activeElement.blur(); return; }
    var dock = toggle.parentElement, from = dock.offsetHeight;
    dock.getAnimations().forEach(function (motion) { motion.cancel(); });
    var collapsed = root.classList.toggle("dock-collapsed");
    slide(dock, from, collapsed);
    try { if (collapsed) localStorage.setItem(KEY, "collapsed"); else localStorage.removeItem(KEY); } catch (_) {}
    sync();
  });
  document.addEventListener("live:updated", function () { sync(); keyboard(); });

  window.pokerPage.register(function () {
    region = document.getElementById("live");
    if (!region) return;
    watcher = window.ResizeObserver ? new ResizeObserver(measure) : null;
    root.classList.add("dock-enabled");
    try { root.classList.toggle("dock-collapsed", localStorage.getItem(KEY) === "collapsed"); } catch (_) {}
    sync();
    if (view) {
      view.addEventListener("resize", keyboard);
      view.addEventListener("scroll", keyboard);
      document.addEventListener("focusin", settle);
      document.addEventListener("focusout", settle);
      keyboard();
    }
    return function () {
      if (watcher) watcher.disconnect();
      if (view) {
        view.removeEventListener("resize", keyboard);
        view.removeEventListener("scroll", keyboard);
        document.removeEventListener("focusin", settle);
        document.removeEventListener("focusout", settle);
      }
      region = watcher = null; lifted = 0;
      root.style.removeProperty("--kb");
      root.classList.remove("dock-enabled", "dock-closing", "kb-open", "kb-bar");
    };
  });
})();

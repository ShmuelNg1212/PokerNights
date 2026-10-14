// Movement on the set page when its live region is redrawn, by a poll (live.js) or by an
// action sent in the background (turbo-setup.js). Row positions and the set's state are read
// before the redraw and compared after it: a new row arrives, a row that was pushed slides to
// its place, a new state fades in. Figures are never touched; they show their accepted value
// from the first frame. Without Motion, under reduced motion or in a hidden tab nothing runs.
(function () {
  "use strict";
  var region = null, before = null;
  var REST = "translateY(0px)";

  function moving() { return !!window.pokerMotion && window.pokerMotion.on() && !document.hidden; }
  function rows() { return region.querySelectorAll("li[data-watch]"); }
  // Where the row is laid out on the page, whatever an animation is doing to it now.
  function top(row) {
    var at = row.getBoundingClientRect().top + window.scrollY;
    return row.style.transform ? at - new DOMMatrix(getComputedStyle(row).transform).m42 : at;
  }
  function go(el, keyframes, preset, extra) {
    var M = window.pokerMotion;
    M.settle(el, M.run(el, keyframes, preset, extra), Object.keys(keyframes));
  }

  document.addEventListener("live:updating", function () {
    before = null;
    if (!region || !moving()) return;
    before = { state: region.dataset.state, tops: {} };
    rows().forEach(function (row) { before.tops[row.dataset.watch] = row.getBoundingClientRect().top + window.scrollY; });
  });

  document.addEventListener("live:updated", function () {
    var was = before, arrivals = 0;
    before = null;
    if (!region || !was || !moving()) return;
    if (was.state !== region.dataset.state) { go(region, { opacity: [0, 1] }, "fade"); return; }
    rows().forEach(function (row) {
      var old = was.tops[row.dataset.watch];
      if (old === undefined) {
        // Several players added at once arrive 40ms apart.
        go(row, { opacity: [0, 1], transform: ["translateY(12px)", REST] }, "shift", { delay: 0.04 * arrivals++ });
        return;
      }
      var by = old - top(row);
      if (Math.abs(by) > 1 && Math.abs(by) < window.innerHeight) go(row, { transform: ["translateY(" + by + "px)", REST] }, "shift");
    });
  });

  // Players just added on Add players arrive once: they rise into place 40ms apart, as rows
  // that arrive by a live update do, and carry the brass mark for three seconds. Under reduced
  // motion they carry the mark only. The first keyframe is written before Motion starts
  // (doc/wiki/footguns/motion_starts_a_frame_late.md).
  var HOLD_MS = 3000, FADE_MS = 400;
  function arrive(timers) {
    var rows = Array.prototype.slice.call(region.querySelectorAll("li[data-arrived]"));
    if (!rows.length) return;
    rows.forEach(function (row, at) {
      row.removeAttribute("data-arrived");
      row.classList.add("just-changed");
      if (moving()) {
        row.style.opacity = "0"; row.style.transform = "translateY(12px)";
        go(row, { opacity: [0, 1], transform: ["translateY(12px)", REST] }, "shift", { delay: 0.04 * Math.min(at, 8) });
      }
    });
    timers.push(setTimeout(function () { rows.forEach(function (row) { row.classList.add("change-fading"); }); }, HOLD_MS - FADE_MS));
    timers.push(setTimeout(function () { rows.forEach(function (row) { row.classList.remove("just-changed", "change-fading"); }); }, HOLD_MS));
    // The arrivals are brought into sight above the dock and the message over it, once the dock
    // has measured itself (dock.js reserves its height below the page), and never past the first.
    requestAnimationFrame(function () { requestAnimationFrame(function () {
      if (!rows[0].isConnected) return;
      var dock = region.querySelector(".host-controls"), limit = window.innerHeight;
      if (dock && getComputedStyle(dock).position === "fixed") limit = dock.getBoundingClientRect().top - 96;
      var below = rows[rows.length - 1].getBoundingClientRect().bottom - limit, room = rows[0].getBoundingClientRect().top - 80;
      if (below > 0) window.scrollBy({ top: Math.min(below, room), behavior: moving() ? "smooth" : "auto" });
    }); });
  }

  // motion.js cancels every running animation when the page is left.
  window.pokerPage.register(function () {
    var timers = [];
    region = document.getElementById("live");
    before = null;
    if (region) arrive(timers);
    return function () { timers.forEach(clearTimeout); region = null; before = null; };
  });
})();

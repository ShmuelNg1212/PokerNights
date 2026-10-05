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

  // motion.js cancels every running animation when the page is left.
  window.pokerPage.register(function () {
    region = document.getElementById("live");
    before = null;
    return function () { region = null; before = null; };
  });
})();

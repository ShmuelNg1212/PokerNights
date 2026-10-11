// Carried transfers on the session page (DESIGN.md, "Carried transfers"): the count under the list
// a host ticks before closing, the make-up of a person's figure arriving once, the list of what a
// session took over, and an earlier transfer turning "Carried" while the page is open. It only adds
// movement and one line of words: without it every figure and state is already on the page.
(function () {
  "use strict";
  function M() { return window.pokerMotion; }
  function go(el, keyframes, preset, extra) {
    var motion = M();
    if (!el || !motion || !motion.on() || document.hidden) return;
    // The first keyframe is written before Motion starts (footgun: motion starts a frame late).
    Object.keys(keyframes).forEach(function (name) { el.style[name] = keyframes[name][0]; });
    motion.settle(el, motion.run(el, keyframes, preset, extra), Object.keys(keyframes));
  }
  function rise(items, step, from) {
    items.forEach(function (el, index) {
      go(el, { opacity: [0, 1], transform: ["translateY(" + (from || 8) + "px)", "translateY(0px)"] }, "shift", { delay: index * step });
    });
  }

  // Before closing: how many of the listed transfers are ticked. Amounts are not added up here;
  // the server works the list out and formats every figure.
  function count(pick, moved) {
    var boxes = pick.querySelectorAll("input[name=carry]"), line = pick.querySelector("[data-carry-count]");
    var ticked = pick.querySelectorAll("input[name=carry]:checked").length;
    if (!line) return;
    line.hidden = false;
    line.textContent = ticked === 0 ? "None will be carried. Tonight is settled by itself."
      : ticked === boxes.length ? (ticked === 1 ? "It will be carried into tonight's list." : "All " + ticked + " will be carried into tonight's list.")
      : ticked + " of " + boxes.length + " will be carried into tonight's list.";
    if (moved) go(line, { opacity: [0.4, 1], transform: ["translateY(3px)", "translateY(0px)"] }, "fade");
  }
  document.addEventListener("change", function (event) {
    var box = event.target;
    if (!box.matches || !box.matches("[data-carry-pick] input[name=carry]")) return;
    count(box.closest("[data-carry-pick]"), true);
    // The row answers the tap: it settles back a little when unticked and comes forward when ticked.
    var row = box.closest(".carry-option");
    go(row.querySelector(".grow"), { transform: [box.checked ? "translateX(-4px)" : "translateX(4px)", "translateX(0px)"] }, "drop");
  });

  // What this session took over, opened by a tap: the rows come in one after another.
  var asked = -Infinity;
  document.addEventListener("click", function (event) { if (event.target.closest && event.target.closest(".night-carried > summary")) asked = performance.now(); });
  document.addEventListener("toggle", function (event) {
    var box = event.target;
    if (!box.matches || !box.matches(".night-carried") || !box.open || performance.now() - asked > 400) return;
    rise(Array.from(box.querySelectorAll(".carried-list > li")), 0.045, 6);
  }, true);

  // An earlier transfer was carried while this page was open (nightlive.js redrew it): the row says so.
  document.addEventListener("night:refreshed", function (event) {
    var was = event.detail.paid || {};
    document.querySelectorAll('.night-settle [data-transfer][data-paid="c"]').forEach(function (row) {
      if (was[row.dataset.transfer] !== "0") return;
      go(row.querySelector(".carried-mark"), { opacity: [0, 1], transform: ["translate(-5px, 5px) scale(0.6)", "translate(0px, 0px) scale(1)"] }, "drop");
      go(row.querySelector(".transfer-state"), { opacity: [0, 1] }, "fade", { delay: 0.08 });
      row.classList.add("just-carried");
      setTimeout(function () { row.classList.remove("just-carried"); }, 900);
    });
  });

  // How a figure is made up: once per session and browser, after any sheet that opened by itself has closed.
  function makeup() {
    var list = document.querySelector(".makeup[data-makeup]");
    if (!list) return;
    var key = "rack-makeup:" + list.dataset.makeup;
    try { if (localStorage.getItem(key)) return; } catch (_) { return; }
    if (document.querySelector("dialog[open]")) return; // asked again when it closes
    try { localStorage.setItem(key, "1"); } catch (_) { return; }
    var rows = Array.from(list.children);
    rise(rows, 0.07, 8);
    var total = list.querySelector(".makeup-total dd");
    go(total, { transform: ["scale(1)", "scale(1.08)", "scale(1)"] }, "pulse", { delay: rows.length * 0.07 + 0.1 });
  }
  document.addEventListener("close", function (event) { if (event.target.matches && event.target.matches("dialog")) setTimeout(makeup, 220); }, true);

  window.pokerPage.register(function () {
    var pick = document.querySelector("[data-carry-pick]");
    if (pick) count(pick, false);
    makeup();
  });
})();

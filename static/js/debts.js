// A settlement receipt is local to this page visit. Polling must not remove its Undo form.
(function () {
  "use strict";
  var undoing = false, before = null;
  var reduced = matchMedia("(prefers-reduced-motion: reduce)"), active = new Map();
  function moving() { return window.pokerMotion && window.pokerMotion.on() && !document.hidden; }
  function parts(root) { return root.querySelectorAll("[data-debt], [data-debt-receipt], .group-sessions:not(#debts)"); }
  function key(el) { return el.dataset.debt || (el.dataset.debtReceipt ? "receipt-" + el.dataset.debtReceipt : el.getAttribute("aria-labelledby")); }
  function places() {
    var found = {};
    parts(document).forEach(function (el) {
      if (!el.getClientRects().length) return;
      found[key(el)] = el.getBoundingClientRect().top + scrollY;
    });
    return found;
  }
  function move(el, frames) {
    var M = window.pokerMotion;
    // Motion starts on its next frame. Write the first frame before this redraw can paint.
    Object.keys(frames).forEach(function (name) { el.style[name] = frames[name][0]; });
    var controls = M.run(el, frames, "shift");
    active.set(el, controls);
    M.settle(el, controls, Object.keys(frames));
    M.after(controls, function () { if (active.get(el) === controls) active.delete(el); });
  }
  function stop() {
    active.forEach(function (controls, el) { controls.cancel(); el.style.transform = ""; el.style.opacity = ""; });
    active.clear(); before = null;
  }
  reduced.addEventListener("change", function () { if (reduced.matches) stop(); });
  document.addEventListener("visibilitychange", function () { if (document.hidden) stop(); });
  document.addEventListener("submit", function (event) {
    undoing = !!event.target.closest("[data-debt-receipt]");
  }, true);
  document.addEventListener("turbo:before-render", function (event) {
    before = event.detail.renderMethod === "morph" && document.getElementById("debts") && moving() ? places() : null;
    if (event.detail.renderMethod !== "morph") return;
    var old = document.getElementById("debts"), fresh = event.detail.newBody;
    var receipt = old && old.querySelector("[data-debt-receipt]");
    if (!receipt || fresh.querySelector("[data-debt-receipt]")) return;
    if (undoing && !fresh.querySelector(".message-error")) return;
    var next = fresh.querySelector("#debts");
    if (!next) {
      next = old.cloneNode(false);
      next.appendChild(old.querySelector("h2").cloneNode(true));
      var first = fresh.querySelector(".group-sessions");
      if (!first) return;
      first.before(next);
    }
    if (next.dataset.url === old.dataset.url) next.querySelector("h2").after(receipt.cloneNode(true));
  });
  document.addEventListener("turbo:render", function () {
    undoing = false;
    var was = before; before = null;
    if (!was || !moving()) return;
    // Read each new position before writing transforms. Parents and children never both move.
    var changes = [];
    parts(document).forEach(function (el) {
      if (!el.getClientRects().length) return;
      var old = was[key(el)], by = old === undefined ? null : old - (el.getBoundingClientRect().top + scrollY);
      if (by !== null && Math.abs(by) > 1 && Math.abs(by) < innerHeight * 1.5) changes.push([el, by, false]);
      else if (old === undefined && (el.hasAttribute("data-debt") || el.hasAttribute("data-debt-receipt"))) changes.push([el, 8, true]);
    });
    changes.forEach(function (change) {
      var frames = { transform: ["translateY(" + change[1] + "px)", "translateY(0px)"] };
      if (change[2]) frames.opacity = [0, 1];
      move(change[0], frames);
    });
  });
  window.pokerPage.register(function () { return stop; });
})();

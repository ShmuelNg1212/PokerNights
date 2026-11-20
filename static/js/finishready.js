// Ready to finish (DESIGN.md, "Count-up without a cash-out step"): when the last count is confirmed and the
// counts balance, "Review and finish" rises into the dock once per set and browser. It is the one moment the
// count-up changes its question, from "what does each player have?" to "finish?". Confirming redraws the set
// in place, so the redraw ("live:updated") is watched as well as the page. A tap during the rise interrupts
// it: the press moves the same y. Without Motion, under reduced motion, in a hidden tab and on a later visit
// the action is simply there.
(function () {
  "use strict";
  function arrive() {
    var M = window.pokerMotion, action = document.querySelector(".host-controls [data-finish-ready]");
    if (!action || !M || !M.on() || document.hidden) return;
    if (!action.getClientRects().length) return; // a folded dock: the once is not spent
    var key = "rack-finish:" + action.dataset.finishReady;
    try { if (localStorage.getItem(key)) return; localStorage.setItem(key, "1"); } catch (_) { return; }
    // The first keyframe is written before Motion starts (footgun: motion starts a frame late).
    action.style.opacity = "0"; action.style.transform = "translateY(8px)";
    // Two animations: a press takes over y and clears transform when it ends; nothing else touches opacity.
    var fade = M.run(action, { opacity: [0, 1] }, "progress");
    M.settle(action, M.run(action, { y: [8, 0] }, "progress"), ["transform"]);
    M.after(fade, function () { requestAnimationFrame(function () { requestAnimationFrame(function () { action.style.opacity = ""; }); }); });
  }
  document.addEventListener("live:updated", arrive);
  window.pokerPage.register(arrive);
})();

// What next? on a finished set's page (DESIGN.md, "What next?"): the two choices rise into place once
// per set and browser, the first time the host sees them. Finalizing redraws the set in place, so the
// redraw ("live:updated") is watched as well as the page. A tap during the rise interrupts it: the
// press moves the same y. Without Motion, under reduced motion and on a reload, they are simply there.
(function () {
  "use strict";
  function arrive() {
    var M = window.pokerMotion, step = document.querySelector(".final-layout [data-next-step]");
    if (!step || !M || !M.on() || document.hidden) return;
    var key = "rack-next:" + step.dataset.nextStep;
    try { if (localStorage.getItem(key)) return; localStorage.setItem(key, "1"); } catch (_) { return; }
    Array.prototype.slice.call(step.querySelectorAll(".next-card")).filter(function (card) {
      return card.getClientRects().length;
    }).forEach(function (card, index) {
      // The first keyframe is written before Motion starts (footgun: motion starts a frame late).
      card.style.opacity = "0"; card.style.transform = "translateY(8px)";
      // Two animations: a press takes over y and clears transform when it ends; nothing touches opacity.
      var delay = { delay: 0.08 + index * 0.06 };
      var fade = M.run(card, { opacity: [0, 1] }, "arrive", delay);
      M.settle(card, M.run(card, { y: [8, 0] }, "arrive", delay), ["transform"]);
      M.after(fade, function () { requestAnimationFrame(function () { requestAnimationFrame(function () { card.style.opacity = ""; }); }); });
    });
  }
  document.addEventListener("live:updated", arrive);
  window.pokerPage.register(arrive);
})();

// The set page while a set is prepared and in play (DESIGN.md, "Set page"): a step that has just
// been completed, the start of the set, and the facts behind "Details". It only adds movement:
// without Motion or under reduced motion pokerMotion.run does nothing and the page is the same.
(function () {
  "use strict";
  var region = null, key = "", before = null;

  function go(el, keyframes, preset, extra) {
    var M = window.pokerMotion;
    if (!el || !M || !M.on() || document.hidden) return;
    // The first keyframe is written before Motion starts (footgun: motion starts a frame late).
    Object.keys(keyframes).forEach(function (name) { el.style[name] = keyframes[name][0]; });
    M.settle(el, M.run(el, keyframes, preset, extra), Object.keys(keyframes));
  }
  // What the page says now: each step's state, and the set's state.
  function read() {
    var now = { state: region.dataset.state };
    region.querySelectorAll(".prep-step").forEach(function (step) { now[step.dataset.step] = step.dataset.state; });
    return now;
  }
  function remembered() { try { return JSON.parse(sessionStorage.getItem(key)); } catch (_) { return null; } }
  function remember(now) { try { sessionStorage.setItem(key, JSON.stringify(now)); } catch (_) {} }

  // Compares what was shown with what is shown. Adding players happens on another screen, so the
  // comparison also runs when the set page is opened again.
  function answer(was) {
    var now = read();
    remember(now);
    if (!was) return;
    region.querySelectorAll(".prep-step").forEach(function (step) {
      var name = step.dataset.step, mark = step.querySelector(".prep-mark");
      // A step just completed: its mark lands with the tick. The step that is next now is pointed at.
      if (now[name] === "done" && was[name] && was[name] !== "done") go(mark, { opacity: [0, 1], transform: ["scale(0.5)", "scale(1)"] }, "arrive");
      else if (now[name] === "next" && was[name] === "later") go(mark, { transform: ["scale(1)", "scale(1.18)", "scale(1)"] }, "pulse", { delay: 0.12 });
    });
    // The set starts, once: felt sweeps across the panel from the left and the timer is running.
    if (now.state === "running" && (was.state === "open" || was.state === "setup")) {
      var felt = region.querySelector(".table-v2 .felt");
      go(felt, { clipPath: ["inset(0 100% 0 0)", "inset(0 0% 0 0)"] }, { duration: 0.5, ease: [0.16, 1, 0.3, 1] });
      go(region.querySelector(".table-v2 .pot-side"), { opacity: [0, 1], transform: ["translateY(8px)", "translateY(0px)"] }, "shift", { delay: 0.28 });
    }
  }

  document.addEventListener("live:updating", function () { before = region ? read() : null; });
  document.addEventListener("live:updated", function () { if (region) answer(before); before = null; });
  // "Details" opens: the facts fade in over a few pixels, as disclosures do elsewhere. Closing is immediate.
  // Only when a person opened it: a live update and a wide screen open it too, and those are not events to mark.
  var asked = 0;
  document.addEventListener("click", function (event) { if (event.target.closest && event.target.closest(".set-facts > summary")) asked = performance.now(); });
  document.addEventListener("toggle", function (event) {
    var facts = event.target;
    if (!region || !facts.matches || !facts.matches(".set-facts") || !facts.open || !region.contains(facts) || performance.now() - asked > 400) return;
    go(facts.querySelector(".facts-body"), { opacity: [0, 1], transform: ["translateY(-6px)", "translateY(0px)"] }, "fade");
  }, true);

  window.pokerPage.register(function () {
    region = document.getElementById("live");
    if (!region || !region.querySelector(".table-v2")) { region = null; return; }
    key = "rack-prep:" + region.dataset.url;
    answer(remembered());
    return function () { region = null; before = null; };
  });
})();

// The set page while a set is prepared and in play (DESIGN.md, "Set page"): a step that has just
// been completed, the start of the set, and the facts behind "Details". It only adds movement:
// without Motion or under reduced motion pokerMotion.run does nothing and the page is the same.
(function () {
  "use strict";
  var region = null, key = "", before = null, completion = null;

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

  function clearCompletion(keepOpen) {
    if (!completion) return;
    clearTimeout(completion.close); clearTimeout(completion.light); clearTimeout(completion.end);
    if (completion.fold) completion.fold.classList.remove("prep-completing", "prep-folding");
    completion.mark.classList.remove("prep-ticked");
    if (completion.auto && !keepOpen) completion.fold.open = false;
    if (completion.next) completion.next.classList.remove("prep-next-waiting");
    completion = null;
  }
  function completed(step) {
    var fold = step.closest(".prep-done"), M = window.pokerMotion;
    if (!M || !M.on() || document.hidden) return;
    clearCompletion();
    var mark = fold ? fold.querySelector("summary .prep-mark") : step.querySelector(".prep-mark");
    if (!mark) return;
    mark.classList.add("prep-ticked");
    var next = region.querySelector(".prep-title");
    var item = completion = { fold: fold, mark: mark, next: next };
    if (next) {
      next.classList.add("prep-next-ready", "prep-next-waiting");
      item.light = setTimeout(function () { if (completion === item) next.classList.remove("prep-next-waiting"); }, 260);
    }
    // Show the completed step long enough to draw its tick, then let native details fold it.
    // Only a fold that was closed is ours to close. A person's open fold stays open.
    if (fold && !fold.open && CSS.supports("interpolate-size", "allow-keywords") && CSS.supports("selector(details::details-content)")) {
      item.auto = true;
      fold.classList.add("prep-completing");
      fold.open = true;
      void fold.offsetHeight; // establish the open height before the closing transition
      item.close = setTimeout(function () {
        if (completion !== item || !fold.isConnected) return;
        fold.classList.replace("prep-completing", "prep-folding"); fold.open = false;
      }, 80);
    }
    item.end = setTimeout(function () { if (completion === item) clearCompletion(); }, 290);
  }

  // Compares what was shown with what is shown. Adding players happens on another screen, so the
  // comparison also runs when the set page is opened again.
  function answer(was) {
    var now = read();
    remember(now);
    if (!was) return;
    region.querySelectorAll(".prep-step").forEach(function (step) {
      var name = step.dataset.step;
      if (now[name] === "done" && was[name] && was[name] !== "done") completed(step);
    });
    // The set starts, once: felt sweeps across the panel from the left and the timer is running.
    if (now.state === "running" && (was.state === "open" || was.state === "setup")) {
      // Resume play never replays the start, including after a reload or a new browser tab.
      try { var started = "rack-start:" + region.dataset.url; if (localStorage.getItem(started)) return; localStorage.setItem(started, "1"); } catch (_) { return; }
      var felt = region.querySelector(".table-v2 .felt");
      go(felt, { clipPath: ["inset(0 100% 0 0)", "inset(0 0% 0 0)"] }, { duration: 0.5, ease: [0.16, 1, 0.3, 1] });
      go(region.querySelector(".table-v2 .pot-side"), { opacity: [0, 1], transform: ["translateY(8px)", "translateY(0px)"] }, "shift", { delay: 0.28 });
      region.querySelectorAll(".player-row").forEach(function (row, index) {
        // The money stays fully visible. Only the row's position settles after the felt.
        go(row, { transform: ["translateY(8px)", "translateY(0px)"] }, "progress", { delay: 0.28 + Math.min(index, 8) * 0.03 });
      });
    }
  }

  document.addEventListener("live:updating", function () { clearCompletion(); before = region ? read() : null; });
  document.addEventListener("live:updated", function () { if (region) answer(before); before = null; });
  document.addEventListener("click", function (event) {
    if (completion && event.target.closest && event.target.closest(".prep-done")) clearCompletion(true);
  });

  window.pokerPage.register(function () {
    region = document.getElementById("live");
    if (!region || !region.querySelector(".table-v2")) { region = null; return; }
    key = "rack-prep:" + region.dataset.url;
    answer(remembered());
    return function () { clearCompletion(); region = null; before = null; };
  });
})();

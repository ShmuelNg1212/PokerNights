// Group settings → Players. It only adds: the rows a host just added or brought back are marked and
// rise into place, an opened disclosure eases in, and the Names box counts what is typed.
// Without it every form on the section still works.
(function () {
  "use strict";
  var HOLD_MS = 3000, FADE_MS = 400, MOST = 30;
  window.pokerPage.register(function () {
    var section = document.getElementById("players"), list = section && section.querySelector("[data-roster]");
    if (!list) return;
    var life = new AbortController(), timers = [], M = window.pokerMotion;
    // Motion begins on the next frame, so the element is put at its starting point now
    // (doc/wiki/footguns/motion_starts_a_frame_late.md).
    function move(el, keyframes, preset, extra) {
      if (!el || !M || !M.on()) return;
      Object.keys(keyframes).forEach(function (name) { el.style[name] = keyframes[name][0]; });
      M.settle(el, M.run(el, keyframes, preset, extra), Object.keys(keyframes));
    }
    // The same brass mark as an accepted change on a set, held and then faded.
    function mark(els) {
      els.forEach(function (el) { el.classList.add("just-changed"); });
      timers.push(setTimeout(function () { els.forEach(function (el) { el.classList.add("change-fading"); }); }, HOLD_MS - FADE_MS));
      timers.push(setTimeout(function () { els.forEach(function (el) { el.classList.remove("just-changed", "change-fading"); }); }, HOLD_MS));
    }

    var arrived = Array.from(list.querySelectorAll("[data-arrived]"));
    if (arrived.length) {
      mark(arrived);
      arrived[0].scrollIntoView({ block: "nearest" });
      arrived.forEach(function (row, at) {
        move(row, { opacity: [0, 1], transform: ["translateY(12px)", "translateY(0px)"] }, "shift", { delay: Math.min(at, 8) * 0.04 });
      });
    }
    var left = section.querySelector(".roster-removed[data-changed] > summary");
    if (left) { mark([left]); move(left, { transform: ["scale(1)", "scale(1.03)", "scale(1)"] }, "pulse"); }

    // "toggle" does not bubble, so it is caught on the way down.
    section.addEventListener("toggle", function (event) {
      var details = event.target;
      if (!details.open || !details.matches || !details.matches("details")) return;
      move(details.querySelector(":scope > :not(summary)"), { opacity: [0, 1], transform: ["translateY(-6px)", "translateY(0px)"] }, "fade");
    }, { capture: true, signal: life.signal });

    var tally = section.querySelector("[data-names-tally]"), box = tally && document.getElementById(tally.dataset.namesTally);
    function count() {
      var names = box.value.split("\n").filter(function (line) { return line.trim(); }).length;
      tally.hidden = names < 2;
      tally.textContent = names > MOST ? names + " names. Add " + MOST + " at most at a time." : names + " names";
      if (names > MOST) tally.dataset.over = "1"; else delete tally.dataset.over;
    }
    if (box) { box.addEventListener("input", count, { signal: life.signal }); count(); }

    return function () { life.abort(); timers.forEach(clearTimeout); };
  });
})();

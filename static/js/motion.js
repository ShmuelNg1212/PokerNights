// Shared motion, on Motion (motion.dev). It only adds: under reduced motion, or if the library
// did not load, on() is false, run() returns null and every caller keeps its plain behaviour.
(function () {
  "use strict";
  var root = document.documentElement, reduce = matchMedia("(prefers-reduced-motion: reduce)");
  var running = [], latest = new WeakMap(), pressed = null, tapped = null;
  // Springs for things a finger touches, eases for things that arrive or leave. DESIGN.md, "Motion system".
  var PRESETS = {
    press: { type: "spring", stiffness: 1200, damping: 50 },
    release: { type: "spring", visualDuration: 0.2, bounce: 0.45 },
    sheet: { type: "spring", visualDuration: 0.3, bounce: 0.14 },
    arrive: { type: "spring", visualDuration: 0.24, bounce: 0.3 },
    leave: { duration: 0.2, ease: [0.4, 0, 1, 1] },
    nudge: { duration: 0.3, ease: "easeOut" },
    pulse: { duration: 0.36, ease: "easeOut" }
  };

  function on() { return !!window.Motion && !reduce.matches; }
  function mark() { root.classList.toggle("motion-on", on()); }

  function run(el, keyframes, preset) {
    if (!el || !on()) return null;
    var controls = window.Motion.animate(el, keyframes, PRESETS[preset] || preset);
    running.push(controls); latest.set(el, controls);
    after(controls, function () { var at = running.indexOf(controls); if (at > -1) running.splice(at, 1); });
    return controls;
  }
  // Calls back when the animation ends or is cut short; at once when there is none.
  function after(controls, done) {
    if (!controls || !controls.finished) { done(); return; }
    controls.finished.then(done, done);
  }
  // A spring as a duration and an easing, for the Web Animations API.
  function timing(preset) {
    if (!on()) return null;
    var found = /^(\d+)ms (.+)$/.exec(String(window.Motion.spring(Object.assign({ keyframes: [0, 1] }, PRESETS[preset]))));
    return found ? { duration: Number(found[1]), easing: found[2] } : null;
  }
  function rest(el, controls) { after(controls, function () { if (latest.get(el) === controls) el.style.transform = ""; }); }

  // Buttons sink under a finger and spring back. Listeners are for the whole tab.
  document.addEventListener("pointerdown", function (event) {
    var button = event.target.closest && event.target.closest(".btn");
    if (!button || button.disabled || !on()) return;
    pressed = tapped = button;
    run(button, { y: 3 }, "press");
  });
  function release() {
    var button = pressed; pressed = null;
    if (button) rest(button, run(button, { y: 0 }, "release"));
  }
  window.addEventListener("pointerup", release);
  window.addEventListener("pointercancel", release);

  // An accepted action settles the control that sent it; a refusal nudges what explains it.
  function refusal() {
    var sheet = document.querySelector("dialog[open]");
    return (sheet || document).querySelector("[aria-invalid=true]") || (sheet && sheet.querySelector(".sheet-error")) ||
      Array.from(document.querySelectorAll(".message-error")).pop();
  }
  function nudge() { var el = refusal(); if (el) rest(el, run(el, { x: [0, -6, 6, -3, 0] }, "nudge")); }
  function answered(failed) {
    // After the other listeners, which place the refusal and close an accepted sheet.
    setTimeout(function () {
      if (failed || document.querySelector(".message-error")) { nudge(); return; }
      var button = tapped; tapped = null;
      if (button && button.isConnected && !button.closest("dialog")) rest(button, run(button, { scale: [1, 1.04, 1] }, "pulse"));
    }, 0);
  }
  document.addEventListener("inplace:updated", function () { answered(false); });
  document.addEventListener("inplace:failed", function () { answered(true); });
  if (reduce.addEventListener) reduce.addEventListener("change", mark);

  window.pokerMotion = { on: on, run: run, after: after, timing: timing };

  window.pokerPage.register(function () {
    mark();
    // A form that came back refused by a full page load.
    if (document.body.dataset.method === "POST" && document.querySelector("#main [aria-invalid=true]")) nudge();
    return function () {
      running.splice(0).forEach(function (controls) { try { controls.cancel(); } catch (_) {} });
      pressed = tapped = null;
    };
  });
})();

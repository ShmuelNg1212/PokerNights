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
    pulse: { duration: 0.36, ease: "easeOut" },
    // The set page (flow.js, changes.js). Rows carry money, so they move without bounce.
    shift: { type: "spring", visualDuration: 0.26, bounce: 0 },
    drop: { type: "spring", visualDuration: 0.22, bounce: 0.35 },
    fade: { duration: 0.18, ease: "easeOut" }
  };

  function on() { return !!window.Motion && !reduce.matches; }
  function mark() { root.classList.toggle("motion-on", on()); }

  // "transform" and "opacity" run in the compositor. The separate x, y and scale are for
  // movements that combine on one element; they get a compositor hint while they run.
  function run(el, keyframes, preset, extra) {
    if (!el || !on()) return null;
    var options = PRESETS[preset] || preset;
    if (extra) options = Object.assign({}, options, extra);
    var separate = "x" in keyframes || "y" in keyframes || "scale" in keyframes;
    if (separate) el.style.willChange = "transform";
    var controls = window.Motion.animate(el, keyframes, options);
    running.push(controls); latest.set(el, controls);
    after(controls, function () {
      var at = running.indexOf(controls); if (at > -1) running.splice(at, 1);
      if (separate && latest.get(el) === controls) el.style.willChange = "";
    });
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
  // Leaves no inline style behind once the element's last animation has ended. Motion writes
  // the final value once more on the frame after it reports the end, so this waits two frames.
  function settle(el, controls, properties) {
    after(controls, function () {
      requestAnimationFrame(function () { requestAnimationFrame(function () {
        if (latest.get(el) === controls) (properties || ["transform"]).forEach(function (name) { el.style[name] = ""; });
      }); });
    });
  }
  function rest(el, controls) { settle(el, controls); }

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

  window.pokerMotion = { on: on, run: run, after: after, settle: settle, timing: timing };

  window.pokerPage.register(function () {
    mark();
    // One thing a page is about arrives: [data-pop] springs in from an already-visible default.
    document.querySelectorAll("[data-pop]").forEach(function (el) {
      settle(el, run(el, { opacity: [0, 1], transform: ["scale(0.6)", "scale(1)"] }, "arrive"), ["opacity", "transform"]);
    });
    // A form that came back refused by a full page load.
    if (document.body.dataset.method === "POST" && document.querySelector("#main [aria-invalid=true]")) nudge();
    return function () {
      running.splice(0).forEach(function (controls) { try { controls.cancel(); } catch (_) {} });
      pressed = tapped = null;
    };
  });
})();

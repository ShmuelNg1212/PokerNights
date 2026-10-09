// The front door: the chip answers what a person does on the log in and sign up screens
// (DESIGN.md, "Front door"). Nothing here is needed for a page to work. The arrival itself is
// CSS (app.css), so it starts on the first paint; this script only ends it early.
(function () {
  "use strict";
  var root = document.documentElement;
  function enabled() { return root.dataset.door === "on"; }

  // The top bar's mark carries the chip's name only for the change from or to the front door.
  // Inside the app the name is given up, so screens there change as they did.
  document.addEventListener("submit", function (event) {
    var action = event.target.getAttribute && event.target.getAttribute("action");
    if (action && /\/logout\/$/.test(action)) delete root.dataset.doorDone;
  });
  // Between two front-door screens the browser moves the chip and the sheet. The new screen's
  // own arrival would play on top of that.
  document.addEventListener("turbo:before-render", function (event) {
    var next = event.detail.newBody.querySelector("[data-arrival]");
    if (next && document.querySelector(".entry-page")) next.removeAttribute("data-arrival");
  });

  window.pokerPage.register(function () {
    var page = document.querySelector(".entry-page"), motion = window.pokerMotion;
    if (!page) { if (enabled()) root.dataset.doorDone = "1"; return; }
    delete root.dataset.doorDone;
    var mark = page.querySelector(".door-mark");
    if (!enabled() || !mark) return;
    var ring = [mark.querySelector(".door-ring"), mark.querySelector(".door-under")], moon = mark.querySelector(".door-moon");
    var life = new AbortController(), on = { signal: life.signal }, turn = 0, spin = [], lengths = new WeakMap();

    // Nothing waits: the first key or tap ends the arrival.
    function arrived() {
      if (!page.dataset.arrival) return;
      page.getAnimations({ subtree: true }).forEach(function (animation) { if (animation.animationName) animation.finish(); });
      delete page.dataset.arrival;
    }
    page.addEventListener("keydown", arrived, on);
    page.addEventListener("pointerdown", arrived, on);

    function turnTo(degrees, preset) {
      ring.forEach(function (part) { motion.run(part, { rotate: degrees }, preset); });
    }
    // Each key turns the ring a little; each delete turns it back. The crescent stays still.
    page.addEventListener("input", function (event) {
      var field = event.target;
      if (!field.matches || !field.matches("input:not([type=hidden])")) return;
      var before = lengths.has(field) ? lengths.get(field) : 0, now = field.value.length;
      lengths.set(field, now);
      if (now === before || spin.length) return;
      turn += Math.max(-3, Math.min(3, now - before)) * 20;
      turnTo(turn, { type: "spring", visualDuration: 0.3, bounce: 0.25 });
    }, on);
    page.querySelectorAll("input:not([type=hidden])").forEach(function (field) { lengths.set(field, field.value.length); });

    // Show tips the crescent, like an eye opening; Hide tips it back. After password.js has changed the field.
    page.addEventListener("click", function (event) {
      var button = event.target.closest && event.target.closest("[data-password-toggle]");
      if (!button) return;
      setTimeout(function () { motion.run(moon, { rotate: button.dataset.shown ? -32 : 0 }, "release"); }, 0);
    }, on);

    // While a form is on its way the ring spins. The page that answers is a new page.
    function stopSpin() {
      spin.splice(0).forEach(function (controls) { try { controls.cancel(); } catch (_) {} });
    }
    page.addEventListener("submit", function (event) {
      setTimeout(function () {
        if (event.defaultPrevented || spin.length || !motion.on()) return;
        ring.forEach(function (part) {
          var controls = motion.run(part, { rotate: [turn, turn + 360] }, { duration: 0.9, ease: "linear", repeat: Infinity });
          if (controls) spin.push(controls);
        });
      }, 0);
    }, on);
    // A page restored by the phone's Back is usable again (forms.js does the same for its button).
    window.addEventListener("pageshow", function (event) { if (event.persisted) { stopSpin(); turnTo(turn, "shift"); } }, on);

    // A page that came back refused: the chip shakes once with the notice.
    if (document.body.dataset.method === "POST" && page.querySelector(".notice-bad")) {
      motion.settle(mark, motion.run(mark, { transform: ["translateX(0px)", "translateX(-6px)", "translateX(6px)", "translateX(-3px)", "translateX(0px)"] }, "nudge"));
    }
    return function () { life.abort(); stopSpin(); };
  });
})();

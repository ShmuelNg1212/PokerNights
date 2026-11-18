// Short vibrations at a few moments (DESIGN.md, "Sheet drag and haptics"). It only adds: where the
// phone has no way to vibrate, or Vibration is switched off in the account menu, play() does nothing.
// Android: navigator.vibrate. iPhone: Safari has no vibration API, but a click on the label of an
// <input type="checkbox" switch> plays the system switch tick. That is not a documented haptics API;
// it may do nothing outside a direct tap. Either way nothing else changes.
(function () {
  "use strict";
  var KEY = "rack-haptics", last = 0, helper = null;
  var PATTERNS = { tick: 8, done: [10, 50, 14], refused: [24, 40, 24] };
  var TICKS = { tick: 1, done: 1, refused: 2 };
  var vibrates = typeof navigator.vibrate === "function";
  var ticks = !vibrates && "switch" in HTMLInputElement.prototype;

  function can() { return vibrates || ticks; }
  function enabled() {
    try { return localStorage.getItem(KEY) !== "off"; } catch (_) { return true; } // storage that fails means on
  }
  function set(on) {
    try { if (on) localStorage.removeItem(KEY); else localStorage.setItem(KEY, "off"); } catch (_) {}
    sync();
  }

  // The iPhone's switch. It sits in the open dialog when there is one: a modal dialog makes the rest of
  // the page inert. It is in no form, hidden from assistive technology, and its clicks and changes stop
  // at the label, so no page listener (the account menu's outside tap, a form's change) sees them.
  function make() {
    var label = document.createElement("label"), input = document.createElement("input");
    label.className = "haptic-switch"; label.dataset.haptic = ""; label.setAttribute("aria-hidden", "true");
    input.type = "checkbox"; input.setAttribute("switch", ""); input.tabIndex = -1;
    label.appendChild(input);
    ["click", "change", "input"].forEach(function (name) {
      label.addEventListener(name, function (event) { event.stopPropagation(); });
    });
    return label;
  }
  function tick() {
    var home = document.querySelector("dialog[open]") || document.body;
    if (!home) return;
    if (!helper) helper = make();
    if (helper.parentNode !== home) home.appendChild(helper);
    var focused = document.activeElement;
    helper.click();
    if (focused && focused !== document.activeElement && focused.focus) focused.focus({ preventScroll: true });
  }

  function play(kind) {
    if (!can() || !enabled() || document.hidden || !(kind in PATTERNS)) return;
    var now = Date.now();
    if (now - last < 60) return;
    last = now;
    try {
      if (vibrates) { navigator.vibrate(PATTERNS[kind]); return; }
      tick();
      if (TICKS[kind] > 1) setTimeout(function () { if (!document.hidden) try { tick(); } catch (_) {} }, 70);
    } catch (_) {}
  }

  // The Vibration switch in the account menu. It is hidden where the phone cannot vibrate.
  function sync() {
    document.querySelectorAll("[data-haptics-switch]").forEach(function (button) {
      button.hidden = !can();
      button.setAttribute("aria-checked", String(enabled()));
    });
  }
  document.addEventListener("click", function (event) {
    var button = event.target.closest && event.target.closest("[data-haptics-switch]");
    if (!button) return;
    var on = !enabled();
    set(on);
    if (on) play("tick"); // switching on says what it does
  });

  window.pokerHaptics = { play: play, can: can, enabled: enabled, set: set };
  window.pokerPage.register(function () {
    sync();
    return function () { if (helper && helper.parentNode) helper.remove(); };
  });
})();

// The account token at the end of the header (#account, a native disclosure, permanent across screen
// changes). Without this script it opens and closes as any <details>; with it, the panel comes from the
// token as the bell's does (it grows from the caret and drops 4px, and leaves faster, upward), and a tap
// outside or Escape closes it. Focus stays on the token: Log out is the next stop for the keyboard.
(function () {
  "use strict";

  function box() { return document.getElementById("account"); }
  function panel(el) { return el.querySelector(".account-panel"); }
  function summary(el) { return el.querySelector(".account-button"); }

  function open(el) {
    if (el.classList.contains("is-open")) return;
    var sheet = panel(el), turning = !!el.dataset.leaving;
    delete el.dataset.leaving;
    el.open = true;
    el.classList.add("is-open");
    // The caret sits under the token's middle, measured from the panel's right edge.
    var from = sheet.getBoundingClientRect().right, at = summary(el).getBoundingClientRect();
    sheet.style.setProperty("--caret", Math.max(16, Math.round(from - (at.left + at.width / 2))) + "px");
    var M = window.pokerMotion;
    if (!M || !M.on() || document.hidden) return;
    // Caught while leaving, it turns back from where it is; otherwise the first keyframe is written
    // before Motion starts (doc/wiki/footguns/motion_starts_a_frame_late.md).
    var rest = { opacity: 1, transform: "translateY(0px) scale(1)" };
    if (!turning) { sheet.style.opacity = "0"; sheet.style.transform = "translateY(-4px) scale(0.96)"; }
    M.settle(sheet, M.run(sheet, turning ? rest : { opacity: [0, 1], transform: ["translateY(-4px) scale(0.96)", rest.transform] }, "shift"), ["opacity", "transform"]);
  }

  function close(el, instant, restore) {
    if (!el.open) return;
    var sheet = panel(el);
    el.classList.remove("is-open");
    el.dataset.leaving = "1";
    function gone() { if (!el.classList.contains("is-open")) { delete el.dataset.leaving; el.open = false; sheet.style.opacity = ""; sheet.style.transform = ""; } }
    var M = window.pokerMotion, leaving = !instant && M && M.on() && !document.hidden ? M.run(sheet, { opacity: 0, transform: "translateY(-4px) scale(0.98)" }, "leave") : null;
    if (leaving) M.after(leaving, gone); else gone();
    if (restore) summary(el).focus({ preventScroll: true });
  }

  // The token survives screen changes, so it is answered here, once, for every page.
  document.addEventListener("click", function (event) {
    var el = box();
    if (!el) return;
    if (!el.contains(event.target)) { close(el); return; }
    if (event.target.closest(".account-button")) {
      event.preventDefault(); // the script, not the browser, opens and closes it, so it can move
      // Open, or opened natively before this script ran: close. Closing: turn back and open.
      if (el.classList.contains("is-open") || (el.open && !el.dataset.leaving)) close(el); else open(el);
    }
  });
  document.addEventListener("keydown", function (event) {
    var el = box();
    if (event.key === "Escape" && el && el.open) { event.preventDefault(); close(el, false, true); }
  });
  // Going to another screen closes it at once; a refresh of the same page (nightlive.js, the set's
  // morph) is a visit to the same path and leaves it open.
  document.addEventListener("turbo:visit", function (event) {
    var el = box();
    if (el && el.open && new URL(event.detail.url, location.href).pathname !== location.pathname) close(el, true);
  });
})();

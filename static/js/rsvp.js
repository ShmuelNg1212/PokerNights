// Who's coming on the session page. It only adds movement: a host's confirmation opens in place
// and the rows under it slide; after an answer, the host's or anyone's, each person glides from
// where they were to where they are now, and the person the host just answered for carries the
// brass mark. Without it the disclosures and forms work as they are.
(function () {
  "use strict";
  var REST = "translateY(0px)", HOLD_MS = 3000, FADE_MS = 400;
  var opening = null, before = null, acted = null, timers = [];

  function moving() { return !!window.pokerMotion && window.pokerMotion.on() && !document.hidden; }
  function board() { return document.querySelector(".rsvp"); }
  // Motion begins on the next frame, so the element is put at its starting point now
  // (doc/wiki/footguns/motion_starts_a_frame_late.md).
  function move(el, keyframes, preset, extra) {
    var M = window.pokerMotion;
    Object.keys(keyframes).forEach(function (name) { el.style[name] = keyframes[name][0]; });
    M.settle(el, M.run(el, keyframes, preset, extra), Object.keys(keyframes));
  }
  // What can move, by a name that survives a redraw: people by member, the rest by their place.
  function key(el) {
    if (el.dataset.person) return "p" + el.dataset.person;
    if (el.dataset.key) return el.dataset.key;
    if (el.classList.contains("rsvp-seats")) return "seats";
    return "t" + el.textContent.trim();
  }
  function parts(root) {
    return root.querySelectorAll(".rsvp-row, .rsvp-group-title, .rsvp-more, .rsvp-seats");
  }
  // Where each part is laid out, whatever an animation is doing to it now. A part inside a closed
  // disclosure has no place.
  function places(root) {
    var found = {};
    parts(root).forEach(function (el) {
      if (!el.getClientRects().length) return;
      var at = el.getBoundingClientRect().top + window.scrollY;
      if (el.style.transform) at -= new DOMMatrix(getComputedStyle(el).transform).m42;
      found[key(el)] = at;
    });
    return found;
  }
  // Every part that was on the page slides from its old place to its new one.
  function slide(root, was) {
    var arrivals = 0;
    parts(root).forEach(function (el) {
      if (!el.getClientRects().length) return;
      var old = was[key(el)];
      if (old === undefined) {
        if (!el.dataset.person || !acted || acted !== el.dataset.person) return;
        move(el, { opacity: [0, 1], transform: ["translateY(12px)", REST] }, "shift", { delay: 0.04 * arrivals++ });
        return;
      }
      var by = old - (el.getBoundingClientRect().top + window.scrollY);
      if (Math.abs(by) > 1 && Math.abs(by) < window.innerHeight * 1.5) move(el, { transform: ["translateY(" + by + "px)", REST] }, "shift");
    });
  }
  function mark(row) {
    timers.splice(0).forEach(clearTimeout);
    document.querySelectorAll(".rsvp-row.just-changed").forEach(function (el) { el.classList.remove("just-changed", "change-fading"); });
    row.classList.add("just-changed");
    timers.push(setTimeout(function () { row.classList.add("change-fading"); }, HOLD_MS - FADE_MS));
    timers.push(setTimeout(function () { row.classList.remove("just-changed", "change-fading"); }, HOLD_MS));
  }

  // A tap on a host's row: note where everything is before the disclosure changes the layout.
  document.addEventListener("click", function (event) {
    var summary = event.target.closest && event.target.closest(".rsvp-host > summary");
    opening = summary && moving() ? places(board()) : null;
  }, true);
  // "toggle" does not bubble, so it is caught on the way down. Opening one row closes another
  // (the disclosures share a name); both toggles come after one tap, and the first one moves.
  document.addEventListener("toggle", function (event) {
    var details = event.target;
    if (!details.matches || !details.matches(".rsvp-host") || !opening) return;
    var was = opening; opening = null;
    if (details.open) {
      var panel = details.querySelector(".rsvp-confirm");
      move(panel, { opacity: [0, 1], transform: ["translateY(-8px)", REST] }, "shift");
      var button = panel.querySelector("button[type=submit]");
      if (button) move(button, { opacity: [0, 1], transform: ["scale(0.96)", "scale(1)"] }, "arrive", { delay: 0.05 });
    }
    slide(board(), was);
  }, true);
  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    var open = document.querySelector(".rsvp-host[open]");
    if (!open || !open.contains(document.activeElement)) return;
    opening = moving() ? places(board()) : null;
    open.open = false;
    open.querySelector("summary").focus();
  });

  // An answer sent from a host's row.
  document.addEventListener("turbo:submit-start", function (event) {
    var form = event.target, member = form.closest(".rsvp-host") && form.querySelector("[name=member]");
    acted = member ? member.value : null;
  });
  // Any redraw of the page, by the host's answer or by the refresh after someone else's.
  document.addEventListener("turbo:before-render", function (event) {
    before = event.detail.renderMethod === "morph" && board() && moving() ? places(board()) : null;
  });
  document.addEventListener("turbo:render", function (event) {
    var was = before, person = acted, root = board();
    before = null;
    if (event.detail.renderMethod !== "morph" || !root) { acted = null; return; }
    var row = person && root.querySelector('.rsvp-row[data-person="' + person + '"]');
    // A redraw keeps a disclosure open (turbo-setup.js); the answered one has done its work.
    if (row) { var open = row.querySelector(".rsvp-host[open]"); if (open) open.open = false; }
    if (was) slide(root, was);
    acted = null;
    if (row) mark(row);
  });
})();

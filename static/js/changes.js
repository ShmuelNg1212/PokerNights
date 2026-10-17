// Highlight accepted server values only. Amounts themselves never interpolate.
(function () {
  "use strict";
  var region = null, prefix = "", seen = {};
  var HOLD_MS = 3000, FADE_MS = 400;
  // With Motion a small thing springs in; without it the CSS animation, or nothing, plays.
  function move(el, keyframes, preset, extra) {
    var M = window.pokerMotion;
    if (!el || !M) return;
    M.settle(el, M.run(el, keyframes, preset, extra), Object.keys(keyframes));
  }
  function pop(el) { move(el, { opacity: [0, 1], transform: ["scale(0.6)", "scale(1)"] }, "arrive"); }
  // The books balancing is a moment, once per set: the rule draws, then the words rise.
  function balanced(el) {
    var rule = window.pokerMotion && window.pokerMotion.timing("sheet");
    if (!rule) return;
    el.style.setProperty("--balance-ms", rule.duration + "ms");
    el.style.setProperty("--balance-ease", rule.easing);
    move(el.querySelector(".books-message"), { opacity: [0, 1], transform: ["translateY(8px)", "translateY(0px)"] }, "shift", { delay: 0.24 });
  }
  // An override covering the difference is not the books balancing, so it gets no reveal.
  function overridden(el) { return el.hasAttribute("data-overridden") || /override/i.test(el.textContent); }
  function update() {
    if (!region) return;
    region.querySelectorAll("[data-balance]").forEach(function (el) {
      if (overridden(el)) return;
      var key = "balanced:" + el.dataset.balance;
      try { if (!localStorage.getItem(key)) { el.classList.add("balance-arrived"); localStorage.setItem(key, "1"); balanced(el); } } catch (_) {}
    });
    // A set coming back to be corrected is a moment too, once per reopening: the brass rule draws, then the reason rises.
    region.querySelectorAll("[data-reopened]").forEach(function (el) {
      var key = "reopened:" + el.dataset.reopened;
      try {
        if (localStorage.getItem(key)) return;
        localStorage.setItem(key, "1");
        el.classList.add("reopen-arrived");
        move(el.querySelector(".correction-text"), { opacity: [0, 1], transform: ["translateY(8px)", "translateY(0px)"] }, "shift", { delay: 0.18 });
      } catch (_) {}
    });
    region.querySelectorAll("[data-watch]").forEach(function (el) {
      var key = prefix + el.dataset.watch, value = el.dataset.value;
      var previous = seen[key];
      try { if (previous === undefined) previous = sessionStorage.getItem(key); } catch (_) {}
      if (previous != null && previous !== value) {
        var was = previous.split(":"), now = value.split(":");
        el.classList.add("just-changed");
        // The badge sits in the line under the name, which the row has twice: in the button
        // that opens the player's sheet and in the plain line shown without it. One is displayed.
        var badges = el.querySelectorAll(".change-label");
        if (badges.length) {
          // A player row: bought in, buy-in count, cashed out, status.
          var rebuy = Number(now[1]) > Number(was[1]);
          badges.forEach(function (badge) {
            badge.textContent = rebuy ? "Rebuy added" : "Updated";
            badge.hidden = false;
            if (badge.getClientRects().length) pop(badge);
          });
          var edge = el.querySelector(".buy-stack i:last-of-type");
          if (edge && rebuy) {
            edge.classList.add("new-edge");
            move(edge, { opacity: [0, 1], transform: ["translateY(-8px)", "translateY(0px)"] }, "drop");
          }
          if (now[3] === "left" && was[3] !== "left") {
            el.classList.add("just-left");
            pop(el.querySelector(".player-identity > .badge:not(.change-label)"));
          }
        }
        // A count row: its status badge.
        var status = el.querySelector("[data-status]");
        if (status && was[0] !== now[0]) pop(status);
        // The mark fades out over its last moments instead of vanishing.
        setTimeout(function () { el.classList.add("change-fading"); }, HOLD_MS - FADE_MS);
        setTimeout(function () { el.classList.remove("just-changed", "change-fading", "just-left"); badges.forEach(function (badge) { badge.hidden = true; }); }, HOLD_MS);
      }
      seen[key] = value;
      try { sessionStorage.setItem(key, value); } catch (_) {}
    });
  }
  // The books gap (DESIGN.md, "Books off: motion"). Both redraws, a poll (live.js) and an action's
  // answer (turbo-setup.js), say "live:updating" before and "live:updated" after, so the panel is
  // read before and compared after. It arrives once per set and amount; when the books then
  // balance, a copy of it leaves from where it stood. The amount never moves through other values.
  var before = null, ghosts = [];
  function still() { return !window.pokerMotion || !window.pokerMotion.on() || document.hidden; }
  function gap() { return region && (region.querySelector("#books-gap") || region.querySelector(".discrepancy")); }
  function gapKey(el) {
    var amount = el.dataset.gap;
    if (amount == null) { var text = el.querySelector(".discrepancy-amount"); amount = text ? text.textContent.trim() : ""; }
    return "gap:" + region.dataset.url + ":" + amount;
  }
  // True the first time this browser sees this amount for this set. Refused storage counts as seen.
  function firstSight(el) {
    try {
      var key = gapKey(el), fresh = !localStorage.getItem(key);
      localStorage.setItem(key, "1");
      return fresh;
    } catch (_) { return false; }
  }
  function clearGhosts() { ghosts.splice(0).forEach(function (ghost) { ghost.remove(); }); }
  // The panel that was there leaves from where it stood while the page already shows the new state.
  function leave(copy, box) {
    copy.removeAttribute("id"); copy.removeAttribute("role");
    copy.setAttribute("aria-hidden", "true"); copy.inert = true;
    copy.classList.add("books-ghost");
    copy.style.left = box.left + "px"; copy.style.top = box.top + "px";
    copy.style.width = box.width + "px"; copy.style.height = box.height + "px";
    // The first keyframe is in place before Motion starts (doc/wiki/footguns/motion_starts_a_frame_late.md).
    copy.style.opacity = "1"; copy.style.transform = "translateY(0px)";
    document.body.appendChild(copy);
    ghosts.push(copy);
    var gone = function () { var at = ghosts.indexOf(copy); if (at > -1) ghosts.splice(at, 1); copy.remove(); };
    var controls = window.pokerMotion.run(copy, { opacity: [1, 0], transform: ["translateY(0px)", "translateY(-4px)"] }, "leave");
    if (!controls) { gone(); return; }
    window.pokerMotion.after(controls, gone);
    setTimeout(gone, 1000);
  }
  document.addEventListener("live:updating", function () {
    before = null;
    if (!region) return;
    var el = gap();
    before = { there: !!el };
    if (el && !still()) { before.box = el.getBoundingClientRect(); before.copy = el.cloneNode(true); }
  });
  function books() {
    var was = before, el = gap();
    before = null;
    if (!was || !region) return;
    if (el) {
      // A changed amount on a panel that stayed is just the new amount.
      if (firstSight(el) && !was.there && !still()) {
        el.style.opacity = "0"; el.style.transform = "translateY(8px)";
        move(el, { opacity: [0, 1], transform: ["translateY(8px)", "translateY(0px)"] }, "shift");
      }
    } else if (was.copy && region.querySelector("[data-balance]") && !still()) {
      leave(was.copy, was.box);
    }
  }

  document.addEventListener("live:updated", function () { books(); update(); });
  document.addEventListener("turbo:before-cache", clearGhosts);
  window.pokerPage.register(function () {
    region = document.getElementById("live");
    if (!region) return;
    prefix = "rack:" + region.dataset.url + ":";
    seen = {};
    before = null;
    // On first sight the gap is simply there; it is noted so that it does not arrive later.
    var el = gap();
    if (el) firstSight(el);
    update();
    return function () { region = null; before = null; clearGhosts(); };
  });
})();

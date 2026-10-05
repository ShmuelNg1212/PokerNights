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
  function update() {
    if (!region) return;
    region.querySelectorAll("[data-balance]").forEach(function (el) {
      var key = "balanced:" + el.dataset.balance;
      try { if (!localStorage.getItem(key)) { el.classList.add("balance-arrived"); localStorage.setItem(key, "1"); balanced(el); } } catch (_) {}
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
  document.addEventListener("live:updated", update);
  window.pokerPage.register(function () {
    region = document.getElementById("live");
    if (!region) return;
    prefix = "rack:" + region.dataset.url + ":";
    seen = {};
    update();
    return function () { region = null; };
  });
})();

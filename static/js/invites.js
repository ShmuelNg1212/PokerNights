// Group settings → Invite players. It only adds: Share where the phone has a share sheet, the new link
// dropping into place, Past invites marked after a revoke, and the disclosure easing open. Copy is
// copy.js's. Without it every link can still be selected and every form still works.
(function () {
  "use strict";
  var HOLD_MS = 3000, FADE_MS = 400;
  window.pokerPage.register(function () {
    var section = document.getElementById("invites"), list = section && section.querySelector("[data-invites]");
    if (!section) return;
    var life = new AbortController(), timers = [], M = window.pokerMotion;
    // Motion begins on the next frame, so the element is put at its starting point now
    // (doc/wiki/footguns/motion_starts_a_frame_late.md).
    function move(el, keyframes, preset, extra) {
      if (!el || !M || !M.on()) return;
      Object.keys(keyframes).forEach(function (name) { el.style[name] = keyframes[name][0]; });
      M.settle(el, M.run(el, keyframes, preset, extra), Object.keys(keyframes));
    }

    if (navigator.share) {
      section.querySelectorAll("[data-invite-share]").forEach(function (button) {
        button.hidden = false;
        button.addEventListener("click", function () {
          // Closing the share sheet rejects; that is an answer, not an error.
          try { navigator.share({ text: button.dataset.inviteText, url: button.dataset.inviteShare }).catch(function () {}); } catch (_) {}
        }, { signal: life.signal });
      });
    }

    // The link just created: it drops into the top of the list, under the person's eye.
    var arrived = list && list.querySelector("[data-arrived]");
    if (arrived) {
      arrived.scrollIntoView({ block: "nearest" });
      move(arrived, { opacity: [0, 1], transform: ["translateY(-12px) scale(.96)", "translateY(0px) scale(1)"] }, "drop");
    }

    // A revoked link is now under Past invites: its summary takes the accepted-change mark.
    var left = section.querySelector(".invites-past[data-changed] > summary");
    if (left) {
      left.classList.add("just-changed");
      move(left, { transform: ["scale(1)", "scale(1.03)", "scale(1)"] }, "pulse");
      timers.push(setTimeout(function () { left.classList.add("change-fading"); }, HOLD_MS - FADE_MS));
      timers.push(setTimeout(function () { left.classList.remove("just-changed", "change-fading"); }, HOLD_MS));
    }

    // "toggle" does not bubble, so it is caught on the way down.
    section.addEventListener("toggle", function (event) {
      var details = event.target;
      if (!details.open || !details.matches || !details.matches("details")) return;
      move(details.querySelector(":scope > :not(summary)"), { opacity: [0, 1], transform: ["translateY(-6px)", "translateY(0px)"] }, "fade");
    }, { capture: true, signal: life.signal });

    return function () { life.abort(); timers.forEach(clearTimeout); };
  });
})();

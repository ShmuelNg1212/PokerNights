// "See the ₱100 difference": the books panel is often already on screen, so the tap leads to
// the record that looks wrong instead. Without this script the link is a plain anchor to #balance.
(function () {
  "use strict";
  var ring = null, timer = 0;

  // The first row whose cash-out differs from its confirmed count, else the discrepancy, else the books.
  function target() {
    // A record that explains the whole gap first, then one that explains part of it, then the books.
    return document.querySelector('#live [data-suspect="full"]') || document.querySelector("#live [data-suspect]") ||
      document.getElementById("books-gap") || document.getElementById("balance");
  }
  // The band a target may sit in: under the sticky header, over whatever is fixed at the bottom.
  function band() {
    var top = 0, bottom = window.innerHeight;
    var header = document.querySelector(".site-header");
    if (header) top = Math.max(0, header.getBoundingClientRect().bottom);
    document.querySelectorAll(".host-controls, .host-controls .next-action").forEach(function (el) {
      if (getComputedStyle(el).position !== "fixed" || !el.getClientRects().length) return;
      bottom = Math.min(bottom, el.getBoundingClientRect().top);
    });
    return { top: top, bottom: bottom };
  }
  function clear() {
    clearTimeout(timer); timer = 0;
    if (ring) { ring.remove(); ring = null; }
  }
  // A Brass ring drawn over the target's own edge, which only fades: a transform on a large
  // panel moves every figure in it, and the ring reads the same on a row and on the whole books.
  function pulse(el) {
    clear();
    var box = el.getBoundingClientRect();
    ring = document.createElement("div");
    ring.className = "gap-ring";
    ring.setAttribute("aria-hidden", "true");
    // 8px clear of the target's edge, so its text does not touch the line, and never past the screen's sides.
    var pad = 8, left = Math.max(4, box.left - pad), right = Math.min(document.documentElement.clientWidth - 4, box.right + pad);
    var radius = parseFloat(getComputedStyle(el).borderTopLeftRadius) || 4;
    ring.style.cssText = "top:" + (box.top - pad + window.scrollY) + "px;left:" + (left + window.scrollX) + "px;width:" + (right - left) + "px;height:" + (box.height + 2 * pad) + "px;border-radius:" + (radius + pad) + "px;opacity:0";
    document.body.appendChild(ring);
    var mine = ring, motion = window.pokerMotion && window.pokerMotion.run(mine, { opacity: [0, 1, 1, 0] }, "pulse", { times: [0, 0.25, 0.6, 1] });
    if (motion) { window.pokerMotion.after(motion, function () { if (ring === mine) clear(); }); return; }
    // Reduced motion, or no Motion: the ring shows still for a moment. Nothing moves.
    mine.style.opacity = "1";
    timer = setTimeout(clear, 900);
  }

  document.addEventListener("click", function (event) {
    var link = event.target.closest && event.target.closest("a[data-books-gap]");
    if (!link || event.defaultPrevented || event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    var el = target();
    if (!el) return; // the anchor does what it can
    event.preventDefault();
    // No record to point at: the tap opens where to look, so it always shows something new.
    var where = !el.hasAttribute("data-suspect") && document.querySelector("#live .discrepancy-where");
    if (where) where.open = true;
    var room = band(), box = el.getBoundingClientRect(), gap = 16;
    var whole = box.top >= room.top && box.bottom <= room.bottom;
    var smooth = window.pokerMotion ? window.pokerMotion.on() : !matchMedia("(prefers-reduced-motion: reduce)").matches;
    // Focus without a scroll of its own, so the page moves once.
    if (!el.hasAttribute("tabindex") && !el.matches("a[href],button,input,select,textarea")) el.setAttribute("tabindex", "-1");
    el.setAttribute("data-gap-focus", "");
    el.focus({ preventScroll: true });
    if (whole) { pulse(el); return; }
    var by = box.top - room.top - gap;
    // A target shorter than the band is centred in it; a taller one starts at its top.
    if (box.height < room.bottom - room.top - 2 * gap) by -= Math.max(0, (room.bottom - room.top - box.height) / 2 - gap);
    var done = false, finish = function () {
      if (done) return; done = true;
      window.removeEventListener("scrollend", finish);
      pulse(el);
    };
    if (!smooth) { window.scrollBy(0, by); finish(); return; }
    window.addEventListener("scrollend", finish);
    window.scrollBy({ top: by, behavior: "smooth" });
    setTimeout(finish, 700); // a browser without scrollend, or a scroll already at its end
  });

  window.pokerPage.register(function () { return clear; });
})();

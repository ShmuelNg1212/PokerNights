// In-flow disclosures use native intrinsic-height motion where supported. Else, keep native
// semantics and animate a measured height. Overlays and RSVP confirmations have their own owner.
(function () {
  "use strict";
  var native = CSS.supports("interpolate-size", "allow-keywords") && CSS.supports("selector(details::details-content)");
  var reduced = matchMedia("(prefers-reduced-motion: reduce)"), active = new Map();

  function eligible(el) {
    return el && el.matches("details") && !el.closest(".account, .rsvp-host, [data-app-link]") && !el.matches(".sheet-source");
  }
  function finish(el, item) {
    if (active.get(el) !== item) return;
    active.delete(el);
    el.open = item.open;
    item.motion.cancel();
    el.style.height = item.height;
    el.style.overflow = item.overflow;
    delete el.dataset.disclosureClosing;
  }
  function finishAll() { active.forEach(function (item, el) { finish(el, item); }); }

  function setOpen(el, open, instant) {
    if (!el) return;
    var previous = active.get(el);
    if (native || !eligible(el) || instant || reduced.matches || document.hidden || !el.animate) {
      if (previous) finish(el, previous);
      el.open = open;
      return;
    }
    if (previous ? previous.open === open : el.open === open) return;
    // Read the current presentation before canceling, so a rapid reversal starts where it is.
    var from = el.getBoundingClientRect().height;
    var item = { open: open, height: previous ? previous.height : el.style.height,
      overflow: previous ? previous.overflow : el.style.overflow };
    if (previous) { active.delete(el); previous.motion.cancel(); }
    el.style.height = item.height;
    el.style.overflow = item.overflow;
    delete el.dataset.disclosureClosing;
    el.open = open;
    var to = el.getBoundingClientRect().height;
    // Hold the content in the document until the close finishes. The marker is its requested
    // closed state: a poll must not remember this temporary open as the person's choice.
    el.open = true;
    if (!open) el.dataset.disclosureClosing = ""; else delete el.dataset.disclosureClosing;
    el.style.height = from + "px";
    el.style.overflow = "hidden";
    active.set(el, item);
    item.motion = el.animate({ height: [from + "px", to + "px"] }, {
      duration: 200, easing: getComputedStyle(el).getPropertyValue("--ease-out").trim()
    });
    item.motion.finished.then(function () { finish(el, item); }, function () { finish(el, item); });
  }

  document.addEventListener("click", function (event) {
    if (native || event.defaultPrevented || !event.target.closest) return;
    var summary = event.target.closest("summary"), el = summary && summary.parentElement;
    if (!eligible(el)) return;
    // A link or field inside the summary still owns its own action.
    var control = event.target.closest("a, button, input, select, textarea, label");
    if (control && summary.contains(control)) return;
    event.preventDefault();
    var item = active.get(el);
    setOpen(el, !(item ? item.open : el.open));
  });
  document.addEventListener("live:updating", finishAll);
  document.addEventListener("visibilitychange", function () { if (document.hidden) finishAll(); });
  reduced.addEventListener("change", finishAll);
  window.pokerDisclosure = { setOpen: setOpen, available: function () { return native || !!Element.prototype.animate; } };
  window.pokerPage.register(function () { return finishAll; });
})();

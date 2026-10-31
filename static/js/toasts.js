// Success messages float as toasts. After an in-place update the page may be scrolled, so
// errors float too; on an ordinary page load they stay at the top where the eye starts.
(function () {
  "use strict";
  function move(el, keyframes, preset) { return window.pokerMotion ? window.pokerMotion.run(el, keyframes, preset) : null; }
  var quietNow = null; // the one quiet toast on screen, if any
  // The newest toast sits lowest; each earlier one is lifted clear of those below it.
  function restack() {
    var lift = 0;
    Array.from(document.querySelectorAll(".toast:not(.leaving):not(.toast-quiet)")).reverse().forEach(function (toast) {
      if (toast.dataset.lift !== String(lift)) {
        toast.dataset.lift = lift;
        if (!move(toast, { y: -lift }, "arrive")) toast.style.transform = lift ? "translateY(" + -lift + "px)" : "";
      }
      lift += toast.offsetHeight + 8;
    });
  }
  function float(message, linger) {
    if (message.classList.contains("toast")) return;
    // A plain success only reports. It sits under the header, a tap goes through it to the page, and
    // that tap also sends it away. A message with something to press stays at the foot with Dismiss.
    var quiet = message.classList.contains("message-success") && !message.querySelector("a, button");
    message.classList.add("toast");
    message.classList.toggle("toast-quiet", quiet);
    message.dataset.lift = "0";
    move(message, { opacity: [0, 1], y: quiet ? [-12, 0] : [16, 0] }, "arrive");
    var timer;
    function dismiss() {
      if (message.classList.contains("leaving")) return;
      clearTimeout(timer);
      message.classList.add("leaving");
      if (quiet) { document.removeEventListener("pointerdown", dismiss, true); if (quietNow === dismiss) quietNow = null; }
      var leaving = move(message, { opacity: 0, y: quiet ? -8 : 12 - Number(message.dataset.lift) }, "leave");
      if (leaving) window.pokerMotion.after(leaving, function () { message.remove(); }); else message.remove();
      restack();
    }
    function resume() { clearTimeout(timer); timer = setTimeout(dismiss, linger); }
    if (quiet) {
      if (quietNow) quietNow();
      quietNow = dismiss;
      document.addEventListener("pointerdown", dismiss, true);
    } else {
      var close = document.createElement("button");
      close.type = "button"; close.className = "btn btn-small btn-quiet"; close.textContent = "Dismiss";
      message.appendChild(close);
      close.addEventListener("click", dismiss);
      message.addEventListener("mouseenter", function () { clearTimeout(timer); });
      message.addEventListener("focusin", function () { clearTimeout(timer); });
      message.addEventListener("mouseleave", resume); message.addEventListener("focusout", resume);
    }
    resume();
    restack();
    return { dismiss: dismiss, renew: resume };
  }
  function list() {
    var found = document.querySelector("#main > .messages");
    if (found) return found;
    found = document.createElement("ul");
    found.className = "messages"; found.setAttribute("role", "status");
    var main = document.getElementById("main");
    main.insertBefore(found, main.firstChild);
    return found;
  }
  // Most successes fit one line; a longer one states a fact worth reading, so it stays longer.
  function successes() { document.querySelectorAll(".message-success").forEach(function (m) { float(m, m.textContent.trim().length > 44 ? 6000 : 3500); }); }
  document.addEventListener("inplace:updated", function (event) {
    successes();
    if (event.detail.form && event.detail.form.closest("dialog")) return; // the sheet shows a refusal beside the field
    document.querySelectorAll(".message-error").forEach(function (m) { m.setAttribute("role", "alert"); float(m, 12000); });
  });
  document.addEventListener("inplace:failed", function (event) {
    if (event.detail.form && event.detail.form.closest("dialog")) return; // the sheet shows it beside the field
    var item = document.createElement("li");
    item.className = "message message-error"; item.setAttribute("role", "alert"); item.textContent = event.detail.message;
    list().appendChild(item);
    float(item, 12000);
  });
  // A toast from a page module: an item it built, floated for `linger` ms. Returns {dismiss, renew}.
  window.pokerToast = function (item, linger) { list().appendChild(item); return float(item, linger); };
  window.pokerPage.register(successes);
})();

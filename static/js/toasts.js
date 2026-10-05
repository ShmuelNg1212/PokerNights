// Success messages float as toasts. After an in-place update the page may be scrolled, so
// errors float too; on an ordinary page load they stay at the top where the eye starts.
(function () {
  "use strict";
  function move(el, keyframes, preset) { return window.pokerMotion ? window.pokerMotion.run(el, keyframes, preset) : null; }
  // The newest toast sits lowest; each earlier one is lifted clear of those below it.
  function restack() {
    var lift = 0;
    Array.from(document.querySelectorAll(".toast:not(.leaving)")).reverse().forEach(function (toast) {
      if (toast.dataset.lift !== String(lift)) {
        toast.dataset.lift = lift;
        if (!move(toast, { y: -lift }, "arrive")) toast.style.transform = lift ? "translateY(" + -lift + "px)" : "";
      }
      lift += toast.offsetHeight + 8;
    });
  }
  function float(message, linger) {
    if (message.classList.contains("toast")) return;
    message.classList.add("toast");
    message.dataset.lift = "0";
    move(message, { opacity: [0, 1], y: [16, 0] }, "arrive");
    var close = document.createElement("button");
    close.type = "button"; close.className = "btn btn-small btn-quiet"; close.textContent = "Dismiss";
    message.appendChild(close);
    var timer;
    function dismiss() {
      if (message.classList.contains("leaving")) return;
      message.classList.add("leaving");
      var leaving = move(message, { opacity: 0, y: 12 - Number(message.dataset.lift) }, "leave");
      if (leaving) window.pokerMotion.after(leaving, function () { message.remove(); }); else message.remove();
      restack();
    }
    function resume() { clearTimeout(timer); timer = setTimeout(dismiss, linger); }
    close.addEventListener("click", dismiss);
    message.addEventListener("mouseenter", function () { clearTimeout(timer); });
    message.addEventListener("focusin", function () { clearTimeout(timer); });
    message.addEventListener("mouseleave", resume); message.addEventListener("focusout", resume);
    resume();
    restack();
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
  function successes() { document.querySelectorAll(".message-success").forEach(function (m) { float(m, 6000); }); }
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
  window.pokerPage.register(successes);
})();

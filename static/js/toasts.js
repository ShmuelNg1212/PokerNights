// Success messages float as toasts. After an in-place update the page may be scrolled, so
// errors float too; on an ordinary page load they stay at the top where the eye starts.
(function () {
  "use strict";
  function float(message, linger) {
    if (message.classList.contains("toast")) return;
    message.classList.add("toast");
    var close = document.createElement("button");
    close.type = "button"; close.className = "btn btn-small btn-quiet"; close.textContent = "Dismiss";
    message.appendChild(close);
    var timer;
    function dismiss() { message.remove(); }
    function resume() { clearTimeout(timer); timer = setTimeout(dismiss, linger); }
    close.addEventListener("click", dismiss);
    message.addEventListener("mouseenter", function () { clearTimeout(timer); });
    message.addEventListener("focusin", function () { clearTimeout(timer); });
    message.addEventListener("mouseleave", resume); message.addEventListener("focusout", resume);
    resume();
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

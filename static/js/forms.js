// Stops a double tap from sending a form twice. The server also refuses a
// repeated request_id, so this is a convenience, not the protection.
(function () {
  "use strict";

  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!form || (form.method || "").toLowerCase() !== "post") return;
    if (form.dataset.sent === "1") {
      event.preventDefault();
      return;
    }
    form.dataset.sent = "1";
    // Disable after the browser has read the clicked button's name and value.
    setTimeout(function () {
      Array.from(form.elements).filter(function (el) { return el.tagName === "BUTTON" && el.type === "submit"; }).forEach(function (button) {
        button.disabled = true;
        button.dataset.label = button.textContent;
        button.textContent = button.dataset.busy || "Sending…";
        button.setAttribute("aria-busy", "true");
      });
    }, 0);
  });

  // A page restored from the back/forward cache must be usable again.
  window.addEventListener("pageshow", function () {
    document.querySelectorAll("form[data-sent]").forEach(function (form) {
      delete form.dataset.sent;
      Array.from(form.elements).filter(function (el) { return el.dataset.label; }).forEach(function (button) { button.disabled = false; if (button.dataset.label) button.textContent = button.dataset.label; button.removeAttribute("aria-busy"); });
    });
  });
})();

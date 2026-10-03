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
      form.querySelectorAll("button[type=submit], button:not([type])").forEach(function (button) {
        button.disabled = true;
        button.dataset.label = button.textContent;
        button.textContent = "Sending…";
        button.setAttribute("aria-busy", "true");
      });
      // Buttons outside the form that submit it through the form attribute.
      if (form.id) {
        document.querySelectorAll('button[form="' + form.id + '"]').forEach(function (button) {
          button.disabled = true;
        button.dataset.label = button.textContent;
        button.textContent = "Sending…";
        button.setAttribute("aria-busy", "true");
        });
      }
    }, 0);
  });

  // A page restored from the back/forward cache must be usable again.
  window.addEventListener("pageshow", function () {
    document.querySelectorAll("form[data-sent]").forEach(function (form) {
      delete form.dataset.sent;
      form.querySelectorAll("button:disabled").forEach(function (button) { button.disabled = false; if (button.dataset.label) button.textContent = button.dataset.label; button.removeAttribute("aria-busy"); });
    });
  });
})();

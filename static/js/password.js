// Lets a person read what they typed in a password field. Without JavaScript the button stays hidden.
(function () {
  "use strict";
  document.querySelectorAll("[data-password-toggle]").forEach(function (button) {
    var form = button.closest("form");
    var fields = Array.from(form.querySelectorAll("input[type=password]"));
    function set(shown) {
      fields.forEach(function (field) { field.type = shown ? "text" : "password"; });
      button.dataset.shown = shown ? "1" : "";
      button.setAttribute("aria-label", (shown ? "Hide" : "Show") + " password");
      button.textContent = shown ? "Hide" : "Show";
    }
    button.hidden = false;
    button.addEventListener("click", function () { set(!button.dataset.shown); });
    // A password is never submitted, saved by the browser or left on screen as plain text.
    form.addEventListener("submit", function () { set(false); });
  });
})();

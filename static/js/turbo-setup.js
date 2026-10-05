// Turbo sends the marked forms in the background and updates the page in place.
// Links are not touched: navigation stays off unless an element says data-turbo="true".
(function () {
  "use strict";
  if (!window.Turbo) return;
  Turbo.session.drive = false;

  var sent = null; // the form whose update is on its way

  document.addEventListener("turbo:submit-start", function (event) { sent = event.target; });

  // An update makes the page match the server. Two things must survive it, as they do
  // across a live poll: text typed in a field that was not part of the form just sent,
  // and a disclosure the person opened.
  function typed(el) {
    if (!el.matches || !el.matches("input[data-keep], textarea[data-keep]")) return false;
    if (sent && el.form === sent) return false;
    if (el.type === "checkbox") return el.checked !== el.defaultChecked;
    return el.hasAttribute("data-count-input") ? el.value.trim() !== "" : el.value !== el.defaultValue;
  }
  document.addEventListener("turbo:before-morph-element", function (event) {
    if (typed(event.target)) event.preventDefault();
  });
  document.addEventListener("turbo:before-morph-attribute", function (event) {
    if (event.detail.attributeName === "open" && event.target.matches("details[data-key]")) event.preventDefault();
  });

  // After the update, tell the page modules. They already know "live:updated".
  document.addEventListener("turbo:render", function () {
    var form = sent;
    sent = null;
    document.dispatchEvent(new CustomEvent("inplace:updated", { detail: { form: form } }));
    var region = document.getElementById("live");
    if (region) region.dispatchEvent(new Event("live:updated", { bubbles: true }));
  });

  // The request never reached the server, or the server failed. Nothing changed; say so and
  // leave the form ready to send again.
  function failed(form, words) {
    sent = null;
    if (form) {
      delete form.dataset.sent;
      form.querySelectorAll("button[type=submit], button:not([type])").forEach(function (button) {
        button.disabled = false; button.removeAttribute("aria-busy");
        if (button.dataset.label) button.textContent = button.dataset.label;
      });
    }
    document.dispatchEvent(new CustomEvent("inplace:failed", { detail: { form: form, message: words } }));
  }
  document.addEventListener("turbo:fetch-request-error", function (event) {
    failed(sent, "That wasn't sent. Check your connection and try again.");
  });
  // A page that is not an in-place update of this one (an error page, or another address)
  // is loaded the ordinary way, so every script starts clean.
  document.addEventListener("turbo:before-fetch-response", function (event) {
    var response = event.detail.fetchResponse;
    if (!sent || !response) return;
    var samePage = new URL(response.location).pathname === window.location.pathname;
    if (response.succeeded && samePage) return;
    event.preventDefault();
    if (response.statusCode >= 500) return failed(sent, "The server could not save that. Nothing changed. Try again.");
    window.location.assign(samePage ? window.location.href : response.location);
  });
})();

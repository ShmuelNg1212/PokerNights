// Turbo changes screens without unloading the page and sends the marked forms in the
// background. Links navigate in the app. A form does so only when it says data-turbo="true";
// every other form posts natively and loads a page, which starts everything afresh.
(function () {
  "use strict";
  if (!window.Turbo) return;
  Turbo.config.forms.mode = "optin";

  // --- Screen changes. A swapped page stops the scripts of the page that is leaving and
  // starts them for the one that arrives (see page.js). An in-place update of the same page
  // ("morph") restarts nothing.
  document.addEventListener("turbo:before-render", function (event) {
    if (event.detail.renderMethod !== "morph") { window.pokerPage.stop(); return; }
    // The same before-event as a live poll (live.js), so flow.js sees both kinds of redraw.
    var region = document.getElementById("live");
    if (region) region.dispatchEvent(new Event("live:updating", { bubbles: true }));
  });
  document.addEventListener("turbo:render", function (event) {
    if (event.detail.renderMethod === "morph") return;
    window.pokerPage.start();
    // A real page load is announced by the browser and starts at the top. A swap is silent,
    // so say the new title once and put focus at the start of the content.
    var announcer = document.getElementById("route-announcer");
    if (announcer) announcer.textContent = document.title;
    var main = document.getElementById("main");
    if (main && !document.querySelector("[autofocus]")) main.focus({ preventScroll: true });
  });

  // A link is fetched when the finger touches it, a moment before the tap completes. Turbo
  // itself prefetches on mouse hover, which a phone only reports together with the tap.
  document.addEventListener("touchstart", function (event) {
    var link = event.target.closest && event.target.closest("a[href]");
    if (link) link.dispatchEvent(new MouseEvent("mouseenter", { bubbles: false }));
  }, { capture: true, passive: true });

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
    if (sent) return failed(sent, "That wasn't sent. Check your connection and try again.");
    // A screen change that could not be fetched: go there the ordinary way, so the service
    // worker can show the offline page. A prefetch that failed is simply forgotten.
    var request = event.detail.request;
    if (request && request.headers && request.headers["X-Sec-Purpose"] === "prefetch") return;
    event.preventDefault();
    if (request && request.url) window.location.assign(request.url.toString());
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

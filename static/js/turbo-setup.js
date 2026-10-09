// Turbo changes screens without unloading the page and sends the marked forms in the
// background. Links navigate in the app. A form does so only when it says data-turbo="true";
// every other form posts natively and loads a page, which starts everything afresh.
(function () {
  "use strict";
  if (!window.Turbo) return;
  Turbo.config.forms.mode = "optin";

  // --- Direction and carried names (DESIGN.md, "Motion between screens"). Where the browser
  // animates a screen change (the View Transition API, which Turbo calls), the stylesheet needs
  // to know which way the change goes, and which elements are the same thing on both screens.
  // Each screen states its depth on <main>; a tapped link that goes deeper or back sets data-go
  // on <html>. The phone's own Back and Forward set nothing, so they keep the plain cross-fade.
  var root = document.documentElement, still = matchMedia("(prefers-reduced-motion: reduce)");
  var tapped = null, action = "advance", leaving = "", carried = [], change = 0;
  document.addEventListener("turbo:click", function (event) { tapped = event.target.closest ? event.target.closest("a[href]") : null; going(tapped); });
  // The tapped link keeps its pressed look until its screen is drawn (app.css, "is-going"). A
  // link that is a button shows the busy line that a sent form shows.
  var waiting = null, waitingTimer = 0;
  function arrived() {
    clearTimeout(waitingTimer);
    if (waiting) { waiting.classList.remove("is-going"); waiting.removeAttribute("aria-busy"); }
    waiting = null;
  }
  function going(link) {
    arrived();
    if (!link) return;
    waiting = link;
    link.classList.add("is-going");
    if (link.matches(".btn")) link.setAttribute("aria-busy", "true");
    waitingTimer = setTimeout(arrived, 8000); // a visit that never came
  }
  document.addEventListener("turbo:load", arrived);
  window.addEventListener("pageshow", arrived);
  document.addEventListener("turbo:before-visit", function () { leaving = window.location.pathname; });
  document.addEventListener("turbo:visit", function (event) { action = event.detail.action; });

  function depth(main) { var value = main.dataset.depth; return value ? Number(value) : null; }
  function words(el) { return el.textContent.replace(/\s+/g, " ").trim(); }
  function carry(from, to, name) {
    [from, to].forEach(function (el) { el.style.viewTransitionName = name; carried.push(el); });
  }
  function settle() {
    root.removeAttribute("data-go");
    carried.splice(0).forEach(function (el) {
      el.style.viewTransitionName = "";
      if (!el.getAttribute("style")) el.removeAttribute("style");
    });
  }
  // The name on the card or row that was tapped, which becomes the next screen's heading.
  function source(link) {
    if (!link || !link.isConnected) return null;
    if (link.matches(".session-link")) return link.querySelector("strong");
    var band = link.closest(".home-band"), card = link.closest(".group-home");
    return (band && band.querySelector(".band-title")) || (card && card.querySelector("h2 a"));
  }
  // Going back: the card or row on the arriving screen that leads to the screen being left.
  function origin(main) {
    var link = Array.from(main.querySelectorAll("a.session-link, .group-home h2 a")).find(function (a) { return a.getAttribute("href") === leaving; });
    return link ? (link.matches(".session-link") ? link.querySelector("strong") : link) : null;
  }
  // A player's chip is carried between a session and one of its sets when it is the only chip
  // of that player in the list on each screen and looks the same on both.
  function chips(from, to) {
    function list(main) {
      var found = {};
      main.querySelectorAll(".night-results .chip[data-m], #live .chip[data-m]").forEach(function (chip) {
        var m = chip.dataset.m;
        found[m] = m in found ? null : chip;
      });
      return found;
    }
    var before = list(from), after = list(to), count = 0;
    Object.keys(before).forEach(function (m) {
      var a = before[m], b = after[m];
      if (!a || !b || count >= 12 || a.className !== b.className || a.textContent !== b.textContent) return;
      var box = a.getBoundingClientRect();
      if (box.bottom < 0 || box.top > window.innerHeight) return;
      carry(a, b, "chip-" + m); count += 1;
    });
  }
  function direct(newBody) {
    settle(); change += 1;
    var link = tapped, from = document.getElementById("main"), to = newBody.querySelector("#main");
    tapped = null;
    if (!document.startViewTransition || still.matches || action === "restore" || !from || !to) return;
    var a = depth(from), b = depth(to), go = null;
    if (a === null || b === null) return;
    if (b > a) go = "deeper"; else if (b < a) go = "back";
    else if (from.dataset.tab && to.dataset.tab && from.dataset.tab !== to.dataset.tab) go = Number(to.dataset.tab) > Number(from.dataset.tab) ? "next" : "prev";
    // The same stats screen with another period, unit or order is not a change of screen. It is
    // swapped at once and stats.js moves what changed.
    else if (from.dataset.stats && from.dataset.stats === to.dataset.stats) { root.dataset.go = "filter"; return; }
    if (!go) return;
    root.dataset.go = go;
    var was = (go === "deeper" && source(link)) || from.querySelector("[data-carry=title]");
    var now = (go === "back" && origin(to)) || to.querySelector("[data-carry=title]");
    if (was && now && words(was) && (words(now).indexOf(words(was)) === 0 || words(was).indexOf(words(now)) === 0)) carry(was, now, "title");
    if ((a === 2 && b === 3) || (a === 3 && b === 2)) chips(from, to);
  }
  // --- Screen changes. A swapped page stops the scripts of the page that is leaving and
  // starts them for the one that arrives (see page.js). An in-place update of the same page
  // ("morph") restarts nothing.
  // The browser photographs the old screen at the moment a transition starts. Turbo's own
  // transition starts before it says what the new screen is, too early to mark what is carried.
  // So the transition starts here, once the markers are set, and Turbo's render waits inside it.
  var drawn = null; // tells the running transition that the new screen is in place
  document.addEventListener("turbo:before-render", function (event) {
    var morph = event.detail.renderMethod === "morph", region = document.getElementById("live");
    // The same before-event as a live poll (live.js), so flow.js sees both kinds of redraw.
    if (morph) { if (region) region.dispatchEvent(new Event("live:updating", { bubbles: true })); }
    else direct(event.detail.newBody);
    var leave = function () { if (!morph) window.pokerPage.stop(); };
    if (!document.startViewTransition || still.matches || root.dataset.go === "filter") { leave(); settle(); return; }
    event.preventDefault();
    var shown = new Promise(function (done) { drawn = done; setTimeout(done, 2000); });
    // The markers stay until the browser reports the whole change finished. Its layers are on
    // screen until then, and a marker removed sooner restarts the old screen's fade: a flash of
    // the previous screen.
    var mine = change, ended = function () { moving = Math.max(0, moving - 1); if (mine === change) settle(); };
    try {
      var transition = document.startViewTransition(function () { leave(); event.detail.resume(); return shown; });
      moving += 1;
      transition.finished.then(ended, ended);
    } catch (_) { leave(); event.detail.resume(); settle(); }
  });
  // Nothing waits for a movement. While one runs, the browser may give a tap to the page itself
  // and report nothing under the finger, so the control is found by its place on the screen and
  // the tap is passed on. Where more than one control is there (a bar over a list), it is left alone.
  var moving = 0;
  function controlAt(x, y) {
    var sheet = document.querySelector("dialog[open]");
    var found = Array.from((sheet || document).querySelectorAll("a[href], button:not(:disabled), summary, label, input:not([type=hidden]), select")).filter(function (el) {
      var box = el.getBoundingClientRect();
      return box.width > 0 && x >= box.left && x <= box.right && y >= box.top && y <= box.bottom && (!el.checkVisibility || el.checkVisibility());
    });
    found = found.filter(function (el) { return !found.some(function (other) { return other !== el && el.contains(other); }); });
    return found.length === 1 ? found[0] : null;
  }
  document.addEventListener("click", function (event) {
    if (!moving || event.target !== root || !event.isTrusted) return;
    var control = controlAt(event.clientX, event.clientY);
    if (control) control.click();
  }, true);
  document.addEventListener("turbo:render", function (event) {
    if (drawn) { drawn(); drawn = null; }
    if (event.detail.renderMethod === "morph") return;
    window.pokerPage.start();
    // A real page load is announced by the browser and starts at the top. A swap is silent,
    // so say the new title once and put focus at the start of the content.
    var announcer = document.getElementById("route-announcer");
    if (announcer) announcer.textContent = document.title;
    var main = document.getElementById("main");
    if (main && !document.querySelector("[autofocus]")) main.focus({ preventScroll: true });
  });

  // A link is fetched when the finger touches it, so the answer is on its way while the finger is
  // still down. Turbo prefetches on mouse hover, which a phone only reports together with the tap,
  // so the touch is passed on as that hover. Turbo then waits 100ms before it sends, in case the
  // mouse is only passing over; a tap is over by then. A finger has arrived, so for the length of
  // this one call Turbo's timer is given no delay. Without this a tap got no head start, and a
  // quick tap asked for the screen twice.
  document.addEventListener("touchstart", function (event) {
    var link = event.target.closest && event.target.closest("a[href]");
    if (!link) return;
    var timer = window.setTimeout;
    window.setTimeout = function (run) { return timer.call(window, run, 0); };
    try { link.dispatchEvent(new MouseEvent("mouseenter", { bubbles: false })); }
    finally { window.setTimeout = timer; }
  }, { capture: true, passive: true });

  var sent = null; // the form whose update is on its way

  document.addEventListener("turbo:submit-start", function (event) { sent = event.target; });

  // One trip instead of two (config/inplace.py). A form sent in the background says which page
  // it was sent from; a view that redirects back to that page is then answered with the page
  // itself. Without the mark on <html> (ANSWER_IN_PLACE=False) nothing is asked for.
  document.addEventListener("turbo:before-fetch-request", function (event) {
    if (root.dataset.inPlace !== "on" || !event.target || event.target.tagName !== "FORM") return;
    if (String(event.detail.fetchOptions.method).toUpperCase() !== "POST") return;
    event.detail.fetchOptions.headers["X-Answer-In-Place"] = window.location.pathname + window.location.search;
  });

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
    if (!response) return;
    // The page itself came back in answer to the form. Turbo expects a redirect here, so its own
    // handling is stopped (which also finishes the submission) and the page is handed to it as a
    // visit that needs no request: the same in-place update a redirect back would have led to.
    var page = response.succeeded && !response.redirected && response.response.headers.get("X-In-Place-Location");
    if (page) {
      event.preventDefault();
      response.responseHTML.then(function (html) {
        Turbo.visit(page, { action: "replace", response: { statusCode: 200, responseHTML: html, redirected: false } });
      });
      return;
    }
    if (!sent) return;
    var samePage = new URL(response.location).pathname === window.location.pathname;
    if (response.succeeded && samePage) return;
    event.preventDefault();
    if (response.statusCode >= 500) return failed(sent, "The server could not save that. Nothing changed. Try again.");
    window.location.assign(samePage ? window.location.href : response.location);
  });
})();

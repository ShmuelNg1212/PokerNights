// The home screen: suggests adding the app after a login on a phone's browser, in the steps that
// fit the phone, and inside the installed app offers a field for a link copied from a chat (a
// phone opens such links in the browser). It reads and writes nothing on the server. Every part
// does nothing unless its checks pass, so a failure leaves the page as it was.
(function () {
  "use strict";
  var DONE = "rack-install", DUE = "rack-install-due";
  var offer = null; // Chrome's kept install event, for the whole tab
  var ua = navigator.userAgent || "";

  function standalone() { return navigator.standalone === true || matchMedia("(display-mode: standalone)").matches; }
  function apple() { return /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1); }
  function phone() { return apple() || /Android/.test(ua) || !!(navigator.userAgentData && navigator.userAgentData.mobile); }
  // The server names a chat app's browser from its user agent (config/chat_browser.py). A page the service
  // worker fetched was asked for with the worker's user agent, so the page's own is read as well.
  function inChat() { return !!document.documentElement.dataset.chatBrowser || /FBAN|FBAV|FB_IAB|Instagram|Line\/|Viber|MicroMessenger/.test(ua); }
  function read(store, key) { try { return store.getItem(key); } catch (_) { return null; } }
  function write(store, key, value) { try { if (value === null) store.removeItem(key); else store.setItem(key, value); return true; } catch (_) { return false; } }
  function part() { return inChat() ? "inapp" : offer ? "install" : apple() ? "ios" : "menu"; }

  window.addEventListener("beforeinstallprompt", function (event) {
    event.preventDefault(); // our sheet asks, not the browser's bar
    offer = event;
    document.dispatchEvent(new CustomEvent("install:offered"));
  });
  window.addEventListener("appinstalled", function () {
    offer = null; write(localStorage, DONE, "done");
    document.dispatchEvent(new CustomEvent("install:done"));
  });

  window.pokerPage.register(function () {
    var dialog = document.getElementById("install-sheet");
    var life = new AbortController(), signal = life.signal, timers = [], opener = null;
    var again = document.querySelector("[data-install-open]"), link = document.querySelector("[data-app-link]");
    var main = document.getElementById("main");

    // The installed app: no suggestion; the link field instead.
    if (standalone()) { if (link) linkField(link, signal); return function () { life.abort(); }; }
    if (!dialog || !dialog.showModal) return;

    function choose() {
      var name = part();
      dialog.querySelectorAll("[data-install-part]").forEach(function (el) { el.hidden = el.dataset.installPart !== name; });
      // On an iPhone the page cannot know the steps were followed, so the person can say so.
      dialog.querySelector("[data-install-done]").hidden = name === "install" || name === "inapp";
      dialog.dataset.part = name;
    }
    function say(text) { dialog.querySelector("[data-install-status]").textContent = text; }
    function open(from) {
      if (dialog.open || document.querySelector("dialog[open]")) return false;
      opener = from || null; say(""); choose();
      dialog.showModal(); dialog.scrollTop = 0;
      if (window.pokerMotion) window.pokerMotion.run(dialog, { transform: ["translateY(" + dialog.offsetHeight + "px)", "translateY(0px)"] }, "sheet");
      var first = dialog.querySelector("[data-install-part]:not([hidden]) .btn") || dialog.querySelector(".install-actions .btn:not([hidden])");
      if (first) first.focus({ preventScroll: true });
      return true;
    }
    function close() {
      if (!dialog.open || dialog.classList.contains("closing")) return;
      var leaving = window.pokerMotion && window.pokerMotion.run(dialog, { transform: "translateY(" + dialog.offsetHeight + "px)" }, "leave");
      function shut() { if (dialog.open) dialog.close(); dialog.classList.remove("closing"); }
      if (leaving) { dialog.classList.add("closing"); window.pokerMotion.after(leaving, shut); window.pokerMotion.settle(dialog, leaving); }
      else shut();
    }
    dialog.addEventListener("close", function () { if (opener && opener.isConnected) opener.focus(); else if (main) main.focus({ preventScroll: true }); }, { signal: signal });
    dialog.addEventListener("cancel", function (event) { event.preventDefault(); close(); }, { signal: signal });
    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) {
        var box = dialog.getBoundingClientRect();
        if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) close();
        return;
      }
      if (event.target.closest("[data-install-close]")) { close(); return; }
      if (event.target.closest("[data-install-done]")) { write(localStorage, DONE, "done"); if (again) again.hidden = true; close(); return; }
      var go = event.target.closest("[data-install-go]");
      if (go) {
        if (!offer) { choose(); return; }
        var kept = offer; offer = null; // the browser lets an event ask once
        try { kept.prompt(); } catch (_) { choose(); return; }
        Promise.resolve(kept.userChoice).then(function (choice) {
          if (signal.aborted) return;
          if (choice && choice.outcome === "accepted") { write(localStorage, DONE, "done"); if (again) again.hidden = true; close(); }
          else choose(); // declined: the menu steps remain
        }, function () {});
        return;
      }
      var copy = event.target.closest("[data-install-copy]");
      if (copy) {
        var address = location.href, done;
        try { done = navigator.clipboard.writeText(address); } catch (_) { say("Copy this address: " + address); return; }
        done.then(function () {
          if (signal.aborted) return;
          copy.textContent = "Copied"; say("Link copied.");
          timers.push(setTimeout(function () { copy.textContent = "Copy link"; }, 2000));
        }, function () { say("Copy this address: " + address); });
      }
    }, { signal: signal });
    document.addEventListener("install:offered", function () { if (dialog.open) choose(); if (again && phone()) again.hidden = false; }, { signal: signal });
    document.addEventListener("install:done", function () { if (again) again.hidden = true; close(); }, { signal: signal });

    var installed = read(localStorage, DONE) === "done";
    if (again && phone() && !installed) {
      again.hidden = false;
      again.addEventListener("click", function () { open(again); }, { signal: signal });
    }

    // A login was just made in this browser: owed once, on the first page that has room for it.
    if (main && main.hasAttribute("data-came-in")) write(sessionStorage, DUE, "1");
    if (phone() && !installed && read(sessionStorage, DUE) === "1" && main && !main.classList.contains("entry-page")) {
      // After the arrival has played; a page that opens its own sheet (the recap) keeps the turn.
      timers.push(setTimeout(function () {
        if (signal.aborted || read(sessionStorage, DUE) !== "1") return;
        if (open(null)) write(sessionStorage, DUE, null);
      }, main.hasAttribute("data-welcome") ? 1100 : 500));
    }
    return function () { life.abort(); timers.forEach(clearTimeout); if (dialog.open) dialog.close(); };
  });

  // Inside the installed app: a pasted PokerNights link opens here.
  function linkField(box, signal) {
    var form = box.querySelector("[data-app-link-form]"), field = form.querySelector("input"), error = form.querySelector("[role=alert]");
    var paste = form.querySelector("[data-app-link-paste]");
    box.hidden = false;
    function refuse(text) { error.textContent = text; error.hidden = false; field.setAttribute("aria-invalid", "true"); field.focus(); }
    function path(text) {
      var found;
      try { found = new URL(text.trim(), location.origin); } catch (_) { return null; }
      if (found.origin !== location.origin) return null;
      return /^\/(join|claim|reset)\/[^/]+\/?$/.test(found.pathname) ? found.pathname : null;
    }
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      error.hidden = true; field.removeAttribute("aria-invalid");
      if (!field.value.trim()) { refuse("Paste the link first."); return; }
      var to = path(field.value);
      if (!to) { refuse("That is not a PokerNights invite, claim or reset link."); return; }
      location.assign(to);
    }, { signal: signal });
    if (navigator.clipboard && navigator.clipboard.readText) {
      paste.hidden = false;
      paste.addEventListener("click", function () {
        navigator.clipboard.readText().then(function (text) { field.value = text; field.focus(); }, function () { field.focus(); });
      }, { signal: signal });
    }
  }
})();

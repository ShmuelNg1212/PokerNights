// Players who arrive at the table on someone else's phone. A row that was not on the set page
// before a redraw is marked as a rebuy is: the brass mark and a badge, "Joined" ("You're in"
// on the viewer's own row), for three seconds, with or without motion; flow.js gives it its
// rise. A redraw by a poll is someone else's change, so it is also said: when no new row is in
// view, a toast names who joined and offers Show; otherwise one line for screen readers. The
// players count draws its brass line. The first sight of a page, and a change of the set's
// state, mark nothing. ARRIVAL_MARKS=False leaves data-arrivals off and this does nothing.
(function () {
  "use strict";
  var HOLD_MS = 3000, FADE_MS = 400, TOAST_MS = 6000;
  var region = null, known = null, state = null, count = null, marked = {}, timers = [], toast = null;

  function rows() { return Array.prototype.slice.call(region.querySelectorAll("li.player-row[data-watch]")); }
  function find(key) { return region && region.querySelector('li.player-row[data-watch="' + key + '"]'); }
  function later(fn, ms) { timers.push(setTimeout(fn, Math.max(0, ms))); }
  function moving() { return !!window.pokerMotion && window.pokerMotion.on() && !document.hidden; }
  function pop(el) {
    var M = window.pokerMotion;
    if (el && M) M.settle(el, M.run(el, { opacity: [0, 1], transform: ["scale(0.6)", "scale(1)"] }, "arrive"), ["opacity", "transform"]);
  }

  // The mark on a row, for as long as `marked` holds its key. A redraw replaces the row, so each
  // redraw puts the mark back on the new one until the time is up.
  function mark(row, fresh) {
    var until = marked[row.dataset.watch];
    row.classList.add("just-changed", "just-arrived");
    row.classList.toggle("change-fading", Date.now() >= until - FADE_MS);
    row.querySelectorAll(".change-label").forEach(function (badge) {
      badge.textContent = row.hasAttribute("data-mine") ? "You’re in" : "Joined";
      badge.hidden = false;
      if (fresh && !document.hidden && badge.getClientRects().length) pop(badge);
    });
  }
  function hold(key) {
    var until = Date.now() + HOLD_MS;
    marked[key] = until;
    later(function () { var row = find(key); if (row && marked[key] === until && row.classList.contains("just-arrived")) row.classList.add("change-fading"); }, HOLD_MS - FADE_MS);
    later(function () {
      if (marked[key] !== until) return;
      delete marked[key];
      var row = find(key);
      if (!row || !row.classList.contains("just-arrived")) return;
      row.classList.remove("just-changed", "change-fading", "just-arrived");
      row.querySelectorAll(".change-label").forEach(function (badge) { badge.hidden = true; });
    }, HOLD_MS);
  }

  // The visible part of the page: under the site header, above a fixed host dock.
  function inView(row) {
    var box = row.getBoundingClientRect(), top = 0, bottom = window.innerHeight;
    var header = document.querySelector(".site-header");
    if (header) top = Math.max(0, header.getBoundingClientRect().bottom);
    var dock = region.querySelector(".host-controls");
    if (dock && getComputedStyle(dock).position === "fixed") bottom = Math.min(bottom, dock.getBoundingClientRect().top);
    return box.top < bottom - box.height / 2 && box.bottom > top + box.height / 2;
  }

  function names(list) {
    if (list.length === 1) return list[0];
    if (list.length <= 3) return list.slice(0, -1).join(", ") + " and " + list[list.length - 1];
    var rest = list.length - 2;
    return list.slice(0, 2).join(", ") + " and " + rest + " others";
  }

  function show(key) {
    var row = find(key);
    if (!row) return;
    var box = row.getBoundingClientRect();
    window.scrollTo({ top: box.top + window.scrollY - window.innerHeight / 3, behavior: moving() ? "smooth" : "auto" });
    hold(key);
    mark(row, true);
    // The row's opener is displayed by CSS once sheets work; its hidden attribute stays.
    var opener = Array.prototype.find.call(row.querySelectorAll(".player-opener"), function (el) { return el.getClientRects().length; });
    if (opener) opener.focus({ preventScroll: true });
  }

  // One toast at a time: a later arrival adds its names to the one already up.
  function tell(arrived) {
    if (!window.pokerToast) return;
    var alive = toast && toast.item.isConnected && !toast.item.classList.contains("leaving");
    if (alive) {
      arrived.forEach(function (row) { if (toast.names.indexOf(row.dataset.name) < 0) toast.names.push(row.dataset.name); });
      toast.words.textContent = names(toast.names) + " joined";
      toast.handle.renew();
      return;
    }
    var item = document.createElement("li"), words = document.createElement("span"), button = document.createElement("button");
    item.className = "message message-arrival";
    words.textContent = names(arrived.map(function (row) { return row.dataset.name; })) + " joined";
    button.type = "button"; button.className = "btn btn-small"; button.textContent = "Show";
    item.appendChild(words); item.appendChild(button);
    var first = arrived[0].dataset.watch;
    toast = { item: item, words: words, names: arrived.map(function (row) { return row.dataset.name; }) };
    toast.handle = window.pokerToast(item, TOAST_MS);
    button.addEventListener("click", function () { if (toast && toast.handle) toast.handle.dismiss(); show(first); });
  }

  function say(text) {
    var news = document.getElementById("arrival-news");
    if (!news) return;
    news.textContent = "";
    requestAnimationFrame(function () { news.textContent = text; });
  }

  function counted() {
    var el = region.querySelector("[data-player-count]");
    return el ? el.dataset.playerCount : null;
  }

  function update(event) {
    if (!region) return;
    var poll = !!(event && event.detail && event.detail.poll);
    var now = {}, arrived = [], same = region.dataset.state === state;
    rows().forEach(function (row) {
      var key = row.dataset.watch;
      now[key] = true;
      if (same && !known[key]) { arrived.push(row); hold(key); mark(row, true); return; }
      if (marked[key]) {
        // A change of its own since (a buy-in) is marked by changes.js; that mark wins.
        if (row.classList.contains("just-changed")) delete marked[key]; else mark(row, false);
      }
    });
    var total = counted();
    if (same && count !== null && total !== null && total !== count) {
      region.querySelectorAll("[data-player-count]").forEach(function (el) {
        el.classList.add("count-arrived");
        later(function () { el.classList.add("change-fading"); }, HOLD_MS - FADE_MS);
        later(function () { el.classList.remove("count-arrived", "change-fading"); }, HOLD_MS);
      });
    }
    known = now; state = region.dataset.state; count = total;
    // Polls stop while the tab is hidden; a redraw seen by nobody announces nothing.
    if (!poll || !arrived.length || document.hidden) return;
    var mine = arrived.filter(function (row) { return row.hasAttribute("data-mine"); });
    var others = arrived.filter(function (row) { return !row.hasAttribute("data-mine"); });
    if (mine.length) say("You were added to this set.");
    if (!others.length) return;
    if (others.some(inView)) say(names(others.map(function (row) { return row.dataset.name; })) + " joined the set.");
    else tell(others); // the toast's list speaks for itself (role status)
  }

  document.addEventListener("live:updated", update);
  window.pokerPage.register(function () {
    region = document.getElementById("live");
    if (!region || region.dataset.arrivals !== "on") { region = null; return; }
    known = {}; marked = {}; toast = null;
    rows().forEach(function (row) { known[row.dataset.watch] = true; });
    state = region.dataset.state; count = counted();
    return function () { timers.forEach(clearTimeout); timers = []; region = null; toast = null; };
  });
})();

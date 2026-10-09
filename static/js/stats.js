// The Stats tab and a player's page. It only adds: a session can be read off the chart by touch,
// pointer or arrow keys; the Month list shows its month as soon as one is picked; and rows glide to
// their new places when the period, unit or order changes, with the page staying where it was
// scrolled. Every page is complete without it.
(function () {
  "use strict";
  var KEY = "stats:places";

  function chart(root, life) {
    var plot = root.querySelector("[data-chart-plot]"), bars = Array.from(root.querySelectorAll(".chart-bar"));
    var cross = root.querySelector("[data-chart-cross]"), dot = root.querySelector("[data-chart-dot]"), say = root.querySelector("[data-chart-say]");
    var at = -1;
    if (!plot || !bars.length || !say) return;
    function show(index) {
      index = Math.max(0, Math.min(bars.length - 1, index));
      if (index === at) return;
      if (at > -1) bars[at].classList.remove("is-on");
      at = index;
      var bar = bars[at];
      bar.classList.add("is-on");
      cross.style.left = dot.style.left = bar.dataset.x + "%";
      dot.style.top = bar.dataset.y + "%";
      cross.hidden = dot.hidden = false;
      say.textContent = bar.dataset.say;
      say.classList.add("is-on");
    }
    function from(event) {
      var box = plot.getBoundingClientRect();
      show(Math.floor((event.clientX - box.left) / box.width * bars.length));
    }
    plot.addEventListener("pointerdown", from, { signal: life.signal });
    plot.addEventListener("pointermove", function (event) { if (event.pointerType === "mouse" || event.buttons) from(event); }, { signal: life.signal });
    root.addEventListener("keydown", function (event) {
      var step = { ArrowLeft: -1, ArrowRight: 1 }[event.key];
      if (step) show(at < 0 ? bars.length - 1 : at + step);
      else if (event.key === "Home") show(0);
      else if (event.key === "End") show(bars.length - 1);
      else return;
      event.preventDefault();
    }, { signal: life.signal });
  }

  // Where each ranked row sat, taken as the order is about to change and spent on the next board.
  function places(list) {
    var top = list.getBoundingClientRect().top, found = {};
    list.querySelectorAll("[data-member]").forEach(function (row) { found[row.dataset.member] = Math.round(row.getBoundingClientRect().top - top); });
    return found;
  }
  function glide(list) {
    var M = window.pokerMotion, before;
    try { before = JSON.parse(sessionStorage.getItem(KEY) || "null"); sessionStorage.removeItem(KEY); } catch (_) { return; }
    // Where the browser carries rows between screens itself (turbo-setup.js), it has already moved them.
    if (!before || !M || !M.on() || document.startViewTransition) return;
    var now = places(list);
    list.querySelectorAll("[data-member]").forEach(function (row) {
      var was = before[row.dataset.member], delta = was == null ? 0 : was - now[row.dataset.member];
      if (delta) M.settle(row, M.run(row, { transform: ["translateY(" + delta + "px)", "translateY(0px)"] }, "shift"));
      else if (was == null) M.settle(row, M.run(row, { opacity: [0, 1] }, "fade"), ["opacity"]);
    });
  }

  // A change of period, unit or order is the same screen, so the page stays where it was scrolled.
  // Turbo starts every new address at the top; for these visits it is told the scrolling is done,
  // and the place is set again once the screen is in, in case the new one is shorter.
  var held = null;
  function hold() { held = { path: location.pathname, y: window.scrollY }; }
  document.addEventListener("turbo:click", function (event) {
    if (event.target.closest && event.target.closest("[data-stat-nav] a")) hold(); else held = null;
  });
  document.addEventListener("turbo:submit-start", function (event) {
    if (event.target.matches && event.target.matches("[data-stat-month]")) hold();
  });
  document.addEventListener("turbo:visit", function (event) {
    if (!held) return;
    if (new URL(event.detail.url, location.href).pathname !== held.path) { held = null; return; }
    try { window.Turbo.navigator.currentVisit.scrolled = true; } catch (_) {}
  });
  document.addEventListener("turbo:load", function () {
    if (!held) return;
    if (Math.abs(window.scrollY - held.y) > 1) window.scrollTo(0, held.y);
    held = null;
  });

  window.pokerPage.register(function () {
    var life = new AbortController();
    document.querySelectorAll("[data-chart]").forEach(function (root) { chart(root, life); });
    var month = document.querySelector("[data-stat-month]");
    if (month) {
      month.classList.add("is-auto");
      month.querySelector("select").addEventListener("change", function () { month.requestSubmit(); }, { signal: life.signal });
    }
    var list = document.querySelector("[data-stat-board]");
    if (list) {
      glide(list);
      document.querySelectorAll("[data-stat-nav]").forEach(function (nav) {
        nav.addEventListener("click", function (event) {
          if (!event.target.closest("a")) return;
          try { sessionStorage.setItem(KEY, JSON.stringify(places(list))); } catch (_) {}
        }, { signal: life.signal });
      });
    }
    return function () { life.abort(); };
  });
})();

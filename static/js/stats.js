// The Stats tab and a player's page. It only adds: a session can be read off the chart by touch,
// pointer or arrow keys; the Month list shows its month as soon as one is picked; and a change of
// period, unit or order keeps the page where it was scrolled and shows what changed: the chosen
// pill's marker slides over, new figures slide in from the side that was tapped toward, and rows
// glide to their new places. Every page is complete without it.
(function () {
  "use strict";

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

  // --- A change of period, unit or order. It is a new address, and the same screen.
  // What the screen looked like when a pill was tapped is held until the new one is in.
  var held = null;
  function choices(group) { return Array.from(group.querySelectorAll("a, select")); }
  function chosen(group) { return group.querySelector("[aria-current], select[data-chosen]"); }
  function places(list) {
    var top = list.getBoundingClientRect().top, found = {};
    list.querySelectorAll("[data-member]").forEach(function (row) { found[row.dataset.member] = Math.round(row.getBoundingClientRect().top - top); });
    return found;
  }
  function hold(control) {
    var group = control.closest("[data-stat-pills]"), was = group && chosen(group), list = document.querySelector("[data-stat-board]");
    var box = was && was.getBoundingClientRect();
    held = {
      path: location.pathname, y: window.scrollY, group: group ? group.dataset.statPills : "",
      from: was ? choices(group).indexOf(was) : -1, to: group ? choices(group).indexOf(control) : -1,
      box: box ? { left: box.left, top: box.top, width: box.width } : null, places: list ? places(list) : null
    };
  }
  document.addEventListener("turbo:click", function (event) {
    var link = event.target.closest && event.target.closest("[data-stat-nav] a");
    if (link) hold(link); else held = null;
  });
  document.addEventListener("turbo:submit-start", function (event) {
    if (event.target.matches && event.target.matches("[data-stat-month]")) hold(event.target.querySelector("select"));
  });
  // Turbo starts every new address at the top. For these visits it is told the scrolling is done,
  // and the place is set again once the screen is in, in case the new one is shorter.
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

  function arrived(was) {
    var M = window.pokerMotion;
    if (!M || !M.on()) return;
    function move(el, keyframes, preset, extra) { if (el) M.settle(el, M.run(el, keyframes, preset, extra), Object.keys(keyframes)); }
    // The marker slides from the pill that was chosen to the one that is.
    var group = document.querySelector('[data-stat-pills="' + was.group + '"]'), now = group && chosen(group);
    var marker = now && now.querySelector(".pill-marker");
    if (marker && was.box) {
      var box = now.getBoundingClientRect();
      move(marker, { transform: [
        "translate(" + (was.box.left - box.left) + "px, " + (was.box.top - box.top) + "px) scaleX(" + (was.box.width / box.width) + ")",
        "translate(0px, 0px) scaleX(1)"
      ] }, "sheet");
    }
    var list = document.querySelector("[data-stat-board]"), body = document.querySelector("[data-stat-body]");
    if (was.group === "sort" && list && was.places) {
      // The same players in another order: each row travels from where it was.
      var top = places(list);
      list.querySelectorAll("[data-member]").forEach(function (row) {
        var before = was.places[row.dataset.member], delta = before == null ? 0 : before - top[row.dataset.member];
        if (delta) move(row, { transform: ["translateY(" + delta + "px)", "translateY(0px)"] }, "shift");
        else if (before == null) move(row, { opacity: [0, 1] }, "fade");
      });
    } else if (body) {
      // Other figures altogether: they come in from the side that was tapped toward.
      var side = was.to < was.from ? -1 : 1;
      move(body, { opacity: [0, 1], transform: ["translateX(" + side * 32 + "px)", "translateX(0px)"] }, "shift");
    }
  }

  window.pokerPage.register(function () {
    var life = new AbortController();
    document.querySelectorAll("[data-chart]").forEach(function (root) { chart(root, life); });
    var month = document.querySelector("[data-stat-month]");
    if (month) {
      month.classList.add("is-auto");
      month.querySelector("select").addEventListener("change", function () { month.requestSubmit(); }, { signal: life.signal });
    }
    if (held && held.path === location.pathname) arrived(held);
    return function () { life.abort(); };
  });
})();

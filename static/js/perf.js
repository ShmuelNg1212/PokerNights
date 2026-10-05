// A readout of how long things take, for a screenshot from a phone. Off unless asked for:
// "?perf=1" on any address turns it on for this tab, "?perf=0" turns it off. After each tap it
// shows the wait for the server, the time to draw and to finish moving, the server's own
// figures (config/timing.py) and the frames that came late. It measures and changes nothing.
(function () {
  "use strict";
  var KEY = "pn-perf", asked = /[?&]perf=([01])(&|$)/.exec(window.location.search);
  try {
    if (asked) { if (asked[1] === "1") sessionStorage.setItem(KEY, "1"); else sessionStorage.removeItem(KEY); }
    if (sessionStorage.getItem(KEY) !== "1") return;
  } catch (_) { return; }

  var root = document.documentElement, SLOW_MS = 25, QUIET_MS = 700, LINES = 5;
  var box = document.createElement("pre"), lines = [];
  var served = {};                 // what the server said about each address, also for a page fetched ahead of the tap
  var tap = null;                  // the tap being followed: {at, label, answered, drawn, server, frames, slow, worst, last}
  box.className = "perf-readout"; box.setAttribute("aria-hidden", "true");
  // Outside <body>, so a screen change does not remove it.
  root.appendChild(box);

  function ms(value) { return Math.round(value); }
  function say(line) { lines.push(line); lines = lines.slice(-LINES); box.textContent = lines.join("\n"); }
  // "app;dur=41.2, db;dur=18.0;desc="15 queries", connect;dur=6.1" as "server 41 db 18 (15q) open 6".
  function server(header) {
    var found = {};
    (header || "").split(",").forEach(function (part) {
      var name = part.trim().split(";")[0], dur = /dur=([\d.]+)/.exec(part), desc = /desc="(\d+)/.exec(part);
      if (name) found[name] = { dur: dur ? Number(dur[1]) : 0, count: desc ? desc[1] : "" };
    });
    if (!found.app) return "";
    return "server " + ms(found.app.dur) + " db " + ms(found.db ? found.db.dur : 0) + " (" + (found.db ? found.db.count : "?") + "q) open " + ms(found.connect ? found.connect.dur : 0);
  }
  function moving() {
    return root.hasAttribute("data-go") || document.getAnimations().some(function (one) { return one.playState === "running" && one.effect && one.effect.getComputedTiming().iterations !== Infinity; });
  }
  function finish(now) {
    var done = tap, parts = [done.label];
    tap = null;
    if (done.answered !== null) {
      parts.push("wait " + (done.ahead ? "0 (fetched ahead)" : ms(done.answered - done.at)));
      if (done.drawn !== null) parts.push("draw " + ms(done.drawn - done.answered), "move " + ms(now - done.drawn));
      parts.push("= " + ms(now - done.at) + "ms");
      if (done.server) parts.push("| " + done.server);
    }
    parts.push("| late " + done.slow + "/" + done.frames + " worst " + ms(done.worst));
    say(parts.join(" "));
  }
  // One loop while a tap is followed: it counts late frames and notices when everything has stopped.
  function frame(now) {
    if (!tap) return;
    if (tap.last) { var gap = now - tap.last; tap.frames += 1; if (gap > SLOW_MS) tap.slow += 1; if (gap > tap.worst) tap.worst = gap; }
    tap.last = now;
    var waiting = tap.expects && tap.drawn === null && now - tap.at < 10000;
    if (!waiting && now - Math.max(tap.at, tap.drawn || 0) > QUIET_MS && !moving()) { finish(tap.stopped || now); return; }
    if (!moving() && !waiting) { if (!tap.stopped) tap.stopped = now; } else tap.stopped = 0;
    requestAnimationFrame(frame);
  }
  document.addEventListener("click", function (event) {
    var el = event.target.closest && event.target.closest("a[href], button, summary, [data-sheet-open]");
    if (!el) return;
    var label = el.getAttribute("href") || el.getAttribute("aria-label") || el.textContent.replace(/\s+/g, " ").trim();
    var following = !!tap;
    tap = { at: performance.now(), label: label.slice(0, 22), expects: false, ahead: false, answered: null, drawn: null, server: "", frames: 0, slow: 0, worst: 0, last: 0, stopped: 0 };
    if (!following) requestAnimationFrame(frame);
  }, true);
  // A screen change or a form sent in the background: the tap now waits for the server.
  function expecting() { if (tap) tap.expects = true; }
  document.addEventListener("turbo:visit", expecting);
  document.addEventListener("turbo:submit-start", expecting);
  document.addEventListener("turbo:before-fetch-response", function (event) {
    var response = event.detail.fetchResponse, said = server(response.response.headers.get("Server-Timing"));
    served[new URL(response.response.url).pathname] = said;
    // The first answer after the tap is the tap's. One that came before it was fetched ahead.
    if (tap && tap.answered === null) { tap.answered = performance.now(); tap.server = said; }
  });
  document.addEventListener("turbo:render", function () {
    if (!tap) return;
    tap.drawn = performance.now();
    if (tap.answered === null) {
      // Shown from the page fetched when the finger touched the link.
      tap.answered = tap.at; tap.ahead = true; tap.server = served[window.location.pathname] || "";
    }
  });

  // The first line: how this document itself arrived.
  window.addEventListener("load", function () {
    var nav = performance.getEntriesByType("navigation")[0];
    if (!nav) return;
    var header = (nav.serverTiming || []).map(function (one) { return one.name + ";dur=" + one.duration + (one.description ? ';desc="' + one.description + '"' : ""); }).join(", ");
    say("load: first byte " + ms(nav.responseStart) + " ready " + ms(nav.domContentLoadedEventEnd) + "ms | " + server(header));
  });
})();

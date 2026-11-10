// A stage: a short moment played over a page that is already complete (the set start overture, the session
// finale). It is a div in #table-sheets, outside the live region, because a poll morphs #live and removes
// inline styles there. Any tap or key, or a hidden tab, ends it in the same frame. One stage at a time.
// taken() tells the scripts that redraw a page or open a sheet that the screen is not theirs yet: a stage is
// up, or the tap or key that ended one is not over.
(function () {
"use strict";
var current = null, held = 0, root = document.documentElement, SWALLOW_MS = 350;

function at(point, scale, turn) {
  return "translate(" + point.x.toFixed(1) + "px, " + point.y.toFixed(1) + "px) scale(" + (scale === undefined ? 1 : scale) + ")" + (turn ? " rotate(" + turn + "deg)" : "");
}
function centre(el) { var r = el.getBoundingClientRect(); return {x: r.left + r.width / 2, y: r.top + r.height / 2, w: r.width, h: r.height}; }

// A key that ends a stage does only that: Enter or Space must not also press the focused control.
function key(event) {
  if (event.key === "Enter" || event.key === " ") event.preventDefault();
  if (current) current.finish(event);
}
function skip(event) { if (current) current.finish(event); }

// options: name (the class), html, hide (an attribute set on <html> while it plays), guard (ms after which it
// ends whatever happened), end (called in the frame it ends), then (called when the tap or key that ended it
// is over, so that what comes next is not pressed by it; at once when nothing was pressed).
function open(options) {
  var M = window.pokerMotion;
  if (current || !M || !M.on() || document.hidden) return null;
  var el = document.createElement("div");
  el.className = options.name; el.setAttribute("aria-hidden", "true");
  el.innerHTML = options.html;
  (document.getElementById("table-sheets") || document.body).appendChild(el);
  var controls = [], timers = [];
  var me = current = {el: el};
  me.live = function () { return current === me; };
  // The first keyframe is written before Motion starts (doc/wiki/footguns/motion_starts_a_frame_late.md).
  me.run = function (node, frames, preset, extra) {
    Object.keys(frames).forEach(function (name) { node.style[name] = frames[name][0]; });
    var running = M.run(node, frames, preset, extra);
    if (running) controls.push(running);
  };
  me.later = function (ms, act) { timers.push(setTimeout(act, ms)); };
  // Ends the stage at once, from any point: the page underneath is already complete.
  me.finish = function (event) {
    if (current !== me) return;
    current = null;
    timers.forEach(clearTimeout);
    controls.forEach(function (running) { try { running.stop(); } catch (_) {} });
    document.removeEventListener("pointerdown", skip, true);
    document.removeEventListener("keydown", key, true);
    document.removeEventListener("visibilitychange", skip);
    if (options.hide) root.removeAttribute(options.hide);
    if (options.end) options.end();
    // What comes next runs once, when the press that ended the stage is over. Until then the screen is taken.
    var over = false; held += 1;
    var then = function () {
      if (over) return;
      over = true; held -= 1;
      document.removeEventListener("keydown", hold, true);
      if (options.then) options.then();
    };
    // A key that is held repeats: it still presses nothing.
    var hold = function (again) { if (again.key === "Enter" || again.key === " ") again.preventDefault(); };
    var press = event && event.type;
    // A skipping tap must not become a tap on the page: the stage stays, unseen, for the click that follows.
    // A tap that is cancelled (a drag) sends no click, so the stage also goes then, and after 350ms at most.
    if (press === "pointerdown" && el.contains(event.target)) {
      el.classList.add("is-gone");
      var gone = function () { el.remove(); then(); };
      el.addEventListener("click", gone, {once: true});
      document.addEventListener("pointercancel", gone, {once: true, capture: true});
      setTimeout(gone, SWALLOW_MS);
      return;
    }
    el.remove();
    // A tap that the browser reports elsewhere (on <html> during a screen change, or on something above the
    // stage) is not ours to swallow, but what comes next still waits until its click has been sent.
    if (press === "pointerdown") {
      var after = function () { setTimeout(then, 0); };
      document.addEventListener("click", after, {once: true, capture: true});
      document.addEventListener("pointercancel", after, {once: true, capture: true});
      setTimeout(then, SWALLOW_MS);
    // A key is still down: what comes next waits for it to come up, so Space does not press it.
    } else if (press === "keydown") {
      document.addEventListener("keydown", hold, true);
      document.addEventListener("keyup", then, {once: true, capture: true});
      setTimeout(then, SWALLOW_MS);
    } else then();
  };
  // A guard first: whatever happens to the caller, the page is never left covered or hidden.
  me.later(options.guard || 4000, function () { me.finish(); });
  if (options.hide) root.setAttribute(options.hide, "");
  document.addEventListener("pointerdown", skip, true);
  document.addEventListener("keydown", key, true);
  document.addEventListener("visibilitychange", skip);
  return me;
}

window.pokerStage = {open: open, at: at, centre: centre, taken: function () { return !!current || held > 0; }};
})();

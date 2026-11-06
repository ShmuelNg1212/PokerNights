// The start of a set (DESIGN.md, "Set start overture"). table.js decides that the set has just started on
// this phone, once per set and browser, and calls play(). The page under the stage is already the running
// set, with every figure at its accepted value: the stage only adds a short overture over it and goes.
// The stage lives in #table-sheets, outside the live region, because a poll morphs #live and removes
// inline styles there. The row tokens, the title's "Set N" and the badge are hidden by an attribute on
// <html> while it plays. Any tap or key, or a hidden tab, ends it in the same frame.
(function () {
"use strict";
var S = null;
var OUT = [0.16, 1, 0.3, 1], INOUT = [0.55, 0, 0.2, 1];
var EXIT_AT = 1300, FLY = 0.46, LAND_GAP = 0.028, CHIP = 44, DISC = 64;
var HIDE = "data-overture";

function motion() { return window.pokerMotion; }
// The first keyframe is written before Motion starts (doc/wiki/footguns/motion_starts_a_frame_late.md).
function run(el, frames, options, extra) {
  Object.keys(frames).forEach(function (name) { el.style[name] = frames[name][0]; });
  var controls = motion().run(el, frames, options, extra);
  if (controls) S.controls.push(controls);
}
function at(point, scale, turn) {
  return "translate(" + point.x.toFixed(1) + "px, " + point.y.toFixed(1) + "px) scale(" + (scale === undefined ? 1 : scale) + ")" + (turn ? " rotate(" + turn + "deg)" : "");
}
function centre(el) { var r = el.getBoundingClientRect(); return {x: r.left + r.width / 2, y: r.top + r.height / 2, w: r.width, h: r.height}; }
function later(ms, act) { S.timers.push(setTimeout(act, ms)); }

// What the page says, read once: the players in the order the chips take, the dealer if a draw seated
// one, the set's label and the blinds. Nothing on the stage says what the page does not.
function read(region) {
  var rows = Array.prototype.slice.call(region.querySelectorAll(".player-row"));
  var tokens = rows.map(function (row) { return row.querySelector(".chip"); }).filter(Boolean);
  var byMember = {};
  tokens.forEach(function (token) { if (token.dataset.m) byMember[token.dataset.m] = token; });
  var order = [], dealer = null, seated = region.querySelector('[data-seats][data-state="seated"]');
  if (seated) {
    seated.querySelectorAll(".seat-order > li .chip").forEach(function (chip, index) {
      var token = byMember[chip.dataset.m];
      if (!token || order.indexOf(token) > -1) return;
      order.push(token);
      if (!index) dealer = token;
    });
  }
  tokens.forEach(function (token) { if (order.indexOf(token) < 0) order.push(token); });
  var label = region.querySelector('[data-carry="title"] small'), badge = region.querySelector(".badge-live");
  var blinds = region.querySelector(".pot-side > div:last-child strong");
  return {order: order, dealer: dealer, label: label, badge: badge, set: label ? label.textContent.trim() : "", blinds: blinds ? blinds.textContent.trim() : ""};
}

function build(page) {
  var stage = document.createElement("div");
  stage.className = "overture"; stage.setAttribute("aria-hidden", "true");
  stage.innerHTML = '<span class="ov-ground"></span><span class="ov-pool"></span><span class="ov-ring"></span>' +
    '<p class="ov-set"></p><p class="ov-call">Shuffle up and deal</p><p class="ov-facts"></p><p class="ov-skip">Tap to skip</p><span class="ov-disc">D</span>';
  var count = page.order.length;
  stage.querySelector(".ov-set").textContent = page.set;
  stage.querySelector(".ov-facts").textContent = count + " player" + (count === 1 ? "" : "s") + (page.blinds ? " · Blinds " + page.blinds : "");
  (document.getElementById("table-sheets") || document.body).appendChild(stage);
  return stage;
}

// Ends the overture at once, from any point: the page underneath is already complete.
function finish(event) {
  if (!S) return;
  var me = S; S = null;
  me.timers.forEach(clearTimeout);
  me.controls.forEach(function (controls) { try { controls.stop(); } catch (_) {} });
  document.removeEventListener("pointerdown", finish, true);
  document.removeEventListener("keydown", finish, true);
  document.removeEventListener("visibilitychange", finish);
  document.documentElement.removeAttribute(HIDE);
  // A skipping tap must not become a tap on the page: the stage stays, unseen, to take the click that follows.
  if (event && event.type === "pointerdown" && me.stage.contains(event.target)) {
    me.stage.classList.add("is-gone");
    var gone = function () { me.stage.remove(); };
    me.stage.addEventListener("click", gone, {once: true});
    setTimeout(gone, 600);
  } else me.stage.remove();
}

function play(region) {
  var M = motion();
  if (S || !region || !M || !M.on() || document.hidden || document.querySelector("dialog[open]")) return;
  var page = read(region);
  if (!page.label) return;
  var stage = build(page);
  S = {stage: stage, controls: [], timers: []};
  document.documentElement.setAttribute(HIDE, "");
  document.addEventListener("pointerdown", finish, true);
  document.addEventListener("keydown", finish, true);
  document.addEventListener("visibilitychange", finish);

  var width = window.innerWidth, height = window.innerHeight, mid = {x: width / 2, y: height * 0.44};
  var rx = Math.min(150, width * 0.36), ry = Math.min(150, height * 0.18);
  function ring(angle, reach) { return {x: mid.x + Math.cos(angle) * rx * (reach || 1), y: mid.y + Math.sin(angle) * ry * (reach || 1)}; }
  var q = function (name) { return stage.querySelector(name); };
  var ground = q(".ov-ground"), pool = q(".ov-pool"), burst = q(".ov-ring"), title = q(".ov-set"), call = q(".ov-call"), facts = q(".ov-facts"), hint = q(".ov-skip"), disc = q(".ov-disc");

  // The room dims to a pool of felt; the dealer button drops and turns to rest; one Brass ring opens from it.
  run(ground, {opacity: [0, 1]}, {duration: 0.24, ease: OUT});
  run(pool, {opacity: [0, 1], transform: ["scale(0.3)", "scale(1)"]}, "sheet");
  run(disc, {transform: [at(mid, 0.2, -620), at(mid, 1, 0)]}, {duration: 0.64, ease: OUT});
  run(disc, {opacity: [0, 1]}, {duration: 0.2, ease: OUT});
  run(burst, {opacity: [0.9, 0], transform: [at(mid, 0.7), at(mid, 3.4)]}, {duration: 0.64, ease: OUT, delay: 0.62});
  run(title, {opacity: [0, 1], transform: ["scale(1.5)", "scale(1)"]}, "arrive", {delay: 0.5});
  run(call, {opacity: [0, 1], transform: ["translateY(8px)", "translateY(0px)"]}, "shift", {delay: 0.56});
  run(facts, {opacity: [0, 1]}, "fade", {delay: 0.66});
  run(hint, {opacity: [0, 1]}, "fade", {delay: 0.3});

  // Each chip sweeps in from outside the ring, 45ms apart, then they all circle the button a little.
  var chips = page.order.map(function (token, index) {
    var chip = token.cloneNode(true); chip.removeAttribute("data-m"); chip.classList.add("ov-chip"); stage.appendChild(chip);
    var start = 0.14 + index * 0.045, angle = -Math.PI / 2 + index * 2 * Math.PI / page.order.length, steps = 6, sweep = 0.7;
    var path = [at(ring(angle - 0.9, 2.4), 0.6)], times = [0], ease = [OUT], arrive = 0.44, length = EXIT_AT / 1000 - start;
    for (var step = 0; step <= steps; step++) {
      path.push(at(ring(angle + sweep * step / steps)));
      times.push((arrive + (length - arrive) * step / steps) / length);
      if (step < steps) ease.push("linear");
    }
    run(chip, {transform: path}, {duration: length, times: times, ease: ease, delay: start});
    run(chip, {opacity: [0, 1]}, {duration: 0.2, ease: OUT, delay: start});
    return {el: chip, token: token, from: path[path.length - 1]};
  });

  // Everything goes to its place on the page. Targets are measured now, not at the start: a poll may
  // have moved the rows since. A row under the host dock or off the screen takes its chip behind that edge.
  later(EXIT_AT, function () {
    if (!S || S.stage !== stage) return;
    var dock = document.querySelector(".host-controls"), floor = height;
    if (dock && getComputedStyle(dock).position === "fixed") floor = dock.getBoundingClientRect().top;
    run(ground, {opacity: [1, 0]}, {duration: 0.36, ease: OUT, delay: 0.06});
    run(pool, {opacity: [1, 0], transform: ["scale(1)", "scale(2.6)"]}, {duration: 0.4, ease: OUT});
    run(call, {opacity: [1, 0]}, {duration: 0.16, ease: "easeOut"});
    run(facts, {opacity: [1, 0]}, {duration: 0.16, ease: "easeOut"});
    run(hint, {opacity: [1, 0]}, {duration: 0.16, ease: "easeOut"});
    chips.forEach(function (chip, index) {
      var to = centre(chip.token), delay = index * LAND_GAP;
      if (to.y > floor - 12) to = {x: to.x, y: floor + 10, w: CHIP * 0.8, gone: true};
      else if (to.y < 0) to = {x: to.x, y: -30, w: CHIP * 0.8, gone: true};
      run(chip.el, {transform: [chip.from, at(to, to.w / CHIP)]}, {duration: FLY, ease: INOUT, delay: delay});
      if (to.gone) run(chip.el, {opacity: [1, 0]}, {duration: 0.16, ease: "easeOut", delay: delay + FLY - 0.16});
    });
    var label = centre(page.label), own = centre(title);
    run(title, {transform: ["translate(0px, 0px) scale(1)", "translate(" + (label.x - own.x).toFixed(1) + "px, " + (label.y - own.y).toFixed(1) + "px) scale(" + (label.h / own.h).toFixed(3) + ")"]}, {duration: FLY, ease: INOUT});
    // The button goes to the dealer a draw seated; without a draw it goes into the badge and claims nobody.
    var home = page.dealer ? centre(page.dealer) : page.badge ? centre(page.badge) : mid;
    if (page.dealer) home = {x: home.x + home.w * 0.42, y: home.y - home.h * 0.36, w: 22};
    else home.w = Math.min(home.h || 22, 22);
    // A dealer under the dock or off the screen: the button goes behind that edge, as the chips do.
    var hidden = !page.dealer || home.y > floor - 12 || home.y < 0;
    if (page.dealer && home.y > floor - 12) home.y = floor + 10;
    else if (page.dealer && home.y < 0) home.y = -30;
    run(disc, {transform: [at(mid, 1, 0), at(home, home.w / DISC, 360)]}, {duration: FLY, ease: INOUT});
    if (hidden) run(disc, {opacity: [1, 0]}, {duration: 0.14, ease: "easeOut", delay: FLY - 0.14});
    later((FLY + Math.max(0, chips.length - 1) * LAND_GAP) * 1000 + 40, finish);
  });
  // A guard: whatever happens to the timers above, the page is never left hidden.
  later(4000, finish);
}

window.pokerOverture = {play: play, finish: finish};
window.pokerPage.register(function () { return finish; });
})();

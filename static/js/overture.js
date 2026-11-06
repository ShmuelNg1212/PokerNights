// The start of a set (DESIGN.md, "Set start overture"). table.js decides that the set has just started on
// this phone, once per set and browser, and calls play(). The page under the stage is already the running
// set, with every figure at its accepted value: the stage only adds a short overture over it and goes.
// The stage lives in #table-sheets, outside the live region, because a poll morphs #live and removes
// inline styles there. The row tokens, the title's "Set N" and the badge are hidden by an attribute on
// <html> while it plays. Any tap or key, or a hidden tab, ends it in the same frame.
(function () {
"use strict";
var S = null, pending = null;
var OUT = [0.16, 1, 0.3, 1], INOUT = [0.55, 0, 0.2, 1];
var EXIT_AT = 1300, FLY = 0.46, LAND_GAP = 0.028, CHIP = 44, DISC = 64, WAIT_FOR_SHEET_MS = 30000;
var HIDE = "data-overture", LIT = "data-felt-lit", LIT_MS = 760, lit = null;

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

// What the page says now: the players in the order the chips take, the dealer if a draw seated one, the
// set's label, the badge and the blinds. Read at the start and again when the chips fly, since a poll may
// have replaced the nodes in between. Nothing on the stage says what the page does not.
function read(region) {
  var tokens = Array.prototype.slice.call(region.querySelectorAll(".player-row .chip"));
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
  var label = region.querySelector('[data-carry="title"] small'), blinds = region.querySelector('[data-fact="blinds"]');
  return {order: order, byMember: byMember, dealer: dealer, label: label, badge: region.querySelector(".badge-live"),
    set: label ? label.textContent.trim() : "", blinds: blinds ? blinds.textContent.trim() : ""};
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

// A key that ends the overture does only that: Enter or Space must not also press the focused control.
function key(event) {
  if (event.key === "Enter" || event.key === " ") event.preventDefault();
  finish(event);
}
// Ends the overture at once, from any point: the page underneath is already complete.
function finish(event) {
  if (pending) { pending.dialog.removeEventListener("close", pending.go); pending = null; }
  if (!S) return;
  var me = S; S = null;
  me.timers.forEach(clearTimeout);
  me.controls.forEach(function (controls) { try { controls.stop(); } catch (_) {} });
  document.removeEventListener("pointerdown", finish, true);
  document.removeEventListener("keydown", key, true);
  document.removeEventListener("visibilitychange", finish);
  document.documentElement.removeAttribute(HIDE);
  // A skipping tap must not become a tap on the page: the stage stays, unseen, for the click that follows.
  // A tap that is cancelled (a drag) sends no click, so the stage also goes then, and after 350ms at most.
  if (event && event.type === "pointerdown" && me.stage.contains(event.target)) {
    me.stage.classList.add("is-gone");
    var gone = function () { me.stage.remove(); };
    me.stage.addEventListener("click", gone, {once: true});
    document.addEventListener("pointercancel", gone, {once: true, capture: true});
    setTimeout(gone, 350);
  } else me.stage.remove();
}

// The felt lights as the overture lands: one Brass ring spreads from the badge and one band of light crosses
// the cloth behind it (app.css, "data-felt-lit"). It is CSS keyed on <html>, because a poll morphs #live and
// removes inline styles there. The ring starts at the badge's place on the felt and reaches its farthest corner.
// Only an overture that played to its landing lights the felt: a skip clears this timer with the others.
function light(region) {
  var felt = region.isConnected && region.querySelector(".felt");
  if (!felt || document.hidden) return;
  var box = felt.getBoundingClientRect();
  if (box.bottom <= 0 || box.top >= window.innerHeight || !box.width) return;
  var badge = region.querySelector(".badge-live"), from = badge ? centre(badge) : {x: box.left + box.width / 2, y: box.top + box.height / 2};
  var x = from.x - box.left, y = from.y - box.top;
  var reach = Math.max(Math.hypot(x, y), Math.hypot(box.width - x, y), Math.hypot(x, box.height - y), Math.hypot(box.width - x, box.height - y));
  unlight();
  var root = document.documentElement;
  root.style.setProperty("--lit-x", x.toFixed(1) + "px");
  root.style.setProperty("--lit-y", y.toFixed(1) + "px");
  root.style.setProperty("--lit-r", Math.ceil(reach) + "px");
  root.setAttribute(LIT, "");
  // A full replacement of the felt would start the light again on the new node: it stops instead.
  var replaced = function () { if (lit && region.querySelector(".felt") !== felt) unlight(); };
  document.addEventListener("live:updated", replaced);
  lit = {timer: setTimeout(unlight, LIT_MS), replaced: replaced};
}
function unlight() {
  if (!lit) return;
  clearTimeout(lit.timer);
  document.removeEventListener("live:updated", lit.replaced);
  lit = null;
  var root = document.documentElement;
  root.removeAttribute(LIT);
  ["--lit-x", "--lit-y", "--lit-r"].forEach(function (name) { root.style.removeProperty(name); });
}

// A sheet or the seat draw stage has the screen: the overture waits until it is closed, for a while.
function waitFor(dialog, region) {
  if (pending) return;
  var since = Date.now();
  pending = {dialog: dialog, go: function () {
    pending = null;
    if (Date.now() - since > WAIT_FOR_SHEET_MS || !region.isConnected || region.dataset.state !== "running") return;
    setTimeout(function () { play(region); }, 0);
  }};
  dialog.addEventListener("close", pending.go, {once: true});
}

function play(region) {
  var M = motion();
  if (S || !region || !M || !M.on() || document.hidden) return;
  var sheet = document.querySelector("dialog[open]");
  if (sheet) { waitFor(sheet, region); return; }
  var page = read(region);
  if (!page.label) return;
  S = {stage: build(page), controls: [], timers: []};
  // A guard first: whatever happens below, the page is never left hidden.
  later(4000, finish);
  document.documentElement.setAttribute(HIDE, "");
  document.addEventListener("pointerdown", finish, true);
  document.addEventListener("keydown", key, true);
  document.addEventListener("visibilitychange", finish);
  try { perform(region, page); } catch (_) { finish(); }
}

function perform(region, page) {
  var stage = S.stage, width = window.innerWidth, height = window.innerHeight, mid = {x: width / 2, y: height * 0.44};
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

  // Each chip sweeps in from outside the ring, then they all circle the button a little. The stagger is 45ms
  // and shrinks for a large table, so the last chip still has its full arrival before the chips fly.
  var count = page.order.length, gap = Math.min(0.045, 0.36 / Math.max(1, count - 1)), arrive = 0.44;
  var chips = page.order.map(function (token, index) {
    var chip = token.cloneNode(true); chip.removeAttribute("data-m"); chip.classList.add("ov-chip"); stage.appendChild(chip);
    var start = 0.14 + index * gap, angle = -Math.PI / 2 + index * 2 * Math.PI / count, steps = 6, sweep = 0.7;
    var path = [at(ring(angle - 0.9, 2.4), 0.6)], times = [0], ease = [OUT], length = EXIT_AT / 1000 - start;
    for (var step = 0; step <= steps; step++) {
      path.push(at(ring(angle + sweep * step / steps)));
      times.push((arrive + (length - arrive) * step / steps) / length);
      if (step < steps) ease.push("linear");
    }
    run(chip, {transform: path}, {duration: length, times: times, ease: ease, delay: start});
    run(chip, {opacity: [0, 1]}, {duration: 0.2, ease: OUT, delay: start});
    return {el: chip, member: token.dataset.m, from: path[path.length - 1]};
  });

  // Everything goes to its place on the page, measured now from what the page says now. A row under the
  // host dock or off the screen takes its chip, or the button, behind that edge.
  later(EXIT_AT, function () {
    if (!S || S.stage !== stage) return;
    try { leave(); } catch (_) { finish(); }
  });
  function leave() {
    var now = read(region), dock = document.querySelector(".host-controls"), floor = height;
    if (dock && getComputedStyle(dock).position === "fixed") floor = dock.getBoundingClientRect().top;
    function edge(point) {
      if (point.y > floor - 12) return {x: point.x, y: floor + 10, w: point.w, gone: true};
      if (point.y < 0) return {x: point.x, y: -30, w: point.w, gone: true};
      return point;
    }
    run(ground, {opacity: [1, 0]}, {duration: 0.36, ease: OUT, delay: 0.06});
    run(pool, {opacity: [1, 0], transform: ["scale(1)", "scale(2.6)"]}, {duration: 0.4, ease: OUT});
    [call, facts, hint].forEach(function (el) { run(el, {opacity: [1, 0]}, {duration: 0.16, ease: "easeOut"}); });
    chips.forEach(function (chip, index) {
      var token = now.byMember[chip.member], delay = index * LAND_GAP;
      // A player no longer on the page: the chip fades where it is.
      if (!token) { run(chip.el, {opacity: [1, 0]}, {duration: 0.2, ease: "easeOut", delay: delay}); return; }
      var to = edge(centre(token));
      run(chip.el, {transform: [chip.from, at(to, (to.gone ? 0.8 * CHIP : to.w) / CHIP)]}, {duration: FLY, ease: INOUT, delay: delay});
      if (to.gone) run(chip.el, {opacity: [1, 0]}, {duration: 0.16, ease: "easeOut", delay: delay + FLY - 0.16});
    });
    if (now.label) {
      var label = centre(now.label), own = centre(title);
      run(title, {transform: ["translate(0px, 0px) scale(1)", "translate(" + (label.x - own.x).toFixed(1) + "px, " + (label.y - own.y).toFixed(1) + "px) scale(" + (label.h / own.h).toFixed(3) + ")"]}, {duration: FLY, ease: INOUT});
    } else run(title, {opacity: [1, 0]}, {duration: 0.16, ease: "easeOut"});
    // The button goes to the dealer a draw seated; without a draw it goes into the badge and claims nobody.
    var dealer = page.dealer && now.byMember[page.dealer.dataset.m], home, hidden = true;
    if (dealer) {
      var token = centre(dealer);
      home = edge({x: token.x + token.w * 0.42, y: token.y - token.h * 0.36, w: 22});
      hidden = !!home.gone;
    } else if (now.badge) {
      var badge = centre(now.badge);
      home = {x: badge.x, y: badge.y, w: Math.min(badge.h || 22, 22)};
    } else home = {x: mid.x, y: mid.y, w: 22};
    run(disc, {transform: [at(mid, 1, 0), at(home, home.w / DISC, 360)]}, {duration: FLY, ease: INOUT});
    if (hidden) run(disc, {opacity: [1, 0]}, {duration: 0.14, ease: "easeOut", delay: FLY - 0.14});
    // The button is home: the felt lights from the badge.
    later(FLY * 1000, function () { light(region); });
    later((FLY + Math.max(0, chips.length - 1) * LAND_GAP) * 1000 + 40, finish);
  }
}

window.pokerOverture = {play: play, finish: finish};
window.pokerPage.register(function () { return function () { finish(); unlight(); }; });
})();

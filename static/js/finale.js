// The end of a session (DESIGN.md, "Session finale"). sheets.js decides that the recap opens by itself, once
// per session and viewer, and calls play() first. The players' chips slide into one stack, the top result
// lands last under a Brass ring, "That's the night" stamps in and stays to be read. Then the stage goes, and only
// then does the recap rise: the sheet never covers the finale (the human, 2026-11-10).
// The page under the stage is the closed session, with every figure at its accepted value. play() calls
// done exactly once: when the stage has gone, on a skip, or at once when the finale cannot play.
(function () {
"use strict";
var S = null;
var OUT = [0.16, 1, 0.3, 1], LIFT = 6, STACK = 84, GAP = 0.03, LAST_START = 0.16, RING_AT = 340, LEAVE_AT = 1100, FADE = 0.16;
var STAGE = '<span class="ov-ground"></span><span class="ov-ring"></span><p class="ov-call">That’s the night</p>';

// The players' chips as the recap draws them. The top result is what the page marks (data-top): nothing
// is worked out here. The others take the order of their members, not of their results: a stack does not
// rank a loss.
function read(region) {
  var rest = [], top = [];
  region.querySelectorAll("[data-recap] [data-recap-bars] > li").forEach(function (line) {
    var chip = line.querySelector(".chip");
    if (chip) (line.hasAttribute("data-top") ? top : rest).push(chip);
  });
  rest.sort(function (a, b) { return (Number(a.dataset.m) || 0) - (Number(b.dataset.m) || 0); });
  return {chips: rest.concat(top), top: top.length};
}

function play(region, done) {
  var called = false, left = false;
  function due() { if (called) return; called = true; if (!left) done(); }
  var St = window.pokerStage, page = St && read(region);
  if (!page || !page.chips.length) { due(); return; }
  var stage = St.open({name: "finale", html: STAGE, guard: 2500, end: function () { S = null; }, then: due});
  if (!stage) { due(); return; }
  S = stage; stage.leave = function () { left = true; stage.finish(); };
  try { perform(stage, page); } catch (_) { stage.finish(); }
}

function perform(stage, page) {
  var at = window.pokerStage.at, el = stage.el, count = page.chips.length;
  var mid = {x: window.innerWidth / 2, y: window.innerHeight * 0.44};
  var lift = Math.min(LIFT, STACK / Math.max(1, count - 1)), gap = Math.min(GAP, LAST_START / Math.max(1, count - 1));
  var ground = el.querySelector(".ov-ground"), ring = el.querySelector(".ov-ring"), call = el.querySelector(".ov-call");
  var foot = mid.y + (count - 1) * lift / 2, moving = [ground, call];

  stage.run(ground, {opacity: [0, 1]}, {duration: 0.16, ease: OUT});
  page.chips.forEach(function (token, index) {
    var chip = token.cloneNode(true), home = {x: mid.x, y: foot - index * lift};
    chip.removeAttribute("data-m"); chip.classList.add("ov-chip");
    if (index >= count - page.top) chip.classList.add("fi-top");
    el.appendChild(chip); moving.push(chip);
    stage.run(chip, {transform: [at({x: home.x, y: home.y + 110}, 0.8), at(home)]}, "shift", {delay: index * gap});
    stage.run(chip, {opacity: [0, 1]}, {duration: 0.12, ease: OUT, delay: index * gap});
  });
  stage.run(call, {opacity: [0, 1], transform: ["scale(1.5)", "scale(1)"]}, "arrive", {delay: 0.2});
  // One Brass ring opens from the top of the stack, only when somebody finished ahead.
  if (page.top) {
    var crown = {x: mid.x, y: foot - (count - 1) * lift};
    // Started by a timer, not by a delay: the first keyframe is written at once, and the ring is not there yet.
    stage.later(RING_AT, function () { stage.run(ring, {opacity: [0.9, 0], transform: [at(crown, 0.5), at(crown, 2.2)]}, {duration: 0.3, ease: OUT}); });
  }
  // The whole picture holds, then the stage fades and goes. Its end is what opens the recap (then: due).
  stage.later(LEAVE_AT, function () {
    if (!stage.live()) return;
    moving.forEach(function (part) { stage.run(part, {opacity: [1, 0]}, {duration: FADE, ease: "easeOut"}); });
  });
  stage.later(LEAVE_AT + FADE * 1000 + 20, function () { stage.finish(); });
}

window.pokerFinale = {play: play};
// A page that is left takes its stage with it, and opens nothing.
window.pokerPage.register(function () { return function () { if (S) S.leave(); }; });
})();

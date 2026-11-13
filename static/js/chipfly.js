// Chip to the pot (DESIGN.md, "Chip to the pot"). When a rebuy or a later buy-in is accepted during play, one
// chip in the player's colour goes from the player's row to the pot; when a cash-out is accepted, one goes
// from the pot to the row. It shows that money moved and counts nothing: the pot and the row already show
// the accepted figures (pot.js, changes.js). Only a change seen by this page view counts, so the values are
// kept in memory, not in storage. The chips fly in a layer in #table-sheets, outside the live region, because
// a poll morphs #live and removes inline styles there. The layer takes no pointer events: a chip never
// stops a tap. Without Motion, under reduced motion, in a hidden tab or after an error nothing is added.
(function () {
"use strict";
var region = null, seen = null, state = null, layer = null, off = false, timers = [], pending = null;
var FLY = 0.36, FADE = 0.12, GAP_MS = 60, MOST = 4, SHEET_MS = 400, CHIP = 44, SMALL = 0.5, EASE = [0.55, 0, 0.2, 1];

// What each player's row says now: "bought in : buy-ins : cashed out : status".
function values() {
  var found = {};
  region.querySelectorAll(".player-row[data-watch]").forEach(function (row) { found[row.dataset.watch] = row.dataset.value; });
  return found;
}
function forget() {
  if (!pending) return;
  clearTimeout(pending.timer);
  pending.dialog.removeEventListener("close", pending.go);
  pending = null;
}
function clear() {
  forget();
  timers.splice(0).forEach(clearTimeout);
  if (layer) { layer.remove(); layer = null; }
}
function later(ms, act) {
  var id = setTimeout(function () { timers.splice(timers.indexOf(id), 1); act(); }, ms);
  timers.push(id);
}

// The rows whose buy-ins or cashed-out amount went up since this page view last looked. A row seen for the
// first time, and a figure that went down (a reversal), move no chip.
function moved(was, now) {
  var list = [];
  Object.keys(now).forEach(function (key) {
    if (was[key] === undefined || was[key] === now[key]) return;
    var a = was[key].split(":"), b = now[key].split(":");
    if (Number(b[1]) > Number(a[1])) list.push({key: key, toPot: true});
    else if (Number(b[2]) > Number(a[2])) list.push({key: key, toPot: false});
  });
  return list;
}

// One chip, measured now from what the page says now. An end under the host dock or off the screen is
// that edge, and the chip fades there (the overture's rule). Two ends out of sight: no chip.
function fly(move) {
  var S = window.pokerStage, M = window.pokerMotion;
  if (!region || !region.isConnected || !M.on() || document.hidden || S.taken() || document.querySelector("dialog[open]")) return;
  var row = Array.prototype.filter.call(region.querySelectorAll(".player-row[data-watch]"), function (el) { return el.dataset.watch === move.key; })[0];
  var token = row && row.querySelector(".chip"), figure = region.querySelector('.pot-main[data-watch="in-play"] .display-amount');
  if (!token || !figure || !token.getClientRects().length || !figure.getClientRects().length) return;
  var dock = document.querySelector(".host-controls"), floor = window.innerHeight;
  if (dock && getComputedStyle(dock).position === "fixed") floor = dock.getBoundingClientRect().top;
  var seat = S.centre(token), pot = S.centre(figure), size = seat.w / CHIP;
  if (seat.y > floor - 12) seat = {x: seat.x, y: floor + 10, gone: true};
  else if (seat.y < 0) seat = {x: seat.x, y: -30, gone: true};
  if (pot.y < 0 || pot.y > floor) pot = {x: pot.x, y: -30, gone: true};
  if (seat.gone && pot.gone) return;
  if (seat.gone) size = 0.8;

  if (!layer || !layer.isConnected) {
    layer = document.createElement("div");
    layer.className = "chipfly"; layer.setAttribute("aria-hidden", "true");
    (document.getElementById("table-sheets") || document.body).appendChild(layer);
  }
  var chip = token.cloneNode(true), home = layer;
  chip.removeAttribute("data-m"); chip.classList.add("fly-chip");
  // The chip is seen at each end that is on the screen, except at the pot, where it is small and faint.
  var path = move.toPot ? [S.at(seat, size), S.at(pot, SMALL)] : [S.at(pot, SMALL), S.at(seat, size)];
  var edge = FADE / FLY, shown = move.toPot ? [seat.gone ? 0 : 1, 1, 1, 0] : [0, 1, 1, seat.gone ? 0 : 1];
  // The first keyframe is in place before Motion starts (doc/wiki/footguns/motion_starts_a_frame_late.md).
  chip.style.transform = path[0]; chip.style.opacity = String(shown[0]);
  home.appendChild(chip);
  var gone = function () { chip.remove(); if (layer === home && !home.firstChild) { home.remove(); layer = null; } };
  var flight = M.run(chip, {transform: path}, {duration: FLY, ease: EASE});
  M.run(chip, {opacity: shown}, {duration: FLY, ease: "linear", times: [0, edge, 1 - edge, 1]});
  if (!flight) { gone(); return; }
  M.after(flight, gone);
  later(FLY * 1000 + 300, gone);
}

function send(moves) {
  moves.forEach(function (move, index) {
    later(index * GAP_MS, function () {
      if (off) return;
      try { fly(move); } catch (error) { fail(error); }
    });
  });
}
// The page is already complete: the chips are given up for this page view, and the error is still reported.
function fail(error) {
  off = true; clear();
  setTimeout(function () { throw error; }, 0);
}

document.addEventListener("live:updated", function () {
  if (!region) return;
  var was = seen, stateWas = state;
  seen = values(); state = region.dataset.state;
  if (off || !was || stateWas !== state) return;
  try {
    var moves = moved(was, seen), M = window.pokerMotion, S = window.pokerStage;
    if (!moves.length || moves.length > MOST || !M || !S || !M.on() || document.hidden || S.taken()) return;
    var dialog = document.querySelector("dialog[open]");
    if (!dialog) { send(moves); return; }
    // The sender's sheet is still closing: the chips start when it has closed. A sheet that stays open
    // (another sheet, the seat draw) gets no chip.
    forget();
    var mine = pending = {dialog: dialog, go: function () { if (pending === mine) { forget(); send(moves); } }};
    mine.timer = setTimeout(function () { if (pending === mine) forget(); }, SHEET_MS);
    dialog.addEventListener("close", mine.go);
  } catch (error) { fail(error); }
});

window.pokerPage.register(function () {
  region = document.getElementById("live");
  if (!region) return;
  seen = values(); state = region.dataset.state; off = false;
  return function () { clear(); region = null; seen = null; state = null; };
});
})();

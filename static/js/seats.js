// The seat draw on the set page (DESIGN.md, "Seat draw"). The server has already drawn: this
// script only plays the result back on a stage, once per draw and browser, and sends the
// dealer's choice of seat. Without it the page shows the same result as a still table and a list.
// The stage lives outside the live region, which live.js replaces on every update.
(function () {
"use strict";
var S = null; // the current page's stage: {region, dialog, table, data, tokens, run, part, ...}
var memory = {}; // what this tab has played, when the browser refuses to remember
var REACH = 44, CLOSE_ICON = '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m18 6-12 12M6 6l12 12"/></svg>';

function seen(draw) { try { return localStorage.getItem("rack-seats:" + draw) || memory[draw] || ""; } catch (_) { return memory[draw] || ""; } }
function mark(draw, part) { memory[draw] = part; try { localStorage.setItem("rack-seats:" + draw, part); } catch (_) {} }
function moving() { return !!(window.pokerMotion && window.pokerMotion.on()); }

// What the page says about the draw: the players clockwise from the dealer, and the dealer's seat once chosen.
function read() {
var el = S.region.querySelector("[data-seats]"); if (!el) return null;
var data = {draw: el.dataset.draw, state: el.dataset.state, fresh: "fresh" in el.dataset, canChoose: "canChoose" in el.dataset, el: el};
if (data.state === "stale") return data;
data.dealerSeat = el.dataset.dealerSeat === undefined ? null : Number(el.dataset.dealerSeat);
data.players = Array.from(el.querySelectorAll(".seat-order > li")).map(function (li, distance) {
var chip = li.querySelector(".chip").cloneNode(true); chip.removeAttribute("data-m");
return {pid: li.dataset.pid, ring: Number(li.dataset.ring), name: li.dataset.name, short: li.dataset.short || "", position: li.dataset.position || "", me: "me" in li.dataset, distance: distance, chip: chip};
});
var form = el.querySelector("[data-seat-pick]");
if (form) data.pick = {url: form.action, csrf: form.querySelector("[name=csrfmiddlewaretoken]").value};
return data;
}

// --- The stage -----------------------------------------------------------------------------
function build() {
var dialog = document.createElement("dialog");
dialog.className = "seat-stage"; dialog.setAttribute("aria-labelledby", "seat-stage-title");
dialog.innerHTML = '<div class="stage-head"><h2 id="seat-stage-title">Seat draw</h2><button type="button" class="btn btn-round" data-stage-close aria-label="Close the seat draw">' + CLOSE_ICON + '</button></div>' +
'<div class="stage-words"><p class="stage-line" aria-live="polite"></p><p class="stage-sub"></p></div>' +
'<div class="stage-room"><div class="stage-table"><div class="seat-felt" aria-hidden="true"></div><div class="stage-seats"></div><div class="stage-tokens"></div><span class="stage-disc" aria-hidden="true">D</span></div></div>' +
'<div class="stage-actions"><button type="button" class="btn btn-primary btn-block" data-stage-done hidden>Done</button><p class="stage-hint" data-stage-hint hidden>Tap to skip</p></div>';
// Inside the container Turbo keeps: a form answered in place redraws the body, and a dialog left in it would be removed.
(document.getElementById("table-sheets") || document.body).appendChild(dialog);
return dialog;
}
function say(line, sub, waiting) {
S.dialog.querySelector(".stage-line").textContent = line;
var el = S.dialog.querySelector(".stage-sub"); el.textContent = sub || ""; el.classList.toggle("is-waiting", !!waiting); el.classList.remove("is-error");
}
// A point on the table's oval, in pixels from its centre: seat 0 at the top, then clockwise.
function at(index, count, reach) {
var angle = (-90 + 360 * index / count) * Math.PI / 180;
return {x: S.table.clientWidth * reach / 100 * Math.cos(angle), y: S.table.clientHeight * reach / 100 * Math.sin(angle)};
}
function css(point, scale) { return "translate(" + point.x.toFixed(1) + "px, " + point.y.toFixed(1) + "px) scale(" + (scale === undefined ? 1 : scale) + ")"; }

// One movement. The first frame is written before Motion starts and the last one stays when it
// ends, so a skipped or switched-off animation leaves the same picture as a finished one.
function anim(el, frames, options) {
var names = Object.keys(frames);
function last() { names.forEach(function (name) { el.style[name] = frames[name][frames[name].length - 1]; }); }
if (!moving() || S.skip) { last(); return; }
names.forEach(function (name) { el.style[name] = frames[name][0]; });
var controls = window.pokerMotion.run(el, frames, options);
if (!controls) { last(); return; }
S.controls.push(controls);
window.pokerMotion.after(controls, last);
}
// A pause inside a part. A skip ends every pause of the part at once.
function wait(ms) {
if (!moving() || S.skip) return Promise.resolve();
return new Promise(function (done) { var timer = setTimeout(finish, ms); function finish() { clearTimeout(timer); done(); } S.waits.push(finish); });
}
function later(ms, act) { wait(ms).then(function () { if (S && S.dialog.open) act(); }); }
function skip() {
if (!S || !S.part) return;
S.skip = true;
S.controls.splice(0).forEach(function (controls) { try { controls.complete(); } catch (_) {} });
S.waits.splice(0).forEach(function (finish) { finish(); });
}
function begin(part) { S.part = part; S.skip = false; S.controls = []; S.waits = []; S.dialog.querySelector("[data-stage-hint]").hidden = !moving(); }
function end() { S.part = ""; S.dialog.querySelector("[data-stage-hint]").hidden = true; }

function token(player) {
var el = document.createElement("div"); el.className = "stage-token" + (player.me ? " is-self" : ""); el.dataset.pid = player.pid;
el.appendChild(player.chip.cloneNode(true));
var name = document.createElement("span"); name.className = "stage-name"; name.textContent = player.name; el.appendChild(name);
var position = document.createElement("span"); position.className = "stage-pos"; position.textContent = player.short; if (!player.short) position.hidden = true; el.appendChild(position);
return el;
}
// Puts the players and the empty seats on the stage for this draw.
function set(data) {
S.data = data; S.count = data.players.length;
var tokens = S.dialog.querySelector(".stage-tokens"), seats = S.dialog.querySelector(".stage-seats");
tokens.replaceChildren(); seats.replaceChildren(); S.tokens = [];
data.players.forEach(function (player) { var el = token(player); tokens.appendChild(el); S.tokens.push(el); });
for (var index = 0; index < S.count; index++) {
var seat = document.createElement(data.pick ? "button" : "span"), angle = (-90 + 360 * index / S.count) * Math.PI / 180;
seat.className = "seat-spot seat-free"; seat.textContent = index + 1; seat.dataset.seat = index;
seat.style.left = (50 + REACH * Math.cos(angle)) + "%"; seat.style.top = (50 + REACH * Math.sin(angle)) + "%";
if (data.pick) { seat.type = "button"; seat.setAttribute("aria-label", "Seat " + (index + 1)); } else seat.setAttribute("aria-hidden", "true");
seats.appendChild(seat);
}
S.dialog.classList.remove("is-choosing", "is-seated");
S.dialog.querySelector("[data-stage-done]").hidden = true;
S.dialog.toggleAttribute("data-dense", S.count >= 9);
}
function dealer() { return S.data.players[0]; }
function middle() { return {x: 0, y: -S.table.clientHeight * 0.05}; }
function discBy(point) { return {x: point.x + 26, y: point.y - 20}; }

// --- The parts. Each ends in a picture that the matching "still" function can also draw. ---
function stillWinner() {
S.shape = "winner";
S.tokens.forEach(function (el, distance) {
el.classList.remove("is-lit", "is-seated", "is-you"); el.classList.toggle("is-dim", false);
el.style.opacity = distance ? "0" : "1";
el.style.transform = distance ? css({x: 0, y: 0}, 0.5) : css(middle(), 1.5);
});
S.disc.style.opacity = "1"; S.disc.style.transform = css(discBy(middle()));
S.dialog.classList.add("is-choosing"); S.dialog.classList.remove("is-seated");
}
function stillSeated(seat) {
S.shape = "seated"; S.seat = seat;
S.tokens.forEach(function (el, distance) {
el.classList.remove("is-lit", "is-dim"); el.classList.add("is-seated"); el.classList.toggle("is-you", el.classList.contains("is-self"));
el.style.opacity = "1"; el.style.transform = css(at((seat + distance) % S.count, S.count, REACH));
});
S.disc.style.opacity = "1"; S.disc.style.transform = css(at(seat, S.count, REACH - 15));
S.dialog.classList.remove("is-choosing"); S.dialog.classList.add("is-seated");
}

// The table arrives: every player is set down around it, in the order they joined.
async function arrive() {
begin("arrive");
say("Drawing the dealer seat", S.count + " players at the table");
S.shape = "ring";
S.disc.style.opacity = "0";
S.tokens.forEach(function (el, distance) {
var player = S.data.players[distance], to = at(player.ring, S.count, REACH);
el.classList.remove("is-dim", "is-lit", "is-seated", "is-you");
anim(el, {opacity: ["0", "1"], transform: [css(to, 0.6), css(to, 1)]}, {type: "spring", visualDuration: 0.3, bounce: 0.3, delay: player.ring * 0.045});
});
await wait(300 + S.count * 45);
}
// The dealer disc runs around the ring, slows, passes the winner by one and springs back.
async function spin() {
begin("spin");
var count = S.count, winner = dealer().ring, rounds = count <= 3 ? 4 : count <= 6 ? 3 : 2, hops = rounds * count + winner + 1;
var path = [], times = [], seconds = 2.6 + count * 0.03, byRing = {};
S.tokens.forEach(function (el, distance) { byRing[S.data.players[distance].ring] = el; });
for (var hop = 0; hop <= hops; hop++) { path.push(css(at(hop % count, count, REACH - 15))); times.push(1 - Math.sqrt(1 - hop / hops)); }
function light(ring) { S.tokens.forEach(function (el) { el.classList.toggle("is-lit", el === byRing[ring]); }); }
anim(S.disc, {opacity: ["0", "1"]}, {duration: 0.2});
anim(S.disc, {transform: path}, {duration: seconds, times: times, ease: "linear"});
times.forEach(function (time, hop) { later(time * seconds * 1000, function () { if (S.part === "spin") light(hop % count); }); });
await wait(seconds * 1000 + 60);
anim(S.disc, {transform: [path[hops], css(at(winner, count, REACH - 15))]}, {type: "spring", visualDuration: 0.34, bounce: 0.5});
light(winner);
S.tokens.forEach(function (el, distance) { el.classList.toggle("is-dim", distance > 0); });
await wait(520);
}
// The winner comes to the middle of the table; the seats empty and show that they can be tapped.
async function crown() {
begin("crown");
var name = dealer().name;
say(name + " has the dealer seat", "");
S.tokens.forEach(function (el, distance) {
var from = at(S.data.players[distance].ring, S.count, REACH);
if (distance) anim(el, {opacity: [el.style.opacity || "1", "0"], transform: [css(from, 1), css({x: 0, y: 0}, 0.5)]}, {duration: 0.32, ease: [0.4, 0, 1, 1], delay: 0.02 * distance});
else anim(el, {transform: [css(from, 1), css(middle(), 1.5)]}, {type: "spring", visualDuration: 0.42, bounce: 0.28});
});
anim(S.disc, {transform: [S.disc.style.transform, css(discBy(middle()))]}, {type: "spring", visualDuration: 0.42, bounce: 0.28});
await wait(380);
S.dialog.classList.add("is-choosing");
S.dialog.querySelectorAll(".stage-seats .seat-spot").forEach(function (seat, index) {
anim(seat, {opacity: ["0", "1"], transform: ["translate(-50%, -50%) scale(0.6)", "translate(-50%, -50%) scale(1)"]}, {type: "spring", visualDuration: 0.26, bounce: 0.35, delay: index * 0.04});
});
await wait(260 + S.count * 40);
S.tokens.forEach(function (el) { el.classList.remove("is-lit", "is-dim"); });
stillWinner();
end();
}
// Waiting for the seat: the winner or a host taps one; everyone else watches.
function choosing() {
var name = dealer().name, mine = dealer().me;
S.waiting = true;
if (S.data.pick) say(name + " has the dealer seat", mine ? "Tap the seat you want." : "Tap a seat for " + name + ", or let them choose.");
else say(name + " has the dealer seat", name + " is choosing a seat", true);
var first = S.dialog.querySelector(".stage-seats button"); if (first) first.focus({preventScroll: true});
}
// The dealer is placed, then everyone else is dealt to their seat clockwise, one at a time.
async function deal(seat) {
begin("deal");
S.waiting = false;
var count = S.count, name = dealer().name;
say(name + " takes seat " + (seat + 1), "Everyone else follows clockwise.");
S.dialog.classList.remove("is-choosing"); S.dialog.classList.add("is-seated");
S.tokens.forEach(function (el, distance) {
var to = at((seat + distance) % count, count, REACH), from = distance ? {x: 0, y: 0} : middle();
// A short arc: up and a little larger on the way, then down onto the seat.
var over = {x: (from.x + to.x) / 2, y: (from.y + to.y) / 2 - 26}, delay = distance ? 0.42 + (distance - 1) * 0.12 : 0;
el.classList.remove("is-lit", "is-dim");
anim(el, {opacity: [distance ? "0" : "1", "1", "1"], transform: [css(from, distance ? 0.5 : 1.5), css(over, 1.22), css(to, 1)]}, {duration: 0.46, times: [0, 0.55, 1], ease: ["easeOut", "easeIn"], delay: delay});
later((delay + 0.44) * 1000, function () { el.classList.add("is-seated"); });
});
anim(S.disc, {transform: [S.disc.style.transform, css(at(seat, count, REACH - 15))]}, {type: "spring", visualDuration: 0.4, bounce: 0.3, delay: 0.1});
await wait(420 + (count - 1) * 120 + 520);
stillSeated(seat);
var me = S.data.players.filter(function (player) { return player.me; })[0];
say("Seats are set", me ? "You are in seat " + ((seat + me.distance) % count + 1) + (me.position ? ": " + me.position.toLowerCase() + " on the first hand." : ".") : name + " deals first.");
end();
var done = S.dialog.querySelector("[data-stage-done]"); done.hidden = false; done.focus({preventScroll: true});
}

function show() {
if (S.dialog.open) return;
S.dialog.showModal();
if (moving()) window.pokerMotion.run(S.dialog, {opacity: [0, 1], transform: ["translateY(24px)", "translateY(0px)"]}, "sheet");
}
function shut() { if (S && S.dialog.open) S.dialog.close(); }
// Plays a draw from "arrive" (the whole draw) or from "winner" (the dealer already known).
async function play(data, from) {
var run = ++S.run;
function gone() { return !S || S.run !== run || !S.dialog.open; }
show(); set(data); S.waiting = false; S.playing = data.draw;
if (from === "arrive") {
await arrive(); if (gone()) return;
await spin(); if (gone()) return;
await crown(); if (gone()) return;
} else stillWinner();
if (seen(data.draw) !== "seat") mark(data.draw, "draw");
// The seat may have been chosen while this phone was still watching the draw.
var latest = read();
if (latest && latest.draw === data.draw && latest.state === "seated") { data.state = "seated"; data.dealerSeat = latest.dealerSeat; }
if (data.state === "seated") { await deal(data.dealerSeat); if (!gone()) mark(data.draw, "seat"); }
else choosing();
}
function refuse(text) { var el = S.dialog.querySelector(".stage-sub"); el.textContent = text; el.classList.remove("is-waiting"); el.classList.add("is-error"); }
// Sends the dealer's seat. The seating plays only after the server has accepted it.
function choose(seat) {
var data = S.data, pick = data && data.pick; if (!pick || S.sending) return;
S.sending = true;
var body = new URLSearchParams({csrfmiddlewaretoken: pick.csrf, request_id: crypto.randomUUID(), seat: String(seat)});
var button = S.dialog.querySelector('.stage-seats [data-seat="' + seat + '"]'); if (button) button.setAttribute("aria-busy", "true");
fetch(pick.url, {method: "POST", body: body, credentials: "same-origin", headers: {"X-Requested-With": "fetch"}})
.then(function (response) { return response.json().then(function (answer) { return {ok: response.ok, answer: answer}; }); })
.then(function (result) {
if (!S || S.data !== data) return;
if (!result.ok) { refuse(result.answer.error || "That did not go through. Try again."); return; }
data.state = "seated"; data.dealerSeat = result.answer.seat;
var run = S.run;
deal(data.dealerSeat).then(function () { if (S && S.run === run) mark(data.draw, "seat"); });
})
.catch(function () { if (S && S.data === data) refuse("No connection. Try again."); })
.then(function () { if (S) S.sending = false; if (button) button.removeAttribute("aria-busy"); });
}

// Decides what this phone should do with what the page now says.
function consider(arrived) {
if (!S) return;
var data = read(), replay = S.region.querySelector("[data-seat-replay]");
if (replay) replay.hidden = false;
if (!data || data.state === "stale") {
if (S.dialog.open && S.playing) { S.run++; S.waiting = false; say("The table changed", "This draw no longer fits the players. A host can draw again."); S.dialog.querySelector("[data-stage-done]").hidden = false; S.dialog.classList.remove("is-choosing"); S.playing = ""; }
return;
}
var known = seen(data.draw), open = S.dialog.open, fresh = arrived || data.fresh;
if (open && S.playing === data.draw) {
// The stage is on this draw: the seat it was waiting for has been chosen.
if (S.waiting && data.state === "seated") { S.data.state = "seated"; S.data.dealerSeat = data.dealerSeat; var run = S.run; deal(data.dealerSeat).then(function () { if (S && S.run === run) mark(data.draw, "seat"); }); }
return;
}
if (document.querySelector("dialog[open]") && !open) return; // another sheet has the screen; the next update asks again
if (data.state === "choosing" && !known && fresh) play(data, "arrive");
else if (data.state === "seated" && known !== "seat" && fresh) play(data, known === "draw" ? "winner" : "arrive");
}

document.addEventListener("live:updated", function () { consider(true); });
document.addEventListener("inplace:updated", function () { consider(true); });
document.addEventListener("click", function (event) {
if (!S || !event.target.closest) return;
if (event.target.closest("[data-seat-replay]")) { var data = read(); if (data && data.players) play(data, "arrive"); return; }
if (!S.dialog.contains(event.target)) return;
if (event.target.closest("[data-stage-close], [data-stage-done]")) { shut(); return; }
var seat = event.target.closest(".stage-seats button");
if (seat && S.waiting) { choose(Number(seat.dataset.seat)); return; }
skip();
});
// The page's own seat buttons: with scripts the choice is sent from the stage, so the seating plays at once.
document.addEventListener("submit", function (event) {
if (!S || !event.target.matches || !event.target.matches("[data-seat-pick]") || !event.submitter) return;
var data = read(); if (!data || !data.pick) return;
event.preventDefault();
var seat = Number(event.submitter.value);
S.run++; show(); set(data); S.playing = data.draw; stillWinner(); choosing(); mark(data.draw, "draw");
choose(seat);
});
window.addEventListener("resize", function () {
if (!S || !S.dialog.open || S.part) return;
if (S.shape === "seated") stillSeated(S.seat); else if (S.shape === "winner") stillWinner();
});

window.pokerPage.register(function () {
var region = document.getElementById("live");
if (!region || !region.querySelector(".table-v2")) return;
var dialog = build();
var me = S = {region: region, dialog: dialog, table: dialog.querySelector(".stage-table"), disc: dialog.querySelector(".stage-disc"), tokens: [], controls: [], waits: [], run: 0, part: "", playing: ""};
// Closing counts as having watched: the stage does not come back for a part this person dismissed.
dialog.addEventListener("close", function () {
if (S !== me) return;
if (me.playing && me.data) mark(me.playing, me.data.state === "seated" ? "seat" : "draw");
skip(); me.run++; me.waiting = false; me.part = "";
});
consider(false);
return function () {
if (S === me) { skip(); S = null; }
if (dialog.open) dialog.close();
dialog.remove();
};
});
})();

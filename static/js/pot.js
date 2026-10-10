// The pot of a set in play ("Still in play") when its amount changes: a buy-in, a cash-out, a
// reversal, by anyone. The digits that changed roll to the accepted amount and the amount added
// rises beside the label. The page's text is the accepted amount from the first frame; for the
// length of the roll the figure is drawn one character per cell, and then it is plain text again.
// Nothing counts through other values. If the drawn copy or the written amount cannot match what
// the server drew, the figure stays as it came. Without Motion or in a hidden tab nothing is added;
// under reduced motion only the amount added shows, and it is still.
(function () {
  "use strict";
  var region = null, last = null, roll = null, off = false;
  var OUT_MS = 120, STEP_MS = 30, STEPS = 4, SEEN_MS = 380, HOLD_MS = 3000, FADE_MS = 400, EASE_IN = "cubic-bezier(0.4,0,1,1)";
  var REST = "translateY(0)";

  // What the pot shows now: the integer amount, the figure's number and the whole figure as read.
  function read() {
    var main = region && region.querySelector('.pot-main[data-watch="in-play"]');
    var figure = main && main.querySelector(".display-amount"), node = figure && figure.firstChild;
    var value = main ? Number(main.dataset.value) : NaN;
    if (!node || node.nodeType !== 3 || !Number.isSafeInteger(value)) return null;
    return { main: main, figure: figure, value: value, text: node.nodeValue.trim(), full: figure.textContent.replace(/\s+/g, " ").trim() };
  }
  function drop() {
    if (!roll) return;
    clearTimeout(roll.timer);
    if (roll.wrap.isConnected) { roll.wrap.replaceWith(roll.node); roll.say.remove(); }
    roll = null;
  }
  function span(name, text) {
    var el = document.createElement("span");
    if (name) el.className = name;
    if (text !== undefined) el.textContent = text;
    return el;
  }

  // An amount as the server writes it (ledger/money.py). Integers only.
  function words(value, unit) {
    if (value < 0) return null;
    var whole = unit === "chips" ? value : Math.floor(value / 100), cents = unit === "chips" ? 0 : value % 100;
    var text = String(whole).replace(/\B(?=(\d{3})+$)/g, ",");
    if (unit === "chips") return text + (value === 1 ? " chip" : " chips");
    return "₱" + text + (cents ? "." + (cents < 10 ? "0" : "") + cents : "");
  }
  // "+₱500" beside the label, for as long as the brass mark stays. Shown only if this script
  // writes the new total exactly as the server did.
  function added(now, was, moving) {
    var panel = now.main.closest("[data-unit]"), label = now.main.querySelector(".pot-label");
    var unit = panel && panel.dataset.unit, by = now.value - was.value;
    if (!label || !unit || words(now.value, unit) !== now.full) return;
    var el = span("pot-delta", (by > 0 ? "+" : "−") + words(Math.abs(by), unit));
    el.setAttribute("aria-hidden", "true");
    label.appendChild(el);
    if (moving) el.animate([{ opacity: 0, transform: "translateY(8px)" }, { opacity: 1, transform: REST }], moving);
    setTimeout(function () { if (moving && el.isConnected) el.animate([{ opacity: 1 }, { opacity: 0 }], { duration: FADE_MS, easing: EASE_IN, fill: "forwards" }); }, HOLD_MS - FADE_MS);
    setTimeout(function () { el.remove(); }, HOLD_MS);
  }

  // The sign before the number, the whole part and what follows it. Whole parts line up from the right.
  function parts(text) { var found = /^(\D*)([\d,]*)(.*)$/.exec(text); return [found[1], found[2], found[3]]; }
  // Each character of the new figure with the character that stood in its place, and where that was.
  function pairs(before, after) {
    var a = parts(before), b = parts(after), list = [], start = 0, at = 0;
    for (var p = 0; p < 3; p++) {
      var slide = p === 1 ? a[p].length - b[p].length : 0;
      for (var i = 0; i < b[p].length; i++) {
        var j = i + slide, had = j >= 0 && j < a[p].length;
        list.push({ ch: b[p][i], old: had ? a[p][j] : undefined, from: had ? start + j : -1, at: at++ });
      }
      start += a[p].length;
    }
    return list;
  }
  // Where each character of a text node starts, as the browser sets it.
  function lefts(node) {
    var range = document.createRange(), xs = [];
    for (var i = 0; i < node.nodeValue.length; i++) { range.setStart(node, i); range.setEnd(node, i + 1); xs.push(range.getBoundingClientRect().left); }
    return xs;
  }
  function turn(now, was, spring) {
    var figure = now.figure, node = figure.firstChild, text = node.nodeValue;
    var height = figure.getBoundingClientRect().height, range = document.createRange();
    range.selectNodeContents(node);
    var width = range.getBoundingClientRect().width, olds = null;
    // The figure got wider or narrower: where the characters that stay were drawn before.
    if (was.text.length !== now.text.length) { node.nodeValue = was.text; olds = lefts(node); node.nodeValue = text; }
    var wrap = span("pot-roll"), say = span("visually-hidden", now.text), cells = pairs(was.text, now.text);
    wrap.setAttribute("aria-hidden", "true");
    cells.forEach(function (c) {
      c.el = span("pot-cell"); c.glyph = span("", c.ch); c.el.appendChild(c.glyph);
      if (c.old !== undefined && c.old !== c.ch) { c.gone = span("pot-gone", c.old); c.el.appendChild(c.gone); }
      wrap.appendChild(c.el);
    });
    figure.replaceChild(wrap, node);
    figure.insertBefore(say, wrap.nextSibling);
    roll = { node: node, wrap: wrap, say: say, timer: 0 };
    // The drawn copy must take exactly the room the plain figure took.
    if (Math.abs(wrap.getBoundingClientRect().width - width) > 0.5 || Math.abs(figure.getBoundingClientRect().height - height) > 0.5) { drop(); return; }
    var far = now.value > was.value ? 60 : -60, step = 0, wait = 0;
    cells.forEach(function (c) {
      if (c.old === c.ch) {
        var by = olds ? olds[c.from] - c.el.getBoundingClientRect().left : 0;
        if (Math.abs(by) > 0.25) c.el.animate([{ transform: "translateX(" + by + "px)" }, { transform: "translateX(0)" }], spring);
        return;
      }
      var delay = wait = STEP_MS * Math.min(step++, STEPS);
      if (c.gone) c.gone.animate([{ opacity: 1, transform: REST }, { opacity: 0, transform: "translateY(" + -far + "%)" }], { duration: OUT_MS, delay: delay, easing: EASE_IN, fill: "both" });
      c.glyph.animate([{ opacity: 0, transform: "translateY(" + far + "%)" }, { opacity: 1, transform: REST }], { duration: spring.duration, delay: delay, easing: spring.easing, fill: "backwards" });
    });
    // A spring without bounce is at rest to the eye well before it reports its end.
    roll.timer = setTimeout(drop, wait + Math.min(spring.duration, SEEN_MS) + 40);
  }

  // The plain figure is put back before a redraw, so a morph compares like with like.
  document.addEventListener("live:updating", drop);
  document.addEventListener("live:updated", function () {
    if (!region) return;
    var was = last, now = read(), M = window.pokerMotion;
    last = now && { value: now.value, text: now.text };
    drop();
    if (off || !was || !now || was.value === now.value || document.hidden || !window.Motion || !M || !now.figure.animate) return;
    try {
      var spring = M.timing("shift");
      added(now, was, spring);
      if (spring) turn(now, was, spring);
    } catch (error) {
      // The figure is already the accepted amount: the roll is given up for this page, and the error is still reported.
      off = true; drop();
      setTimeout(function () { throw error; }, 0);
    }
  });

  window.pokerPage.register(function () {
    region = document.getElementById("live");
    if (!region) return;
    var now = read();
    last = now && { value: now.value, text: now.text };
    off = false;
    return function () { drop(); region = null; last = null; };
  });
})();

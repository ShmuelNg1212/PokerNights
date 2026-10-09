// The app's own number keys. A marked field (data-numpad="pesos|chips|percent|whole") stays a real
// text field: the keys write into it and send "input", so forms, the count preview and live updates
// see ordinary typing. The phone's keyboard is switched off (inputmode="none") only for a field
// these keys can serve, and only once they exist. Anything going wrong gives the keyboard back.
(function () {
  "use strict";
  var root = document.documentElement, coarse = matchMedia("(pointer: coarse)");
  var pad = null, target = null, native = new WeakMap(); // the keys, the field they write to, each field's own inputmode
  var panel = null, leaving = null; // the bottom panel for a page with several number fields, and its exit
  var downAt = 0, downKey = null, hold = 0, broken = false;
  var HOLD = 500; // how long Delete is held to clear the field; the stylesheet's fill takes the same time
  var MAX = 100000000000; // ledger/money.py MAX_CENTAVOS: ₱1 billion in centavos, or that many chips
  var RULES = {
    pesos: { point: true, shape: /^\d{0,10}(\.\d{0,2})?$/, fits: function (v) { return Math.round(Number(v || 0) * 100) <= MAX; } },
    chips: { point: false, shape: /^\d{0,12}$/, fits: function (v) { return Number(v || 0) <= MAX; } },
    percent: { point: true, shape: /^\d{0,2}(\.\d{0,2})?$/, fits: function () { return true; } },
    whole: { point: false, shape: /^\d{0,2}$/, fits: function () { return true; } }
  };
  var DELETE = '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M10 5a2 2 0 0 0-1.34.52l-6.33 5.74a1 1 0 0 0 0 1.48l6.33 5.74A2 2 0 0 0 10 19h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2z"/><path d="m12 9 6 6m0-6-6 6"/></svg>';

  function on() { return !broken && root.dataset.numpad === "on" && coarse.matches; }
  // "amount" is pesos or chips by the form's Unit choice, read when it is needed because the choice can change.
  function rule(field) {
    var kind = field.dataset.numpad;
    if (kind === "amount") { var unit = field.form && field.form.elements.unit; kind = unit && unit.value === "chips" ? "chips" : "pesos"; }
    return RULES[kind];
  }
  function slot(field) { return field.form && field.form.querySelector("[data-numpad-slot]"); }
  // A form with a slot shows the keys in that slot (a sheet). Any other marked field gets the bottom panel.
  function served(field) { return !!pad && on() && !!field && !!field.matches && field.matches("input[data-numpad]") && !!rule(field) && !field.disabled && !field.readOnly && (!!slot(field) || !field.closest("dialog")); }
  function typing(el) { return /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) && !/^(checkbox|radio|button|submit|hidden)$/.test(el.type); }

  function build() {
    var box = document.createElement("div");
    box.className = "numpad"; box.setAttribute("role", "group"); box.setAttribute("aria-label", "Number keys");
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "alt", "0", "del"].forEach(function (key) {
      var button = document.createElement("button");
      button.type = "button"; button.className = "btn numpad-key"; button.dataset.key = key; button.tabIndex = -1;
      if (key === "del") { button.innerHTML = DELETE; button.setAttribute("aria-label", "Delete"); }
      else button.textContent = key;
      box.appendChild(button);
    });
    return box;
  }
  function buildPanel() {
    var box = document.createElement("div");
    box.className = "numpad-panel"; box.setAttribute("role", "group"); box.setAttribute("aria-label", "Number keys");
    box.innerHTML = '<div class="numpad-strip"><div class="numpad-about"><strong data-numpad-label></strong><span class="numpad-note" data-numpad-note aria-live="polite"></span></div>' +
      '<button type="button" class="btn btn-small" data-numpad-next tabindex="-1">Next</button><button type="button" class="btn btn-small btn-primary" data-numpad-done tabindex="-1">Done</button></div>';
    return box;
  }
  function name(field) {
    var label = field.id && document.querySelector('label[for="' + field.id + '"]');
    return field.getAttribute("aria-label") || (label ? label.textContent.trim() : "");
  }
  // The next field: in a list of counts, the first later one still to count (empty, nothing confirmed); otherwise simply the next.
  function following(field) {
    var all = Array.prototype.filter.call(document.querySelectorAll("input[data-numpad]"), function (el) { return served(el) && !slot(el) && el.getClientRects().length; });
    var later = all.slice(all.indexOf(field) + 1);
    return later.filter(function (el) { return !el.value && el.dataset.saved === ""; })[0] || later[0] || null;
  }
  // --- Movement. It only adds, and nothing waits for it: a key has already acted when any of this
  // starts. Without Motion, or under reduced motion, go() does nothing and every key works as before.
  // Motion begins a frame late, so the starting point is written first (footgun: motion_starts_a_frame_late).
  // A key can be pressed while it is still rising, and the press is then the element's latest movement.
  // So each movement here clears what it wrote itself when it ends, unless a later one of these took over.
  var moving = new WeakMap();
  function go(el, keyframes, preset, extra) {
    var M = window.pokerMotion;
    if (!el || !M || !M.on()) return;
    var names = Object.keys(keyframes);
    names.forEach(function (name) { el.style[name] = keyframes[name][0]; });
    var controls = M.run(el, keyframes, preset, extra);
    moving.set(el, controls);
    M.after(controls, function () {
      // Motion writes the final value once more on the frame after it reports the end.
      requestAnimationFrame(function () { requestAnimationFrame(function () {
        if (moving.get(el) !== controls) return;
        names.forEach(function (name) { el.style[name] = ""; });
        if (!el.getAttribute("style")) el.removeAttribute("style");
      }); });
    });
  }
  // A key shows that it was hit, or refused. The stylesheet fades the mark out once it is taken off.
  var marks = new WeakMap();
  function lit(key, name, time) {
    if (!key) return;
    clearTimeout(marks.get(key));
    key.classList.remove("is-hit", "is-refused");
    key.classList.add(name);
    marks.set(key, setTimeout(function () { key.classList.remove(name); }, time));
  }
  // --- The figure. A text field cannot move one of its characters, so while keys are tapped a drawn
  // copy of the field's text lies exactly over it and the field's own glyphs are hidden (the caret
  // stays). Each character is put where the browser itself lays that text out. A typed digit fades
  // and rises into its place, a deleted one fades out, and the others glide to make room. The field's
  // box does not move. Shortly after the last key the copy goes and the field is a plain field again.
  // What is drawn is always the field's own value: nothing rolls or counts. If the copy cannot match
  // the field (the text is wider than the field, anything fails), the field simply shows its text.
  var fig = null, writing = false, figureOff = false;
  var EASE = "cubic-bezier(0.16,1,0.3,1)", EASE_IN = "cubic-bezier(0.4,0,1,1)", IN = 180, OUT = 100, REST = 300;
  var FONT = ["fontFamily", "fontSize", "fontWeight", "fontStretch", "fontStyle", "fontVariantNumeric", "fontFeatureSettings", "fontKerning", "letterSpacing", "lineHeight", "color"];
  function drop() {
    if (!fig) return;
    clearTimeout(fig.timer);
    fig.field.classList.remove("is-figured");
    fig.layer.remove();
    fig = null;
  }
  // The copy takes the field's box, its type, and the line its text is set on.
  function place() {
    var field = fig.field, style = getComputedStyle(field), box = fig.layer.style, line = fig.line.style;
    FONT.forEach(function (name) { box[name] = style[name]; });
    ["Left", "Right", "Top", "Bottom"].forEach(function (side) {
      line[side.toLowerCase()] = parseFloat(style["border" + side + "Width"]) + parseFloat(style["padding" + side]) + "px";
    });
    line.justifyContent = /right|end/.test(style.textAlign) ? "flex-end" : style.textAlign === "center" ? "center" : "flex-start";
    box.left = field.offsetLeft + "px"; box.top = field.offsetTop + "px";
    // offsetLeft is a whole number; the field can sit on a part of a pixel.
    var at = field.getBoundingClientRect(), now = fig.layer.getBoundingClientRect();
    box.left = field.offsetLeft + at.left - now.left + "px"; box.top = field.offsetTop + at.top - now.top + "px";
    box.width = at.width + "px"; box.height = at.height + "px";
  }
  // Where each character of this text starts, as the browser sets it.
  function measure(text) {
    fig.meas.textContent = text;
    var node = fig.meas.firstChild, base = fig.line.getBoundingClientRect().left, range = document.createRange(), xs = [];
    for (var i = 0; i < text.length; i++) { range.setStart(node, i); range.setEnd(node, i + 1); xs.push(range.getBoundingClientRect().left - base); }
    return xs;
  }
  function drawn(ch, x) {
    var el = document.createElement("span"), glyph = document.createElement("span");
    el.className = "numpad-figure-char"; glyph.textContent = ch; el.appendChild(glyph);
    el.style.transform = "translateX(" + x + "px)";
    fig.line.appendChild(el);
    return { ch: ch, x: x, el: el, glyph: glyph };
  }
  function figure(field, before, after) {
    var M = window.pokerMotion;
    if (figureOff || !M || !M.on() || !field.animate) return;
    try {
      if (fig && (fig.field !== field || fig.text !== before || !fig.layer.isConnected)) drop();
      if (!field.offsetParent || field.scrollWidth > field.clientWidth) { drop(); return; }
      if (!fig) {
        var layer = document.createElement("div"), line = document.createElement("div"), meas = document.createElement("span");
        layer.className = "numpad-figure"; layer.setAttribute("aria-hidden", "true"); line.className = "numpad-figure-line"; meas.className = "numpad-figure-text";
        line.appendChild(meas); layer.appendChild(line); field.offsetParent.appendChild(layer);
        fig = { field: field, layer: layer, line: line, meas: meas, chars: [], text: before, timer: 0 };
        place();
        measure(before).forEach(function (x, i) { fig.chars.push(drawn(before[i], x)); });
      } else place();
      clearTimeout(fig.timer);
      var head = 0, tail = 0, most = Math.min(before.length, after.length);
      while (head < most && before[head] === after[head]) head++;
      while (tail < most - head && before[before.length - 1 - tail] === after[after.length - 1 - tail]) tail++;
      var old = fig.chars, gone = old.slice(head, old.length - tail), kept = old.slice(0, head).concat(old.slice(old.length - tail));
      // A glide that is cut by the next key carries on from where it is drawn.
      kept.forEach(function (c) { c.from = c.el.getAnimations().length ? new DOMMatrixReadOnly(getComputedStyle(c.el).transform).m41 : c.x; });
      var xs = measure(after);
      if (fig.meas.getBoundingClientRect().width > fig.line.getBoundingClientRect().width + 0.5) { drop(); return; }
      var added = after.length - head - tail, next = [];
      gone.forEach(function (c) {
        // Only a plain delete is seen leaving. What a new digit replaces goes at once, so two values never overlap.
        if (added) { c.el.remove(); return; }
        c.glyph.animate([{ opacity: 1, transform: "translateY(0)" }, { opacity: 0, transform: "translateY(0.12em)" }], { duration: OUT, easing: EASE_IN, fill: "forwards" })
          .finished.then(function () { c.el.remove(); }, function () {});
      });
      for (var i = 0; i < after.length; i++) {
        var c = i < head ? old[i] : i >= after.length - tail ? old[old.length - (after.length - i)] : null;
        if (!c) {
          c = drawn(after[i], xs[i]);
          c.glyph.animate([{ opacity: 0, transform: "translateY(0.16em)" }, { opacity: 1, transform: "translateY(0)" }], { duration: IN, easing: EASE });
        } else {
          c.el.getAnimations().forEach(function (running) { running.cancel(); });
          c.el.style.transform = "translateX(" + xs[i] + "px)";
          if (Math.abs(c.from - xs[i]) > 0.25) c.el.animate([{ transform: "translateX(" + c.from + "px)" }, { transform: "translateX(" + xs[i] + "px)" }], { duration: IN, easing: EASE });
          c.x = xs[i];
        }
        next.push(c);
      }
      fig.chars = next; fig.text = after;
      field.classList.add("is-figured");
      fig.timer = setTimeout(drop, after ? REST : OUT + 20);
    } catch (error) {
      // The keys must keep working: the figure is given up for this page, and the error is still reported.
      figureOff = true; drop();
      setTimeout(function () { throw error; }, 0);
    }
  }
  // The four rows of keys rise into a sheet, one after another. A key can be tapped before it lands.
  function rise() {
    Array.prototype.forEach.call(pad.children, function (key, at) {
      go(key, { opacity: [0, 1], transform: ["translateY(10px)", "translateY(0px)"] }, "shift", { delay: Math.floor(at / 3) * 0.03 });
    });
  }
  function held(key, yes) { if (key) key.classList.toggle("is-holding", !!yes); }

  function openPanel(field) {
    if (leaving) { leaving.cancel(); leaving = null; }
    if (pad.parentNode !== panel) panel.appendChild(pad);
    var label = panel.querySelector("[data-numpad-label]"), moved = panel.isConnected && label.textContent !== name(field);
    label.textContent = name(field);
    // Next: the keys now belong to another field, and its name comes in from below.
    if (moved) go(label.parentNode, { opacity: [0, 1], transform: ["translateY(8px)", "translateY(0px)"] }, "fade", { duration: 0.16 });
    panel.querySelector("[data-numpad-next]").hidden = !following(field);
    var arriving = !panel.isConnected;
    if (arriving) {
      document.body.appendChild(panel);
      root.classList.add("numpad-open");
      root.style.setProperty("--pad-h", panel.offsetHeight + "px");
      var M = window.pokerMotion, rise = M && M.run(panel, { transform: ["translateY(" + panel.offsetHeight + "px)", "translateY(0px)"] }, "sheet");
      if (rise) M.settle(panel, rise);
    }
    document.dispatchEvent(new CustomEvent("numpad:open"));
    // The field clears the panel; in a list its row goes to the top, so the next one shows. Scroll margins are in the stylesheet.
    var row = field.closest(".count-row"), smooth = window.pokerMotion && window.pokerMotion.on() ? "smooth" : "auto";
    if (row) row.scrollIntoView({ block: "start", behavior: smooth }); else field.scrollIntoView({ block: "nearest", behavior: smooth });
  }
  // at once: the page is being left, or something failed, so nothing waits for a movement.
  function closePanel(atOnce) {
    var box = panel;
    if (!box || !box.isConnected) return;
    var gone = function () { leaving = null; box.remove(); box.style.transform = ""; root.classList.remove("numpad-open"); root.style.removeProperty("--pad-h"); };
    if (leaving) { if (!atOnce) return; var old = leaving; leaving = null; old.cancel(); }
    var M = window.pokerMotion;
    leaving = !atOnce && M && M.run(box, { transform: "translateY(" + box.offsetHeight + "px)" }, "leave");
    if (leaving) { var mine = leaving; M.after(mine, function () { if (leaving === mine) gone(); }); } else gone();
  }

  // The phone's keyboard goes only for a field the keys can serve.
  function mark(field) {
    if (!served(field) || field.getAttribute("inputmode") === "none") return;
    native.set(field, field.getAttribute("inputmode"));
    field.setAttribute("inputmode", "none");
  }
  function unmark(field) {
    if (field.getAttribute("inputmode") !== "none") return;
    var own = native.get(field);
    if (own) field.setAttribute("inputmode", own); else field.setAttribute("inputmode", "decimal");
  }
  function markAll() { document.querySelectorAll("input[data-numpad]").forEach(mark); }

  function show(field) {
    var alt = pad.querySelector('[data-key="alt"]'), point = rule(field).point;
    alt.textContent = point ? "." : "00";
    alt.setAttribute("aria-label", point ? "Decimal point" : "Double zero");
    if (target !== field) drop();
    target = field;
    mark(field);
    var place = slot(field);
    if (!place) { openPanel(field); return; }
    closePanel();
    if (pad.parentNode !== place) { place.appendChild(pad); rise(); }
  }
  function hide(atOnce) {
    drop();
    clearTimeout(hold); held(pad && pad.querySelector(".is-holding"), false);
    if (panel && panel.isConnected) closePanel(atOnce); else if (pad) pad.remove();
    target = null;
  }
  // Something failed: stop, and give every field its keyboard back.
  function giveUp(error) {
    broken = true;
    hide(true);
    if (pad) pad.remove();
    document.querySelectorAll('input[data-numpad][inputmode="none"]').forEach(unmark);
    setTimeout(function () { throw error; }, 0);
  }

  function refuse(field, key) {
    // The finger is on the key, so the refusal shows there as well as on the field.
    lit(key, "is-refused", 260);
    go(key, { transform: ["translateX(0px)", "translateX(-4px)", "translateX(4px)", "translateX(-2px)", "translateX(0px)"] }, "nudge");
    field.classList.add("numpad-refused");
    setTimeout(function () { field.classList.remove("numpad-refused"); }, 260);
    var M = window.pokerMotion, shake = { transform: ["translateX(0px)", "translateX(-5px)", "translateX(5px)", "translateX(-2px)", "translateX(0px)"] };
    var moving = M && M.run(field, shake, "nudge");
    if (moving) M.settle(field, moving);
    if (fig && fig.field === field) go(fig.layer, shake, "nudge"); // the drawn figure shakes with its field
  }
  function write(field, value, caret) {
    var before = field.value;
    field.value = value;
    if (document.activeElement === field) { try { field.setSelectionRange(caret, caret); } catch (_) {} }
    writing = true;
    try { field.dispatchEvent(new Event("input", { bubbles: true })); } finally { writing = false; }
    figure(field, before, value);
  }
  function press(key, button) {
    var field = target;
    if (!field || !field.isConnected) { hide(); return; }
    var value = field.value, from = value.length, to = value.length;
    if (document.activeElement === field && field.selectionStart !== null) { from = field.selectionStart; to = field.selectionEnd; }
    if (key === "del") {
      if (from === to) from = Math.max(0, from - 1);
      if (from !== to) write(field, value.slice(0, from) + value.slice(to), from);
      return;
    }
    var text = key === "alt" ? (rule(field).point ? "." : "00") : key;
    if (text === "." && from === 0) text = "0.";
    var next = value.slice(0, from) + text + value.slice(to), caret = from + text.length;
    var zeros = /^0+(?=\d)/.exec(next); // "05" is 5, and "00" on an empty field is 0
    if (zeros) { next = next.slice(zeros[0].length); caret = Math.max(0, caret - zeros[0].length); }
    if (!rule(field).shape.test(next) || !rule(field).fits(next)) { refuse(field, button); return; }
    write(field, next, caret);
  }
  function act(key, button) { try { press(key, button); } catch (error) { giveUp(error); } }
  // Next goes to the following field; Done puts the keys away.
  function move(step) {
    try {
      var next = step.hasAttribute("data-numpad-next") && target && following(target);
      if (next) { next.focus({ preventScroll: true }); if (target !== next) show(next); return; }
      var field = target;
      hide();
      if (field && document.activeElement === field) field.blur();
    } catch (error) { giveUp(error); }
  }

  // Listeners for the whole tab. Each does nothing while no page has the keys.
  // A key acts as the finger goes down, and the field keeps its focus and caret.
  document.addEventListener("pointerdown", function (event) {
    if (!pad) return;
    var field = event.target.closest && event.target.closest("input[data-numpad]");
    if (field) mark(field); // before the focus that would call the phone's keyboard
    var step = panel && event.target.closest && event.target.closest("[data-numpad-next], [data-numpad-done]");
    if (step && panel.contains(step)) { event.preventDefault(); downAt = Date.now(); downKey = step; move(step); return; }
    var key = event.target.closest && event.target.closest(".numpad-key");
    if (!key || !pad.contains(key)) return;
    event.preventDefault();
    downAt = Date.now(); downKey = key;
    lit(key, "is-hit", 70);
    act(key.dataset.key, key);
    if (key.dataset.key === "del" && target && target.value) {
      held(key, true); // a fill runs across the key for as long as the hold takes
      hold = setTimeout(function () { // held: clear the field
        held(key, false);
        if (target && target.isConnected && target.value) {
          try { write(target, "", 0); } catch (error) { giveUp(error); }
        }
      }, HOLD);
    }
  }, true);
  function lift() { clearTimeout(hold); held(pad && pad.querySelector(".is-holding"), false); }
  window.addEventListener("pointerup", lift);
  window.addEventListener("pointercancel", lift);
  // A key reached without a pointer (a physical keyboard, a screen reader) acts on its click.
  document.addEventListener("click", function (event) {
    var key = pad && event.target.closest && event.target.closest(".numpad-key, [data-numpad-next], [data-numpad-done]");
    if (!key || !(pad.contains(key) || (panel && panel.contains(key)))) return;
    if (key === downKey && Date.now() - downAt < 700) return; // the pointer already acted
    if (key.dataset.key) { lit(key, "is-hit", 70); act(key.dataset.key, key); } else move(key);
  });
  // The panel goes when its field loses focus to anything but another number field or the panel itself.
  document.addEventListener("focusout", function (event) {
    if (!panel || !panel.isConnected || event.target !== target) return;
    setTimeout(function () {
      var now = document.activeElement;
      if (!panel || !panel.isConnected || now === target || panel.contains(now) || (served(now) && !slot(now))) return;
      hide();
    }, 0);
  });
  // Typing that is not from these keys (a physical keyboard, a paste) is shown by the field itself.
  document.addEventListener("input", function (event) { if (fig && !writing && event.target === fig.field) drop(); }, true);
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && panel && panel.isConnected && !document.querySelector("dialog[open]")) { var field = target; hide(); if (field) field.blur(); }
  });
  // An in-place update makes the page match the server. The field's keyboard setting and keys in a slot stay.
  document.addEventListener("turbo:before-morph-attribute", function (event) {
    if (pad && event.detail.attributeName === "inputmode" && served(event.target)) event.preventDefault();
  });
  document.addEventListener("turbo:before-morph-element", function (event) {
    if (pad && event.target.hasAttribute && event.target.hasAttribute("data-numpad-slot") && event.target.contains(pad)) event.preventDefault();
  });
  function refreshed() {
    if (!pad) return;
    drop();
    markAll();
    if (target && !target.isConnected) { // the field was redrawn: carry on with the same one, or put the keys away
      var again = target.dataset.keep && document.querySelector('input[data-numpad][data-keep="' + target.dataset.keep + '"]');
      if (again && panel && panel.isConnected && document.activeElement === again) target = again; else hide();
    }
  }
  document.addEventListener("focusin", function (event) {
    if (!pad) return;
    if (served(event.target)) { try { show(event.target); } catch (error) { giveUp(error); } }
    else if (pad.isConnected && typing(event.target)) hide(); // a text field: the phone's keyboard is on its way
  });
  // "close" does not bubble; the capture phase still passes here. The sheet takes its content back.
  document.addEventListener("close", function (event) { if (pad && event.target.contains && event.target.contains(pad)) hide(); }, true);
  document.addEventListener("live:updated", refreshed);
  document.addEventListener("inplace:updated", refreshed);
  function changed() { if (!pad) return; if (on()) markAll(); else { hide(); document.querySelectorAll('input[data-numpad][inputmode="none"]').forEach(unmark); } }
  if (coarse.addEventListener) coarse.addEventListener("change", changed);

  // sheets.js calls this once a sheet holds its form and before it rises, so the sheet opens at its full height.
  window.pokerNumpad = {
    prepare: function (container) {
      if (!pad) return;
      try {
        var first = container.querySelector("input:not([type=hidden]), button");
        if (first && served(first)) show(first);
      } catch (error) { giveUp(error); }
    }
  };

  window.pokerPage.register(function () {
    if (broken || root.dataset.numpad !== "on") return;
    pad = build(); panel = buildPanel();
    markAll();
    return function () {
      hide(true);
      pad.remove();
      pad = panel = null;
    };
  });
})();

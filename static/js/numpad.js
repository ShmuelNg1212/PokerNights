// The app's own number keys. A marked field (data-numpad="pesos|chips|percent|whole") stays a real
// text field: the keys write into it and send "input", so forms, the count preview and live updates
// see ordinary typing. The phone's keyboard is switched off (inputmode="none") only for a field
// these keys can serve, and only once they exist. Anything going wrong gives the keyboard back.
(function () {
  "use strict";
  var root = document.documentElement, coarse = matchMedia("(pointer: coarse)");
  var pad = null, target = null, native = new WeakMap(); // the keys, the field they write to, each field's own inputmode
  var downAt = 0, downKey = null, hold = 0, broken = false;
  var MAX = 100000000000; // ledger/money.py MAX_CENTAVOS: ₱1 billion in centavos, or that many chips
  var RULES = {
    pesos: { point: true, shape: /^\d{0,10}(\.\d{0,2})?$/, fits: function (v) { return Math.round(Number(v || 0) * 100) <= MAX; } },
    chips: { point: false, shape: /^\d{0,12}$/, fits: function (v) { return Number(v || 0) <= MAX; } },
    percent: { point: true, shape: /^\d{0,2}(\.\d{0,2})?$/, fits: function () { return true; } },
    whole: { point: false, shape: /^\d{0,2}$/, fits: function () { return true; } }
  };
  var DELETE = '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M10 5a2 2 0 0 0-1.34.52l-6.33 5.74a1 1 0 0 0 0 1.48l6.33 5.74A2 2 0 0 0 10 19h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2z"/><path d="m12 9 6 6m0-6-6 6"/></svg>';

  function on() { return !broken && root.dataset.numpad === "on" && coarse.matches; }
  function rule(field) { return RULES[field.dataset.numpad]; }
  function slot(field) { return field.form && field.form.querySelector("[data-numpad-slot]"); }
  function served(field) { return !!pad && on() && !!field.matches && field.matches("input[data-numpad]") && !!rule(field) && !field.disabled && !field.readOnly && !!slot(field); }
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
    target = field;
    mark(field);
    var place = slot(field);
    if (pad.parentNode !== place) place.appendChild(pad);
  }
  function hide() {
    clearTimeout(hold);
    if (pad) pad.remove();
    target = null;
  }
  // Something failed: stop, and give every field its keyboard back.
  function giveUp(error) {
    broken = true;
    hide();
    document.querySelectorAll('input[data-numpad][inputmode="none"]').forEach(unmark);
    setTimeout(function () { throw error; }, 0);
  }

  function refuse(field) {
    field.classList.add("numpad-refused");
    setTimeout(function () { field.classList.remove("numpad-refused"); }, 260);
    var M = window.pokerMotion, moving = M && M.run(field, { transform: ["translateX(0px)", "translateX(-5px)", "translateX(5px)", "translateX(-2px)", "translateX(0px)"] }, "nudge");
    if (moving) M.settle(field, moving);
  }
  function write(field, value, caret) {
    field.value = value;
    if (document.activeElement === field) { try { field.setSelectionRange(caret, caret); } catch (_) {} }
    field.dispatchEvent(new Event("input", { bubbles: true }));
  }
  function press(key) {
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
    if (!rule(field).shape.test(next) || !rule(field).fits(next)) { refuse(field); return; }
    write(field, next, caret);
  }
  function act(key) { try { press(key); } catch (error) { giveUp(error); } }

  // Listeners for the whole tab. Each does nothing while no page has the keys.
  // A key acts as the finger goes down, and the field keeps its focus and caret.
  document.addEventListener("pointerdown", function (event) {
    if (!pad) return;
    var field = event.target.closest && event.target.closest("input[data-numpad]");
    if (field) mark(field); // before the focus that would call the phone's keyboard
    var key = event.target.closest && event.target.closest(".numpad-key");
    if (!key || !pad.contains(key)) return;
    event.preventDefault();
    downAt = Date.now(); downKey = key;
    act(key.dataset.key);
    if (key.dataset.key === "del") hold = setTimeout(function () { // held: clear the field
      if (target && target.isConnected && target.value) { try { write(target, "", 0); } catch (error) { giveUp(error); } }
    }, 500);
  }, true);
  function lift() { clearTimeout(hold); }
  window.addEventListener("pointerup", lift);
  window.addEventListener("pointercancel", lift);
  // A key reached without a pointer (a physical keyboard, a screen reader) acts on its click.
  document.addEventListener("click", function (event) {
    var key = pad && event.target.closest && event.target.closest(".numpad-key");
    if (!key || !pad.contains(key)) return;
    if (key === downKey && Date.now() - downAt < 700) return; // the pointer already acted
    act(key.dataset.key);
  });
  document.addEventListener("focusin", function (event) {
    if (!pad) return;
    if (served(event.target)) { try { show(event.target); } catch (error) { giveUp(error); } }
    else if (pad.isConnected && typing(event.target)) hide(); // a text field: the phone's keyboard is on its way
  });
  // "close" does not bubble; the capture phase still passes here. The sheet takes its content back.
  document.addEventListener("close", function (event) { if (pad && event.target.contains && event.target.contains(pad)) hide(); }, true);
  document.addEventListener("live:updated", function () { if (pad) markAll(); });
  document.addEventListener("inplace:updated", function () { if (pad) markAll(); });
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
    pad = build();
    markAll();
    return function () { hide(); pad = null; };
  });
})();

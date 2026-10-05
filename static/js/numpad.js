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
  // The next field to fill: the first later one that is empty with nothing saved, else simply the next.
  function following(field) {
    var all = Array.prototype.filter.call(document.querySelectorAll("input[data-numpad]"), function (el) { return served(el) && !slot(el) && el.getClientRects().length; });
    var later = all.slice(all.indexOf(field) + 1);
    return later.filter(function (el) { return !el.value && !el.dataset.saved; })[0] || later[0] || null;
  }
  function openPanel(field) {
    if (leaving) { leaving.cancel(); leaving = null; }
    if (pad.parentNode !== panel) panel.appendChild(pad);
    panel.querySelector("[data-numpad-label]").textContent = name(field);
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
    target = field;
    mark(field);
    var place = slot(field);
    if (!place) { openPanel(field); return; }
    closePanel();
    if (pad.parentNode !== place) place.appendChild(pad);
  }
  function hide(atOnce) {
    clearTimeout(hold);
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
    var key = pad && event.target.closest && event.target.closest(".numpad-key, [data-numpad-next], [data-numpad-done]");
    if (!key || !(pad.contains(key) || (panel && panel.contains(key)))) return;
    if (key === downKey && Date.now() - downAt < 700) return; // the pointer already acted
    if (key.dataset.key) act(key.dataset.key); else move(key);
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

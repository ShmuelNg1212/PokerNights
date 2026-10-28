// Session denominations and one player's stack. The preview never records money.
(function () {
  "use strict";
  var LIMIT = 100000000000n;
  var STACK = 20, SHOWN_STACKS = 4; // a stack is 20 chips of a colour; past four stacks the rack shows one column and ×N
  var drafts = Object.create(null);
  function remember(form) {
    if (form.closest('dialog.closing')) return;
    var values = {};
    form.querySelectorAll('[data-chip-quantity]').forEach(function (input) { values[input.name] = input.value; });
    if (Object.values(values).some(function (value) { return value.trim() !== ''; }))
      drafts[form.dataset.chipKey] = {revision: form.querySelector('[name=chip_revision]').value, values: values};
    else delete drafts[form.dataset.chipKey];
  }
  function amount(value, unit) {
    if (unit === "chips") return value.toLocaleString("en-US") + (value === 1n ? " chip" : " chips");
    var cents = value % 100n;
    return "₱" + (value / 100n).toLocaleString("en-US") + (cents ? "." + String(cents).padStart(2, "0") : "");
  }
  function preview(form) {
    // Turbo can retire controls in an accepted sheet while its closing motion finishes.
    if (form.closest('dialog.closing')) return;
    var quantityRows = Array.from(form.querySelectorAll('[data-chip-quantity-row]'));
    if (quantityRows.some(function (row) { return !row.querySelector('[data-chip-quantity]'); })) return;
    var revision = form.querySelector('[name=chip_revision]').value;
    var current = form.dataset.chipCurrentRevision;
    document.querySelectorAll('[data-chip-count]').forEach(function (other) {
      if (other.dataset.chipKey === form.dataset.chipKey && Number(other.dataset.chipCurrentRevision) > Number(current)) current = other.dataset.chipCurrentRevision;
    });
    var stale = String(revision) !== String(current);
    form.querySelector('[data-chip-stale]').hidden = !stale;
    form.querySelector('.btn-primary').disabled = stale;
    form.querySelector('[data-chip-empty]').disabled = stale;
    var total = 0n, typed = false, invalid = false, pairs = [], shares = [];
    form.querySelectorAll("[data-chip-quantity-row]").forEach(function (row) {
      var input = row.querySelector("[data-chip-quantity]"), text = input.value.trim(), subtotal = 0n;
      var bad = !!text && !/^[0-9]{1,12}$/.test(text);
      if (text) { typed = true; pairs.push([input.name.slice(4), text]); }
      if (!bad && text) subtotal = BigInt(text) * BigInt(row.dataset.value);
      if (subtotal > LIMIT) bad = true;
      total += subtotal; invalid = invalid || bad;
      input.setAttribute("aria-invalid", bad ? "true" : "false");
      row.querySelector("[data-chip-subtotal]").textContent = bad ? "Check quantity" : amount(subtotal, form.dataset.unit);
      rack(row, bad || !text ? 0 : Number(text));
      shares.push([row, bad ? 0n : subtotal]);
    });
    invalid = invalid || total > LIMIT;
    form.querySelector("[data-chip-preview-label]").textContent = "· preview";
    form.querySelector("[data-chip-total]").textContent = stale ? "Recount needed" : invalid ? "Check quantities" : typed ? amount(total, form.dataset.unit) : "—";
    makeup(form, invalid || stale ? 0n : total, shares);
    var hint = form.querySelector("[data-chip-hint]");
    hint.textContent = invalid ? "Use whole quantities. The total must be within the allowed amount." : "";
    hint.hidden = !invalid;
    if (carrier(form)) form.querySelector('.btn-primary').textContent = typed && !invalid && !stale ? "Use " + amount(total, form.dataset.unit) : "Use count";
    return {total: total, typed: typed, invalid: invalid, stale: stale, pairs: pairs, revision: Number(revision)};
  }

  // --- The rack. The quantity field is the record; the drawing follows it and is hidden from screen readers.
  // Full stacks stand as ridged columns, loose chips lie as discs beside them.
  function rack(row, n) {
    var box = row.querySelector("[data-chip-rack]");
    if (!box) return;
    var stacks = Math.floor(n / STACK), loose = n % STACK, html = "";
    if (box.dataset.n === String(n)) return;
    box.dataset.n = String(n);
    for (var i = 0; i < (stacks > SHOWN_STACKS ? 1 : stacks); i++) html += '<i class="rack-stack"></i>';
    if (stacks > SHOWN_STACKS) html += '<b class="rack-more">×' + stacks + "</b>"; // one column and its count, never more columns than stacks
    for (var j = 0; j < loose; j++) html += '<i class="rack-disc"></i>';
    box.innerHTML = html;
  }
  // The make-up bar: each colour's share of the total, in its colour.
  function makeup(form, total, shares) {
    var bar = form.querySelector("[data-chip-makeup]");
    if (!bar) return;
    bar.replaceChildren();
    if (total <= 0n) return;
    shares.forEach(function (share) {
      if (share[1] <= 0n) return;
      var part = document.createElement("i");
      part.style.background = share[0].style.getPropertyValue("--c");
      part.style.flexGrow = String(Number(share[1] * 10000n / total) || 1);
      bar.appendChild(part);
    });
  }
  // A tap on the drawn chip adds one, holding it takes one off, and +20 adds a stack.
  // The row's field takes focus, so the keys serve it next. Taking the last chip off leaves the field blank.
  function add(row, step) {
    var input = row.querySelector("[data-chip-quantity]"), text = input.value.trim();
    var now = /^[0-9]{1,12}$/.test(text) ? Number(text) : 0, next = now + step;
    if (next < 0 || String(next).length > 12) return;
    if (document.activeElement !== input) input.focus({preventScroll: true});
    input.value = next ? String(next) : "";
    input.dispatchEvent(new Event("input", {bubbles: true}));
    if (step < 0) return;
    var box = row.querySelector("[data-chip-rack]");
    land(step === 1 && box.querySelector(".rack-disc:last-of-type") || box.querySelector(".rack-more") || box.querySelector(".rack-stack:last-of-type"));
  }
  // The newest disc or stack drops into place. Without Motion, or under reduced motion, it is simply there.
  function land(el) {
    var M = window.pokerMotion;
    if (!el || !M || !M.on()) return;
    el.style.opacity = "0"; el.style.transform = "translateY(-8px)"; // Motion starts a frame late (footgun)
    var moving = M.run(el, { opacity: [0, 1], transform: ["translateY(-8px)", "translateY(0px)"] }, "drop");
    if (moving) M.settle(el, moving, ["opacity", "transform"]); else { el.style.opacity = ""; el.style.transform = ""; }
  }
  var HOLD = 500, holding = null, held = null; // the same hold as the number keys' Delete
  document.addEventListener("pointerdown", function (event) {
    var tap = event.target.closest && event.target.closest("[data-chip-tap], [data-chip-stack]");
    if (!tap) return;
    event.preventDefault(); // the field keeps focus
    clearTimeout(holding); held = null;
    if (tap.hasAttribute("data-chip-tap")) holding = setTimeout(function () { held = tap; add(tap.closest("[data-chip-quantity-row]"), -1); }, HOLD);
  });
  function lift() { clearTimeout(holding); }
  window.addEventListener("pointerup", lift);
  window.addEventListener("pointercancel", lift);
  document.addEventListener("click", function (event) {
    var tap = event.target.closest && event.target.closest("[data-chip-tap], [data-chip-stack]");
    var row = tap && tap.closest("[data-chip-quantity-row]");
    if (!row) return;
    if (held === tap) { held = null; return; } // the hold already took one off
    add(row, tap.hasAttribute("data-chip-stack") ? STACK : 1);
  });

  // --- On the set page the sheet is a calculator. It writes its total into the player's count field and
  // its quantities into the row's chip field; "Confirm all counts", or the card's Send, saves both.
  // The native chip page has no chip field, so it still sends the count itself.
  function carrier(form) {
    return form.closest("dialog") ? document.querySelector('[data-chip-carry="' + form.dataset.chipKey + '"]') : null;
  }
  function plain(value, unit) {
    if (unit === "chips") return String(value);
    var cents = value % 100n;
    return String(value / 100n) + (cents ? "." + String(cents).padStart(2, "0") : "");
  }
  function shownBy(carry) { try { return carry.value ? JSON.parse(carry.value).shown : null; } catch (_) { return null; } }
  function storeKey() { var region = document.getElementById("live"); return region && region.dataset.url ? "rack-chips:" + region.dataset.url : null; }
  // A chip field holds only while its count field still shows the sheet's total: typing over it drops the chips.
  function holdChips() {
    var kept = {};
    document.querySelectorAll("[data-chip-carry]").forEach(function (carry) {
      var key = carry.dataset.chipCarry, field = document.querySelector('[data-sheet-return="' + key + '"]');
      if (carry.value && (!field || field.value.trim() !== shownBy(carry))) carry.value = "";
      if (carry.value) kept[key] = carry.value;
      var note = document.querySelector('[data-chip-note="' + key + '"]');
      if (note) note.hidden = !carry.value;
    });
    // Kept for this tab, as counts.js keeps the typed counts, so leaving the page does not lose the breakdown.
    try { var at = storeKey(); if (at) { if (Object.keys(kept).length) sessionStorage.setItem(at, JSON.stringify(kept)); else sessionStorage.removeItem(at); } } catch (_) {}
  }
  function recall() {
    var kept;
    try { kept = JSON.parse(sessionStorage.getItem(storeKey())); } catch (_) {}
    if (!kept) return;
    Object.keys(kept).forEach(function (key) {
      var carry = document.querySelector('[data-chip-carry="' + key + '"]');
      if (carry && !carry.value) carry.value = kept[key];
    });
  }
  function fill(form, empty) {
    var carry = carrier(form), field = carry && document.querySelector('[data-sheet-return="' + form.dataset.chipKey + '"]');
    if (!field) return false;
    if (empty) form.querySelectorAll("[data-chip-quantity]").forEach(function (input) { input.value = ""; });
    var sum = preview(form);
    if (sum.stale) return true;
    if (!empty && (sum.invalid || !sum.typed)) {
      var hint = form.querySelector("[data-chip-hint]");
      if (!sum.invalid) { hint.textContent = "Enter a quantity, or choose No chips left."; hint.hidden = false; }
      return true;
    }
    var shown = plain(empty ? 0n : sum.total, form.dataset.unit);
    carry.value = JSON.stringify({quantities: empty ? [] : sum.pairs, revision: sum.revision, empty_stack: !!empty, shown: shown});
    field.value = shown;
    // A key typed next goes after the total. Focus comes back when the sheet closes, and moves the caret to the start.
    field.addEventListener("focus", function () { try { field.setSelectionRange(field.value.length, field.value.length); } catch (_) {} }, {once: true});
    field.dispatchEvent(new Event("input", {bubbles: true})); // the host dock's preview follows
    remember(form);
    holdChips();
    var close = form.closest("dialog").querySelector(".sheet-head button");
    if (close) close.click();
    return true;
  }
  // The sheet opens with the quantities its chip field holds, when the page came back from a refusal.
  function refill(form) {
    var carry = carrier(form), data = null;
    if (!carry || !carry.value) return;
    try { data = JSON.parse(carry.value); } catch (_) { return; }
    var inputs = Array.from(form.querySelectorAll("[data-chip-quantity]"));
    if (inputs.some(function (input) { return input.value.trim(); })) return;
    (data.quantities || []).forEach(function (pair) {
      var input = form.querySelector('[name="qty_' + pair[0] + '"]');
      if (input) input.value = pair[1];
    });
  }
  function update(root) {
    root.querySelectorAll("[data-chip-count]").forEach(function (form) {
      var draft = drafts[form.dataset.chipKey];
      if (draft) {
        form.querySelector('[name=chip_revision]').value = draft.revision;
        form.querySelectorAll('[data-chip-quantity]').forEach(function (input) {
          if (Object.hasOwn(draft.values, input.name)) input.value = draft.values[input.name];
        });
      }
      preview(form);
    });
  }
  document.addEventListener("input", function (event) {
    if (event.target.matches("[data-chip-quantity]")) {
      var form = event.target.closest('form'); remember(form); preview(form);
    }
  });
  // Before forms.js, Turbo and sheets.js see it: a calculator sheet sends nothing.
  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!form.matches || !form.matches("[data-chip-count]")) return;
    var empty = !!event.submitter?.matches("[data-chip-empty]");
    if (fill(form, empty)) { event.preventDefault(); event.stopPropagation(); }
  }, true);
  document.addEventListener("input", function (event) {
    if (event.target.matches && event.target.matches("[data-sheet-return]")) holdChips();
  });
  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!form.matches("[data-chip-count]") || !event.submitter?.matches("[data-chip-empty]")) return;
    // Empty stack is an explicit zero, not an inference from untouched fields.
    form.querySelectorAll("[data-chip-quantity]").forEach(function (input) { input.value = ""; });
    preview(form);
  }, true);
  document.addEventListener("keydown", function (event) {
    if (event.key !== "Enter" || !event.target.matches || !event.target.matches("[data-chip-preset-name]")) return;
    event.preventDefault();
    event.target.form.querySelector("[data-chip-save-preset]").click();
  });
  document.addEventListener("sheet:shown", function (event) {
    event.detail.body.querySelectorAll("[data-chip-count]").forEach(refill);
    update(event.detail.body);
  });
  document.addEventListener("live:updating", function () { document.querySelectorAll('[data-chip-count]').forEach(remember); });
  document.addEventListener("inplace:updated", function (event) {
    var form = event.detail.form;
    if (form?.matches('[data-chip-count]') && !document.querySelector('.message-error')) delete drafts[form.dataset.chipKey];
  });
  document.addEventListener("live:updated", function () { update(document); holdChips(); });
  document.addEventListener("inplace:updated", holdChips);

  window.pokerPage.register(function () {
    drafts = Object.create(null);
    document.documentElement.classList.add("chip-rack-on"); // the rack controls work from here on
    recall();
    setTimeout(holdChips, 0); // after counts.js has put back the typed counts the chip fields belong to
    update(document);
    var form = document.querySelector("[data-chip-values]");
    if (!form || form.querySelector("fieldset[disabled]")) return;
    var life = new AbortController(), list = form.querySelector("[data-chip-value-rows]"),
      template = form.querySelector("[data-chip-value-template]"), count = form.querySelector("[name=chips-TOTAL_FORMS]"),
      add = form.querySelector("[data-chip-add]"), palette = JSON.parse(document.getElementById("chip-colours").textContent);
    function rows() { return Array.from(list.querySelectorAll("[data-chip-value-row]")).filter(function (row) { return !row.querySelector('[name$="-DELETE"]').checked; }); }
    function paint(row) {
      var select = row.querySelector("select"), colour = palette.find(function (item) { return item.key === select.value; });
      row.querySelector("[data-chip-swatch]").style.backgroundColor = colour ? colour.hex : "transparent";
    }
    function sync() {
      var active = rows();
      add.disabled = active.length >= 12;
      list.querySelectorAll("[data-chip-value-row]").forEach(function (row) {
        paint(row);
        var removed = row.querySelector('[name$="-DELETE"]').checked;
        row.hidden = removed;
        row.querySelectorAll("input:not([type=checkbox]), select").forEach(function (field) { field.required = !removed && !field.name.endsWith("-label"); });
      });
    }
    form.addEventListener("click", function (event) {
      if (!event.target.closest("[data-chip-add]")) return;
      event.preventDefault();
      if (rows().length >= 12) return;
      // Reuse a removed slot so repeated add/remove actions cannot exhaust the formset limit.
      var slot = Array.from(list.querySelectorAll("[data-chip-value-row]")).find(function (row) { return row.hidden; });
      if (slot) blank(slot); else slot = fresh();
      sync();
      var motion = window.pokerMotion;
      if (motion) motion.settle(slot, motion.run(slot, { opacity: [0, 1], transform: ["translateY(8px)", "translateY(0px)"] }, "shift"), ["opacity", "transform"]);
      slot.querySelector("select").focus();
    }, {signal: life.signal});
    function blank(row) {
      row.querySelectorAll("input").forEach(function (input) { input.value = input.type === "checkbox" ? "on" : ""; input.checked = false; });
      row.querySelector("select").value = ""; row.querySelectorAll(".errorlist").forEach(function (el) { el.remove(); });
    }
    function fresh() {
      var holder = document.createElement("template"); holder.innerHTML = template.innerHTML.replaceAll("__prefix__", count.value);
      var row = holder.content.firstElementChild; list.appendChild(row); count.value = String(Number(count.value) + 1);
      return row;
    }
    // A group preset fills the rows in place; the server's Fill does the same without JavaScript. Nothing saves.
    var pick = document.querySelector("[data-chip-preset-form]"), offered = document.getElementById("chip-presets");
    if (pick && offered) {
      var presets = JSON.parse(offered.textContent);
      pick.addEventListener("submit", function (event) {
        var chosen = presets[pick.elements.preset.value];
        if (!chosen) return;
        event.preventDefault();
        var all = Array.from(list.querySelectorAll("[data-chip-value-row]"));
        chosen.rows.forEach(function (values, at) {
          var row = all[at] || fresh();
          blank(row);
          row.querySelector('[name$="-colour"]').value = values.colour;
          row.querySelector('[name$="-label"]').value = values.label;
          row.querySelector('[name$="-value"]').value = values.value;
        });
        all.slice(chosen.rows.length).forEach(function (row) { row.querySelector('[name$="-DELETE"]').checked = true; });
        sync();
        form.querySelector("[data-chip-from-preset]").value = pick.elements.preset.value;
        pick.querySelector("[data-chip-preset-note]").textContent = "Filled from " + chosen.name + ". Check the values, then save.";
        var motion = window.pokerMotion;
        if (motion) rows().forEach(function (row, at) {
          motion.settle(row, motion.run(row, { opacity: [0, 1], transform: ["translateY(8px)", "translateY(0px)"] }, "shift", { delay: at * 0.03 }), ["opacity", "transform"]);
        });
      }, {signal: life.signal});
    }
    form.addEventListener("change", function (event) {
      var row = event.target.closest("[data-chip-value-row]"); if (!row) return;
      if (event.target.name.endsWith("-DELETE")) {
        sync(); add.focus();
      } else paint(row);
    }, {signal: life.signal});
    sync();
    return function () { life.abort(); };
  });
})();

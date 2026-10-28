// Session denominations and one player's stack. The preview never records money.
(function () {
  "use strict";
  var LIMIT = 100000000000n;
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
    var total = 0n, typed = false, invalid = false;
    form.querySelectorAll("[data-chip-quantity-row]").forEach(function (row) {
      var input = row.querySelector("[data-chip-quantity]"), text = input.value.trim(), subtotal = 0n;
      var bad = !!text && !/^[0-9]{1,12}$/.test(text);
      if (text) typed = true;
      if (!bad && text) subtotal = BigInt(text) * BigInt(row.dataset.value);
      if (subtotal > LIMIT) bad = true;
      total += subtotal; invalid = invalid || bad;
      input.setAttribute("aria-invalid", bad ? "true" : "false");
      row.querySelector("[data-chip-subtotal]").textContent = bad ? "Check quantity" : amount(subtotal, form.dataset.unit);
    });
    invalid = invalid || total > LIMIT;
    form.querySelector("[data-chip-preview-label]").textContent = "· preview";
    form.querySelector("[data-chip-total]").textContent = stale ? "Recount needed" : invalid ? "Check quantities" : typed ? amount(total, form.dataset.unit) : "—";
    form.querySelector("[data-chip-hint]").textContent = invalid
      ? "Use whole quantities. The total must be within the allowed amount."
      : "Leave unused colours blank. Use Empty stack if there are no chips left.";
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
  document.addEventListener("sheet:shown", function (event) { update(event.detail.body); });
  document.addEventListener("live:updating", function () { document.querySelectorAll('[data-chip-count]').forEach(remember); });
  document.addEventListener("inplace:updated", function (event) {
    var form = event.detail.form;
    if (form?.matches('[data-chip-count]') && !document.querySelector('.message-error')) delete drafts[form.dataset.chipKey];
  });
  document.addEventListener("live:updated", function () { update(document); });

  window.pokerPage.register(function () {
    drafts = Object.create(null);
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

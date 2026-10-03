// Dialog forms stay outside polling.
(function () {
  "use strict";
  var region = document.getElementById("live"), mount = document.getElementById("table-sheets");
  if (!region || !mount || !window.HTMLDialogElement) return;
  var dialog = document.createElement("dialog");
  dialog.className = "sheet"; dialog.setAttribute("aria-labelledby", "sheet-title");
  dialog.innerHTML = '<div class="sheet-head"><h2 id="sheet-title"></h2><button type="button" class="btn btn-round" aria-label="Close sheet"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m18 6-12 12M6 6l12 12"/></svg></button></div><div class="sheet-body"></div>';
  mount.appendChild(dialog);
  var body = dialog.querySelector(".sheet-body"), opener, source, key;
  var draftKey = "rack-draft:" + region.dataset.url;
  document.documentElement.classList.add("sheets-enabled");
  function find(id) { return region.querySelector('[data-sheet-source="' + id + '"]'); }
  function open(id, button) {
    source = find(id); if (!source || dialog.open) return;
    key = id; opener = button;
    dialog.querySelector("h2").textContent = source.dataset.title;
    body.appendChild(source.querySelector(".sheet-content"));
    dialog.showModal();
    var field = body.querySelector("input:not([type=hidden]), button");
    if (field) { field.focus(); if (field.select) field.select(); }
  }
  function close() {
    if (!dialog.open || dialog.classList.contains("closing")) return;
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) dialog.close();
    else { dialog.classList.add("closing"); setTimeout(function () { dialog.close(); dialog.classList.remove("closing"); }, 200); }
  }
  dialog.addEventListener("cancel", function (event) { event.preventDefault(); close(); });
  dialog.querySelector(".sheet-head button").addEventListener("click", close);
  dialog.addEventListener("click", function (event) {
    if (event.target !== dialog) return;
    var box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) close();
  });
  dialog.addEventListener("close", function () {
    var current = find(key), content = body.querySelector(".sheet-content");
    if (content && current) {
      var replacement = current.querySelector(".sheet-content");
      if (replacement) replacement.replaceWith(content); else current.appendChild(content);
    }
    body.replaceChildren();
    var target = opener && opener.isConnected ? opener : region.querySelector('[data-sheet-open="' + key + '"]');
    if (target) target.focus(); else region.querySelector("h1")?.focus();
  });
  // Explicit wrap keeps focus within the sheet even with browser-specific dialog traversal.
  dialog.addEventListener("keydown", function (event) {
    if (event.key !== "Tab") return;
    var items = Array.from(dialog.querySelectorAll('button:not(:disabled), input:not([type=hidden]):not(:disabled), select, textarea, a[href], summary')).filter(function (el) { return el.getClientRects().length; });
    var first = items[0], last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) { last.focus(); event.preventDefault(); }
    if (!event.shiftKey && document.activeElement === last) { first.focus(); event.preventDefault(); }
  });
  document.addEventListener("click", function (event) {
    var trigger = event.target.closest("[data-sheet-open]");
    if (trigger) open(trigger.dataset.sheetOpen, trigger);
    var quick = event.target.closest("[data-amount]");
    if (quick) { var field = quick.closest("form").querySelector("[name=amount]"); field.value = quick.dataset.amount; field.focus(); }
  });
  document.addEventListener("submit", function (event) {
    if (!dialog.contains(event.target)) return;
    var form = event.target, fields = {};
    form.querySelectorAll("[data-keep]").forEach(function (el) { fields[el.dataset.keep] = el.value; });
    try { sessionStorage.setItem(draftKey, JSON.stringify({key: key, action: form.getAttribute("action"), fields: fields, left: !!form.querySelector('[name=left]:checked')})); } catch (_) {}
  });
  // Refused server submissions reopen the form with the exact typed values.
  var saved;
  try { saved = JSON.parse(sessionStorage.getItem(draftKey)); sessionStorage.removeItem(draftKey); } catch (_) {}
  var error = document.querySelector(".message-error");
  if (saved && error && find(saved.key)) {
    open(saved.key, region.querySelector('[data-sheet-open="' + saved.key + '"]'));
    var form = Array.from(body.querySelectorAll("form")).find(function (el) { return el.getAttribute("action") === saved.action; });
    if (form) {
      form.querySelectorAll("[data-keep]").forEach(function (el) { if (Object.hasOwn(saved.fields, el.dataset.keep)) el.value = saved.fields[el.dataset.keep]; });
      var field = form.querySelector("[name=amount]");
      var note = document.createElement("p"); note.className = "sheet-error"; note.id = "sheet-error"; note.setAttribute("role", "alert"); note.textContent = error.textContent;
      form.prepend(note);
      if (field) { field.setAttribute("aria-invalid", "true"); field.setAttribute("aria-describedby", note.id); field.focus(); }
      var left = form.querySelector("[name=left]"); if (left) left.checked = saved.left;
    }
  }
})();

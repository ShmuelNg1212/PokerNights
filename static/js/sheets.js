// Bottom sheets for one focused task (buy-in, cash-out, player details, the session recap).
// The sheet is a native dialog this script creates per page and removes when the page is left.
(function () {
"use strict";
var S = null; // the current page's sheet: {region, dialog, body, opener, key, draftKey, discard}
function find(id) { return S.region.querySelector('[data-sheet-source="' + id + '"]'); }
function open(id, button) {
var source = find(id); if (!source || S.dialog.open) return;
S.key = id; S.opener = button;
S.dialog.querySelector("h2").textContent = source.dataset.title;
S.body.appendChild(source.querySelector(".sheet-content"));
S.dialog.showModal();
if (window.pokerMotion) window.pokerMotion.run(S.dialog, { transform: ["translateY(" + S.dialog.offsetHeight + "px)", "translateY(0px)"] }, "sheet");
var field = S.body.querySelector("input:not([type=hidden]), button");
if (field) { field.focus(); if (field.select) field.select(); }
}
function close() {
var dialog = S.dialog;
if (!dialog.open || dialog.classList.contains("closing")) return;
// With Motion the sheet leaves from wherever it is, so a close during the rise turns it around.
var leaving = window.pokerMotion && window.pokerMotion.run(dialog, { transform: "translateY(" + dialog.offsetHeight + "px)" }, "leave");
if (leaving) {
dialog.classList.add("closing");
window.pokerMotion.after(leaving, function () { if (dialog.open) dialog.close(); dialog.classList.remove("closing"); });
window.pokerMotion.settle(dialog, leaving);
}
else if (matchMedia("(prefers-reduced-motion: reduce)").matches) dialog.close();
else { dialog.classList.add("closing"); setTimeout(function () { if (dialog.open) dialog.close(); dialog.classList.remove("closing"); }, 200); }
}
// Puts a refusal inside the sheet, beside the amount, and makes the form ready to send again.
function showError(form, text) {
var note = form.querySelector(".sheet-error") || document.createElement("p");
note.className = "sheet-error"; note.id = "sheet-error"; note.setAttribute("role", "alert"); note.textContent = text;
form.prepend(note);
var field = form.querySelector("[name=amount]");
if (field) { field.setAttribute("aria-invalid", "true"); field.setAttribute("aria-describedby", note.id); field.focus(); }
}

// Listeners for the whole tab. Each does nothing on a page without a sheet.
document.addEventListener("click", function (event) {
var trigger = event.target.closest("[data-sheet-open]");
if (trigger && S) open(trigger.dataset.sheetOpen, trigger);
var quick = event.target.closest("[data-amount]");
if (quick) { var field = quick.closest("form").querySelector("[name=amount]"); field.value = quick.dataset.amount; field.focus(); }
});
document.addEventListener("submit", function (event) {
if (!S || !S.dialog.contains(event.target)) return;
var form = event.target, fields = {};
form.querySelectorAll("[data-keep]").forEach(function (el) { fields[el.dataset.keep] = el.value; });
try { sessionStorage.setItem(S.draftKey, JSON.stringify({key: S.key, action: form.getAttribute("action"), fields: fields, left: !!form.querySelector('[name=left]:checked')})); } catch (_) {}
});
// A form in the sheet was sent in the background (see turbo-setup.js) and the page has been updated.
document.addEventListener("inplace:updated", function (event) {
if (!S) return;
var form = event.detail.form;
try { sessionStorage.removeItem(S.draftKey); } catch (_) {}
if (!form || !S.dialog.contains(form)) return;
var error = document.querySelector(".message-error");
if (error) {
// Refused: keep the sheet and what was typed, and take the fresh request id from the page.
var source = find(S.key), fresh = source && Array.from(source.querySelectorAll("form")).find(function (el) { return el.getAttribute("action") === form.getAttribute("action"); });
var id = form.querySelector("[name=request_id]"), freshId = fresh && fresh.querySelector("[name=request_id]");
if (id && freshId) id.value = freshId.value;
delete form.dataset.sent;
form.querySelectorAll("button[type=submit]").forEach(function (button) { button.disabled = false; button.removeAttribute("aria-busy"); if (button.dataset.label) button.textContent = button.dataset.label; });
showError(form, error.textContent);
return;
}
S.discard = true; // the page already holds a fresh copy of the sheet's form
close();
});
document.addEventListener("inplace:failed", function (event) {
if (S && event.detail.form && S.dialog.contains(event.detail.form)) showError(event.detail.form, event.detail.message);
});

window.pokerPage.register(function () {
var region = document.getElementById("live") || document.querySelector(".night-layout"), mount = document.getElementById("table-sheets");
if (!region || !mount || !window.HTMLDialogElement) return;
var dialog = document.createElement("dialog");
dialog.className = "sheet"; dialog.setAttribute("aria-labelledby", "sheet-title");
dialog.innerHTML = '<div class="sheet-head"><h2 id="sheet-title"></h2><button type="button" class="btn btn-round" aria-label="Close sheet"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m18 6-12 12M6 6l12 12"/></svg></button></div><div class="sheet-body"></div>';
mount.replaceChildren(dialog);
var me = S = {region: region, dialog: dialog, body: dialog.querySelector(".sheet-body"), opener: null, key: null,
              draftKey: "rack-draft:" + region.dataset.url, discard: false};
document.documentElement.classList.add("sheets-enabled");
dialog.addEventListener("cancel", function (event) { event.preventDefault(); close(); });
dialog.querySelector(".sheet-head button").addEventListener("click", close);
dialog.addEventListener("click", function (event) {
if (event.target !== dialog) return;
var box = dialog.getBoundingClientRect();
if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) close();
});
dialog.addEventListener("close", function () {
var current = me.region.querySelector('[data-sheet-source="' + me.key + '"]'), content = me.body.querySelector(".sheet-content");
if (me.discard) { content = null; me.discard = false; }
if (content && current) {
var replacement = current.querySelector(".sheet-content");
if (replacement) replacement.replaceWith(content); else current.appendChild(content);
}
me.body.replaceChildren();
if (S !== me) return; // the page is being left; there is nothing to focus
var target = me.opener && me.opener.isConnected ? me.opener : me.region.querySelector('[data-sheet-open="' + me.key + '"]');
if (target) target.focus(); else me.region.querySelector("h1")?.focus();
});
dialog.addEventListener("keydown", function (event) {
if (event.key !== "Tab") return;
var items = Array.from(dialog.querySelectorAll('button:not(:disabled), input:not([type=hidden]):not(:disabled), select, textarea, a[href], summary')).filter(function (el) { return el.getClientRects().length; });
var first = items[0], last = items[items.length - 1];
if (event.shiftKey && document.activeElement === first) { last.focus(); event.preventDefault(); }
if (!event.shiftKey && document.activeElement === last) { first.focus(); event.preventDefault(); }
});
function stop() {
if (S === me) S = null;
if (dialog.open) dialog.close();
dialog.remove();
document.documentElement.classList.remove("sheets-enabled");
}
var recap = region.querySelector("[data-recap]");
if (recap) {
try {
var seen = "rack-recap:" + recap.dataset.recap;
if (!localStorage.getItem(seen)) {
localStorage.setItem(seen, "1");
open("recap", region.querySelector('[data-sheet-open="recap"]'));
}
} catch (_) {}
return stop;
}
// A refused form that came back by a full page load: reopen its sheet with what was typed.
var saved;
try { saved = JSON.parse(sessionStorage.getItem(me.draftKey)); sessionStorage.removeItem(me.draftKey); } catch (_) {}
var error = document.querySelector(".message-error");
if (saved && error && find(saved.key)) {
open(saved.key, region.querySelector('[data-sheet-open="' + saved.key + '"]'));
var form = Array.from(me.body.querySelectorAll("form")).find(function (el) { return el.getAttribute("action") === saved.action; });
if (form) {
form.querySelectorAll("[data-keep]").forEach(function (el) { if (Object.hasOwn(saved.fields, el.dataset.keep)) el.value = saved.fields[el.dataset.keep]; });
showError(form, error.textContent);
var left = form.querySelector("[name=left]"); if (left) left.checked = saved.left;
}
}
return stop;
});
})();

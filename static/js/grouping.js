// Amount fields group their digits as they are typed: "1000" reads "1,000", as the rows show it.
// Only peso and chip amounts are grouped (data-numpad="pesos|chips|amount"); a count of one chip colour,
// a percentage and a seat count keep plain digits. The server reads "1,000" as 1000 (ledger/money.py),
// so a field that is not grouped, or a page without this script, sends the same amount.
// numpad.js works on the digits without the commas (window.pokerGroup.raw) and sends "input", which groups.
(function () {
  "use strict";
  var KINDS = { pesos: true, chips: true, amount: true };

  function grouped(field) { return !!field && field.matches && field.matches("input[data-numpad]") && !!KINDS[field.dataset.numpad]; }
  function raw(text) { return String(text).replace(/,/g, ""); }
  // Commas go into the whole part only. Anything that is not an amount yet is left as it is.
  function group(text) {
    var plain = raw(text);
    if (!/^\d*(\.\d*)?$/.test(plain)) return text;
    var at = plain.indexOf("."), whole = at < 0 ? plain : plain.slice(0, at);
    return whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (at < 0 ? "" : plain.slice(at));
  }
  // The caret stays after the same digit: count the characters before it that are not commas.
  function place(text, kept) {
    if (kept <= 0) return 0;
    for (var i = 0, seen = 0; i < text.length; i++) {
      if (text[i] !== ",") seen++;
      if (seen === kept) return i + 1;
    }
    return text.length;
  }
  function apply(field) {
    var before = field.value, after = group(before);
    if (after === before) return;
    var focused = document.activeElement === field, caret = focused && field.selectionStart !== null ? field.selectionStart : before.length;
    var kept = raw(before.slice(0, caret)).length;
    field.value = after;
    if (focused) { try { var at = place(after, kept); field.setSelectionRange(at, at); } catch (_) {} }
  }

  window.pokerGroup = { grouped: grouped, group: group, raw: raw, apply: apply };

  document.addEventListener("input", function (event) { if (grouped(event.target)) apply(event.target); }, true);
  // A value written by a script or by the server: a quick amount, a preset, a kept draft.
  document.addEventListener("focusout", function (event) { if (grouped(event.target)) apply(event.target); }, true);
  window.pokerPage.register(function () {
    document.querySelectorAll("input[data-numpad]").forEach(function (field) { if (grouped(field)) apply(field); });
  });
})();

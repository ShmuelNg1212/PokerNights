// Local preview only. Confirmed counts and cash-outs remain server records.
(function () {
  "use strict";
  function parse(text, chips) {
    var clean = text.replace(/,/g, "").replace(chips ? /chips/g : /₱|PHP/g, "").trim();
    if (!(chips ? /^\d+$/ : /^(?:\d+(?:\.\d{0,2})?|\.\d{1,2})$/).test(clean)) return null;
    var parts = clean.split(".");
    var value = chips ? BigInt(clean) : BigInt(parts[0] || "0") * 100n + BigInt(((parts[1] || "") + "00").slice(0, 2));
    return value <= 100000000000n ? value : null;
  }
  function format(value, chips) {
    var whole = chips ? value : value / 100n;
    var text = String(whole).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return chips ? text + (value === 1n ? " chip" : " chips") : "₱" + text + (value % 100n ? "." + String(value % 100n).padStart(2, "0") : "");
  }
  // Typed counts that are not confirmed yet are kept for this tab, so leaving the page does not lose them.
  function key() { var region = document.getElementById("live"); return region && region.dataset.url ? "rack-counts:" + region.dataset.url : null; }
  function remember(typed) {
    try { if (Object.keys(typed).length) sessionStorage.setItem(key(), JSON.stringify(typed)); else sessionStorage.removeItem(key()); } catch (_) {}
  }
  function recall() {
    var typed;
    try { typed = JSON.parse(sessionStorage.getItem(key())); } catch (_) {}
    if (!typed) return;
    Object.keys(typed).forEach(function (keep) {
      var input = document.querySelector('[data-count-input][data-keep="' + keep + '"]');
      if (input && !input.value) input.value = typed[keep];
    });
  }
  function update() {
    var box = document.querySelector("[data-count-preview]");
    if (!box || typeof BigInt !== "function") return;
    var chips = box.dataset.unit === "chips";
    var remaining = 0n, missing = 0, invalid = 0, drafts = 0, typed = {};
    document.querySelectorAll("[data-count-input]").forEach(function (input) {
      var text = input.value.trim(), value = null;
      if (text) {
        drafts++; typed[input.dataset.keep] = input.value;
        value = parse(text, chips);
        if (value === null) invalid++;
      } else if (input.dataset.saved !== "") value = BigInt(input.dataset.saved);
      else missing++;
      var error = input.parentElement.querySelector("[data-count-error]");
      var bad = !!text && value === null;
      input.toggleAttribute("aria-invalid", bad);
      if (bad) input.setAttribute("aria-invalid", "true");
      error.hidden = !bad;
      error.textContent = bad ? (chips ? "Use whole chips within the allowed amount." : "Use pesos with at most two decimal places within the allowed amount.") : "";
      if (value !== null) remaining += value;
    });
    var cash = BigInt(box.dataset.cash), bought = BigInt(box.dataset.bought);
    var total = remaining + cash + BigInt(box.dataset.rake || "0"), difference = total - bought;
    var complete = box.dataset.players !== "0" && !missing && !invalid && box.dataset.stray !== "1";
    var status;
    if (invalid) status = "Preview unavailable: check the highlighted counts.";
    else if (box.dataset.players === "0") status = "No buy-ins recorded.";
    else if (box.dataset.stray === "1") status = "Cash-out without a buy-in. Check the records.";
    else if (complete && difference === 0n) status = "All counts match buy-ins.";
    else if (difference !== 0n) status = format(difference < 0n ? -difference : difference, chips) + (difference > 0n ? " extra." : missing ? " still to account for." : " missing.");
    else status = "Total matches so far; finish counting.";
    // Severity is in the colour and mark too: every count in and matching, or every count in and not.
    var tone = invalid || box.dataset.stray === "1" ? "warn" : complete ? (difference === 0n ? "good" : "warn") : "";
    if (box.dataset.players === "0") tone = "";
    // A recorded override covers the difference; typed counts put the stack check back.
    if (!drafts && box.dataset.covered) { status = box.dataset.covered; tone = ""; }
    var shown = invalid ? "Unavailable" : format(total, chips);
    function put(key, text) { box.querySelector("[data-count-" + key + "]").textContent = text; }
    put("label", drafts ? "Preview · unsaved counts" : "Confirmed counts");
    put("remaining", invalid ? "Unavailable" : format(remaining, chips));
    put("accounted", shown);
    put("status", status);
    box.querySelector("[data-count-status]").dataset.tone = tone;
    var coverage = missing + " still to count." + (invalid ? " " + invalid + " invalid." : "");
    put("coverage", coverage);
    // The collapsed dock bar repeats the running total and the verdict, so both stay readable while typing.
    var bar = document.querySelector("[data-dock-status]");
    if (bar) {
      bar.textContent = status; bar.parentElement.querySelector("[data-dock-coverage]").textContent = coverage;
      bar.dataset.tone = tone;
      document.querySelector("[data-dock-accounted]").textContent = shown;
      var prefix = document.querySelector("[data-dock-prefix]");
      if (prefix) prefix.textContent = drafts ? "Preview · " : "";
    }
    // While counts are typed, the main button confirms them and stands in for the next step.
    var confirm = document.querySelector("[data-confirm-typed]"), hint = document.getElementById("batch-why");
    if (confirm) {
      confirm.hidden = !drafts;
      if (!confirm.hasAttribute("aria-busy")) { confirm.disabled = invalid > 0; confirm.textContent = "Confirm " + drafts + (drafts === 1 ? " count" : " counts"); }
      document.querySelectorAll("[data-next-server]").forEach(function (el) { el.hidden = drafts > 0; });
      if (hint) hint.textContent = !drafts ? hint.dataset.hint : invalid ? "Check the highlighted counts first." : "Typed counts are not saved until you confirm them.";
    }
    // The numpad's strip repeats the running total while a count is typed (numpad.js).
    var note = document.querySelector("[data-numpad-note]");
    if (note) note.textContent = (drafts ? "Preview · " : "") + shown + " of " + format(bought, chips) + " · " + (missing && !invalid ? missing + " to count" : status);
    remember(typed);
  }
  document.addEventListener("input", function (event) { if (event.target.matches("[data-count-input]")) update(); });
  document.addEventListener("change", update);
  document.addEventListener("live:updated", update);
  document.addEventListener("numpad:open", update);
  window.addEventListener("pageshow", update);
  // Sending the counts hands them to the server, which shows a refused one again itself.
  document.addEventListener("submit", function (event) {
    if (event.target.id === "counts-form" && key()) { try { sessionStorage.removeItem(key()); } catch (_) {} }
  });
  window.pokerPage.register(function () {
    var on = !!document.querySelector("[data-count-preview]") && typeof BigInt === "function";
    document.documentElement.classList.toggle("counts-enhanced", on);
    if (!on) return;
    recall();
    update();
    return function () { document.documentElement.classList.remove("counts-enhanced"); };
  });
})();

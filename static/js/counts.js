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
  function update() {
    var box = document.querySelector("[data-count-preview]");
    if (!box || typeof BigInt !== "function") return;
    var chips = box.dataset.unit === "chips";
    var remaining = 0n, missing = 0, invalid = 0, drafts = false;
    document.querySelectorAll("[data-count-input]").forEach(function (input) {
      var text = input.value.trim(), value = null;
      if (text) {
        drafts = true;
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
    var total = remaining + cash, difference = total - bought;
    var complete = box.dataset.players !== "0" && !missing && !invalid && box.dataset.stray !== "1";
    var status;
    if (invalid) status = "Preview unavailable: check the highlighted counts.";
    else if (box.dataset.players === "0") status = "No buy-ins recorded.";
    else if (box.dataset.stray === "1") status = "Cash-out without a buy-in. Check the records.";
    else if (complete && difference === 0n) status = "All counts match buy-ins.";
    else if (difference !== 0n) status = format(difference < 0n ? -difference : difference, chips) + (difference > 0n ? " extra." : missing ? " still to account for." : " missing.");
    else status = "Total matches so far; finish counting.";
    function put(key, text) { box.querySelector("[data-count-" + key + "]").textContent = text; }
    put("label", drafts ? "Preview · unsaved counts" : "Confirmed counts");
    put("remaining", invalid ? "Unavailable" : format(remaining, chips));
    put("accounted", invalid ? "Unavailable" : format(total, chips));
    put("status", status);
    put("coverage", missing + " still to count." + (invalid ? " " + invalid + " invalid." : ""));
  }
  document.addEventListener("input", function (event) { if (event.target.matches("[data-count-input]")) update(); });
  document.addEventListener("change", update);
  document.addEventListener("live:updated", update);
  window.addEventListener("pageshow", update);
  update();
})();

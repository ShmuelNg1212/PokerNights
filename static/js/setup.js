// New session: choosing a preset fills the game and the stakes at once and leaves the rest of
// the form as typed. Without this script the "Use" button reloads the page with the preset.
(function () {
  "use strict";
  var root = document.documentElement;

  window.pokerPage.register(function () {
    var chooser = document.querySelector("[data-preset-form]"), form = document.querySelector("[data-preset-target]");
    if (!chooser || !form) return;
    var select = chooser.querySelector("select");
    function fill() {
      var option = select.options[select.selectedIndex], values = null;
      try { values = JSON.parse(option.dataset.fill); } catch (_) {}
      if (!values) { chooser.submit(); return; } // the page was drawn before presets carried their values
      Object.keys(values).forEach(function (name) {
        var field = form.elements[name];
        if (!field || field.value === String(values[name])) return;
        field.value = values[name];
        // The numpad follows the unit, and a refusal's mark belongs to the earlier value.
        field.dispatchEvent(new Event("change", { bubbles: true }));
      });
      var chosen = form.elements.preset_id;
      if (!chosen) { chosen = document.createElement("input"); chosen.type = "hidden"; chosen.name = "preset_id"; form.appendChild(chosen); }
      chosen.value = option.value;
    }
    select.addEventListener("change", fill);
    root.classList.add("preset-fills");
    return function () { select.removeEventListener("change", fill); root.classList.remove("preset-fills"); };
  });

  // The game and stakes read as one line while folded; it follows the form. A field the browser
  // refuses must be seen, so its fold opens.
  window.pokerPage.register(function () {
    var fold = document.querySelector("[data-stakes-fold]"), form = document.querySelector("[data-preset-target]");
    var line = fold && fold.querySelector("[data-stakes-summary]");
    if (!line || !form) return;
    function grouped(text) {
      var parts = String(text).trim().split(".");
      parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      if (parts[1] !== undefined) { if (/^0*$/.test(parts[1])) parts.pop(); else parts[1] = parts[1].padEnd(2, "0"); }
      return parts.join(".");
    }
    function money(name) {
      var value = form.elements[name] ? form.elements[name].value.trim() : "";
      if (!value) return "";
      return form.elements.unit.value === "chips" ? grouped(value) + " chips" : "₱" + grouped(value);
    }
    function rake() {
      var mode = form.elements.rake_mode.value;
      var percent = form.elements.rake_percentage.value.trim(), flat = money("rake_flat");
      if (mode === "percent") return percent ? "rake " + percent + "%" : "rake not set";
      if (mode === "flat") return flat ? "rake " + flat : "rake not set";
      return "rake off";
    }
    function show() {
      var small = money("small_blind"), big = money("big_blind"), low = money("min_buy_in"), high = money("max_buy_in"), usual = money("default_buy_in");
      var game = form.elements.game_type;
      line.textContent = small && big && low && high && usual
        ? game.options[game.selectedIndex].text + " · " + small + " / " + big + " · buy-in " + low + " to " + high + " · usual " + usual + " · " + rake()
        : line.dataset.empty;
    }
    function refused() { fold.open = true; }
    form.addEventListener("input", show); form.addEventListener("change", show);
    form.addEventListener("invalid", refused, true);
    show();
    return function () { form.removeEventListener("input", show); form.removeEventListener("change", show); form.removeEventListener("invalid", refused, true); };
  });

  // The chip preset list shows only the presets of the chosen unit. Options leave the list, because iOS shows a hidden one.
  window.pokerPage.register(function () {
    var form = document.querySelector("[data-preset-target]");
    var chooser = form && form.elements.chip_preset_id, unit = form && form.elements.unit;
    if (!chooser || !unit) return;
    var all = Array.prototype.slice.call(chooser.options);
    function follow() {
      var chosen = chooser.value, fitting = all.filter(function (option) { return !option.dataset.unit || option.dataset.unit === unit.value; });
      chooser.replaceChildren.apply(chooser, fitting);
      chooser.value = fitting.some(function (option) { return option.value === chosen; }) ? chosen : "";
      chooser.closest(".field").hidden = fitting.length < 2;
    }
    unit.addEventListener("change", follow);
    follow();
    return function () { unit.removeEventListener("change", follow); chooser.replaceChildren.apply(chooser, all); };
  });
})();

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
})();

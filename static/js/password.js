// Lets a person read what they typed in a password field. Without JavaScript the button stays hidden.
(function () {
  "use strict";
  window.pokerPage.register(function () {
  var life = new AbortController();
  document.querySelectorAll("[data-password-toggle]").forEach(function (button) {
    var form = button.closest("form");
    var fields = Array.from(form.querySelectorAll("input[type=password]"));
    function set(shown) {
      fields.forEach(function (field) { field.type = shown ? "text" : "password"; });
      button.dataset.shown = shown ? "1" : "";
      button.setAttribute("aria-label", (shown ? "Hide" : "Show") + " password");
      button.textContent = shown ? "Hide" : "Show";
    }
    button.hidden = false;
    button.addEventListener("click", function () { set(!button.dataset.shown); }, { signal: life.signal });
    // A password is never submitted, saved by the browser or left on screen as plain text.
    form.addEventListener("submit", function () { set(false); }, { signal: life.signal });
  });
  // The two rules a phone can judge tick as the person types. The server still judges all four on sending,
  // so a tick never lets through what it refuses. Django counts characters as Python does: code points.
  var tests = {
    length: function (value) { return Array.from(value).length >= 8; },
    digits: function (value) { return value.length > 0 && !/^\p{Nd}+$/u.test(value); },
  };
  document.querySelectorAll("[data-password-rules]").forEach(function (list) {
    var box = list.closest(".field"), field = box.querySelector("input"), status = box.querySelector("[data-rules-status]");
    var rules = Array.from(list.querySelectorAll("[data-rule]"));
    function update(announce) {
      var said = [];
      rules.forEach(function (rule) {
        var met = tests[rule.dataset.rule](field.value);
        if (met === ("met" in rule.dataset)) return;
        if (met) rule.dataset.met = ""; else delete rule.dataset.met;
        said.push(rule.textContent + (met ? ": done" : ": not yet"));
      });
      if (announce && said.length && status) status.textContent = said.join(". ") + ".";
    }
    update(false);  // a value the browser filled in before this ran
    field.addEventListener("input", function () { update(true); }, { signal: life.signal });
  });
  return function () { life.abort(); };
  });
})();

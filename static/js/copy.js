// Copies a link that is shown once. Without JavaScript the button stays hidden and the field is selected by hand.
(function () {
  "use strict";
  window.pokerPage.register(function () {
  var life = new AbortController(), timers = [];
  document.querySelectorAll("[data-copy]").forEach(function (button) {
    var field = document.getElementById(button.dataset.copy);
    var status = document.querySelector('[data-copy-status="' + button.dataset.copy + '"]');
    if (!field || !status) return;
    function say(text, shown) {
      status.textContent = text;
      status.classList.toggle("visually-hidden", !shown);
    }
    function rest() { button.textContent = "Copy"; delete button.dataset.copied; }
    // "Copied" is shown only once the browser has confirmed it.
    function copied() {
      if (life.signal.aborted) return;
      button.textContent = "Copied";
      button.dataset.copied = "1";
      say("Link copied.", false);
      timers.push(setTimeout(rest, 2000));
    }
    // The link cannot be shown again, so a refusal is said and the whole address is left selected.
    function refused() {
      if (life.signal.aborted) return;
      rest();
      field.focus();
      field.setSelectionRange(0, field.value.length);
      say("Could not copy. The link is selected: copy it from the menu.", true);
    }
    button.hidden = false;
    button.addEventListener("click", function () {
      var done;
      try { done = navigator.clipboard.writeText(field.value); } catch (error) { refused(); return; }
      done.then(copied, refused);
    }, { signal: life.signal });
  });
  return function () { life.abort(); timers.forEach(clearTimeout); };
  });
})();

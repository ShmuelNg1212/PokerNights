// The "Add players" picker: search, selection count, capacity message and the
// button text. The form works without this script; the server checks everything again.
(function () {
  "use strict";

  var form = document.querySelector("form[data-pick]");
  if (!form) return;

  var free = parseInt(form.dataset.free, 10) || 0;
  var search = form.querySelector("[data-pick-search]");
  var rows = Array.prototype.slice.call(form.querySelectorAll("[data-pick-row]"));
  var boxes = Array.prototype.slice.call(form.querySelectorAll('input[name="member_id"]:not(:disabled)'));
  var summary = form.querySelector("[data-pick-summary]");
  var warning = form.querySelector("[data-pick-warning]");
  var empty = form.querySelector("[data-pick-empty]");
  var submit = form.querySelector("[data-pick-submit]");

  function plural(count, word) {
    return count + " " + word + (count === 1 ? "" : "s");
  }

  // Searching only hides rows. The checkboxes stay in the form, so a tick is never lost.
  function filter() {
    var query = search.value.trim().toLowerCase();
    var shown = 0;
    rows.forEach(function (row) {
      var match = row.dataset.name.indexOf(query) !== -1;
      row.hidden = !match;
      if (match) shown += 1;
    });
    empty.hidden = shown !== 0;
  }

  function update() {
    var chosen = boxes.filter(function (box) { return box.checked; });
    var names = chosen.map(function (box) { return box.dataset.label; });
    var count = chosen.length;
    var over = count - free;

    summary.textContent = count === 0 ? "No player selected." : "Selected (" + count + "): " + names.join(", ");
    submit.textContent = count === 0 ? "Add players" : "Add " + plural(count, "player");

    if (over > 0) {
      warning.textContent = (free === 0 ? "No seat is free" : "Only " + plural(free, "seat") + (free === 1 ? " is" : " are") + " free") +
        ". Remove " + plural(over, "player") + ".";
      warning.hidden = false;
    } else {
      warning.hidden = true;
    }
    submit.disabled = count === 0 || over > 0;
  }

  form.querySelector("[data-pick-search-box]").hidden = false;
  search.addEventListener("input", filter);
  // Enter in the search field must not send the form by accident.
  search.addEventListener("keydown", function (event) { if (event.key === "Enter") event.preventDefault(); });
  form.addEventListener("change", update);
  update();
})();

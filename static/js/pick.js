// The "Add players" page: search the roster, preview the new names as they are typed, count
// the ticks and the names against the free seats, and name the button after the total.
// The form works without this script; the server checks everything again.
(function () {
  "use strict";
  var NAME_MAX = 60, HOLD_MS = 3000, FADE_MS = 400;

  window.pokerPage.register(function () {
  var life = new AbortController(), timers = [];
  var form = document.querySelector("form[data-pick]");
  if (!form) return;

  var free = parseInt(form.dataset.free, 10) || 0;
  var known = { roster: {}, seated: [], removed: [], several: true };
  try { known = Object.assign(known, JSON.parse(form.dataset.known || "{}")); } catch (_) {}
  var search = form.querySelector("[data-pick-search]");
  var rows = Array.prototype.slice.call(form.querySelectorAll("[data-pick-row]"));
  var boxes = Array.prototype.slice.call(form.querySelectorAll('input[name="member_id"]:not(:disabled)'));
  var summary = form.querySelector("[data-pick-summary]");
  var warning = form.querySelector("[data-pick-warning]");
  var empty = form.querySelector("[data-pick-empty]");
  var submit = form.querySelector("[data-pick-submit]");
  var namesBox = form.querySelector("[data-names]");
  var preview = form.querySelector("[data-names-preview]");
  var shown = {}; // preview lines by name, so a line that stays is not drawn again
  var problems = 0;

  function plural(count, word) {
    return count + " " + word + (count === 1 ? "" : "s");
  }
  function clean(line) { return line.split(/\s+/).filter(Boolean).join(" "); }
  function typed() { return namesBox ? namesBox.value.split("\n").map(clean).filter(Boolean) : []; }

  // Searching only hides rows. The checkboxes stay in the form, so a tick is never lost.
  function filter() {
    var query = search.value.trim().toLowerCase();
    var count = 0;
    rows.forEach(function (row) {
      var match = row.dataset.name.indexOf(query) !== -1;
      row.hidden = !match;
      if (match) count += 1;
    });
    empty.hidden = count !== 0;
  }

  // The same brass mark as a row that just changed on the set page, held and then faded.
  function mark(el) {
    el.classList.remove("just-changed", "change-fading");
    void el.offsetWidth;
    el.classList.add("just-changed");
    timers.push(setTimeout(function () { el.classList.add("change-fading"); }, HOLD_MS - FADE_MS));
    timers.push(setTimeout(function () { el.classList.remove("just-changed", "change-fading"); }, HOLD_MS));
  }

  // A name on the roster is ticked there instead, and its line leaves the box.
  function tickInstead(name) {
    var key = name.toLowerCase(), id = String(known.roster[key]);
    var box = boxes.filter(function (b) { return b.value === id; })[0];
    if (!box) return;
    box.checked = true;
    var row = box.closest("[data-pick-row]");
    if (row && row.hidden && search) { search.value = ""; filter(); }
    namesBox.value = namesBox.value.split("\n").filter(function (line) { return clean(line).toLowerCase() !== key; }).join("\n");
    update();
    if (row) {
      var label = row.querySelector("label") || row;
      mark(label);
      label.scrollIntoView({ block: "nearest", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    }
    namesBox.focus({ preventScroll: true });
  }

  // What each typed name will do, in the words the server would use.
  function verdicts(names) {
    var seen = {}, seated = {}, removed = {};
    known.seated.forEach(function (n) { seated[n] = 1; });
    known.removed.forEach(function (n) { removed[n] = 1; });
    return names.map(function (name) {
      var key = name.toLowerCase(), out = { name: name, key: key };
      if (name.length > NAME_MAX) out.problem = "Too long: " + NAME_MAX + " characters at most";
      else if (seen[key]) out.problem = "Typed twice";
      else if (seated[key]) out.problem = "Already at the table";
      else if (key in known.roster) { out.problem = "On the roster"; out.tick = boxes.some(function (b) { return b.value === String(known.roster[key]); }); }
      else if (removed[key]) out.problem = "Removed from this group. Bring them back in Group settings";
      else out.state = "New";
      seen[key] = 1;
      return out;
    });
  }

  function draw(list) {
    var keep = {}, M = window.pokerMotion;
    preview.hidden = list.length === 0;
    list.forEach(function (v, at) {
      var id = v.key + "|" + (v.problem || v.state), li = shown[id];
      if (!li) {
        li = document.createElement("li");
        var name = document.createElement("span"), state = document.createElement("span");
        name.className = "name"; name.textContent = v.name;
        state.className = "state"; state.textContent = v.problem || v.state;
        li.appendChild(name); li.appendChild(state);
        if (v.problem) li.dataset.problem = "";
        if (v.tick) {
          var button = document.createElement("button");
          button.type = "button"; button.className = "link-button"; button.textContent = "Tick " + v.name + " instead";
          button.addEventListener("click", function () { tickInstead(v.name); });
          li.appendChild(button);
        }
        // A new line fades in; nothing moves sideways while the host types. First frame first
        // (doc/wiki/footguns/motion_starts_a_frame_late.md).
        if (M && M.on()) { li.style.opacity = "0"; M.settle(li, M.run(li, { opacity: [0, 1] }, "fade"), ["opacity"]); }
      }
      keep[id] = li;
      if (preview.children[at] !== li) preview.insertBefore(li, preview.children[at] || null);
    });
    Object.keys(shown).forEach(function (id) { if (!keep[id]) shown[id].remove(); });
    shown = keep;
  }

  function update() {
    var chosen = boxes.filter(function (box) { return box.checked; });
    var names = typed(), list = verdicts(names);
    if (preview) draw(list);
    problems = list.filter(function (v) { return v.problem; }).length;
    var count = chosen.length + names.length;
    var over = count - free;

    var parts = [];
    if (chosen.length) parts.push(chosen.length + " ticked");
    if (names.length) parts.push(names.length + " new");
    // While names are typed the line holds counts only: it is read out as it changes.
    summary.textContent = count === 0 ? "No player selected." : names.length ? parts.join(" · ") + "." :
      "Selected (" + count + "): " + chosen.map(function (box) { return box.dataset.label; }).join(", ");
    submit.textContent = count === 0 ? "Add players" : "Add " + plural(count, "player");

    var say = "";
    if (over > 0) {
      say = (free === 0 ? "No seat is free" : "Only " + plural(free, "seat") + (free === 1 ? " is" : " are") + " free") +
        ". Remove " + plural(over, "player") + ".";
    } else if (!known.several && names.length > 1) {
      say = "Type one new name at a time.";
    } else if (problems) {
      say = (problems === 1 ? "One name needs" : problems + " names need") + " a change before adding.";
    }
    warning.textContent = say;
    warning.hidden = !say;
    if (namesBox) namesBox.toggleAttribute("aria-invalid", problems > 0);
    submit.disabled = count === 0 || !!say;
  }

  var searchBox = form.querySelector("[data-pick-search-box]");
  if (searchBox && search) {
    searchBox.hidden = false;
    search.addEventListener("input", filter, { signal: life.signal });
    // Enter in the search field must not send the form by accident.
    search.addEventListener("keydown", function (event) { if (event.key === "Enter") event.preventDefault(); }, { signal: life.signal });
  }
  if (preview) preview.setAttribute("aria-label", "New names");
  form.addEventListener("change", update, { signal: life.signal });
  if (namesBox) namesBox.addEventListener("input", update, { signal: life.signal });
  update();
  return function () { life.abort(); timers.forEach(clearTimeout); };
  });
})();

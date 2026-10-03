// Highlight accepted server values only. Amounts themselves never interpolate.
(function () {
  "use strict";
  var region = document.getElementById("live");
  if (!region) return;
  var prefix = "rack:" + region.dataset.url + ":";
  var seen = {};
  function update() {
    region.querySelectorAll("[data-watch]").forEach(function (el) {
      var key = prefix + el.dataset.watch, value = el.dataset.value;
      var previous = seen[key];
      try { if (previous === undefined) previous = sessionStorage.getItem(key); } catch (_) {}
      if (previous != null && previous !== value) {
        el.classList.add("just-changed");
        var badge = el.querySelector(".change-label");
        if (badge) badge.hidden = false;
        setTimeout(function () { el.classList.remove("just-changed"); if (badge) badge.hidden = true; }, 3000);
      }
      seen[key] = value;
      try { sessionStorage.setItem(key, value); } catch (_) {}
    });
  }
  document.addEventListener("live:updated", update);
  update();
})();

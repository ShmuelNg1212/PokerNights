// The closed session page: a transfer settles when the server accepts its payment, and
// "Settled" arrives once per session in this browser. Only classes are set here; the movement is CSS.
(function () {
  "use strict";
  var pending = null; // the transfer whose "Mark paid" was just sent
  function arrive(region) {
    var el = region.querySelector("[data-settled]");
    if (!el) return;
    var key = "settled:" + el.dataset.settled;
    try { if (localStorage.getItem(key)) return; localStorage.setItem(key, "1"); } catch (_) { return; }
    el.classList.add("settle-arrived");
  }
  document.addEventListener("submit", function (event) {
    var row = event.target.closest && event.target.closest("[data-transfer]");
    pending = row && row.dataset.paid === "0" ? row.dataset.transfer : null;
  });
  document.addEventListener("inplace:updated", function () {
    var region = document.querySelector(".night-settle"), id = pending;
    pending = null;
    if (!region) return;
    var row = id && region.querySelector('[data-transfer="' + id + '"]');
    if (row && row.dataset.paid === "1") {
      row.classList.add("just-paid");
      setTimeout(function () { row.classList.remove("just-paid"); }, 900);
    }
    arrive(region);
  });
  window.pokerPage.register(function () {
    var region = document.querySelector(".night-settle");
    if (region) arrive(region);
  });
})();

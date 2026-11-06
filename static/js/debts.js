// A settlement receipt is local to this page visit. Polling must not remove its Undo form.
(function () {
  "use strict";
  var undoing = false;
  document.addEventListener("submit", function (event) {
    undoing = !!event.target.closest("[data-debt-receipt]");
  }, true);
  document.addEventListener("turbo:before-render", function (event) {
    if (event.detail.renderMethod !== "morph") return;
    var old = document.getElementById("debts"), fresh = event.detail.newBody;
    var receipt = old && old.querySelector("[data-debt-receipt]");
    if (!receipt || fresh.querySelector("[data-debt-receipt]")) return;
    if (undoing && !fresh.querySelector(".message-error")) return;
    var next = fresh.querySelector("#debts");
    if (!next) {
      next = old.cloneNode(false);
      next.appendChild(old.querySelector("h2").cloneNode(true));
      var first = fresh.querySelector(".group-sessions");
      if (!first) return;
      first.before(next);
    }
    if (next.dataset.url === old.dataset.url) next.querySelector("h2").after(receipt.cloneNode(true));
  });
  document.addEventListener("turbo:render", function () { undoing = false; });
})();

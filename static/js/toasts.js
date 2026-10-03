(function () {
  "use strict";
  document.querySelectorAll(".message-success").forEach(function (message) {
    message.classList.add("toast");
    var close = document.createElement("button");
    close.type = "button"; close.className = "btn btn-small btn-quiet"; close.textContent = "Dismiss";
    message.appendChild(close);
    var timer;
    function dismiss() { message.remove(); }
    function resume() { clearTimeout(timer); timer = setTimeout(dismiss, 6000); }
    close.addEventListener("click", dismiss);
    message.addEventListener("mouseenter", function () { clearTimeout(timer); });
    message.addEventListener("focusin", function () { clearTimeout(timer); });
    message.addEventListener("mouseleave", resume); message.addEventListener("focusout", resume);
    resume();
  });
})();

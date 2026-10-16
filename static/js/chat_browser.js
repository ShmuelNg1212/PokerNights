// The front door inside a chat app's browser (templates/partials/chat_browser.html). The card is the
// server's; this adds Copy link, says so when Open in Chrome did not leave the page, and folds the card
// away on Continue here. Without it the card still reads, and Continue here is a plain link.
(function () {
  "use strict";
  var HERE = "chat_here";

  window.pokerPage.register(function () {
    var card = document.getElementById("chat-browser");
    if (!card) return;
    var life = new AbortController(), signal = life.signal, timers = [], left = false;
    var status = card.querySelector("[data-chat-status]"), copy = card.querySelector("[data-chat-copy]");
    var motion = window.pokerMotion;

    function say(text) { status.textContent = text; }
    // Plays the three dots again, from the start.
    function point() {
      card.classList.remove("is-pointing");
      void card.offsetWidth;
      card.classList.add("is-pointing");
    }

    if (copy && navigator.clipboard && navigator.clipboard.writeText) {
      copy.hidden = false;
      copy.addEventListener("click", function () {
        var address = copy.dataset.chatCopy, done;
        function refused() { if (!signal.aborted) say("Copy this address: " + address); }
        try { done = navigator.clipboard.writeText(address); } catch (_) { refused(); return; }
        done.then(function () {
          if (signal.aborted) return;
          copy.textContent = "Copied";
          say(card.dataset.chatKind === "ios" ? "Link copied. Paste it into Safari." : "Link copied. Paste it into your browser.");
          timers.push(setTimeout(function () { copy.textContent = "Copy link"; }, 2000));
        }, refused);
      }, { signal: signal });
    }

    // A chat app may refuse to hand the page over. If it is still on screen, the menu is the way.
    document.addEventListener("visibilitychange", function () { if (document.hidden) left = true; }, { signal: signal });
    window.addEventListener("pagehide", function () { left = true; }, { signal: signal });
    card.querySelectorAll("[data-chat-open]").forEach(function (open) {
      open.addEventListener("click", function () {
        left = false;
        timers.push(setTimeout(function () {
          if (signal.aborted || left || document.hidden) return;
          say("Didn’t open? Use the three dots at the top instead.");
          point();
        }, 1500));
      }, { signal: signal });
    });

    card.querySelector("[data-chat-here]").addEventListener("click", function (event) {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.button) return;
      event.preventDefault();
      try { document.cookie = HERE + "=1; path=/; SameSite=Lax" + (location.protocol === "https:" ? "; Secure" : ""); } catch (_) {}
      fold();
    }, { signal: signal });

    // The card leaves; what was under it rises into its place.
    function fold() {
      var sheet = card.parentElement, room = card.offsetHeight + parseFloat(getComputedStyle(card).marginBottom || 0);
      var heading = sheet.querySelector("h1");
      var leaving = motion && motion.run(card, { opacity: 0, transform: "scale(.97)" }, "leave");
      function gone() {
        card.hidden = true;
        Array.prototype.forEach.call(sheet.children, function (el) {
          if (el === card || !el.getClientRects().length || !motion) return;
          motion.settle(el, motion.run(el, { transform: ["translateY(" + room + "px)", "translateY(0px)"] }, "shift"));
        });
        if (heading) { heading.setAttribute("tabindex", "-1"); heading.focus({ preventScroll: true }); }
      }
      if (leaving) { motion.after(leaving, gone); motion.settle(card, leaving, ["transform", "opacity"]); } else gone();
    }

    return function () { life.abort(); timers.forEach(clearTimeout); };
  });
})();

// Collapses the host dock to one bar on phones. The choice is a class on <html>,
// outside the live region, so a poll that redraws the dock keeps it.
(function () {
  "use strict";
  var region = null, watcher = null; // set while a set page is shown
  var root = document.documentElement, KEY = "rack-dock";
  var view = window.visualViewport;
  var open = 0, lifted = 0; // px: the keyboard's height, and how far the dock is raised above the page's bottom edge
  var base = 0, baseWidth = 0, basePage = 0, seat = 0, hidden = 0, leftAt = 0, loop = 0, readout = null;

  // The page reserves the measured dock height, so the last row clears the dock in either state.
  function measure() {
    var dock = region && region.querySelector(".host-controls");
    if (dock) root.style.setProperty("--dock-h", Math.ceil(dock.getBoundingClientRect().height) + "px");
  }

  function sync() {
    var toggle = region && region.querySelector(".dock-toggle");
    if (!toggle) return;
    toggle.hidden = false;
    toggle.setAttribute("aria-expanded", String(!root.classList.contains("dock-collapsed") && !root.classList.contains("kb-bar")));
    // A live update replaces a dock that was still closing.
    if (!toggle.parentElement.getAnimations || !toggle.parentElement.getAnimations().length) root.classList.remove("dock-closing");
    if (watcher) { watcher.disconnect(); watcher.observe(toggle.parentElement); }
    measure();
  }

  // An iPhone keyboard covers the bottom of the page instead of resizing it, and a fixed dock
  // stays under it. With the keyboard open the visible frame (the visual viewport) is shorter
  // than the page's frame and slides inside it as the person scrolls. Two numbers, kept apart:
  //   open   - the keyboard's height: how much shorter the visible frame is than it was with no
  //            field in use. A scroll does not change it. It decides the bar.
  //   hidden - how much of the page frame the keyboard covers; the page reserves that room.
  //   lifted - how far the page's bottom edge is below the visible frame's. It falls to 0 as the
  //            visible frame slides down. It only positions the dock.
  function typing(el) {
    return !!el && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable) && !/^(checkbox|radio|button|submit)$/.test(el.type);
  }
  // Some browsers shorten the page itself when the keyboard opens (Chrome on an iPhone, older
  // Android). There the dock is already on the keyboard and must not be raised again. So the
  // offset is measured from the page frame's bottom edge as it is now: read from the dock's own
  // position while the two frames coincide, otherwise from how much the page has shortened.
  function frame(dock) {
    var active = document.activeElement, height = view.height, now = Date.now(), none = { open: 0, lifted: 0, hidden: 0 };
    if (Math.abs(view.scale - 1) >= 0.01 || getComputedStyle(dock).position !== "fixed") { seat = 0; return none; }
    if (view.width !== baseWidth) { baseWidth = view.width; base = height; basePage = root.clientHeight; } // first look, or the phone was turned
    if (typing(active)) { leftAt = 0; if (height > base) { base = height; basePage = root.clientHeight; } }
    else {
      // No field in use: this is the full height, once a closing keyboard has had time to go.
      if (!leftAt) leftAt = now;
      if (height >= base || now - leftAt > 600) { base = height; basePage = root.clientHeight; }
      seat = 0;
      return none;
    }
    var covered = Math.round(base - height);
    if (covered < 80) { seat = 0; return none; } // a browser toolbar, not a keyboard
    if (Math.abs(view.offsetTop) < 1) seat = dock.getBoundingClientRect().bottom + lifted;
    var edge = seat || base - Math.max(0, basePage - root.clientHeight);
    return { open: covered, lifted: Math.max(0, Math.round(edge - view.offsetTop - height)), hidden: Math.max(0, Math.round(edge - height)) };
  }
  // reveal: a field has just gained focus, so it may be moved clear of the bar.
  function keyboard(reveal) {
    var dock = region && region.querySelector(".host-controls");
    if (!dock || !view) return;
    var now = frame(dock), active = document.activeElement, opened = now.open > 0 && open === 0;
    var bar = now.open > 0 && !(dock.contains(active) && !active.matches(".dock-toggle"));
    if (now.lifted !== lifted) {
      lifted = now.lifted;
      if (lifted) root.style.setProperty("--kb", lifted + "px"); else root.style.removeProperty("--kb");
    }
    if (now.hidden !== hidden) {
      hidden = now.hidden;
      if (hidden) root.style.setProperty("--kb-h", hidden + "px"); else root.style.removeProperty("--kb-h");
    }
    if (now.open !== open || bar !== root.classList.contains("kb-bar")) {
      open = now.open;
      root.classList.toggle("kb-open", open > 0);
      root.classList.toggle("kb-bar", bar);
      dock.getAnimations().forEach(function (motion) { motion.cancel(); });
      sync();
    }
    // An iPhone reports a sliding frame only now and then, so while the keyboard is open it is read every frame.
    if (open && !loop) loop = requestAnimationFrame(watch);
    // The browser scrolls a focused field clear of the keyboard, not of the bar above it. Only
    // then: a scroll made with the keyboard open is the person's own and is left alone.
    if ((reveal || opened) && bar && region.contains(active)) {
      var under = active.getBoundingClientRect().bottom + 12 - dock.getBoundingClientRect().top;
      if (under > 0) window.scrollBy(0, under);
    }
    if (readout) report(dock);
  }
  function watch() {
    if (!region || !open) { loop = 0; return; }
    loop = requestAnimationFrame(watch); // booked first, so keyboard() does not start a second watcher
    keyboard();
    if (!open) { cancelAnimationFrame(loop); loop = 0; }
  }
  function focused() { setTimeout(function () { keyboard(true); }, 0); } // the focus has moved by then
  function left() { setTimeout(keyboard, 0); }

  // "?kb=1" on a set page shows what this script reads, for a screenshot from a phone.
  function report(dock) {
    var box = dock.getBoundingClientRect();
    readout.style.top = Math.round(view.offsetTop + 4) + "px";
    readout.textContent = "keyboard " + open + " lifted " + lifted + " hidden " + hidden + " seat " + Math.round(seat) + "\nvisible " + Math.round(view.height) + " offset " + Math.round(view.offsetTop) +
      " scale " + view.scale + "\nfull " + Math.round(base) + " inner " + window.innerHeight + " client " + root.clientHeight +
      "\ndock " + Math.round(box.top) + "-" + Math.round(box.bottom) + " scrollY " + Math.round(window.scrollY) +
      "\napp " + (window.navigator.standalone === true || matchMedia("(display-mode: standalone)").matches) +
      " field " + typing(document.activeElement);
  }

  // The dock slides between its two heights. While it closes, "dock-closing" keeps the
  // content rendered so it leaves with the edge. Reduced motion changes the size at once.
  function slide(dock, from, closing) {
    var to = dock.offsetHeight;
    if (!dock.animate || from === to || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (closing) root.classList.add("dock-closing");
    dock.style.overflow = "hidden";
    var done = function () { dock.style.overflow = ""; root.classList.remove("dock-closing"); };
    var frames = [{ height: from + "px" }, { height: to + "px" }], motion;
    // Opening uses the sheet spring where the browser can draw it; otherwise the fixed curve.
    var spring = !closing && window.pokerMotion && window.pokerMotion.timing("sheet");
    try { motion = spring && dock.animate(frames, spring); } catch (_) {}
    if (!motion) motion = dock.animate(frames, closing ? { duration: 200, easing: "cubic-bezier(0.4,0,1,1)" } : { duration: 320, easing: "cubic-bezier(0.16,1,0.3,1)" });
    motion.onfinish = motion.oncancel = done;
  }

  document.addEventListener("click", function (event) {
    var toggle = region && event.target.closest(".dock-toggle");
    if (!toggle || !region.contains(toggle)) return;
    // Above the keyboard the bar is not a choice to save: a tap puts the keyboard away.
    if (root.classList.contains("kb-bar")) { if (document.activeElement) document.activeElement.blur(); return; }
    var dock = toggle.parentElement, from = dock.offsetHeight;
    dock.getAnimations().forEach(function (motion) { motion.cancel(); });
    var collapsed = root.classList.toggle("dock-collapsed");
    slide(dock, from, collapsed);
    try { if (collapsed) localStorage.setItem(KEY, "collapsed"); else localStorage.removeItem(KEY); } catch (_) {}
    sync();
  });
  function keyboard0() { keyboard(); } // an event listener passes its event; it is not a reveal
  document.addEventListener("live:updated", function () { sync(); keyboard(); });

  window.pokerPage.register(function () {
    region = document.getElementById("live");
    if (!region) return;
    watcher = window.ResizeObserver ? new ResizeObserver(measure) : null;
    root.classList.add("dock-enabled");
    try { root.classList.toggle("dock-collapsed", localStorage.getItem(KEY) === "collapsed"); } catch (_) {}
    sync();
    if (view) {
      view.addEventListener("resize", keyboard0);
      view.addEventListener("scroll", keyboard0);
      document.addEventListener("focusin", focused);
      document.addEventListener("focusout", left);
      if (/[?&]kb=1(&|$)/.test(window.location.search) && region.querySelector(".host-controls")) {
        readout = document.createElement("pre");
        readout.className = "kb-readout";
        document.body.appendChild(readout);
      }
      keyboard();
    }
    return function () {
      if (watcher) watcher.disconnect();
      if (view) {
        view.removeEventListener("resize", keyboard0);
        view.removeEventListener("scroll", keyboard0);
        document.removeEventListener("focusin", focused);
        document.removeEventListener("focusout", left);
      }
      cancelAnimationFrame(loop);
      if (readout) readout.remove();
      region = watcher = readout = null; open = lifted = hidden = seat = loop = base = baseWidth = basePage = leftAt = 0;
      root.style.removeProperty("--kb");
      root.style.removeProperty("--kb-h");
      root.classList.remove("dock-enabled", "dock-closing", "kb-open", "kb-bar");
    };
  });
})();

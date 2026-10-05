// Every page script registers here instead of running once at load.
//
//   pokerPage.register(function start() { ...find elements, begin...; return function stop() { ...clean up... }; });
//
// "start" runs when a page arrives and must do nothing when its elements are absent.
// "stop" (optional) runs when the page is left: clear timers, abandon requests, drop
// references. Listeners on `document` or `window` that should live for the whole tab
// are registered outside start, once. A script that ignores this rule keeps running
// after the screen changes; see doc/wiki/footguns/scripts_run_once_per_tab.md.
(function () {
  "use strict";
  var starts = [], stops = [], running = false;
  function later(error) { setTimeout(function () { throw error; }, 0); } // report, but let the other modules run
  function run(start) {
    try { var stop = start(); if (typeof stop === "function") stops.push(stop); } catch (error) { later(error); }
  }
  var page = window.pokerPage = {
    register: function (start) { starts.push(start); if (running) run(start); },
    start: function () { if (running) page.stop(); running = true; starts.forEach(run); },
    stop: function () {
      running = false;
      stops.splice(0).reverse().forEach(function (stop) { try { stop(); } catch (error) { later(error); } });
    },
    running: function () { return running; }
  };
  // Scripts are deferred, so every module has registered by the time the document is parsed.
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", page.start);
  else page.start();
})();

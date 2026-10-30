// Share a closed session to the group chat: draws the results card on a canvas from the data the
// server wrote (#share-card), then hands the picture and the text to the phone's share sheet, a
// download or the clipboard. Every amount is the server's own string; nothing is formatted here.
// If the card cannot be drawn the sheet keeps the text and Copy, and the page is as it was.
(function () {
  "use strict";
  var W = 1080, EDGE = 36, PAD = 64, LEFT = EDGE + PAD, RIGHT = W - EDGE - PAD;
  var INK_CHIPS = { 4: 1, 6: 1, 7: 1, 8: 1, 9: 1 }; // chips light enough for dark lettering (.k4 … in app.css)
  var life = null, made = null; // made: {json, file, url} for the card last drawn

  // A page colour as canvas accepts it everywhere: painted once and read back. A colour the
  // canvas cannot read leaves the pixel clear, which stops the card instead of drawing it black.
  var probe = null;
  function colour(value) {
    probe = probe || document.createElement("canvas").getContext("2d", { willReadFrequently: true });
    probe.clearRect(0, 0, 1, 1);
    probe.fillStyle = "rgba(0,0,0,0)"; probe.fillStyle = value; probe.fillRect(0, 0, 1, 1);
    var d = probe.getImageData(0, 0, 1, 1).data;
    if (!d[3]) throw new Error("colour not read: " + value);
    return "rgb(" + d[0] + "," + d[1] + "," + d[2] + ")";
  }
  function palette() {
    var style = getComputedStyle(document.documentElement), out = { chips: [] };
    ["ground", "rail", "rule", "line", "bone", "bone-dim", "ink", "brass", "up", "down"].forEach(function (name) {
      out[name] = colour(style.getPropertyValue("--" + name).trim());
    });
    for (var k = 1; k <= 10; k++) out.chips[k] = colour(style.getPropertyValue("--c" + k).trim());
    return out;
  }

  function painter(ctx, C, family) {
    function font(size, weight, narrow) { ctx.font = weight + " " + (narrow ? "condensed " : "") + size + "px " + family; }
    // Text that must fit a width: the name gives way with an ellipsis; amounts are never passed here.
    function fit(text, width) {
      if (ctx.measureText(text).width <= width) return text;
      var cut = text;
      while (cut.length > 1 && ctx.measureText(cut + "…").width > width) cut = cut.slice(0, -1);
      return cut.replace(/\s+$/, "") + "…";
    }
    function text(value, x, y, fill, align) {
      ctx.fillStyle = fill; ctx.textAlign = align || "left"; ctx.textBaseline = "alphabetic"; ctx.fillText(value, x, y);
    }
    function rule(y, fill) { ctx.fillStyle = fill || C.rule; ctx.fillRect(LEFT, y, RIGHT - LEFT, 2); }
    // The player's chip, as .chip draws it: six bone notches on the rim, a dark ring, the label.
    // k 0 is the rake fund: brass with dark ink, as .chip-fund.
    function chip(cx, cy, r, who) {
      var fund = who.k === 0;
      var c = fund ? C.brass : C.chips[who.k] || C.chips[1], step = Math.PI / 3, from = -Math.PI / 2 - Math.PI / 15;
      ctx.fillStyle = c; ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = C.bone;
      for (var i = 0; i < 6; i++) {
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.arc(cx, cy, r, from + i * step, from + i * step + Math.PI * 2 / 15); ctx.closePath(); ctx.fill();
      }
      ctx.fillStyle = "rgba(0,0,0,.28)"; ctx.beginPath(); ctx.arc(cx, cy, r * 0.61, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = c; ctx.beginPath(); ctx.arc(cx, cy, r * 0.56, 0, Math.PI * 2); ctx.fill();
      font(Math.round(r * (who.chip.length > 1 ? 0.56 : 0.68)), 800);
      ctx.fillStyle = fund || INK_CHIPS[who.k] ? C.ink : "#fff"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(who.chip, cx, cy + r * 0.04);
    }
    // The result's mark, as the screens draw it: up-right, down-right or a level stroke.
    function mark(x, y, size, sign, fill) {
      ctx.strokeStyle = fill; ctx.lineWidth = Math.max(4, size / 7); ctx.lineCap = "round"; ctx.lineJoin = "round";
      ctx.beginPath();
      if (sign === "even") { ctx.moveTo(x, y); ctx.lineTo(x + size, y); }
      else {
        var up = sign === "plus", top = y - size / 2, bottom = y + size / 2;
        ctx.moveTo(x, up ? bottom : top); ctx.lineTo(x + size, up ? top : bottom);
        ctx.moveTo(x + size * 0.3, up ? top : bottom); ctx.lineTo(x + size, up ? top : bottom); ctx.lineTo(x + size, up ? top + size * 0.7 : bottom - size * 0.7);
      }
      ctx.stroke();
    }
    function arrow(x, y, length, fill) {
      ctx.strokeStyle = fill; ctx.lineWidth = 4; ctx.lineCap = "round"; ctx.lineJoin = "round";
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + length, y); ctx.moveTo(x + length - 12, y - 12); ctx.lineTo(x + length, y); ctx.lineTo(x + length - 12, y + 12); ctx.stroke();
    }
    return { font: font, fit: fit, text: text, rule: rule, chip: chip, mark: mark, arrow: arrow };
  }

  // One pass lays the card out from the top; it runs dry first to learn the height, then draws.
  function compose(ctx, card, C, family, logo, dry) {
    var p = painter(ctx, C, family), y = EDGE + PAD;
    var tone = { plus: C.up, minus: C.down, even: C.bone };
    function draw(fn) { if (!dry) fn(); }

    draw(function () {
      if (logo) ctx.drawImage(logo, LEFT, y, 52, 52);
      p.font(32, 700); p.text("PokerNights", LEFT + (logo ? 68 : 0), y + 38, C["bone-dim"]);
    });
    y += 52 + 56;

    // The table name carries the card: as large as fits on one line, never under 60px.
    var size = 96; p.font(size, 800);
    while (size > 60 && ctx.measureText(card.title).width > RIGHT - LEFT) { size -= 4; p.font(size, 800); }
    var lines = [card.title];
    if (ctx.measureText(card.title).width > RIGHT - LEFT) {
      // Still too long at the smallest size: break at the last word that fits, and shorten only the second line.
      var words = card.title.split(" "), head = words.shift();
      while (words.length && ctx.measureText(head + " " + words[0]).width <= RIGHT - LEFT) head += " " + words.shift();
      lines = words.length ? [p.fit(head, RIGHT - LEFT), p.fit(words.join(" "), RIGHT - LEFT)] : [p.fit(head, RIGHT - LEFT)];
    }
    lines.forEach(function (line) {
      draw(function () { p.font(size, 800); p.text(line, LEFT, y + size * 0.78, C.bone); });
      y += size + 8;
    });
    y += 12;
    draw(function () { p.font(36, 500); p.text(p.fit(card.when, RIGHT - LEFT), LEFT, y + 30, C["bone-dim"]); });
    y += 52;
    draw(function () { p.font(36, 500); p.text(p.fit(card.facts, RIGHT - LEFT), LEFT, y + 30, C["bone-dim"]); });
    y += 52 + 44;

    function heading(label) {
      draw(function () { p.rule(y); p.font(32, 700); p.text(label, LEFT, y + 62, C["bone-dim"]); });
      y += 92;
    }

    heading("Results");
    card.rows.forEach(function (row) {
      var lead = row.place === 1 && row.sign === "plus";
      var h = lead ? 136 : 108, r = lead ? 42 : 34, name = lead ? 54 : 44, figure = lead ? 64 : 50, mid = y + (h - 14) / 2;
      draw(function () {
        p.font(34, 700); p.text(String(row.place), LEFT + 14, mid + 12, C["bone-dim"], "center");
        p.chip(LEFT + 52 + r, mid, r, row);
        p.font(figure, 800, true);
        var wide = ctx.measureText(row.amount).width, icon = Math.round(figure * 0.42);
        p.text(row.amount, RIGHT, mid + figure * 0.35, tone[row.sign], "right");
        p.mark(RIGHT - wide - icon - 16, mid, icon, row.sign, tone[row.sign]);
        var nameX = LEFT + 52 + r * 2 + 24;
        p.font(name, lead ? 800 : 600);
        p.text(p.fit(row.name, RIGHT - wide - icon - 44 - nameX), nameX, mid + name * 0.35, C.bone);
        // The size of the result, as the recap's bars show it.
        ctx.fillStyle = C.rule; ctx.fillRect(nameX, y + h - 16, RIGHT - nameX, 6);
        if (row.share) { ctx.fillStyle = tone[row.sign]; ctx.fillRect(nameX, y + h - 16, Math.max(6, (RIGHT - nameX) * row.share / 100), 6); }
      });
      y += h;
    });
    y += 36;

    heading("Who pays whom");
    if (!card.transfers.length) {
      draw(function () { p.font(40, 500); p.text("Nobody owes anything.", LEFT, y + 38, C.bone); });
      y += 72;
    }
    card.transfers.forEach(function (t) {
      var h = 96, r = 28, mid = y + h / 2 - 6;
      draw(function () {
        p.font(46, 800, true);
        var wide = ctx.measureText(t.amount).width;
        p.text(t.amount, RIGHT, mid + 16, C.bone, "right");
        // Two names share what the amount leaves: chip, name, arrow, chip, name.
        var room = (RIGHT - wide - 32 - LEFT - (r * 2 + 16) * 2 - 88) / 2;
        p.font(40, 600);
        // A short name leaves its unused half to the other one.
        var a = ctx.measureText(t.payer.name).width, b = ctx.measureText(t.payee.name).width;
        var payer = p.fit(t.payer.name, Math.max(room, room * 2 - b)), payee = p.fit(t.payee.name, Math.max(room, room * 2 - a)), x = LEFT;
        p.chip(x + r, mid, r, t.payer); x += r * 2 + 16;
        p.font(40, 600); p.text(payer, x, mid + 14, C.bone); x += ctx.measureText(payer).width + 20;
        p.arrow(x, mid, 48, C.brass); x += 48 + 20;
        p.chip(x + r, mid, r, t.payee); x += r * 2 + 16;
        p.font(40, 600); p.text(payee, x, mid + 14, C.bone);
        ctx.fillStyle = C.rule; ctx.fillRect(LEFT, y + h - 2, RIGHT - LEFT, 2);
      });
      y += h;
    });
    y += 40;

    if (card.foot.length) {
      draw(function () { p.font(30, 500); p.text(p.fit(card.foot.join(" · "), RIGHT - LEFT), LEFT, y + 26, C["bone-dim"]); });
      y += 40;
    }
    return y + PAD + EDGE;
  }

  function panel(ctx, C, height) {
    ctx.fillStyle = C.ground; ctx.fillRect(0, 0, W, height);
    var x = EDGE, y = EDGE, w = W - EDGE * 2, h = height - EDGE * 2, r = 52;
    ctx.beginPath();
    ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
    ctx.fillStyle = C.rail; ctx.fill();
    ctx.strokeStyle = C.rule; ctx.lineWidth = 2; ctx.stroke();
    ctx.fillStyle = C.brass; ctx.fillRect(LEFT, EDGE, 120, 6); // the brass mark the screens use for "this is the news"
  }

  function loadMark(url) {
    return new Promise(function (done) {
      if (!url) { done(null); return; }
      var image = new Image();
      image.onload = function () { done(image); }; image.onerror = function () { done(null); };
      image.src = url;
    });
  }

  // Resolves to {file, url}. Rejects when the page's font or the canvas is not there to draw with.
  function render(card, markUrl) {
    var family = getComputedStyle(document.body).fontFamily, first = family.split(",")[0].trim();
    if (!document.fonts || !document.fonts.load) return Promise.reject(new Error("no font loading"));
    return Promise.all([
      document.fonts.load("800 64px " + first), document.fonts.load("500 36px " + first), loadMark(markUrl)
    ]).then(function (got) {
      if (!document.fonts.check("800 64px " + first)) throw new Error("font not ready");
      var C = palette(), canvas = document.createElement("canvas"), ctx = canvas.getContext("2d");
      canvas.width = W; canvas.height = 10;
      var height = Math.ceil(compose(ctx, card, C, family, got[2], true));
      canvas.height = height; // resets the context
      panel(ctx, C, height);
      compose(ctx, card, C, family, got[2], false);
      // A canvas that refused to draw is all one colour along this line: the title crosses it.
      var row = ctx.getImageData(LEFT, EDGE + PAD + 52 + 56 + 40, RIGHT - LEFT, 1).data, differs = false;
      for (var i = 4; i < row.length && !differs; i += 4) differs = row[i] !== row[0] || row[i + 1] !== row[1];
      if (!differs) throw new Error("blank card");
      return new Promise(function (done, fail) {
        canvas.toBlob(function (blob) {
          if (!blob) { fail(new Error("no picture")); return; }
          var file; try { file = new File([blob], card.file, { type: "image/png" }); } catch (_) { file = null; }
          done({ file: file, blob: blob, url: URL.createObjectURL(blob), height: height });
        }, "image/png");
      });
    });
  }

  function canShareFiles(file) {
    try { return !!(file && navigator.share && navigator.canShare && navigator.canShare({ files: [file] })); } catch (_) { return false; }
  }

  function prepare(body) {
    var root = body.querySelector("[data-share]"), source = document.getElementById("share-card");
    if (!root || !source) return;
    var json = source.textContent, card = JSON.parse(json);
    var stage = root.querySelector("[data-share-stage]"), preview = root.querySelector("[data-share-preview]");
    var actions = root.querySelector("[data-share-actions]");
    var status = root.querySelector("[data-share-status]"), text = root.querySelector("[data-share-text]");
    var plain = root.querySelector("[data-share-plain]"), field = root.querySelector("textarea");
    var share = actions.querySelector('[data-share-do="share"]'), save = actions.querySelector('[data-share-do="save"]');
    var signal = life.signal, timers = [];
    function say(message) { status.textContent = message; }
    function accepted(button, label) {
      var was = button.dataset.label || (button.dataset.label = button.textContent);
      button.textContent = label; say(label + ".");
      if (window.pokerMotion) window.pokerMotion.settle(button, window.pokerMotion.run(button, { scale: [1, 1.04, 1] }, "pulse"));
      timers.push(setTimeout(function () { button.textContent = was; }, 2000));
    }
    function copy(button) {
      function refused() {
        text.open = true; field.focus(); field.setSelectionRange(0, field.value.length);
        say("Could not copy. The text is selected: copy it from the menu.");
      }
      var done; try { done = navigator.clipboard.writeText(card.text); } catch (_) { refused(); return; }
      done.then(function () { if (!signal.aborted) accepted(button, "Copied"); }, refused);
    }
    function send(button) {
      var files = canShareFiles(made && made.file), done;
      // Straight from the tap: the picture already exists, so nothing is awaited before the phone's sheet.
      try { done = navigator.share(files ? { files: [made.file], text: card.text } : { text: card.text }); }
      catch (_) { say("Could not open sharing here. Save the image or copy the text."); return; }
      done.then(function () { if (!signal.aborted) accepted(button, "Shared"); }, function (error) {
        if (error && error.name === "AbortError") return; // the person closed the phone's sheet
        say("Could not share. Save the image or copy the text.");
      });
    }
    function download(button) {
      var link = document.createElement("a");
      link.href = made.url; link.download = card.file; document.body.appendChild(link); link.click(); link.remove();
      accepted(button, "Saved");
    }
    root.addEventListener("click", function (event) {
      var button = event.target.closest("[data-share-do]");
      if (!button || button.disabled) return;
      var what = button.dataset.shareDo;
      if (what === "copy") copy(button); else if (!made) return; else if (what === "share") send(button); else download(button);
    }, { signal: signal });
    signal.addEventListener("abort", function () { timers.forEach(clearTimeout); });

    // Without the card the sheet is the text and one Copy.
    function textOnly() {
      stage.hidden = actions.hidden = true;
      text.open = true; plain.hidden = false; root.classList.add("share-plain");
    }
    function show() {
      preview.src = made.url;
      var ready = preview.decode ? preview.decode() : Promise.resolve();
      ready.catch(function () {}).then(function () {
        if (signal.aborted) return;
        var files = canShareFiles(made.file);
        share.hidden = !navigator.share;
        share.textContent = files ? "Share" : "Share text";
        // One primary: Share where the phone takes the picture, Save image where it does not.
        share.classList.toggle("btn-primary", files); save.classList.toggle("btn-primary", !files);
        actions.classList.toggle("share-first", files);
        text.open = false; plain.hidden = true; root.classList.remove("share-plain");
        actions.hidden = false; stage.hidden = false;
        stage.classList.remove("is-dealt"); void stage.offsetWidth; stage.classList.add("is-dealt");
        var first = files ? share : save, active = document.activeElement;
        if (!active || active === document.body || active.closest(".sheet-head")) first.focus({ preventScroll: true });
      });
    }
    if (made && made.json === json) { show(); return; }
    render(card, root.dataset.mark).then(function (drawn) {
      if (made) URL.revokeObjectURL(made.url);
      made = drawn; made.json = json;
      if (!signal.aborted) show();
    }, function () { if (!signal.aborted) textOnly(); });
  }

  document.addEventListener("sheet:shown", function (event) {
    if (!life || event.detail.key !== "share") return;
    life.abort(); life = new AbortController(); // one set of listeners per opening
    try { prepare(event.detail.body); } catch (_) { /* the text and its field are already in the sheet */ }
  });
  window.pokerPage.register(function () {
    if (!document.getElementById("share-card")) return;
    life = new AbortController();
    return function () {
      life.abort(); life = null;
      if (made) { URL.revokeObjectURL(made.url); made = null; }
    };
  });
})();

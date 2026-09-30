/* Renk Yerleştirme prototipi — ARAYÜZ (v1: PARÇA mekaniği). Kurallar yalnız engine.js'te (PLevel); burada yalnız gösterim, giriş ve kayıt vardır.
 * Oyuncu yalnız hangi parçayı göndereceğini seçer. Seçilen parçanın TAM şekli gösterilir, oyun hedef konumu hesaplar ve parçanın
 * dolduracağı TÜM hücreler tahtada (hafif yanıp sönen) hayalet olarak görünür. "Gönder" parçayı tek grup olarak yollar.
 * Animasyon kozmetiktir: mantıksal durum tıklamada ANINDA değişir; işçilerin varış sırası = yerleşme sırası (en derinden başla),
 * bu yüzden hiçbir işçi, yeni dolmuş bir kutunun içinden geçmez. */
(function () {
  'use strict';
  var CB = window.CB, LEVELS = window.CB_LEVELS, VECTORS = window.CB_VECTORS || { levels: [] };
  var $ = function (id) { return document.getElementById(id); };
  var qs = new URLSearchParams(location.search);
  function clampInt(v, lo, hi, d) { var n = parseInt(v, 10); return isNaN(n) ? d : Math.max(lo, Math.min(hi, n)); }
  function clampNum(v, lo, hi, d) { var n = parseFloat(v); return isNaN(n) ? d : Math.max(lo, Math.min(hi, n)); }
  var cfg = { hint: clampInt(qs.get('hint'), 0, 2, 1), ghost: qs.get('ghost') !== '0', speed: clampNum(qs.get('speed'), 0.5, 200, 1),
              undo: clampInt(qs.get('undo'), 0, 9, 0), test: qs.get('mode') === 'test', player: qs.get('player') || '' };
  var byId = {}; LEVELS.forEach(function (l) { byId[l.id] = l; });
  var order = (qs.get('levels') || '').split(',').filter(function (x) { return byId[x]; });
  if (!order.length) order = LEVELS.map(function (l) { return l.id; });

  var canvas = $('board'), ctx = canvas.getContext('2d');
  var G = { lv: null, level: null, palette: null, st: null, visual: null, status: 'idle', history: [], selected: -1, opt: null, previewSealed: [], previewStuck: false,
            workers: [], dest: null, pops: {}, attemptNo: 0, undoLeft: 0, waveEnd: 0, pending: null, readyAt: 0, switches: 0, previews: [], cur: null, testIdx: 0,
            s: 10, ox: 0, oy: 0, dpr: 1, cw: 0, ch: 0, sealedShown: [], wonAt: 0, handSig: '' };
  var LOG = { meta: { app: 'renk-yerlestirme-prototip-v1-parca', started: new Date().toISOString(), ua: navigator.userAgent, player: cfg.player, test: cfg.test }, attempts: [] };
  function now() { return performance.now() / 1000; }

  // ---------------------------------------------------------------- renk yardımcıları
  function rgb(h) { var n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
  function mix(a, b, t) { var x = rgb(a), y = rgb(b); return 'rgb(' + Math.round(x[0] + (y[0] - x[0]) * t) + ',' + Math.round(x[1] + (y[1] - x[1]) * t) + ',' + Math.round(x[2] + (y[2] - x[2]) * t) + ')'; }
  function col(i) { return G.palette.colors[i]; }
  function isDark(h) { var c = rgb(h); return (c[0] * 299 + c[1] * 587 + c[2] * 114) / 1000 < 90; }
  var FLOOR = '#46516a', GHOST_BASE = '#cfd6e4';   // koyu zemin: hayalet (henüz boş) hedef hücreler öne çıkar

  // ---------------------------------------------------------------- seviye / deneme
  function loadLevel(id) {
    var lv = byId[id]; if (!lv) return;
    G.lv = lv; G.level = new CB.PLevel(lv.grid, lv.pieces); G.palette = lv.palette; G.attemptNo = 0;
    newAttempt('load'); layout(); fillSelectors();
  }
  function newAttempt(reason) {
    if (G.cur && !G.cur.outcome) { G.cur.outcome = reason === 'load' ? 'switch' : 'restart'; G.cur.t1 = Date.now(); }
    G.st = G.level.newState(); G.visual = new Uint8Array(G.st.filled); G.status = 'idle'; G.history = []; G.selected = -1; G.opt = null;
    G.previewSealed = []; G.previewStuck = false; G.workers = []; G.dest = null; G.pops = {}; G.pending = null; G.sealedShown = []; G.undoLeft = cfg.undo; G.wonAt = 0; G.handSig = '';
    G.cur = { level: G.lv.id, attempt: ++G.attemptNo, reason: reason, hint: cfg.hint, ghost: cfg.ghost, speed: cfg.speed, undo_budget: cfg.undo, pieces: G.level.P,
              t0: Date.now(), tokens: [], moves: [], outcome: null };
    LOG.attempts.push(G.cur); G.readyAt = now(); G.switches = 0; G.previews = []; saveLog();
    setMsg('Bir renge bas: o rengin parçası (sabit şekil) tahtada nereye gideceğini gösterir. Hangisini ŞİMDİ göndermelisin?', 'info');
    refresh();
  }

  // ---------------------------------------------------------------- yerleşim (canvas)
  function layout() {
    var wrap = $('boardWrap'); G.cw = wrap.clientWidth; G.ch = wrap.clientHeight; G.dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(G.cw * G.dpr); canvas.height = Math.round(G.ch * G.dpr);
    if (!G.level) return;
    var cols = G.level.w + 3, rows = G.level.h + 3;
    G.s = Math.max(5, Math.floor(Math.min(G.cw / cols, G.ch / rows)));
    G.ox = Math.floor((G.cw - G.level.w * G.s) / 2); G.oy = Math.floor((G.ch - G.level.h * G.s) / 2);
  }
  function cx(cell) { var w = G.level.w; return G.ox + (cell % w) * G.s + G.s / 2; }
  function cy(cell) { var w = G.level.w; return G.oy + Math.floor(cell / w) * G.s + G.s / 2; }

  // ---------------------------------------------------------------- çizim
  function box(x, y, s, color, pop, c2) {
    var g = c2 || ctx, k = 1 + (pop || 0), sz = (s - 2) * k, px = x + (s - sz) / 2, py = y + (s - sz) / 2;
    g.fillStyle = color; g.fillRect(px, py, sz, sz);
    g.fillStyle = 'rgba(255,255,255,.28)'; g.fillRect(px, py, sz, Math.max(1, sz * 0.14));
    g.fillStyle = 'rgba(0,0,0,.22)'; g.fillRect(px, py + sz - Math.max(1, sz * 0.14), sz, Math.max(1, sz * 0.14));
    g.strokeStyle = isDark(color) ? '#000' : 'rgba(0,0,0,.45)'; g.lineWidth = 1; g.strokeRect(px + .5, py + .5, sz - 1, sz - 1);
  }
  // bir hücre kümesinin dış çerçevesi (birleşik şekil)
  function outline(tis, color, lw) {
    var L = G.level, s = G.s, set = {}; tis.forEach(function (t) { set[t] = 1; });
    ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.beginPath();
    tis.forEach(function (ti) {
      var tg = L.targets[ti], x = G.ox + tg.c * s, y = G.oy + tg.r * s, e = 1;
      [[-1, 0, x + e, y, x + s - e, y], [1, 0, x + e, y + s, x + s - e, y + s], [0, -1, x, y + e, x, y + s - e], [0, 1, x + s, y + e, x + s, y + s - e]].forEach(function (d) {
        var rr = tg.r + d[0], cc = tg.c + d[1], nt = (rr >= 0 && rr < L.h && cc >= 0 && cc < L.w) ? L.tIdx[rr * L.w + cc] : -1;
        if (nt < 0 || !set[nt]) { ctx.moveTo(d[2], d[3]); ctx.lineTo(d[4], d[5]); }
      });
    });
    ctx.stroke();
  }
  function draw() {
    var t = now(), L = G.level; if (!L) return; var s = G.s, w = L.w;
    ctx.setTransform(G.dpr, 0, 0, G.dpr, 0, 0); ctx.clearRect(0, 0, G.cw, G.ch);
    ctx.fillStyle = '#10141d'; ctx.fillRect(0, 0, G.cw, G.ch);
    for (var r = 0; r < L.h; r++) for (var c = 0; c < w; c++) {
      var i = r * w + c, k = L.kind[i], x = G.ox + c * s, y = G.oy + r * s;
      if (k === 1 || k === 3) { ctx.fillStyle = FLOOR; ctx.fillRect(x, y, s, s); ctx.fillStyle = 'rgba(0,0,0,.10)'; if ((r + c) % 2) ctx.fillRect(x, y, s, s); }
      else if (k === 2) { ctx.fillStyle = '#f2c230'; ctx.fillRect(x, y, s, s); ctx.fillStyle = '#222'; for (var q = -s; q < s; q += s / 2) { ctx.beginPath(); ctx.moveTo(x + q, y + s); ctx.lineTo(x + q + s / 4, y + s); ctx.lineTo(x + q + s / 4 + s, y); ctx.lineTo(x + q + s, y); ctx.fill(); } }
    }
    drawDepot(t);
    var sealedSet = {}, pvSealed = {};
    G.sealedShown.forEach(function (ti) { sealedSet[ti] = 1; });
    G.previewSealed.forEach(function (ti) { pvSealed[ti] = 1; });
    for (var ti = 0; ti < L.n; ti++) {
      var tg = L.targets[ti], x0 = G.ox + tg.c * s, y0 = G.oy + tg.r * s, color = col(tg.col);
      if (G.visual[ti]) { var age = t - (G.pops[ti] || -9); box(x0, y0, s, color, age < 0.28 ? 0.35 * (1 - age / 0.28) : 0); }
      else {
        ctx.fillStyle = cfg.ghost ? mix(color, GHOST_BASE, 0.45) : '#aab2c2'; ctx.fillRect(x0 + 1, y0 + 1, s - 2, s - 2);
        ctx.strokeStyle = 'rgba(0,0,0,.35)'; ctx.lineWidth = 1; ctx.strokeRect(x0 + 1.5, y0 + 1.5, s - 3, s - 3);
      }
    }
    // ÖNİZLEME: seçili parçanın gideceği TÜM hücreler, hafif yanıp sönen hayalet (parça rengi) + birleşik çerçeve
    if (G.opt && G.status === 'idle') {
      var pc = col(G.level.pieces[G.selected].col), blink = 0.5 + 0.18 * Math.sin(t * 5.5);
      G.opt.cells.forEach(function (ti2) {
        var tg2 = L.targets[ti2], x1 = G.ox + tg2.c * s, y1 = G.oy + tg2.r * s;
        ctx.globalAlpha = blink; ctx.fillStyle = pc; ctx.fillRect(x1 + 1, y1 + 1, s - 2, s - 2); ctx.globalAlpha = 1;
      });
      outline(G.opt.cells, isDark(pc) ? '#fff' : '#111', Math.max(2, s * 0.09));
      outline(G.opt.cells, isDark(pc) ? '#111' : '#fff', Math.max(1, s * 0.03));
    }
    // yol boyunca hedef çerçevesi: işçiler yürürken parçanın hedefi
    if (G.dest && G.status === 'anim') outline(G.dest.cells, 'rgba(255,255,255,.75)', Math.max(1.5, s * 0.07));
    if (G.status === 'idle') G.previewSealed.forEach(function (ti3) { hatch(ti3, 'rgba(255,60,60,.95)', t, false); });
    if (G.status === 'sealed') G.sealedShown.forEach(function (ti4) { hatch(ti4, 'rgba(255,40,40,1)', t, true); });
    drawWorkers(t);
    if (G.status === 'won') {
      var sweep = ((t - G.wonAt) * 14) % (L.h + L.w + 6);
      for (var tj = 0; tj < L.n; tj++) { var tq = L.targets[tj], dd = tq.r + tq.c; if (Math.abs(dd - sweep) < 1.6) { ctx.fillStyle = 'rgba(255,255,255,.55)'; ctx.fillRect(G.ox + tq.c * s, G.oy + tq.r * s, s, s); } }
    }
  }
  function hatch(ti, color, t, pulse) {
    var tg = G.level.targets[ti], s = G.s, x = G.ox + tg.c * s, y = G.oy + tg.r * s, a = pulse ? 0.55 + 0.45 * Math.sin(t * 6) : 0.9;
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = 'rgba(255,0,0,.35)'; ctx.fillRect(x, y, s, s);
    ctx.strokeStyle = color; ctx.lineWidth = Math.max(1.5, s * 0.12); ctx.beginPath(); ctx.moveTo(x + 2, y + 2); ctx.lineTo(x + s - 2, y + s - 2); ctx.moveTo(x + s - 2, y + 2); ctx.lineTo(x + 2, y + s - 2); ctx.stroke(); ctx.restore();
  }
  function outward(cell) {
    var L = G.level, r = Math.floor(cell / L.w), c = cell % L.w;
    if (r === 0) return [0, -1]; if (r === L.h - 1) return [0, 1]; if (c === 0) return [-1, 0]; if (c === L.w - 1) return [1, 0]; return null;
  }
  function drawDepot(t) {
    var L = G.level, s = G.s; if (!L.entrances.length || L.entrances.length > 3) return;
    L.entrances.forEach(function (e) {
      var d = outward(e); if (!d) return; var x = cx(e) + d[0] * s * 1.15, y = cy(e) + d[1] * s * 1.15;
      ctx.fillStyle = '#2b3246'; ctx.fillRect(x - s * 0.9, y - s * 0.75, s * 1.8, s * 1.5);
      ctx.strokeStyle = '#ffb703'; ctx.lineWidth = 1.5; ctx.strokeRect(x - s * 0.9 + .5, y - s * 0.75 + .5, s * 1.8 - 1, s * 1.5 - 1);
      for (var k = 0; k < L.K; k++) box(x - s * 0.8 + k * s * 0.55, y - s * 0.1, s * 0.5, col(k), 0);
      ctx.fillStyle = '#ffb703'; ctx.font = '700 ' + Math.max(8, Math.floor(s * 0.45)) + 'px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic'; ctx.fillText('DEPO', x, y - s * 0.22);
    });
  }
  function drawWorkers(t) {
    var s = G.s, list = [];
    G.workers.forEach(function (w) {
      if (t < w.depart) return;
      var p = Math.min(1, (t - w.depart) / w.travel), steps = w.path.length - 1, px, py;
      if (steps <= 0) { px = cx(w.path[0]); py = cy(w.path[0]); }
      else { var f = p * steps, i = Math.min(steps - 1, Math.floor(f)), u = f - i; px = cx(w.path[i]) + (cx(w.path[i + 1]) - cx(w.path[i])) * u; py = cy(w.path[i]) + (cy(w.path[i + 1]) - cy(w.path[i])) * u; }
      list.push({ w: w, x: px, y: py });
    });
    list.sort(function (a, b) { return a.y - b.y; });
    list.forEach(function (o) {
      var w = o.w, done = w.state === 1, hop = done ? Math.abs(Math.sin((t - w.doneAt) * 14)) * s * 0.25 : 0, x = o.x, y = o.y - hop, r = s * 0.3;
      ctx.fillStyle = 'rgba(0,0,0,.3)'; ctx.beginPath(); ctx.ellipse(o.x, o.y + r * 0.9, r * 0.9, r * 0.4, 0, 0, 7); ctx.fill();
      ctx.fillStyle = '#ff7a00'; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();
      ctx.fillStyle = '#f4d7b0'; ctx.beginPath(); ctx.arc(x, y - r * 0.85, r * 0.55, 0, 7); ctx.fill();
      ctx.fillStyle = '#ffd60a'; ctx.beginPath(); ctx.arc(x, y - r * 1.1, r * 0.6, Math.PI, 0); ctx.fill();
      ctx.strokeStyle = '#000'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.stroke();
      if (!done) box(x - s * 0.22, y - r * 2.3 - s * 0.08, s * 0.44, col(w.color), 0);                   // taşınan kutu (parçanın kutularından biri)
    });
  }

  // ---------------------------------------------------------------- parça çizimi (el / panel)
  function drawPiece(cv, p, cellPx, colr) {
    var rows = 0, cols = 0; p.cells.forEach(function (x) { rows = Math.max(rows, x[0] + 1); cols = Math.max(cols, x[1] + 1); });
    var dpr = window.devicePixelRatio || 1, pad = 3; cv.style.width = (cols * cellPx + pad * 2) + 'px'; cv.style.height = (rows * cellPx + pad * 2) + 'px';
    cv.width = Math.round((cols * cellPx + pad * 2) * dpr); cv.height = Math.round((rows * cellPx + pad * 2) * dpr);
    var g = cv.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, cv.width, cv.height);
    p.cells.forEach(function (x) { box(pad + x[1] * cellPx, pad + x[0] * cellPx, cellPx, colr, 0, g); });
  }
  function shapeLabel(p) {
    var n = p.cells.length, rows = 0, cols = 0; p.cells.forEach(function (x) { rows = Math.max(rows, x[0] + 1); cols = Math.max(cols, x[1] + 1); });
    if (rows === 1 || cols === 1) return 'I' + n; if (rows === 2 && cols === 2 && n === 4) return 'Kare'; return n + ' kutu';
  }

  // ---------------------------------------------------------------- parça gönderme
  function feasibleNow() { return G.level.options(G.st); }
  function send(pi) {
    if (G.status !== 'idle') return;
    var L = G.level, res = L.place(G.st, pi);
    if (!res) { toast('Bu parça şu an yerleşemez'); return; }
    var t0 = now(), routes = L.routesFor(res), before = G.st, optsBefore = L.options(G.st).filter(Boolean).length, p = L.pieces[pi];
    G.history.push({ piece: pi, before: before, n: p.cells.length, col: p.col });
    G.st = res.state;
    G.pending = { sealed: res.sealed, won: res.won, stuck: res.stuck };
    G.dest = { cells: res.placed.slice() };
    // işçi takvimi (bir grup): varış sırası = yerleştirme sırası; grup birlikte yola çıkar
    var v = 7 * cfg.speed, gap = 0.08 / cfg.speed, tr = routes.map(function (q) { return Math.max(1, q.length - 1) / v; }), T0 = 0.05;
    for (var i = 0; i < res.placed.length; i++) T0 = Math.max(T0, tr[i] - i * gap + 0.05);
    G.workers = res.placed.map(function (ti, i) { return { ti: ti, path: routes[i], depart: t0 + T0 + i * gap - tr[i], arrive: t0 + T0 + i * gap, travel: tr[i], color: p.col, state: 0, doneAt: 0 }; });
    G.waveEnd = t0 + T0 + (res.placed.length - 1) * gap + 0.45;
    var a = G.cur;
    a.tokens.push(p.id);
    a.moves.push({ i: a.moves.length + 1, token: p.id, color: p.ch, size: p.cells.length, shape: JSON.stringify(p.cells), t_ms: Date.now() - a.t0, decide_ms: Math.round((t0 - G.readyAt) * 1000),
                   preview_switches: G.switches, previewed: G.previews.slice(), placed: res.placed.length, pos: [res.pos.r, res.pos.c], options_before: optsBefore,
                   available_before: L.remainingPieces(before), filled_after: L.filledCount(res.state.filled), sealed_after: res.sealed.length > 0, stuck_after: res.stuck, preview_shown: cfg.hint >= 1 });
    G.selected = -1; G.opt = null; G.previewSealed = []; G.previewStuck = false; G.status = 'anim'; saveLog(); refresh();
  }
  function finishWave() {
    G.workers = []; G.dest = null; G.readyAt = now(); G.switches = 0; G.previews = [];
    var p = G.pending; G.pending = null;
    if (p.won) { G.status = 'won'; G.wonAt = now(); G.cur.outcome = 'won'; G.cur.t1 = Date.now();
      setMsg('Resim tamamlandı! ' + G.history.length + ' parça gönderdin. ' + (cfg.test ? '' : 'Yeniden başlatabilir ya da başka seviye seçebilirsin.'), 'good'); }
    else if (p.sealed.length) { G.status = 'sealed'; G.sealedShown = p.sealed; G.cur.sealed_at_move = G.cur.moves.length; G.cur.outcome = 'sealed'; G.cur.t1 = Date.now();
      setMsg('Kilitlendi: ' + p.sealed.length + ' boş hücreye artık girişten yol yok (kırmızı). Bu seviye bu hâliyle tamamlanamaz.' + (G.undoLeft > 0 ? ' Geri alabilirsin.' : ''), 'bad'); }
    else if (p.stuck) { G.status = 'stuck'; G.cur.stuck_at_move = G.cur.moves.length; G.cur.outcome = 'stuck'; G.cur.t1 = Date.now();
      setMsg('Sıkıştı: kalan parçalardan hiçbiri boş hücrelere yerleşemiyor. Bu seviye bu hâliyle tamamlanamaz.' + (G.undoLeft > 0 ? ' Geri alabilirsin.' : ''), 'bad'); }
    else { G.status = 'idle'; setMsg('Sıradaki parça? ' + (cfg.hint ? 'Bir renge bir kez bas: nereye gideceğini göster; aynı renge/Gönder\'e tekrar bas: gönder.' : ''), 'info'); }
    saveLog(); refresh();
  }
  function select(pi) {
    if (G.status !== 'idle') return;
    var L = G.level, p = L.pieces[pi]; if (!p || G.st.used[pi]) return;
    var o = L.chooseTarget(G.st.filled, pi); if (!o) { toast('Bu parça şu an hiçbir yere yerleşemez'); return; }
    if (cfg.hint === 0) { send(pi); return; }
    if (G.selected === pi) { send(pi); return; }
    G.selected = pi; G.opt = o; G.switches++; G.previews.push(p.id);
    G.previewSealed = []; G.previewStuck = false;
    var text = 'Önizleme — ' + G.palette.names[p.col] + ' parça, ' + p.cells.length + ' kutu. Hedef hücreler tahtada yanıp sönüyor. Göndermek için aynı parçaya ya da Gönder\'e bas; ya da başka parçanın nereye gideceğine bak.', cls = 'info';
    if (cfg.hint >= 2) {
      var res = L.place(G.st, pi); G.previewSealed = res.sealed.filter(function (ti) { return true; }); G.previewStuck = res.stuck;
      if (res.won) text += ' Bu parça resmi tamamlar.';
      else if (res.sealed.length) { text += ' ⚠ Bu parça ' + res.sealed.length + ' boş hücreyi erişilemez yapar.'; cls = 'bad'; }
      else if (res.stuck) { text += ' ⚠ Bu parçadan sonra kalan hiçbir parça yerleşemez.'; cls = 'bad'; }
      else text += ' Bu parça hiçbir şeyi hemen kapatmaz.';
    }
    setMsg(text, cls); refresh();
  }
  function undo() {
    if (G.undoLeft <= 0 || !G.history.length || G.status === 'anim' || G.status === 'won') return;
    var h = G.history.pop(); G.st = h.before; G.visual = new Uint8Array(h.before.filled); G.status = 'idle'; G.undoLeft--; G.sealedShown = []; G.opt = null; G.selected = -1; G.previewSealed = [];
    G.cur.outcome = null; G.cur.tokens.push('U'); G.cur.moves.push({ i: G.cur.moves.length + 1, token: 'U', t_ms: Date.now() - G.cur.t0 }); G.readyAt = now(); G.switches = 0; G.previews = [];
    setMsg('Son parça geri alındı. Kalan geri alma: ' + G.undoLeft, 'info'); saveLog(); refresh();
  }
  function abandon() { if (G.cur && !G.cur.outcome) { G.cur.outcome = 'abandon'; G.cur.t1 = Date.now(); } nextLevel(); }
  function nextLevel() {
    if (!cfg.test) return;
    if (G.cur && !G.cur.outcome) { G.cur.outcome = 'abandon'; G.cur.t1 = Date.now(); }
    G.testIdx++;
    if (G.testIdx >= order.length) { showModal('<h3>Test bitti</h3><p>Teşekkürler. Lütfen kaydı indir ve araştırmacıya ver.</p><p><button onclick="window.CBGAME.downloadLog()">Kaydı indir</button></p>'); saveLog(); return; }
    loadLevel(order[G.testIdx]);
  }

  // ---------------------------------------------------------------- panel / el
  function setMsg(t, cls) { var m = $('msg'); m.textContent = t; m.className = cls || 'info'; }
  var toastTimer = 0;
  function toast(t) { var e = $('toast'); e.textContent = t; e.classList.add('show'); clearTimeout(toastTimer); toastTimer = setTimeout(function () { e.classList.remove('show'); }, 1600); }
  function nextOfColour(ci, st) { var L = G.level, r = -1; L.pieces.forEach(function (p) { if (r < 0 && p.col === ci && !(st || G.st).used[p.i]) r = p.i; }); return r; }
  function buildHand(seen, idle) {
    var L = G.level, hand = $('hand'), opts = L.options(seen), sel = G.selected >= 0 ? L.pieces[G.selected].col : -1;
    var key = G.lv.id + '#' + G.attemptNo + '|' + L.letters.map(function (x, ci) { var pi = nextOfColour(ci, seen); return pi < 0 ? 'u' : (opts[pi] ? 'f' + pi : 'x' + pi); }).join('') + '|' + sel + '|' + (idle ? 1 : 0);
    if (key === G.handSig) return; G.handSig = key;
    hand.innerHTML = '';
    L.letters.forEach(function (x, ci) {
      var pi = nextOfColour(ci, seen), left = L.pieces.filter(function (p) { return p.col === ci && !seen.used[p.i]; }).length;
      var b = document.createElement('button'), cv = document.createElement('canvas'), ok = pi >= 0 && !!opts[pi];
      b.className = 'pcard' + (sel === ci ? ' sel' : '') + (ok ? '' : ' nofit'); b.id = 'cb' + ci; b.style.background = col(ci); b.style.color = isDark(col(ci)) ? '#fff' : '#111';
      b.disabled = !idle || !ok;
      var p0 = pi >= 0 ? L.pieces[pi] : L.pieces.filter(function (p) { return p.col === ci; })[0];
      drawPiece(cv, p0, 16, isDark(col(ci)) ? '#ffffff88' : '#00000055'); b.appendChild(cv);
      var t = document.createElement('span'); t.textContent = (ci + 1) + ' · ' + G.palette.names[ci]; b.appendChild(t);
      var sm = document.createElement('small'); sm.textContent = p0.cells.length + ' hücre · kalan ' + left + ' parça' + (pi >= 0 && !ok ? ' · yerleşemez' : ''); b.appendChild(sm);
      b.addEventListener('click', function () { if (pi >= 0) select(pi); }); hand.appendChild(b);
    });
  }
  function refresh() {
    var L = G.level; if (!L) return;
    var seen = G.status === 'anim' ? { filled: G.visual, used: G.st.used } : G.st;   // animasyon sürerken oyuncunun GÖRDÜĞÜ durum
    var n = L.n, done = L.filledCount(seen.filled), rem = L.remaining(seen.filled), idle = G.status === 'idle', opts = L.options(seen);
    $('lvlTitle').textContent = cfg.test ? ('Seviye ' + (G.testIdx + 1) + ' / ' + order.length) : G.lv.name;
    $('lvlMeta').textContent = n + ' hücre · ' + L.K + ' renk · ' + L.P + ' parça · giriş hücresi: ' + L.entrances.length + (cfg.test ? '' : ' · ' + G.lv.id);
    $('progTxt').textContent = 'Yerleşen: ' + done + ' / ' + n + ' kutu (' + Math.round(100 * done / n) + '%) · gönderilen parça: ' + G.history.length + ' / ' + L.P;
    $('progBar').style.width = (100 * done / n) + '%';
    var remP = L.counts.map(function () { return 0; }), fit = L.counts.map(function () { return 0; });
    L.pieces.forEach(function (p) { if (!seen.used[p.i]) { remP[p.col]++; if (opts[p.i]) fit[p.col]++; } });
    var rows = '<tr><th></th><th>Kalan kutu</th><th>Kalan parça</th><th>Şimdi yerleşebilen</th></tr>';
    for (var i = 0; i < L.K; i++) rows += '<tr><td><span class="sw" style="background:' + col(i) + '"></span>' + G.palette.names[i] + '</td><td>' + rem[i] + '</td><td>' + remP[i] + '</td><td>' + fit[i] + (remP[i] - fit[i] > 0 ? ' <span class="warn">(' + (remP[i] - fit[i]) + ' yerleşemez)</span>' : '') + '</td></tr>';
    $('stock').innerHTML = rows;
    var hist = ''; G.history.forEach(function (h) { hist += '<i style="background:' + col(h.col) + '" title="' + G.palette.names[h.col] + ': ' + h.n + ' kutu">' + h.n + '</i>'; });
    $('history').innerHTML = hist || '<span class="meta">henüz yok</span>';
    buildHand(seen, idle);
    var sp = $('selShape'), si = $('selInfo');
    if (G.selected >= 0 && G.opt) {
      var p = L.pieces[G.selected]; sp.style.display = ''; drawPiece(sp, p, 22, col(p.col));
      si.textContent = 'Seçili: ' + G.palette.names[p.col] + ' · ' + p.cells.length + ' kutu → tahtada ' + G.opt.cells.length + ' hücre işaretli';
    } else { sp.style.display = 'none'; si.textContent = 'Parça seç: şekli burada, hedefi tahtada görünür.'; }
    $('sendBtn').disabled = !(idle && G.selected >= 0); $('sendBtn').style.display = cfg.hint === 0 ? 'none' : '';
    $('undoBtn').disabled = !(G.undoLeft > 0 && G.history.length && (G.status === 'idle' || G.status === 'sealed' || G.status === 'stuck')); $('undoBtn').style.display = cfg.undo > 0 ? '' : 'none';
    $('undoBtn').textContent = 'Geri al (' + G.undoLeft + ')';
    var ab = $('abandonBtn'); ab.style.display = cfg.test ? '' : 'none'; ab.textContent = (G.status === 'won') ? 'Sonraki seviye' : 'Bu seviyeyi bırak';
    if (!cfg.test) devInfo();
  }
  function devInfo() {
    var s = G.lv.stats || {}, t = [];
    ['p_random', 'decision_states', 'free_states', 'forced_states', 'trap_instant', 'trap_delayed', 'n_states'].forEach(function (k) { if (s[k] != null) t.push(k + ' = ' + s[k]); });
    if (s.heuristics) t.push('sezgiseller (kazanır?): ' + Object.keys(s.heuristics).map(function (k) { return k + '=' + (s.heuristics[k] ? 'E' : 'H'); }).join(' '));
    $('devInfo').innerHTML = 'Çözücü ölçümü (araştırma; oyunda gösterilmez):<br>' + t.join(' · ') + '<br>Kayıt: ' + LOG.attempts.length + ' deneme.';
  }
  function fillSelectors() {
    $('hintSel').value = String(cfg.hint); $('ghostChk').checked = cfg.ghost; $('speedSel').value = [1, 2, 4].indexOf(cfg.speed) >= 0 ? String(cfg.speed) : '1'; $('undoSel').value = String(cfg.undo);
    if (cfg.test) { $('lvlLbl').style.display = 'none'; $('dev').style.display = 'none'; $('parityBtn').style.display = 'none'; $('hintSel').parentNode.style.display = 'none'; $('ghostChk').parentNode.style.display = 'none'; $('undoLbl').style.display = 'none'; }
    if (!$('levelSel').options.length) $('levelSel').innerHTML = LEVELS.map(function (l) { return '<option value="' + l.id + '">' + l.id + ' · ' + l.name + ' (' + l.cells + ' hücre, ' + l.pieces.length + ' parça)</option>'; }).join('');
    $('levelSel').value = G.lv.id;
  }

  // ---------------------------------------------------------------- kayıt
  function saveLog() { try { localStorage.setItem('cb_log_v1', JSON.stringify(LOG)); } catch (e) { /* yoksay */ } }
  function downloadLog() {
    LOG.meta.exported = new Date().toISOString();
    var blob = new Blob([JSON.stringify(LOG, null, 1)], { type: 'application/json' }), a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = 'renk_yerlestirme_parca_kayit_' + (cfg.player || 'oyuncu') + '_' + Date.now() + '.json'; document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }

  // ---------------------------------------------------------------- parity paneli
  function showModal(html) { $('modalBody').innerHTML = html; $('modal').classList.add('show'); }
  function runParity() {
    var ok = 0, total = 0, bad = [], rows = '';
    VECTORS.levels.forEach(function (lv) {
      var L = new CB.PLevel(lv.grid, lv.pieces), lok = 0;
      lv.cases.forEach(function (c) {
        total++; var sim = L.simulate(c.sequence);
        if (JSON.stringify(sim) === JSON.stringify(c.expected)) { ok++; lok++; } else bad.push(lv.level_id + '/' + c.name);
      });
      rows += '<tr><td>' + lv.level_id + '</td><td>' + lv.cases.length + '</td><td>' + lok + '</td></tr>';
    });
    showModal('<h3>Parity testi: prototip çekirdeği ↔ Python referansı (piece_ref.py)</h3><p>Beklenen çıktılar (her adımda TÜM parçaların seçtiği hedef konum, yerleşen hücreler sırasıyla, kilit/sıkışma/kazanma bayrakları) Python\'da üretildi ve bu sayfaya gömüldü; aşağıda tarayıcıdaki <code>engine.js</code> ile aynı dizileri oynatıp tam eşitlik arıyoruz.</p>' +
      '<p><b class="' + (ok === total ? 'ok' : 'warn') + '">' + ok + ' / ' + total + ' vaka birebir aynı</b> (' + VECTORS.levels.length + ' seviye)' + (bad.length ? '<br>Farklı: ' + bad.join(', ') : '') + '</p><table><tr><th>Seviye</th><th>Vaka</th><th>Eşleşen</th></tr>' + rows + '</table>');
    return { ok: ok, total: total, bad: bad };
  }

  // ---------------------------------------------------------------- döngü / olaylar
  function frame() {
    var t = now();
    if (G.status === 'anim') {
      G.workers.forEach(function (w) { if (w.state === 0 && t >= w.arrive) { w.state = 1; w.doneAt = t; G.visual[w.ti] = 1; G.pops[w.ti] = t; } });
      if (t >= G.waveEnd) { G.visual = new Uint8Array(G.st.filled); finishWave(); }
      else if (Math.floor(t * 8) !== frame.last) { frame.last = Math.floor(t * 8); refresh(); }
    }
    draw(); requestAnimationFrame(frame);
  }
  $('restartBtn').addEventListener('click', function () { newAttempt('restart'); });
  $('abandonBtn').addEventListener('click', function () { if (G.status === 'won') nextLevel(); else abandon(); });
  $('sendBtn').addEventListener('click', function () { if (G.selected >= 0) send(G.selected); });
  $('undoBtn').addEventListener('click', undo);
  $('logBtn').addEventListener('click', downloadLog);
  $('parityBtn').addEventListener('click', runParity);
  $('modalClose').addEventListener('click', function () { $('modal').classList.remove('show'); });
  $('levelSel').addEventListener('change', function () { loadLevel(this.value); });
  $('hintSel').addEventListener('change', function () { cfg.hint = parseInt(this.value, 10); newAttempt('restart'); });
  $('ghostChk').addEventListener('change', function () { cfg.ghost = this.checked; });
  $('speedSel').addEventListener('change', function () { cfg.speed = parseFloat(this.value); });
  $('undoSel').addEventListener('change', function () { cfg.undo = parseInt(this.value, 10); newAttempt('restart'); });
  window.addEventListener('resize', layout);
  window.addEventListener('keydown', function (e) {
    if (e.target && /select|input|textarea/i.test(e.target.tagName)) return;
    if (e.key >= '1' && e.key <= '9') { var pi = nextOfColour(parseInt(e.key, 10) - 1); if (pi >= 0) select(pi); }
    else if (e.key === 'Enter' || e.key === ' ') { if (G.selected >= 0) { e.preventDefault(); send(G.selected); } }
    else if (e.key === 'z' || e.key === 'Z') undo();
    else if (e.key === 'r' || e.key === 'R') newAttempt('restart');
  });
  if (window.ResizeObserver) new ResizeObserver(layout).observe($('boardWrap'));

  // otomasyon / araştırma API'si (tarayıcı testleri ve kayıt için). Parça = indeks ya da id ('P3')
  function pidx(x) { if (typeof x === 'number') return x; var ci = G.level.letters.indexOf(x); if (ci >= 0) return nextOfColour(ci); var k = -1; G.level.pieces.forEach(function (p) { if (p.id === x) k = p.i; }); return k; }
  window.CBGAME = {
    send: function (x) { var i = pidx(x); if (cfg.hint === 0) send(i); else { G.selected = -1; select(i); select(i); } },
    select: function (x) { select(pidx(x)); },
    state: function () { return { status: G.status, filled: G.level.filledCount(G.st.filled), n: G.level.n, waves: G.history.length, level: G.lv.id, sealed: G.sealedShown.length, selected: G.selected,
                                  left: G.level.remainingPieces(G.st), undoLeft: G.undoLeft, opt: G.opt ? G.opt.cells.length : 0 }; },
    restart: function () { newAttempt('restart'); }, loadLevel: loadLevel, downloadLog: downloadLog, getLog: function () { return LOG; }, runParity: runParity,
    setCfg: function (o) { for (var k in o) cfg[k] = o[k]; fillSelectors(); newAttempt('restart'); }, undo: undo, nextLevel: nextLevel
  };

  // başlat
  var start = cfg.test ? order[0] : (qs.get('level') && byId[qs.get('level')] ? qs.get('level') : LEVELS[0].id);
  G.testIdx = 0; loadLevel(start); requestAnimationFrame(frame);
})();

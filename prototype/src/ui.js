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
              undo: clampInt(qs.get('undo'), 0, 9, 0), path: (['0', 'A', 'B', 'C'].indexOf((qs.get('path') || '').toUpperCase()) >= 0 ? qs.get('path').toUpperCase() : 'C'), test: qs.get('mode') === 'test', player: qs.get('player') || '' };
  var byId = {}; LEVELS.forEach(function (l) { byId[l.id] = l; });
  var order = (qs.get('levels') || '').split(',').filter(function (x) { return byId[x]; });
  if (!order.length) order = LEVELS.map(function (l) { return l.id; });

  var canvas = $('board'), ctx = canvas.getContext('2d');
  var G = { lv: null, level: null, palette: null, st: null, visual: null, status: 'idle', history: [], selected: -1, opt: null, previewSealed: [], previewStuck: false, read: null,
            workers: [], dest: null, pops: {}, attemptNo: 0, undoLeft: 0, waveEnd: 0, pending: null, readyAt: 0, switches: 0, previews: [], cur: null, testIdx: 0,
            s: 10, ox: 0, oy: 0, dpr: 1, cw: 0, ch: 0, sealedShown: [], wonAt: 0, handSig: '' };
  var LOG = { meta: { app: 'renk-yerlestirme-prototip-v1-parca', started: new Date().toISOString(), ua: navigator.userAgent, player: cfg.player, test: cfg.test }, attempts: [] };
  function now() { return performance.now() / 1000; }

  // ---------------------------------------------------------------- RESİM MODU (lv.art): gizli piksel grid üzerinde PIXEL-ART resim
  // Mantık yalnız engine.js'te (grid = piksel-art'ın dolu piksel maskesi, parça = sabit piksel yaması). Burada yalnız görsel:
  // grid çizgisi/hücre kenarı/koridor ÇİZİLMEZ; resim, tam sayı ölçekli en-yakın-komşu pikseller olarak kesintisiz yüzey oluşturur.
  var IMG = { ready: false, N: 96, art: null, ghost: null, built: null, bctx: null, sil: null, colors: null, sprites: {}, paths: {}, sparks: [], tmp: null };
  function mkCanvas(w, h) { var c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
  function imgInit(lv) {
    var A = window.CB_ART.pixels(), N = A.N, art = mkCanvas(N, N), gh = mkCanvas(N, N), sl = mkCanvas(N, N), ai = art.getContext('2d').createImageData(N, N), gi = gh.getContext('2d').createImageData(N, N), si = sl.getContext('2d').createImageData(N, N);
    for (var i = 0; i < N * N; i++) {
      var v = A.idx[i]; if (!v) continue; var c = rgb(A.pal[v]), k = i * 4, lum = (c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11) / 255, g = 160 + 66 * lum;   // hayalet: silik pixel-art tonu
      ai.data[k] = c[0]; ai.data[k + 1] = c[1]; ai.data[k + 2] = c[2]; ai.data[k + 3] = 255;
      gi.data[k] = g - 8; gi.data[k + 1] = g - 3; gi.data[k + 2] = g + 8; gi.data[k + 3] = 235; si.data[k] = si.data[k + 1] = si.data[k + 2] = si.data[k + 3] = 255;
    }
    art.getContext('2d').putImageData(ai, 0, 0); gh.getContext('2d').putImageData(gi, 0, 0); sl.getContext('2d').putImageData(si, 0, 0);
    IMG.N = N; IMG.art = art; IMG.ghost = gh; IMG.sil = sl; IMG.built = mkCanvas(N, N); IMG.bctx = IMG.built.getContext('2d'); IMG.sprites = {}; IMG.paths = {}; IMG.sparks = []; IMG.tmp = null;
    IMG.colors = G.level.targets.map(function (tg) { return A.pal[A.idx[tg.r * N + tg.c]]; });
    IMG.ready = true;
  }
  function imgReveal(ti) { var tg = G.level.targets[ti]; IMG.bctx.fillStyle = IMG.colors[ti]; IMG.bctx.fillRect(tg.c, tg.r, 1, 1); }
  function imgSync(filled) { IMG.bctx.clearRect(0, 0, IMG.N, IMG.N); for (var ti = 0; ti < G.level.n; ti++) if (filled[ti]) imgReveal(ti); IMG.sparks = []; G.flash = null; G.revealQ = []; }
  function absCells(pi) { var p = G.level.pieces[pi]; return p.cells.map(function (x) { return [x[0] + p.ar, x[1] + p.ac]; }); }
  function pieceTis(pi) { var L = G.level; return absCells(pi).map(function (x) { return L.tIdx[x[0] * L.w + x[1]]; }); }
  function sprite(pi) {   // parçanın piksel yaması (resmin gerçek renkleriyle, hücre başına 1 px)
    if (IMG.sprites[pi]) return IMG.sprites[pi];
    var tis = pieceTis(pi), L = G.level, r0 = 1e9, c0 = 1e9, r1 = -1, c1 = -1;
    tis.forEach(function (ti) { var tg = L.targets[ti]; r0 = Math.min(r0, tg.r); c0 = Math.min(c0, tg.c); r1 = Math.max(r1, tg.r); c1 = Math.max(c1, tg.c); });
    var cv = mkCanvas(c1 - c0 + 1, r1 - r0 + 1), g = cv.getContext('2d');
    tis.forEach(function (ti) { var tg = L.targets[ti]; g.fillStyle = IMG.colors[ti]; g.fillRect(tg.c - c0, tg.r - r0, 1, 1); });
    return (IMG.sprites[pi] = { cv: cv, r0: r0, c0: c0, w: c1 - c0 + 1, h: r1 - r0 + 1 });
  }
  function drawSpriteTo(cv, pi, box) {   // tam sayı ölçek, yumuşatma yok
    var sp = sprite(pi), sc = Math.max(1, Math.floor(box / Math.max(sp.w, sp.h))), dpr = window.devicePixelRatio || 1;
    cv.style.width = sp.w * sc + 'px'; cv.style.height = sp.h * sc + 'px'; cv.width = Math.round(sp.w * sc * dpr); cv.height = Math.round(sp.h * sc * dpr);
    var g = cv.getContext('2d'); g.imageSmoothingEnabled = false; g.clearRect(0, 0, cv.width, cv.height); g.drawImage(sp.cv, 0, 0, cv.width, cv.height);
  }
  function pixCanvas(tis, color) { var L = G.level, c = mkCanvas(IMG.N, IMG.N), g = c.getContext('2d'); g.fillStyle = color; tis.forEach(function (ti) { var tg = L.targets[ti]; g.fillRect(tg.c, tg.r, 1, 1); }); return c; }
  // hücre kümesi → hücre birimlerinde dış kenar yolu (piksel basamaklı; piksel-art için doğru dil)
  function edgePath(tis) {
    var L = G.level, set = {}, p = new Path2D(); tis.forEach(function (t) { set[t] = 1; });
    tis.forEach(function (ti) {
      var tg = L.targets[ti], x = tg.c, y = tg.r;
      [[-1, 0, x, y, x + 1, y], [1, 0, x, y + 1, x + 1, y + 1], [0, -1, x, y, x, y + 1], [0, 1, x + 1, y, x + 1, y + 1]].forEach(function (d) {
        var rr = tg.r + d[0], cc = tg.c + d[1], nt = (rr >= 0 && rr < L.h && cc >= 0 && cc < L.w) ? L.tIdx[rr * L.w + cc] : -1;
        if (nt < 0 || !set[nt]) { p.moveTo(d[2], d[3]); p.lineTo(d[4], d[5]); }
      });
    });
    return p;
  }
  function pieceEdge(pi) { if (!IMG.paths[pi]) IMG.paths[pi] = edgePath(pieceTis(pi)); return IMG.paths[pi]; }
  // yerleştirmenin görsel birimleri: teslimat başına küçük bir PİKSEL KÜMESİ (≤6 komşu hücre); rota = kümenin en sığ hücresine gerçek rota
  function artClusters(res, routes) {
    var L = G.level, D = res.bfs.dist, idx = {}, assigned = {}, out = [], CAP = 6;
    res.placed.forEach(function (ti, i) { idx[ti] = i; });
    res.placed.forEach(function (t0) {
      if (assigned[t0]) return; var cl = [t0], q = [t0]; assigned[t0] = 1;
      while (q.length && cl.length < CAP) {
        var u = q.shift(), tg = L.targets[u];
        [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(function (d) {
          if (cl.length >= CAP) return; var rr = tg.r + d[0], cc = tg.c + d[1]; if (rr < 0 || cc < 0 || rr >= L.h || cc >= L.w) return;
          var nt = L.tIdx[rr * L.w + cc]; if (nt < 0 || assigned[nt] || idx[nt] === undefined) return; assigned[nt] = 1; cl.push(nt); q.push(nt);
        });
      }
      out.push(cl);
    });
    var units = out.map(function (cl) { var rep = cl.reduce(function (b, t) { return D[L.targets[t].cell] < D[L.targets[b].cell] ? t : b; }, cl[0]); return { ti: rep, cells: cl, path: routes[idx[rep]], d: D[L.targets[rep].cell] }; });
    units.sort(function (a, b) { return (b.d - a.d) || (a.ti - b.ti); });   // en derinden başla: hiçbir işçi, görünür biçimde dolmuş bir kümenin içinden geçmez
    return units;
  }

  // ---------------------------------------------------------------- renk yardımcıları
  function rgb(h) { var n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
  function mix(a, b, t) { var x = rgb(a), y = rgb(b); return 'rgb(' + Math.round(x[0] + (y[0] - x[0]) * t) + ',' + Math.round(x[1] + (y[1] - x[1]) * t) + ',' + Math.round(x[2] + (y[2] - x[2]) * t) + ')'; }
  function col(i) { return G.palette.colors[i]; }
  function isDark(h) { var c = rgb(h); return (c[0] * 299 + c[1] * 587 + c[2] * 114) / 1000 < 90; }
  var PAPER = '#eef1f6', GHOST_BASE = '#eef1f6';   // tek bütün, temiz zemin; yürüme yolları/duvarlar/hücre sınırları görünmez

  // ---------------------------------------------------------------- seviye / deneme
  function loadLevel(id) {
    var lv = byId[id]; if (!lv) return;
    G.lv = lv; G.level = new CB.PLevel(lv.grid, lv.pieces); G.palette = lv.palette; G.attemptNo = 0;
    G.handQ = lv.hand ? lv.hand.map(function (q) { return q.map(function (id) { return G.level.pieces.findIndex(function (p) { return p.id === id; }); }); }) : null;
    if (lv.art) { imgInit(lv); if (!qs.get('path')) cfg.path = 'A'; }
    newAttempt('load'); layout(); fillSelectors();
  }
  function newAttempt(reason) {
    G.revealQ = [];
    if (G.cur && !G.cur.outcome) { G.cur.outcome = reason === 'load' ? 'switch' : 'restart'; G.cur.t1 = Date.now(); }
    G.st = G.level.newState(); G.visual = new Uint8Array(G.st.filled); G.status = 'idle'; G.history = []; G.selected = -1; G.opt = null; G.read = null; G.read = null;
    G.previewSealed = []; G.previewStuck = false; G.workers = []; G.dest = null; G.pops = {}; G.pending = null; G.sealedShown = []; G.sealedCv = null; G.undoLeft = cfg.undo; G.wonAt = 0; G.handSig = ''; if (G.lv.art) imgSync(G.st.filled);
    G.cur = { level: G.lv.id, attempt: ++G.attemptNo, reason: reason, hint: cfg.hint, ghost: cfg.ghost, speed: cfg.speed, undo_budget: cfg.undo, pieces: G.level.P,
              t0: Date.now(), tokens: [], moves: [], outcome: null };
    LOG.attempts.push(G.cur); G.readyAt = now(); G.switches = 0; G.previews = []; saveLog();
    setMsg('Elindeki 3 parçadan birine bas: kedinin üzerinde nereye gideceği görünür (göndermez). Üçünü de karşılaştır: hangisini ŞİMDİ göndermelisin?', 'info');
    refresh();
  }

  // ---------------------------------------------------------------- yerleşim (canvas)
  function layout() {
    var wrap = $('boardWrap'); G.cw = wrap.clientWidth; G.ch = wrap.clientHeight; G.dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(G.cw * G.dpr); canvas.height = Math.round(G.ch * G.dpr);
    if (!G.level) return;
    if (G.lv && G.lv.art) {   // resim modu: tam sayı cihaz pikseli ölçeği (keskin piksel-art), kare tahta
      var d = G.dpr, ps = Math.max(2, Math.floor(Math.min(G.cw * d / (G.level.w + 8), G.ch * d / (G.level.h + 8)))); G.s = ps / d;
      G.ox = Math.round((G.cw * d - G.level.w * ps) / 2) / d; G.oy = Math.round(Math.max(ps * 4, (G.ch * d - (G.level.h + 4) * ps) / 2)) / d; return;
    }
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
  function rrect(x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
  var AMBER = '255,176,46';
  // B — kritik alan: yerleşince erişimi kapanacak hücreler yumuşak kehribar nabzı (alarm kırmızısı değil); yolu uzayacaklar daha soluk
  function drawCritical(t) {
    var L = G.level, s = G.s, pulse = 0.5 + 0.5 * Math.sin(t * 3.2);
    G.read.detour.forEach(function (ti) {
      var tg = L.targets[ti], x = G.ox + tg.c * s, y = G.oy + tg.r * s;
      ctx.fillStyle = 'rgba(' + AMBER + ',' + (0.10 + 0.08 * pulse).toFixed(3) + ')'; ctx.fillRect(x, y, s, s);
    });
    if (!G.read.cut.length) return;
    ctx.save();
    G.read.cut.forEach(function (ti) {
      var tg = L.targets[ti], x = G.ox + tg.c * s, y = G.oy + tg.r * s;
      ctx.fillStyle = 'rgba(' + AMBER + ',' + (0.30 + 0.25 * pulse).toFixed(3) + ')'; ctx.fillRect(x, y, s, s);
    });
    ctx.shadowColor = 'rgba(' + AMBER + ',.95)'; ctx.shadowBlur = s * (0.5 + 0.5 * pulse);
    ctx.strokeStyle = 'rgba(255,150,20,' + (0.55 + 0.35 * pulse).toFixed(3) + ')'; ctx.lineWidth = Math.max(2, s * 0.09); ctx.lineJoin = 'round';
    var set = {}; G.read.cut.forEach(function (ti) { set[ti] = 1; });
    ctx.beginPath();
    G.read.cut.forEach(function (ti) {   // kesilen bölgenin dış çerçevesi
      var tg = L.targets[ti], x = G.ox + tg.c * s, y = G.oy + tg.r * s;
      [[-1, 0, x, y, x + s, y], [1, 0, x, y + s, x + s, y + s], [0, -1, x, y, x, y + s], [0, 1, x + s, y, x + s, y + s]].forEach(function (d) {
        var rr = tg.r + d[0], cc = tg.c + d[1], nt = (rr >= 0 && rr < L.h && cc >= 0 && cc < L.w) ? L.tIdx[rr * L.w + cc] : -1;
        if (nt < 0 || !set[nt]) { ctx.moveTo(d[2], d[3]); ctx.lineTo(d[4], d[5]); }
      });
    });
    ctx.stroke(); ctx.restore();
  }
  // A — worker izi: seçili parçanın GERÇEK rotasında (send'deki işçilerle aynı yollar) girişten hedefe akan ışık paketleri + silik ayak izleri
  function drawTrail(t) {
    var s = G.s, routes = G.read.routes, pc = col(G.level.pieces[G.selected].col), dark = mix(pc, '#1b2440', 0.45), speed = 4.5, maxLen = 0;
    routes.forEach(function (r) { maxLen = Math.max(maxLen, r.length - 1); });
    var cycle = maxLen / speed + 0.9, tt = t % cycle, seen = {};
    ctx.save(); ctx.fillStyle = dark;
    routes.forEach(function (r) {   // ayak izleri: rota hücrelerinde küçük, silik noktalar (kalıcı çizgi yok)
      for (var i = 1; i < r.length - 1; i++) { if (seen[r[i]]) continue; seen[r[i]] = 1; ctx.globalAlpha = 0.2; ctx.beginPath(); ctx.arc(cx(r[i]), cy(r[i]), Math.max(1.5, s * 0.055), 0, 7); ctx.fill(); }
    });
    routes.forEach(function (r) {   // akan ışık paketi + kısa kuyruk
      var steps = r.length - 1; if (steps <= 0) return;
      var f = tt * speed; if (f > steps + 0.6) return;
      for (var k = 0; k < 7; k++) {
        var ff = f - k * 0.22; if (ff < 0 || ff > steps) continue;
        var i = Math.min(steps - 1, Math.floor(ff)), u = ff - i, px = cx(r[i]) + (cx(r[i + 1]) - cx(r[i])) * u, py = cy(r[i]) + (cy(r[i + 1]) - cy(r[i])) * u;
        var fade = f > steps ? Math.max(0, 1 - (f - steps) / 0.6) : 1;
        ctx.globalAlpha = (0.75 - k * 0.1) * fade; ctx.shadowColor = pc; ctx.shadowBlur = k === 0 ? s * 0.5 : 0;
        ctx.fillStyle = k === 0 ? '#ffffff' : dark; ctx.beginPath(); ctx.arc(px, py, Math.max(2, s * (0.11 - k * 0.008)), 0, 7); ctx.fill();
        if (k === 0) { ctx.shadowBlur = 0; ctx.globalAlpha = 0.9 * fade; ctx.strokeStyle = dark; ctx.lineWidth = Math.max(1, s * 0.03); ctx.stroke(); }
      }
    });
    ctx.restore();
  }
  function draw() {
    var t = now(), L = G.level; if (!L) return; if (G.lv.art) { drawArt(t); return; }
    var s = G.s, w = L.w;
    ctx.setTransform(G.dpr, 0, 0, G.dpr, 0, 0); ctx.clearRect(0, 0, G.cw, G.ch);
    ctx.fillStyle = '#10141d'; ctx.fillRect(0, 0, G.cw, G.ch);
    // GÖRSEL: tahta tek parça düz zemin. Mantıksal grid/yol (duvar, zemin, giriş) çizilmez; yalnız hedef figür görünür.
    var pad = s * 0.7; ctx.fillStyle = PAPER; rrect(G.ox - pad, G.oy - pad, w * s + pad * 2, L.h * s + pad * 2, s * 0.6); ctx.fill();
    L.entrances.forEach(function (e) {   // giriş: zeminin kenarında küçük sarı işaret (koridor değil)
      var d = outward(e); if (!d) return; var ex = cx(e), ey = cy(e), q = s * 0.3;
      ctx.fillStyle = '#ffb703'; ctx.beginPath(); ctx.moveTo(ex - d[0] * s * 0.5 - d[1] * q, ey - d[1] * s * 0.5 + d[0] * q); ctx.lineTo(ex - d[0] * s * 0.5 + d[1] * q, ey - d[1] * s * 0.5 - d[0] * q); ctx.lineTo(ex + d[0] * s * 0.05, ey + d[1] * s * 0.05); ctx.fill();
    });
    drawDepot(t);
    var sealedSet = {}, pvSealed = {};
    G.sealedShown.forEach(function (ti) { sealedSet[ti] = 1; });
    G.previewSealed.forEach(function (ti) { pvSealed[ti] = 1; });
    for (var ti = 0; ti < L.n; ti++) {
      var tg = L.targets[ti], x0 = G.ox + tg.c * s, y0 = G.oy + tg.r * s, color = col(tg.col);
      if (G.visual[ti]) { var age = t - (G.pops[ti] || -9); box(x0, y0, s, color, age < 0.28 ? 0.35 * (1 - age / 0.28) : 0); }
      else {
        ctx.fillStyle = cfg.ghost ? mix(color, GHOST_BASE, 0.5) : '#c3cad8'; ctx.fillRect(x0 - 0.25, y0 - 0.25, s + 0.5, s + 0.5);   // dikişsiz: hücre sınırı yok
      }
    }
    var allT = []; for (var tt = 0; tt < L.n; tt++) allT.push(tt);
    outline(allT, 'rgba(40,50,80,.35)', Math.max(1, s * 0.05));   // figürün siluet çerçevesi
    if (G.read && G.status === 'idle' && (cfg.path === 'B' || cfg.path === 'C')) drawCritical(t);
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
    if (G.read && G.status === 'idle' && (cfg.path === 'A' || cfg.path === 'C')) drawTrail(t);
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
  // ---- RESİM MODU çizimi
  function drawHole(s) {
    var L = G.level, e = L.entrances[0], ex = G.ox + (e % L.w + 0.5) * s, ey = G.oy + L.h * s + s * 0.5;
    ctx.fillStyle = '#6b4a35'; ctx.beginPath(); ctx.ellipse(ex, ey, s * 6, s * 2.6, 0, 0, 7); ctx.fill();
    ctx.fillStyle = '#2d1b12'; ctx.beginPath(); ctx.ellipse(ex, ey + s * 0.2, s * 4.8, s * 1.9, 0, 0, 7); ctx.fill();
  }
  function artRoutesSubset(routes) {   // iz için en çok 9 temsilci rota (en uzun + eşit aralıklı)
    var idx = routes.map(function (r, i) { return i; }).sort(function (a, b) { return routes[b].length - routes[a].length; }), out = [], k = Math.max(1, Math.floor(idx.length / 9));
    for (var i = 0; i < idx.length && out.length < 9; i += k) out.push(routes[idx[i]]);
    return out;
  }
  function drawArtTrail(t) {
    var s = G.s, rd = G.read; if (!rd.sub) rd.sub = artRoutesSubset(rd.routes);
    var routes = rd.sub, speed = 44, maxLen = 0, seen = {};
    routes.forEach(function (r) { maxLen = Math.max(maxLen, r.length - 1); });
    var cycle = maxLen / speed + 0.8, tt = t % cycle, rad = Math.max(2.2, s * 0.55);
    ctx.save();
    routes.forEach(function (r) {   // ayak izleri: rota boyunca silik noktalar
      ctx.fillStyle = 'rgba(70,40,90,.30)';
      for (var i = 3; i < r.length - 1; i += 4) { if (seen[r[i]]) continue; seen[r[i]] = 1; ctx.fillRect(cx(r[i]) - s * 0.3, cy(r[i]) - s * 0.3, Math.max(1.5, s * 0.6), Math.max(1.5, s * 0.6)); }
    });
    routes.forEach(function (r) {   // akan ışık paketleri (gerçek worker rotası)
      var steps = r.length - 1; if (steps <= 0) return; var f = tt * speed; if (f > steps + 0.5) return;
      var fade = f > steps ? Math.max(0, 1 - (f - steps) / 0.5) : 1;
      for (var k = 0; k < 8; k++) {
        var ff = f - k * 1.4; if (ff < 0 || ff > steps) continue;
        var i = Math.min(steps - 1, Math.floor(ff)), u = ff - i, px = cx(r[i]) + (cx(r[i + 1]) - cx(r[i])) * u, py = cy(r[i]) + (cy(r[i + 1]) - cy(r[i])) * u;
        ctx.globalAlpha = (0.95 - k * 0.11) * fade; ctx.shadowColor = '#ffd36a'; ctx.shadowBlur = k === 0 ? s * 2 : 0;
        ctx.fillStyle = k === 0 ? '#fff' : 'rgba(255,215,120,.95)'; ctx.beginPath(); ctx.arc(px, py, rad * (1 - k * 0.08), 0, 7); ctx.fill();
        if (k === 0) { ctx.shadowBlur = 0; ctx.strokeStyle = 'rgba(90,50,20,.8)'; ctx.lineWidth = 1; ctx.stroke(); }
      }
    });
    ctx.restore();
  }
  function drawArtCritical(t) {   // B: yerleşince girişten erişilemeyecek piksel bölgesi kehribar nabzı; yolu uzayacak bölge daha soluk
    var rd = G.read, s = G.s, W = G.level.w * s, pulse = 0.5 + 0.5 * Math.sin(t * 3.2);
    if (!rd.cutCv) { rd.detCv = rd.detour.length ? pixCanvas(rd.detour, 'rgb(' + AMBER + ')') : null; rd.cutCv = rd.cut.length ? pixCanvas(rd.cut, 'rgb(' + AMBER + ')') : null; rd.cutEdge = rd.cut.length ? edgePath(rd.cut) : null; }
    if (rd.detCv) { ctx.save(); ctx.globalAlpha = 0.16 + 0.1 * pulse; ctx.drawImage(rd.detCv, G.ox, G.oy, W, W); ctx.restore(); }
    if (rd.cutCv) {
      ctx.save(); ctx.globalAlpha = 0.38 + 0.28 * pulse; ctx.drawImage(rd.cutCv, G.ox, G.oy, W, W); ctx.restore();
      ctx.save(); ctx.translate(G.ox, G.oy); ctx.scale(s, s); ctx.shadowColor = 'rgba(' + AMBER + ',.95)'; ctx.shadowBlur = s * (1.5 + 1.5 * pulse); ctx.strokeStyle = 'rgba(255,140,20,' + (0.6 + 0.3 * pulse).toFixed(2) + ')'; ctx.lineWidth = 0.6; ctx.lineJoin = 'round'; ctx.stroke(rd.cutEdge); ctx.restore();
    }
  }
  function drawArt(t) {
    var L = G.level, s = G.s, N = L.w, ox = G.ox, oy = G.oy, W = N * s;
    // gecikmeli piksel teslimatları: işçi vardığında kümenin pikselleri tek tek belirir
    if (G.revealQ && G.revealQ.length) {
      var keep = []; G.revealQ.forEach(function (q) { if (q.at <= t) { G.visual[q.ti] = 1; imgReveal(q.ti); if (q.ti % 2 === 0 && IMG.sparks.length < 260) { var cell = G.level.targets[q.ti].cell; IMG.sparks.push({ x: cx(cell), y: cy(cell), t0: t }); } } else keep.push(q); }); G.revealQ = keep;
    }
    ctx.setTransform(G.dpr, 0, 0, G.dpr, 0, 0); ctx.clearRect(0, 0, G.cw, G.ch); ctx.fillStyle = '#10141d'; ctx.fillRect(0, 0, G.cw, G.ch);
    var pad = s * 3; ctx.fillStyle = PAPER; rrect(ox - pad, oy - pad, W + pad * 2, W + pad * 2, s * 5); ctx.fill();   // tek bütün, temiz zemin
    drawHole(s); if (!IMG.ready) return;
    ctx.imageSmoothingEnabled = false;
    if (cfg.ghost) ctx.drawImage(IMG.ghost, ox, oy, W, W);                       // henüz inşa edilmemiş pikseller: çok silik silüet
    ctx.drawImage(IMG.built, ox, oy, W, W);                                      // inşa edilmiş pikseller
    if (G.status === 'sealed' && G.sealedShown.length) {
      if (!G.sealedCv) G.sealedCv = pixCanvas(G.sealedShown, 'rgb(255,120,40)');
      ctx.save(); ctx.globalAlpha = 0.3 + 0.2 * Math.sin(t * 5); ctx.drawImage(G.sealedCv, ox, oy, W, W); ctx.restore(); ctx.imageSmoothingEnabled = false;
    }
    if (G.read && G.status === 'idle' && (cfg.path === 'B' || cfg.path === 'C')) { drawArtCritical(t); ctx.imageSmoothingEnabled = false; }
    if (G.selected >= 0 && G.status === 'idle') {   // ÖNİZLEME: seçili piksel yaması resmin gerçek renkleriyle, hafif nabızla belirir
      var sp = sprite(G.selected), pulse = 0.5 + 0.5 * Math.sin(t * 5.2);
      ctx.save(); ctx.globalAlpha = 0.55 + 0.4 * pulse; ctx.drawImage(sp.cv, ox + sp.c0 * s, oy + sp.r0 * s, sp.w * s, sp.h * s); ctx.restore(); ctx.imageSmoothingEnabled = false;
      ctx.save(); ctx.translate(ox, oy); ctx.scale(s, s); ctx.lineJoin = 'miter'; ctx.shadowColor = 'rgba(255,255,255,.95)'; ctx.shadowBlur = s * (1.5 + 1.5 * pulse); ctx.strokeStyle = 'rgba(255,255,255,.95)'; ctx.lineWidth = 0.7; ctx.stroke(pieceEdge(G.selected));
      ctx.shadowBlur = 0; ctx.strokeStyle = 'rgba(70,40,20,.9)'; ctx.lineWidth = 0.22; ctx.stroke(pieceEdge(G.selected)); ctx.restore();
    }
    if (G.read && G.status === 'idle' && (cfg.path === 'A' || cfg.path === 'C')) drawArtTrail(t);
    if (G.flash) {   // tamamlanan yamanın parıltısı
      var age = t - G.flash.t0; if (age > 0.9) G.flash = null; else {
        var fs = sprite(G.flash.pi), fa = 1 - age / 0.9;
        ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 0.5 * fa; ctx.drawImage(fs.cv, ox + fs.c0 * s, oy + fs.r0 * s, fs.w * s, fs.h * s); ctx.restore(); ctx.imageSmoothingEnabled = false;
        ctx.save(); ctx.translate(ox, oy); ctx.scale(s, s); ctx.globalAlpha = fa; ctx.shadowColor = '#fff'; ctx.shadowBlur = s * 3; ctx.strokeStyle = '#fff'; ctx.lineWidth = 0.6; ctx.stroke(pieceEdge(G.flash.pi)); ctx.restore();
      }
    }
    IMG.sparks = IMG.sparks.filter(function (p) { return t - p.t0 < 0.4; });
    IMG.sparks.forEach(function (p) { var a = (t - p.t0) / 0.4, z = Math.max(1.5, s * (0.5 + 0.6 * (1 - a))); ctx.globalAlpha = 1 - a; ctx.fillStyle = '#fff6c8'; ctx.fillRect(p.x - z / 2, p.y - a * s * 1.2 - z / 2, z, z); }); ctx.globalAlpha = 1;
    drawWorkers(t);
    if (G.status === 'won') {   // parıltı süpürmesi (yalnız kedinin pikselleri üzerinde, basamaklı)
      var tmp = IMG.tmp || (IMG.tmp = mkCanvas(N, N)), g = tmp.getContext('2d'), sw = ((t - G.wonAt) * 0.9 % 1.6) * 1.6 * N - 0.3 * N;
      g.globalCompositeOperation = 'source-over'; g.clearRect(0, 0, N, N); var gr = g.createLinearGradient(sw - 0.12 * N, 0, sw + 0.12 * N, 0.3 * N); gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(0.5, 'rgba(255,255,255,.7)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
      g.fillStyle = gr; g.fillRect(0, 0, N, N); g.globalCompositeOperation = 'destination-in'; g.drawImage(IMG.sil, 0, 0); ctx.drawImage(tmp, ox, oy, W, W);
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
      if (w.state === 0 && steps > 0) {   // kısa ömürlü hafif ışık izi (kalıcı yol çizgisi yok)
        var f2 = p * steps, tr0 = Math.max(0, f2 - 2.5), i0 = Math.floor(tr0);
        ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.strokeStyle = col(w.color); ctx.globalAlpha = 0.22; ctx.lineWidth = s * 0.28; ctx.beginPath();
        ctx.moveTo(cx(w.path[i0]) + (cx(w.path[Math.min(steps, i0 + 1)]) - cx(w.path[i0])) * (tr0 - i0), cy(w.path[i0]) + (cy(w.path[Math.min(steps, i0 + 1)]) - cy(w.path[i0])) * (tr0 - i0));
        for (var k2 = i0 + 1; k2 <= Math.floor(f2); k2++) ctx.lineTo(cx(w.path[k2]), cy(w.path[k2]));
        ctx.lineTo(px, py); ctx.stroke(); ctx.restore();
      }
      if (G.lv.art) { if (w.jx === undefined) { w.jx = (Math.random() - 0.5) * s * 0.9; w.jy = (Math.random() - 0.5) * s * 0.5; } px += w.jx; py += w.jy; }   // kalabalık görünümü (yalnız çizim; rota değişmez)
      list.push({ w: w, x: px, y: py });
    });
    list.sort(function (a, b) { return a.y - b.y; });
    list.forEach(function (o) {
      var w = o.w, done = w.state === 1, hop = done ? Math.abs(Math.sin((t - w.doneAt) * 14)) * s * 0.25 : 0, x = o.x, y = o.y - hop, r = G.lv.art ? Math.max(s * 0.5, 2.4) : s * 0.3;
      ctx.fillStyle = 'rgba(0,0,0,.3)'; ctx.beginPath(); ctx.ellipse(o.x, o.y + r * 0.9, r * 0.9, r * 0.4, 0, 0, 7); ctx.fill();
      ctx.fillStyle = '#ff7a00'; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();
      ctx.fillStyle = '#f4d7b0'; ctx.beginPath(); ctx.arc(x, y - r * 0.85, r * 0.55, 0, 7); ctx.fill();
      ctx.fillStyle = '#ffd60a'; ctx.beginPath(); ctx.arc(x, y - r * 1.1, r * 0.6, Math.PI, 0); ctx.fill();
      ctx.strokeStyle = '#000'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.stroke();
      if (!done) { if (G.lv.art) { var cz = Math.max(2, s * 1.3); ctx.fillStyle = w.cargo; ctx.fillRect(x - cz / 2, y - r * 2.1 - cz, cz, cz); ctx.strokeStyle = 'rgba(40,20,10,.8)'; ctx.lineWidth = 1; ctx.strokeRect(x - cz / 2 + 0.5, y - r * 2.1 - cz + 0.5, cz - 1, cz - 1); } else box(x - s * 0.22, y - r * 2.3 - s * 0.08, s * 0.44, col(w.color), 0); }                   // taşınan kutu (parçanın kutularından biri)
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
  // YOL OKUNABİLİRLİĞİ (yalnız görsel): seçili parçanın GERÇEK worker rotası (engine.routesFor, send ile aynı) ve yerleşince
  // değişecek erişim. cut = boş kalıp girişten erişilemeyecek hücreler; detour = erişilebilir ama yolu belirgin uzayacak hücreler.
  function computeRead(pi) {
    var L = G.level, res = L.place(G.st, pi); if (!res) return null;
    var b0 = L.bfs(G.st.filled), b1 = L.bfs(res.state.filled), placed = {}, cutSet = {}, detour = [];
    res.placed.forEach(function (ti) { placed[ti] = 1; }); res.sealed.forEach(function (ti) { cutSet[ti] = 1; });
    for (var ti = 0; ti < L.n; ti++) {
      if (G.st.filled[ti] || placed[ti] || cutSet[ti]) continue;
      var c = L.targets[ti].cell, d0 = b0.dist[c], d1 = b1.dist[c];
      if (d0 >= 0 && d1 >= 0 && d1 > d0 + 1) detour.push(ti);
    }
    return { routes: L.routesFor(res), cut: res.sealed.slice(), detour: detour, stuck: res.stuck, won: res.won };
  }
  function feasibleNow() { return G.level.options(G.st); }
  function send(pi) {
    if (G.status !== 'idle') return;
    var L = G.level, res = L.place(G.st, pi);
    if (!res) { toast('Bu parça şu an yerleşemez'); return; }
    var t0 = now(), routes = L.routesFor(res), before = G.st, optsBefore = L.options(G.st).filter(Boolean).length, p = L.pieces[pi];
    G.lastPi = pi; G.history.push({ piece: pi, before: before, n: p.cells.length, col: p.col });
    G.st = res.state;
    G.pending = { sealed: res.sealed, won: res.won, stuck: res.stuck };
    G.dest = { cells: res.placed.slice() };
    // işçi takvimi (bir grup): varış sırası = yerleştirme sırası; grup birlikte yola çıkar
    var units = G.lv.art ? artClusters(res, routes) : res.placed.map(function (ti, i) { return { ti: ti, cells: [ti], path: routes[i] }; });
    var v = (G.lv.art ? 44 : 7) * cfg.speed, gap = (G.lv.art ? 0.045 : 0.08) / cfg.speed, tr = units.map(function (u) { return Math.max(1, u.path.length - 1) / v; }), T0 = 0.05;
    for (var i = 0; i < units.length; i++) T0 = Math.max(T0, tr[i] - i * gap + 0.05);
    G.workers = units.map(function (u, i) { return { ti: u.ti, cells: u.cells, path: u.path, depart: t0 + T0 + i * gap - tr[i], arrive: t0 + T0 + i * gap, travel: tr[i], color: p.col, state: 0, doneAt: 0, cargo: G.lv.art ? IMG.colors[u.ti] : null }; });
    G.waveEnd = t0 + T0 + (units.length - 1) * gap + 0.45 + (G.lv.art ? 0.25 : 0);
    var a = G.cur;
    a.tokens.push(p.id);
    a.moves.push({ i: a.moves.length + 1, token: p.id, color: p.ch, size: p.cells.length, shape: JSON.stringify(p.cells), t_ms: Date.now() - a.t0, decide_ms: Math.round((t0 - G.readyAt) * 1000),
                   preview_switches: G.switches, previewed: G.previews.slice(), placed: res.placed.length, pos: [res.pos.r, res.pos.c], options_before: optsBefore,
                   available_before: L.remainingPieces(before), filled_after: L.filledCount(res.state.filled), sealed_after: res.sealed.length > 0, stuck_after: res.stuck, preview_shown: cfg.hint >= 1, path_mode: cfg.path, pv_cut: G.read ? G.read.cut.length : null, pv_detour: G.read ? G.read.detour.length : null });
    G.selected = -1; G.opt = null; G.read = null; G.previewSealed = []; G.previewStuck = false; G.status = 'anim'; saveLog(); refresh();
  }
  function finishWave() {
    if (G.lv.art) { var pi0 = G.lastPi; G.revealQ = []; IMG.bctx.clearRect(0, 0, IMG.N, IMG.N); for (var q = 0; q < G.level.n; q++) if (G.st.filled[q]) imgReveal(q); }
    if (G.lv.art && G.dest) G.flash = { t0: now(), pi: G.lastPi };
    G.workers = []; G.dest = null; G.readyAt = now(); G.switches = 0; G.previews = [];
    var p = G.pending; G.pending = null;
    if (p.won) { G.status = 'won'; G.wonAt = now(); G.cur.outcome = 'won'; G.cur.t1 = Date.now();
      setMsg('Resim tamamlandı! ' + G.history.length + ' parça gönderdin. ' + (cfg.test ? '' : 'Yeniden başlatabilir ya da başka seviye seçebilirsin.'), 'good'); }
    else if (p.sealed.length) { G.status = 'sealed'; G.sealedShown = p.sealed; G.sealedCv = null; G.cur.sealed_at_move = G.cur.moves.length; G.cur.outcome = 'sealed'; G.cur.t1 = Date.now();
      setMsg('Kilitlendi: ' + (G.lv.art ? 'kedinin bir bölümüne' : p.sealed.length + ' boş hücreye') + ' artık girişten yol yok (turuncu). Bu seviye bu hâliyle tamamlanamaz.' + (G.undoLeft > 0 ? ' Geri alabilirsin.' : ''), 'bad'); }
    else if (p.stuck) { G.status = 'stuck'; G.cur.stuck_at_move = G.cur.moves.length; G.cur.outcome = 'stuck'; G.cur.t1 = Date.now();
      setMsg('Sıkıştı: kalan parçalardan hiçbiri boş hücrelere yerleşemiyor. Bu seviye bu hâliyle tamamlanamaz.' + (G.undoLeft > 0 ? ' Geri alabilirsin.' : ''), 'bad'); }
    else { G.status = 'idle'; setMsg('Sıradaki parça? ' + (cfg.hint ? 'Bir parçaya bir kez bas: nereye gideceğini göster; aynı parçaya/Gönder\'e tekrar bas: gönder.' : ''), 'info'); }
    saveLog(); refresh();
  }
  function select(pi) {
    if (G.status !== 'idle') return;
    var L = G.level, p = L.pieces[pi]; if (!p || G.st.used[pi]) return;
    var o = L.chooseTarget(G.st.filled, pi); if (!o) { toast('Bu parça şu an hiçbir yere yerleşemez'); return; }
    if (cfg.hint === 0) { send(pi); return; }
    if (G.selected === pi) { send(pi); return; }
    G.selected = pi; G.opt = o; G.read = computeRead(pi); G.switches++; G.previews.push(p.id);
    G.previewSealed = []; G.previewStuck = false;
    var text = G.lv.art ? 'Seçili bölge kedinin üzerinde parlıyor; ışık noktaları işçilerin gerçek rotası. Göndermek için aynı karta ya da Gönder\'e bas; başka karta bakarak karşılaştırabilirsin.' : 'Önizleme — ' + G.palette.names[p.col] + ' parça, ' + p.cells.length + ' kutu. Hedef hücreler tahtada yanıp sönüyor. Göndermek için aynı parçaya ya da Gönder\'e bas; ya da başka parçanın nereye gideceğine bak.', cls = 'info';
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
    var h = G.history.pop(); G.st = h.before; G.visual = new Uint8Array(h.before.filled); G.status = 'idle'; G.undoLeft--; G.sealedShown = []; G.opt = null; G.read = null; G.selected = -1; G.previewSealed = []; if (G.lv.art) imgSync(G.st.filled);
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
  // EL: her zaman en fazla 3 kart — renk başına 1 slot. Slot, o rengin level verisindeki SIRADAKİ parçasını gösterir; gönderilen kartın yerine yalnız o slot yenilenir.
  function handPieces(st) {
    if (G.handQ) { var o2 = []; G.handQ.forEach(function (q) { for (var i = 0; i < q.length; i++) if (!st.used[q[i]]) { o2.push(q[i]); break; } }); return o2; }
    var out = []; G.level.letters.forEach(function (x, ci) { var pi = nextOfColour(ci, st); if (pi >= 0) out.push(pi); }); return out; }
  function buildHand(seen, idle) {
    var L = G.level, hand = $('hand'), opts = L.options(seen), hp = handPieces(seen);
    var key = G.lv.id + '#' + G.attemptNo + '|' + hp.map(function (pi) { return pi + (opts[pi] ? 'f' : 'x'); }).join(',') + '|' + G.selected + '|' + (idle ? 1 : 0);
    if (key === G.handSig) return; G.handSig = key;
    hand.innerHTML = '';
    hp.forEach(function (pi, slot) {
      var p = L.pieces[pi], b = document.createElement('button'), cv = document.createElement('canvas'), ok = !!opts[pi], n = p.cells.length, c0 = col(p.col);
      if (G.lv.art) {
        b.className = 'pcard art' + (G.selected === pi ? ' sel' : '') + (ok ? '' : ' nofit'); b.id = 'slot' + slot; b.dataset.piece = p.id; b.dataset.i = pi; b.disabled = !idle || !ok; b.title = 'Parça ' + (slot + 1);
        var bx = document.createElement('div'); bx.className = 'pshape'; drawSpriteTo(cv, pi, 84); bx.appendChild(cv); b.appendChild(bx);
        var sn = document.createElement('span'); sn.className = 'pn'; sn.textContent = String(slot + 1); b.appendChild(sn);
        b.addEventListener('click', function () { select(pi); }); hand.appendChild(b); return;
      }
      b.className = 'pcard' + (G.selected === pi ? ' sel' : '') + (ok ? '' : ' nofit'); b.id = 'slot' + slot; b.dataset.piece = p.id; b.dataset.i = pi;
      b.style.background = mix(c0, '#ffffff', 0.45); b.style.borderColor = c0; b.disabled = !idle || !ok; b.title = G.palette.names[p.col] + ' · ' + n + ' hücre' + (ok ? '' : ' · şu an yerleşemez');
      var box2 = document.createElement('div'); box2.className = 'pshape'; drawPiece(cv, p, 22, c0); box2.appendChild(cv); b.appendChild(box2);
      var sm = document.createElement('span'); sm.className = 'pn'; sm.textContent = (slot + 1) + ' · ' + G.palette.names[p.col] + ' · ' + n + ' hücre' + (ok ? '' : ' (yerleşemez)'); b.appendChild(sm);
      b.addEventListener('click', function () { select(pi); }); hand.appendChild(b);
    });
    if (!hp.length) hand.innerHTML = '<span class="meta">parça kalmadı</span>';
  }
  function refresh() {
    var L = G.level; if (!L) return;
    var seen = G.status === 'anim' ? { filled: G.visual, used: G.st.used } : G.st;   // animasyon sürerken oyuncunun GÖRDÜĞÜ durum
    var n = L.n, done = L.filledCount(seen.filled), rem = L.remaining(seen.filled), idle = G.status === 'idle', opts = L.options(seen);
    $('lvlTitle').textContent = cfg.test ? ('Seviye ' + (G.testIdx + 1) + ' / ' + order.length) : G.lv.name;
    $('lvlMeta').textContent = G.lv.art ? 'Resmi bölge bölge inşa et · ' + L.P + ' parça' + (cfg.test ? '' : ' · ' + G.lv.id) : n + ' hücre · ' + L.K + ' renk · ' + L.P + ' parça · giriş hücresi: ' + L.entrances.length + (cfg.test ? '' : ' · ' + G.lv.id);
    $('progTxt').textContent = G.lv.art ? 'Resim: %' + Math.round(100 * done / n) + ' tamamlandı · gönderilen parça: ' + G.history.length + ' / ' + L.P : 'Yerleşen: ' + done + ' / ' + n + ' kutu (' + Math.round(100 * done / n) + '%) · gönderilen parça: ' + G.history.length + ' / ' + L.P;
    $('progBar').style.width = (100 * done / n) + '%';
    $('stock').innerHTML = '';   // renk stoğu karar alanında gösterilmez
    var hist = ''; G.history.forEach(function (h) { hist += '<i style="background:' + col(h.col) + '" title="' + h.n + ' hücre">' + (G.lv.art ? '' : h.n) + '</i>'; });
    $('history').innerHTML = hist || '<span class="meta">henüz yok</span>';
    buildHand(seen, idle);
    var sp = $('selShape'), si = $('selInfo');
    if (G.selected >= 0 && G.opt) {
      var p = L.pieces[G.selected]; sp.style.display = '';
      if (G.lv.art) {
        drawSpriteTo(sp, G.selected, 80); si.textContent = 'Seçili bölge: kedinin %' + Math.round(100 * G.opt.cells.length / n) + '\'i';
        if (G.read && (cfg.path === 'B' || cfg.path === 'C')) si.textContent += ' · ' + (G.read.won ? 'resmi tamamlar' : G.read.cut.length ? 'dikkat: kedinin %' + Math.round(100 * G.read.cut.length / n) + '\'ine giden yol kapanır' : G.read.detour.length ? 'bazı yolları uzatır' : 'yolları etkilemez');
      } else {
        drawPiece(sp, p, 22, col(p.col));
        si.textContent = 'Seçili: ' + G.palette.names[p.col] + ' · ' + p.cells.length + ' hücre → tahtada ' + G.opt.cells.length + ' hücre işaretli';
        if (G.read && (cfg.path === 'B' || cfg.path === 'C')) si.textContent += ' · ' + (G.read.won ? 'resmi tamamlar' : G.read.cut.length ? G.read.cut.length + ' hücrenin yolu kapanır' : G.read.detour.length ? G.read.detour.length + ' hücrenin yolu uzar' : 'yolları etkilemez');
      }
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
  var PATH_NAMES = { '0': 'Kapalı', A: 'A · Worker izi', B: 'B · Kritik alan', C: 'C · İz + kritik alan' };
  function setPathMode(m) {
    cfg.path = m; if ($('pathSel')) $('pathSel').value = m;
    Array.prototype.forEach.call(document.querySelectorAll('#pathPills button'), function (b) { b.classList.toggle('on', b.dataset.m === m); });
    $('pathTag').textContent = 'Yol görünümü: ' + PATH_NAMES[m]; if (G.level) refresh();
  }
  function fillSelectors() {
    setPathMode(cfg.path);
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
      G.workers.forEach(function (w) { if (w.state === 0 && t >= w.arrive) { w.state = 1; w.doneAt = t; if (G.lv.art) { (w.cells || [w.ti]).forEach(function (c, k) { G.revealQ.push({ ti: c, at: t + k * 0.02 }); }); } else { G.visual[w.ti] = 1; G.pops[w.ti] = t; } } });
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
  $('pathSel').addEventListener('change', function () { setPathMode(this.value); });
  Array.prototype.forEach.call(document.querySelectorAll('#pathPills button'), function (b) { b.addEventListener('click', function () { setPathMode(b.dataset.m); }); });
  $('ghostChk').addEventListener('change', function () { cfg.ghost = this.checked; });
  $('speedSel').addEventListener('change', function () { cfg.speed = parseFloat(this.value); });
  $('undoSel').addEventListener('change', function () { cfg.undo = parseInt(this.value, 10); newAttempt('restart'); });
  window.addEventListener('resize', layout);
  window.addEventListener('keydown', function (e) {
    if (e.target && /select|input|textarea/i.test(e.target.tagName)) return;
    if (e.key >= '0' && e.key <= '9') { var hp = handPieces(G.st), pi = hp[parseInt(e.key, 10) - 1]; if (pi != null) select(pi); }
    else if (e.key === 'Enter' || e.key === ' ') { if (G.selected >= 0) { e.preventDefault(); send(G.selected); } }
    else if (e.key === 'z' || e.key === 'Z') undo();
    else if (e.key === 'r' || e.key === 'R') newAttempt('restart');
  });
  if (window.ResizeObserver) new ResizeObserver(layout).observe($('boardWrap'));

  // otomasyon / araştırma API'si (tarayıcı testleri ve kayıt için). Parça = indeks ya da id ('P3')
  function pidx(x) { if (typeof x === 'number') return x; if (handPieces(G.st).map(function (q) { return G.level.pieces[q].id; }).indexOf(x) < 0 && G.level.letters.indexOf(x) < 0) return -1; var ci = G.level.letters.indexOf(x); if (ci >= 0) return nextOfColour(ci); var k = -1; G.level.pieces.forEach(function (p) { if (p.id === x) k = p.i; }); return k; }
  window.CBGAME = {
    send: function (x) { var i = pidx(x); if (cfg.hint === 0) send(i); else { G.selected = -1; select(i); select(i); } },
    select: function (x) { select(pidx(x)); },
    state: function () { return { status: G.status, filled: G.level.filledCount(G.st.filled), n: G.level.n, waves: G.history.length, level: G.lv.id, sealed: G.sealedShown.length, selected: G.selected,
                                  left: G.level.remainingPieces(G.st), undoLeft: G.undoLeft, opt: G.opt ? G.opt.cells.length : 0 }; },
    read: function () { return G.read ? { cut: G.read.cut.slice(), detour: G.read.detour.slice(), stuck: G.read.stuck, won: G.read.won, routes: G.read.routes.map(function (r) { return r.slice(); }) } : null; },
    workerPaths: function () { return G.workers.map(function (w) { return w.path.slice(); }); },
    setPath: setPathMode, pathMode: function () { return cfg.path; },
    previewCells: function () { return G.opt ? G.opt.cells.slice().sort(function (a, b) { return a - b; }) : null; },
    destCells: function () { return G.dest ? G.dest.cells.slice().sort(function (a, b) { return a - b; }) : null; },
    restart: function () { newAttempt('restart'); }, loadLevel: loadLevel, downloadLog: downloadLog, getLog: function () { return LOG; }, runParity: runParity,
    setCfg: function (o) { for (var k in o) cfg[k] = o[k]; fillSelectors(); newAttempt('restart'); }, undo: undo, nextLevel: nextLevel
  };

  // başlat
  var start = cfg.test ? order[0] : (qs.get('level') && byId[qs.get('level')] ? qs.get('level') : (byId.CAT96 ? 'CAT96' : LEVELS[0].id));
  G.testIdx = 0; loadLevel(start); requestAnimationFrame(frame);
})();

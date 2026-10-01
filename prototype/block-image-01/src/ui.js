/* block-image-01 — ARAYÜZ. Kurallar yalnız engine.js'te; burada gösterim, giriş ve animasyon vardır.
 * Döngü: GÖR (3 kart) → SEÇ (kart: hedef bloğu resimde belirir) → GÖNDER → işçiler taşır → blok yerine oturur → resim büyür → o slota yeni blok gelir.
 * Animasyon kozmetiktir: mantıksal durum tıklamada ANINDA değişir; işçilerin varış sırası = yerleşme sırası (en derinden başla). */
(function () {
  'use strict';
  var LV = window.BI_LEVEL, VEC = window.BI_VECTORS || [], BI = window.BI, qs = new URLSearchParams(location.search);
  var $ = function (id) { return document.getElementById(id); };
  var L = new BI.Level(LV.grid, LV.pieces, LV.hand), CELLCOL = [];   // CELLCOL (kedinin görünen rengi) aşağıda piece.color'dan kurulur; level verisindeki eski kedi renk listesi render kaynağı DEĞİLDİR
  // PARÇA RENGİ: level tasarımcısının verdiği piece.color (turuncu/mavi/kırmızı/yeşil). Hedef resimden TÜRETİLMEZ, slota bağlı DEĞİLDİR, mekanik DEĞİLDİR (yalnız görsel kimlik).
  var COLHEX = { orange: '#ff9f1c', blue: '#3b82f6', red: '#ef4444', green: '#2fb67c', dark: '#2e2a35' };
  var PCOL = LV.pieces.map(function (p) { if (!COLHEX[p.color]) throw new Error('piece.color eksik: ' + p.id); return COLHEX[p.color]; });
  var OWNER = new Int32Array(L.n); L.pieces.forEach(function (p) { p.cells.forEach(function (ti) { OWNER[ti] = p.i; }); });
  for (var ci = 0; ci < L.n; ci++) CELLCOL[ci] = PCOL[OWNER[ci]];   // targetColor[cell] = owningPiece.color  (kedi = 25 parçanın birleşmiş hâli)
  // RESİM RENGİ (yalnız art verisi olan seviyelerde, ör. L01): parçanın her hücresinin gerçek piksel-art rengi (piece.art). Kimlik rengi (piece.color) kartın/işçinin/önizleme çerçevesinin rengi olarak kalır.
  var HAS_ART = !!(LV.pieces[0] && LV.pieces[0].art), ARTCOL = [];
  if (HAS_ART) L.pieces.forEach(function (p, i) { p.cells.forEach(function (ti, k) { ARTCOL[ti] = LV.pieces[i].art[k]; }); });
  var cfg = { colors: HAS_ART && qs.get('colors') !== 'piece' ? 'art' : 'piece', speed: Math.max(0.5, Math.min(200, parseFloat(qs.get('speed')) || 1)), path: ['0', 'A', 'B'].indexOf((qs.get('path') || '').toUpperCase()) >= 0 ? qs.get('path').toUpperCase() : 'A' };
  var canvas = $('board'), ctx = canvas.getContext('2d');
  var G = { st: null, visual: null, status: 'idle', selected: -1, read: null, workers: [], pops: {}, history: [], waveEnd: 0, pending: null, wonAt: 0, sealedShown: [], sealedPath: null,
            s: 10, ox: 0, oy: 0, dpr: 1, cw: 0, ch: 0, handSig: '', flash: null, sparks: [] };
  function now() { return performance.now() / 1000; }
  function cellCol(ti) { return cfg.colors === 'art' ? ARTCOL[ti] : CELLCOL[ti]; }

  // ---------------------------------------------------------------- renk
  function rgb(h) { var n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
  function mix(a, b, t) { var x = rgb(a), y = rgb(b); return 'rgb(' + Math.round(x[0] + (y[0] - x[0]) * t) + ',' + Math.round(x[1] + (y[1] - x[1]) * t) + ',' + Math.round(x[2] + (y[2] - x[2]) * t) + ')'; }
  function setMsg(t, cls) { var m = $('msg'); m.textContent = t; m.className = cls || ''; }

  // ---------------------------------------------------------------- oyun akışı
  function newGame() {
    G.st = L.newState(); G.visual = new Uint8Array(G.st.filled); G.status = 'idle'; G.selected = -1; G.read = null; G.workers = []; G.pops = {}; G.history = []; G.pending = null; G.sealedShown = []; G.sealedPath = null; G.handSig = ''; G.flash = null; G.sparks = []; G.wonAt = 0;
    setMsg('Üç bloktan birine bas: resimde nereye oturacağı görünür. Hangisini ŞİMDİ göndermelisin?'); refresh();
  }
  function computeRead(slot) {
    var res = L.place(G.st, slot); if (!res) return null;
    return { slot: slot, cells: res.cells.slice(), routes: res.steps.map(function (s) { return s.route; }), cut: res.sealed.slice(), won: res.won, stuck: res.stuck, piece: res.piece };
  }
  function select(slot) {
    if (G.status !== 'idle') return; var cards = L.cards(G.st); if (cards[slot] === null || cards[slot] === undefined) return;
    var rd = computeRead(slot); if (!rd) { setMsg('Bu blok şu an yerleşemez: hedefine giden yol kapalı.', 'bad'); return; }
    if (G.selected === slot) { send(slot); return; }
    G.selected = slot; G.read = rd; setMsg('Seçili bloğun hedefi resimde parlıyor; ışık noktaları işçilerin rotası. Göndermek için aynı karta ya da Gönder\'e bas.'); refresh();
  }
  function send(slot) {
    if (G.status !== 'idle') return; var res = L.place(G.st, slot); if (!res) { setMsg('Bu blok şu an yerleşemez.', 'bad'); return; }
    var t0 = now(), before = G.st; G.history.push({ slot: slot, before: before, piece: res.piece }); G.st = res.state; G.pending = { sealed: res.sealed, won: res.won, stuck: res.stuck }; G.dest = res.cells.slice();
    var steps = res.steps, v = (HAS_ART ? 64 : 48) * cfg.speed, gap = Math.min(0.03, 0.6 / Math.max(1, steps.length - 1)) / cfg.speed, tr = steps.map(function (s) { return Math.max(1, s.route.length - 1) / v; }), T0 = 0.05, i;
    for (i = 0; i < steps.length; i++) T0 = Math.max(T0, tr[i] - i * gap + 0.05);
    G.workers = steps.map(function (s, k) { return { ti: s.ti, path: s.route, depart: t0 + T0 + k * gap - tr[k], arrive: t0 + T0 + k * gap, travel: tr[k], state: 0, doneAt: 0, cargo: PCOL[res.piece] }; });
    G.waveEnd = t0 + T0 + (steps.length - 1) * gap + 0.22 / Math.sqrt(cfg.speed);
    G.selected = -1; G.read = null; G.status = 'anim'; setMsg(''); refresh();
  }
  function finishWave() {
    G.visual = new Uint8Array(G.st.filled); G.workers = []; var p = G.pending; G.pending = null; G.flash = { t0: now(), cells: G.dest.slice() };
    if (p.won) { G.status = 'won'; G.wonAt = now(); setMsg('Resim tamamlandı! ' + G.history.length + ' blok gönderdin.', 'good'); }
    else if (p.sealed.length) { G.status = 'sealed'; G.sealedShown = p.sealed; G.sealedPath = null; setMsg('Kilitlendi: resmin bir bölümüne artık girişten yol yok (turuncu). Yeniden başlat.', 'bad'); }
    else if (p.stuck) { G.status = 'stuck'; setMsg('Sıkıştı: elindeki bloklardan hiçbirine yol yok. Yeniden başlat.', 'bad'); }
    else {
      G.status = 'idle'; var dg = L.diagnose(G.st);
      if (dg.deadlock) setMsg('Çıkmaz: elindeki hiçbir blok oyunu sürdüremiyor (kartlar duruyor, hepsi resmi kapatıyor). Yeniden başlat.', 'bad');
      else setMsg('Sıradaki blok? Bir karta bas: hedefi görünür.');
    }
    if (window.console && console.debug) console.debug('[el]', JSON.stringify(handDiag()));
    refresh();
  }
  function undoNone() {}

  // ---------------------------------------------------------------- yerleşim / çizim
  function layout() {
    var wrap = $('boardWrap'); G.cw = wrap.clientWidth; G.ch = wrap.clientHeight; G.dpr = window.devicePixelRatio || 1; var d = G.dpr;
    canvas.width = Math.round(G.cw * d); canvas.height = Math.round(G.ch * d);
    var ps = Math.max(4, Math.floor(Math.min(G.cw * d / (L.w + 3), (G.ch - 26) * d / (L.h + 3)))); G.s = ps / d;
    G.ox = Math.round((G.cw * d - L.w * ps) / 2) / d; G.oy = Math.round(((G.ch - 22) * d - L.h * ps) / 2) / d;
  }
  function cx(cell) { return G.ox + (cell % L.w + 0.5) * G.s; } function cy(cell) { return G.oy + (Math.floor(cell / L.w) + 0.5) * G.s; }
  function rrect(x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
  function rrg(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
  /* FİZİKSEL KÜÇÜK BLOK (resim modu): her hedef hücre ayrı bir kutu — aralık (gap), alt/yan gölge, üst yüz + üst ışık, hafif bevel; rengi hedef hücrenin gerçek kedi rengi.
   * Mantıksal parça 19 tane; görsel blok 460 tane (render birimi). Bloklar birbirine yapışıp düz yüzey oluşturmaz. */
  function artBlock(g, x, y, s, color, pop, drop) {
    var d = G.dpr || 1, gap = Math.max(1, Math.round(s * d * 0.07)) / d, k = 1 + (pop || 0), sz = (s - gap) * k, px = x + (s - sz) / 2, py = y + (s - sz) / 2 - (drop || 0);
    var hl = Math.max(1 / d, Math.round(sz * d * 0.13) / d), sh = Math.max(1 / d, Math.round(sz * d * 0.17) / d), r = sz >= 11 ? sz * 0.13 : 0, dark = mix(color, '#000000', 0.28), light = mix(color, '#ffffff', 0.34);
    if (r) { rrg(g, px, py, sz, sz, r); g.fillStyle = dark; g.fill(); rrg(g, px, py, sz, sz - sh, r); g.fillStyle = color; g.fill(); g.fillStyle = light; g.fillRect(px + r * 0.7, py + hl * 0.35, sz - r * 1.4, hl); }
    else { g.fillStyle = dark; g.fillRect(px, py, sz, sz); g.fillStyle = color; g.fillRect(px, py, sz, sz - sh); g.fillStyle = light; g.fillRect(px, py, sz, hl); }
    g.fillStyle = 'rgba(255,255,255,.13)'; g.fillRect(px, py + hl, Math.max(1 / d, hl * 0.7), sz - sh - hl);    // sol kenar ışığı
    g.fillStyle = 'rgba(0,0,0,.10)'; g.fillRect(px + sz - Math.max(1 / d, hl * 0.7), py + hl, Math.max(1 / d, hl * 0.7), sz - sh - hl);   // sağ kenar gölgesi
  }
  function block(g, x, y, s, color, pop, drop) {
    if (cfg.colors === 'art') { artBlock(g, x, y, s, color, pop, drop); return; }   // küçük renkli blok: ince aralık, üstte ışık, altta gölge
    var gap = 0, k = 1 + (pop || 0), sz = (s - gap) * k, px = x + (s - sz) / 2, py = y + (s - sz) / 2;
    g.fillStyle = color; g.fillRect(px, py, sz, sz);
    g.fillStyle = 'rgba(255,255,255,.16)'; g.fillRect(px, py, sz, Math.max(1, sz * 0.12)); g.fillStyle = 'rgba(0,0,0,.10)'; g.fillRect(px, py + sz - Math.max(1, sz * 0.10), sz, Math.max(1, sz * 0.10));
  }
  function edgePath(tis) {
    var set = {}, p = new Path2D(); tis.forEach(function (t) { set[t] = 1; });
    tis.forEach(function (ti) {
      var tg = L.targets[ti], x = tg.c, y = tg.r;
      [[-1, 0, x, y, x + 1, y], [1, 0, x, y + 1, x + 1, y + 1], [0, -1, x, y, x, y + 1], [0, 1, x + 1, y, x + 1, y + 1]].forEach(function (d) {
        var rr = tg.r + d[0], cc = tg.c + d[1], nt = (rr >= 0 && rr < L.h && cc >= 0 && cc < L.w) ? L.tIdx[rr * L.w + cc] : -1; if (nt < 0 || !set[nt]) { p.moveTo(d[2], d[3]); p.lineTo(d[4], d[5]); }
      });
    });
    return p;
  }
  function drawHole() { var e = L.entrances[0], ex = G.ox + (e % L.w + 0.5) * G.s, ey = G.oy + L.h * G.s + G.s * 0.15; ctx.fillStyle = '#9b7a55'; ctx.beginPath(); ctx.ellipse(ex, ey, G.s * 2.6, G.s * 1.0, 0, 0, 7); ctx.fill(); ctx.fillStyle = '#4a3322'; ctx.beginPath(); ctx.ellipse(ex, ey + G.s * 0.08, G.s * 2.0, G.s * 0.72, 0, 0, 7); ctx.fill(); }
  function drawTrail(t) {
    var s = G.s, routes = G.read.routes, speed = 38, maxLen = 0, seen = {}; routes.forEach(function (r) { maxLen = Math.max(maxLen, r.length - 1); });
    var pcol = PCOL[G.read.piece], cycle = maxLen / speed + 0.7, tt = t % cycle, rad = Math.max(2.4, s * 0.2); ctx.save();
    routes.forEach(function (r) { ctx.fillStyle = 'rgba(120,80,40,.25)'; for (var i = 1; i < r.length - 1; i += 2) { if (seen[r[i]]) continue; seen[r[i]] = 1; ctx.beginPath(); ctx.arc(cx(r[i]), cy(r[i]), Math.max(1.3, s * 0.07), 0, 7); ctx.fill(); } });
    routes.forEach(function (r) {
      var steps = r.length - 1; if (steps <= 0) return; var f = tt * speed; if (f > steps + 0.5) return; var fade = f > steps ? Math.max(0, 1 - (f - steps) / 0.5) : 1;
      for (var k = 0; k < 6; k++) {
        var ff = f - k * 0.7; if (ff < 0 || ff > steps) continue; var i = Math.min(steps - 1, Math.floor(ff)), u = ff - i, px = cx(r[i]) + (cx(r[i + 1]) - cx(r[i])) * u, py = cy(r[i]) + (cy(r[i + 1]) - cy(r[i])) * u;
        ctx.globalAlpha = (0.95 - k * 0.14) * fade; ctx.shadowColor = pcol; ctx.shadowBlur = k === 0 ? s * 0.8 : 0; ctx.fillStyle = k === 0 ? '#fff' : pcol; ctx.beginPath(); ctx.arc(px, py, rad * (1 - k * 0.09), 0, 7); ctx.fill();
        if (k === 0) { ctx.shadowBlur = 0; ctx.strokeStyle = pcol; ctx.lineWidth = 1.5; ctx.stroke(); }
      }
    });
    ctx.restore();
  }
  function drawWorkers(t) {
    var s = G.s, list = [];
    G.workers.forEach(function (w) {
      if (t < w.depart) return; var p = Math.min(1, (t - w.depart) / w.travel), steps = w.path.length - 1, px, py;
      if (steps <= 0) { px = cx(w.path[0]); py = cy(w.path[0]); } else { var f = p * steps, i = Math.min(steps - 1, Math.floor(f)), u = f - i; px = cx(w.path[i]) + (cx(w.path[i + 1]) - cx(w.path[i])) * u; py = cy(w.path[i]) + (cy(w.path[i + 1]) - cy(w.path[i])) * u; }
      list.push({ w: w, x: px, y: py });
    });
    list.sort(function (a, b) { return a.y - b.y; });
    list.forEach(function (o) {
      var w = o.w, done = w.state === 1, hop = done ? Math.abs(Math.sin((t - w.doneAt) * 14)) * s * 0.3 : 0, x = o.x, y = o.y - hop, r = Math.max(s * 0.38, 4);
      ctx.fillStyle = 'rgba(0,0,0,.18)'; ctx.beginPath(); ctx.ellipse(o.x, o.y + r * 0.9, r * 0.9, r * 0.4, 0, 0, 7); ctx.fill();
      ctx.fillStyle = '#ff7a00'; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); ctx.fillStyle = '#f4d7b0'; ctx.beginPath(); ctx.arc(x, y - r * 0.85, r * 0.55, 0, 7); ctx.fill();
      ctx.fillStyle = '#ffd60a'; ctx.beginPath(); ctx.arc(x, y - r * 1.1, r * 0.6, Math.PI, 0); ctx.fill(); ctx.strokeStyle = 'rgba(0,0,0,.6)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.stroke();
      if (!done) { if (cfg.colors === 'art') { var cb = Math.max(s * 0.95, 7); artBlock(ctx, x - cb / 2, y - r * 2.2 - cb * 0.7, cb, ARTCOL[w.ti], 0, 0); } else { var cz = Math.max(s * 0.7, 6); ctx.fillStyle = w.cargo; ctx.fillRect(x - cz / 2, y - r * 2.2 - cz * 0.6, cz, cz); } }   // taşınan blok: tek renk (piece.color)
    });
  }
  function draw() {
    var t = now(), s = G.s, w = L.w, h = L.h, ox = G.ox, oy = G.oy;
    ctx.setTransform(G.dpr, 0, 0, G.dpr, 0, 0); ctx.clearRect(0, 0, G.cw, G.ch);
    drawHole();
    var preview = {}; if (G.read && G.status === 'idle') G.read.cells.forEach(function (ti) { preview[ti] = 1; });
    var sealedSet = {}; G.sealedShown.forEach(function (ti) { sealedSet[ti] = 1; });
    for (var ti = 0; ti < L.n; ti++) {
      var tg = L.targets[ti], x = ox + tg.c * s, y = oy + tg.r * s, col = cellCol(ti);
      if (G.visual[ti]) { var age = t - (G.pops[ti] || -9); block(ctx, x, y, s, col, age < 0.22 ? 0.4 * (1 - age / 0.22) : 0, cfg.colors === 'art' && age < 0.16 ? (1 - age / 0.16) * s * 0.45 : 0); }
      else if (cfg.colors === 'art') { var gp = Math.max(1, Math.round(s * G.dpr * 0.07)) / G.dpr; ctx.fillStyle = mix(col, '#ffffff', 0.68); ctx.fillRect(x + gp / 2, y + gp / 2, s - gp, s - gp); }   // hayalet: ince aralıklı soluk küçük kareler
      else { ctx.fillStyle = mix(col, '#ffffff', 0.66); ctx.fillRect(x, y, s, s); }   // soluk hayalet resim (düz küçük bloklar)   // soluk hayalet resim (düz küçük bloklar)
    }
    var pulse = 0.5 + 0.5 * Math.sin(t * 5.2);
    if (G.read && G.status === 'idle') {   // seçili bloğun hedefi
      var rd = G.read; if (!rd.edge) rd.edge = edgePath(rd.cells);
      var pc = PCOL[rd.piece];
      rd.cells.forEach(function (ti2) { var tg2 = L.targets[ti2], gq = cfg.colors === 'art' ? Math.max(1, Math.round(s * G.dpr * 0.07)) / G.dpr : 0; ctx.fillStyle = mix(cellCol(ti2), '#ffffff', 0.5); ctx.fillRect(ox + tg2.c * s + gq / 2, oy + tg2.r * s + gq / 2, s - gq, s - gq); });   // kedinin final rengi (= parça rengi) açık tonu; üstüne glow/çerçeve
      ctx.save(); ctx.translate(ox, oy); ctx.scale(s, s); ctx.lineJoin = 'miter'; ctx.shadowColor = pc; ctx.shadowBlur = s * (1.1 + 1.1 * pulse); ctx.strokeStyle = pc; ctx.lineWidth = 0.34; ctx.stroke(rd.edge); ctx.shadowBlur = 0; ctx.strokeStyle = '#fff'; ctx.lineWidth = 0.08; ctx.stroke(rd.edge); ctx.restore();
      if (cfg.path === 'B' && rd.cut.length) {   // kritik alan (geliştirici modu): yerleşince erişilemeyecek hücreler
        ctx.save(); ctx.fillStyle = 'rgba(255,170,30,' + (0.35 + 0.3 * pulse).toFixed(2) + ')'; rd.cut.forEach(function (ti3) { var tg3 = L.targets[ti3]; ctx.fillRect(ox + tg3.c * s, oy + tg3.r * s, s, s); }); ctx.restore();
      }
      if (cfg.path === 'A') drawTrail(t);
    }
    if (G.status === 'sealed' && G.sealedShown.length) { ctx.save(); ctx.fillStyle = 'rgba(255,140,30,' + (0.35 + 0.25 * Math.sin(t * 5)).toFixed(2) + ')'; G.sealedShown.forEach(function (ti4) { var tg4 = L.targets[ti4]; ctx.fillRect(ox + tg4.c * s, oy + tg4.r * s, s, s); }); ctx.restore(); }
    if (G.flash) { var age2 = t - G.flash.t0; if (age2 > 0.7) G.flash = null; else { ctx.save(); ctx.fillStyle = 'rgba(255,255,255,' + (0.6 * (1 - age2 / 0.7)).toFixed(2) + ')'; G.flash.cells.forEach(function (ti5) { var tg5 = L.targets[ti5]; ctx.fillRect(ox + tg5.c * s, oy + tg5.r * s, s, s); }); ctx.restore(); } }
    G.sparks = G.sparks.filter(function (p) { return t - p.t0 < 0.4; });
    G.sparks.forEach(function (p) { var a = (t - p.t0) / 0.4, z = Math.max(2, s * (0.35 + 0.35 * (1 - a))); ctx.globalAlpha = 1 - a; ctx.fillStyle = '#fff3b0'; ctx.fillRect(p.x - z / 2, p.y - a * s * 1.1 - z / 2, z, z); }); ctx.globalAlpha = 1;
    drawWorkers(t);
    if (G.status === 'won') {   // parıltı süpürmesi
      var sweep = ((t - G.wonAt) * 16) % (w + h + 8) - 4; ctx.save(); ctx.fillStyle = 'rgba(255,255,255,.55)';
      for (var tj = 0; tj < L.n; tj++) { var tq = L.targets[tj]; if (Math.abs(tq.r + tq.c - sweep) < 1.7) ctx.fillRect(ox + tq.c * s, oy + tq.r * s, s, s); } ctx.restore();
    }
  }

  // ---------------------------------------------------------------- el / panel
  function drawPieceTo(cv, pi, cell) {
    var cs = L.pieces[pi].cells.map(function (ti) { return L.targets[ti]; }), r0 = 1e9, c0 = 1e9, r1 = -1, c1 = -1; cs.forEach(function (t) { r0 = Math.min(r0, t.r); c0 = Math.min(c0, t.c); r1 = Math.max(r1, t.r); c1 = Math.max(c1, t.c); });
    if (HAS_ART) { var small = window.innerWidth < 720; cell = Math.max(3, Math.min(cell, Math.floor((small ? 88 : 116) / (c1 - c0 + 1)), Math.floor((small ? 60 : 84) / (r1 - r0 + 1)))); }   // büyük parçalar karta sığsın
    var wpx = (c1 - c0 + 1) * cell, hpx = (r1 - r0 + 1) * cell, d = window.devicePixelRatio || 1; cv.style.width = wpx + 'px'; cv.style.height = hpx + 'px'; cv.width = Math.round(wpx * d); cv.height = Math.round(hpx * d);
    var g = cv.getContext('2d'); g.setTransform(d, 0, 0, d, 0, 0); var artMode = cfg.colors === 'art'; L.pieces[pi].cells.forEach(function (ti) { var t = L.targets[ti]; if (artMode) { artBlock(g, (t.c - c0) * cell, (t.r - r0) * cell, cell, ARTCOL[ti], 0, 0); return; } g.fillStyle = PCOL[pi]; g.fillRect((t.c - c0) * cell, (t.r - r0) * cell, cell - 1, cell - 1); });   // piece modu: TEK renk, düz · resim modu: gerçek pikseller
  }
  function buildHand(seen, idle) {
    var hand = $('hand'), cards = L.cards(seen), opts = L.options(seen);
    var key = cards.map(function (c, i) { return c === null ? '-' : c + (opts[i] ? 'f' : 'x'); }).join(',') + '|' + G.selected + '|' + (idle ? 1 : 0) + '|' + cfg.colors; if (key === G.handSig) return; G.handSig = key; hand.innerHTML = '';
    cards.forEach(function (c, slot) {
      var b = document.createElement('button'), cv = document.createElement('canvas'), pn = document.createElement('span'); pn.className = 'pn';
      if (c === null) {   // kuyruk bitti: slot görünür kalır (boş yuva), ama bekleyen parça varsa asla boş olmaz (L.audit denetler)
        b.className = 'card empty'; b.id = 'slot' + slot; b.dataset.slot = slot; b.dataset.piece = ''; b.disabled = true; b.title = 'Blok ' + (slot + 1) + ' — kuyruk bitti'; pn.textContent = String(slot + 1) + ' · kuyruk bitti'; b.appendChild(pn); hand.appendChild(b); return;
      }
      var ok = !!opts[slot];   // yerleşemeyen kart GİZLENMEZ: soluk görünür, nedeni yazılır, basınca açıklama çıkar
      b.className = 'card' + (G.selected === slot ? ' sel' : '') + (ok ? '' : ' nofit'); b.id = 'slot' + slot; b.dataset.slot = slot; b.dataset.piece = L.pieces[c].id; b.disabled = !idle; b.title = 'Blok ' + (slot + 1); b.style.borderColor = G.selected === slot ? PCOL[c] : ''; if (G.selected === slot) b.style.boxShadow = '0 0 0 3px ' + PCOL[c] + '44, 0 2px 0 ' + PCOL[c];
      drawPieceTo(cv, c, window.innerWidth < 720 ? 13 : 17); b.appendChild(cv); pn.textContent = String(slot + 1) + (ok ? '' : ' · yol kapalı'); b.appendChild(pn);
      b.addEventListener('click', function () { select(slot); }); hand.appendChild(b);
    });
    if (cards.every(function (c) { return c === null; })) { var n = document.createElement('span'); n.style.color = '#9a8a72'; n.textContent = 'blok kalmadı'; hand.appendChild(n); }
  }
  function handDiag() { var d = L.diagnose(G.st), a = L.audit(G.st); return { ptr: G.st.ptr.slice(), queues: L.hand.map(function (q) { return q.map(function (p) { return L.pieces[p].id; }); }), hand: a.ids, slots: d.slots, continuable: d.continuable, deadlock: d.deadlock, audit: a }; }
  function refresh() {
    var seen = G.status === 'anim' ? { filled: G.visual, ptr: (G.history.length && G.history[G.history.length - 1].before.ptr) || G.st.ptr } : G.st, done = L.filledCount(seen.filled), idle = G.status === 'idle';
    $('progTxt').textContent = 'Resim %' + Math.round(100 * done / L.n) + ' · ' + G.history.length + ' / ' + LV.pieces.length + ' blok';
    buildHand(seen, idle); $('sendBtn').disabled = !(idle && G.selected >= 0);
    Array.prototype.forEach.call(document.querySelectorAll('#pathPills button'), function (b) { b.classList.toggle('on', b.dataset.m === cfg.path); });
    Array.prototype.forEach.call(document.querySelectorAll('#colPills button'), function (b) { b.classList.toggle('on', b.dataset.c === cfg.colors); });
  }
  function setPath(m) { cfg.path = m; refresh(); }
  function setColors(m) { if (!HAS_ART) return; cfg.colors = m === 'piece' ? 'piece' : 'art'; G.handSig = ''; refresh(); }
  function showModal(html) { $('modalBody').innerHTML = html; $('modal').classList.add('show'); }
  function runParity() {
    var ok = 0, total = 0, bad = [], rows = '';
    VEC.forEach(function (lv) { var LL = new BI.Level(lv.grid, lv.pieces, lv.hand), lok = 0; lv.cases.forEach(function (c) { total++; if (JSON.stringify(LL.simulate(c.sequence)) === JSON.stringify(c.expected)) { ok++; lok++; } else bad.push(lv.level_id + '/' + c.name); }); rows += '<tr><td>' + lv.level_id + '</td><td>' + lv.cases.length + '</td><td>' + lok + '</td></tr>'; });
    showModal('<h3>Parity: tarayıcı motoru ↔ Python referansı (tools/ref.py)</h3><p><b>' + ok + ' / ' + total + ' vaka birebir aynı</b>' + (bad.length ? '<br>Farklı: ' + bad.join(', ') : '') + '</p><table><tr><th>Seviye</th><th>Vaka</th><th>Eşleşen</th></tr>' + rows + '</table>'); return { ok: ok, total: total, bad: bad };
  }

  // ---------------------------------------------------------------- döngü / olaylar
  function frame() {
    var t = now();
    if (G.status === 'anim') {
      G.workers.forEach(function (w) { if (w.state === 0 && t >= w.arrive) { w.state = 1; w.doneAt = t; G.visual[w.ti] = 1; G.pops[w.ti] = t; if (G.sparks.length < 80) G.sparks.push({ x: cx(L.targets[w.ti].cell), y: cy(L.targets[w.ti].cell), t0: t }); } });
      if (t >= G.waveEnd) finishWave(); else if (Math.floor(t * 8) !== frame.last) { frame.last = Math.floor(t * 8); refresh(); }
    }
    draw(); requestAnimationFrame(frame);
  }
  if (LV.title) { var bs = document.querySelector('.brand small'); if (bs) bs.textContent = LV.title; document.title = 'Blok Resim · ' + LV.title; }
  if (HAS_ART) { $('colPills').style.display = 'flex'; Array.prototype.forEach.call(document.querySelectorAll('#colPills button'), function (b) { b.addEventListener('click', function () { setColors(b.dataset.c); }); }); }
  $('restartBtn').addEventListener('click', newGame); $('sendBtn').addEventListener('click', function () { if (G.selected >= 0) send(G.selected); }); $('parityBtn').addEventListener('click', runParity);
  $('modalClose').addEventListener('click', function () { $('modal').classList.remove('show'); });
  $('speedSel').addEventListener('change', function () { cfg.speed = parseFloat(this.value); });
  Array.prototype.forEach.call(document.querySelectorAll('#pathPills button'), function (b) { b.addEventListener('click', function () { setPath(b.dataset.m); }); });
  window.addEventListener('resize', function () { layout(); G.handSig = ''; refresh(); });
  window.addEventListener('keydown', function (e) {
    if (e.target && /select|input|textarea/i.test(e.target.tagName)) return;
    if (e.key >= '1' && e.key <= '3') select(parseInt(e.key, 10) - 1); else if (e.key === 'Enter' || e.key === ' ') { if (G.selected >= 0) { e.preventDefault(); send(G.selected); } } else if (e.key === 'r' || e.key === 'R') newGame();
  });
  if (window.ResizeObserver) new ResizeObserver(function () { layout(); }).observe($('boardWrap'));

  window.CBGAME = {
    select: select, send: function (slot) { G.selected = -1; select(slot); select(slot); },
    state: function () { return { status: G.status, filled: L.filledCount(G.st.filled), n: L.n, placed: G.history.length, pieces: LV.pieces.length, selected: G.selected, left: L.remaining(G.st), cards: L.cards(G.st).map(function (c) { return c === null ? null : L.pieces[c].id; }) }; },
    previewCells: function () { return G.read ? G.read.cells.slice().sort(function (a, b) { return a - b; }) : null; },
    destCells: function () { return G.dest ? G.dest.slice().sort(function (a, b) { return a - b; }) : null; },
    read: function () { return G.read ? { cells: G.read.cells.slice(), routes: G.read.routes.map(function (r) { return r.slice(); }), cut: G.read.cut.slice() } : null; },
    workerPaths: function () { return G.workers.map(function (w) { return w.path.slice(); }); }, workerCount: function () { return G.workers.length; },
    geo: function () { return { ox: G.ox, oy: G.oy, s: G.s, dpr: G.dpr }; }, alphaAt: function (x, y) { return ctx.getImageData(x, y, 1, 1).data[3]; },
    pieceColor: function (pi) { return LV.pieces[pi].color; }, targetColors: function (pi) { return L.pieces[pi].cells.map(function (ti) { return CELLCOL[ti]; }); }, targetColor: function (ti) { return CELLCOL[ti]; }, owner: function (ti) { return OWNER[ti]; }, ghostPixel: function (ti) { return CBGAME.cellPixel(ti); },
    cardPixels: function (pi) { var cv = document.createElement('canvas'); drawPieceTo(cv, pi, 17); var d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data, set = {}; for (var i = 0; i < d.length; i += 4) if (d[i + 3] > 0) set[d[i] + ',' + d[i + 1] + ',' + d[i + 2] + ',' + d[i + 3]] = 1; return Object.keys(set); },
    cellPixel: function (ti) { var t = L.targets[ti], d = G.dpr, x = Math.round((G.ox + (t.c + 0.5) * G.s) * d), y = Math.round((G.oy + (t.r + 0.5) * G.s) * d), p = ctx.getImageData(x, y, 1, 1).data; return [p[0], p[1], p[2]]; },
    workerCargo: function () { return G.workers.map(function (w) { return w.cargo; }); }, hexToRgb: rgb,
    handDiag: handDiag, setColors: setColors, artColor: function (ti) { return ARTCOL[ti]; }, colorMode: function () { return cfg.colors; }, restart: newGame, setPath: setPath, runParity: runParity, level: L, info: LV
  };
  layout(); newGame(); requestAnimationFrame(frame);
})();

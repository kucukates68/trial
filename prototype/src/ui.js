/* Renk Yerleştirme prototipi — ARAYÜZ. Kurallar yalnız engine.js'te; burada yalnız gösterim, giriş ve kayıt vardır.
 * Animasyon kozmetiktir: dalga tıklanınca mantıksal durum ANINDA değişir (solver ile aynı, atomik); işçiler bunu gösterir.
 * İşçilerin varış sırası = yerleştirme sırası (arkadan öne), bu yüzden hiçbir işçi, dolmuş bir kutunun içinden geçmez. */
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
  var G = { lv: null, level: null, palette: null, filled: null, visual: null, status: 'idle', history: [], selected: -1, plan: null, previewSealed: [],
            workers: [], pops: {}, attemptNo: 0, undoLeft: 0, waveEnd: 0, pending: null, readyAt: 0, switches: 0, cur: null, testIdx: 0, s: 10, ox: 0, oy: 0, dpr: 1, cw: 0, ch: 0,
            sealedShown: [], wonAt: 0 };
  var LOG = { meta: { app: 'renk-yerlestirme-prototip-v0', started: new Date().toISOString(), ua: navigator.userAgent, player: cfg.player, test: cfg.test }, attempts: [] };
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
    G.lv = lv; G.level = new CB.Level(lv.grid, lv.W); G.palette = lv.palette; G.attemptNo = 0;
    buildColorButtons(); newAttempt('load'); layout(); fillSelectors();
  }
  function newAttempt(reason) {
    if (G.cur && !G.cur.outcome) { G.cur.outcome = reason === 'load' ? 'switch' : 'restart'; G.cur.t1 = Date.now(); }
    G.filled = G.level.newFilled(); G.visual = new Uint8Array(G.filled); G.status = 'idle'; G.history = []; G.selected = -1; G.plan = null;
    G.previewSealed = []; G.workers = []; G.pops = {}; G.pending = null; G.sealedShown = []; G.undoLeft = cfg.undo; G.wonAt = 0;
    G.cur = { level: G.lv.id, attempt: ++G.attemptNo, reason: reason, hint: cfg.hint, ghost: cfg.ghost, speed: cfg.speed, undo_budget: cfg.undo, W: G.lv.W,
              t0: Date.now(), tokens: [], moves: [], outcome: null };
    LOG.attempts.push(G.cur); G.readyAt = now(); G.switches = 0; saveLog();
    setMsg('Bir renge bas. İşçiler kutuları hedefte yerleştirir; yerleşen kutular yolu kapatabilir.', 'info');
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
  function box(x, y, s, color, pop) {
    var k = 1 + (pop || 0), sz = (s - 2) * k, px = x + (s - sz) / 2, py = y + (s - sz) / 2;
    ctx.fillStyle = color; ctx.fillRect(px, py, sz, sz);
    ctx.fillStyle = 'rgba(255,255,255,.28)'; ctx.fillRect(px, py, sz, Math.max(1, sz * 0.14));
    ctx.fillStyle = 'rgba(0,0,0,.22)'; ctx.fillRect(px, py + sz - Math.max(1, sz * 0.14), sz, Math.max(1, sz * 0.14));
    ctx.strokeStyle = isDark(color) ? '#000' : 'rgba(0,0,0,.45)'; ctx.lineWidth = 1; ctx.strokeRect(px + .5, py + .5, sz - 1, sz - 1);
  }
  function draw() {
    var t = now(), L = G.level; if (!L) return; var s = G.s, w = L.w;
    ctx.setTransform(G.dpr, 0, 0, G.dpr, 0, 0); ctx.clearRect(0, 0, G.cw, G.ch);
    ctx.fillStyle = '#10141d'; ctx.fillRect(0, 0, G.cw, G.ch);
    // zemin / duvar / giriş
    for (var r = 0; r < L.h; r++) for (var c = 0; c < w; c++) {
      var i = r * w + c, k = L.kind[i], x = G.ox + c * s, y = G.oy + r * s;
      if (k === 1 || k === 3) { ctx.fillStyle = FLOOR; ctx.fillRect(x, y, s, s); ctx.fillStyle = 'rgba(0,0,0,.10)'; if ((r + c) % 2) ctx.fillRect(x, y, s, s); }
      else if (k === 2) { ctx.fillStyle = '#f2c230'; ctx.fillRect(x, y, s, s); ctx.fillStyle = '#222'; for (var q = -s; q < s; q += s / 2) { ctx.beginPath(); ctx.moveTo(x + q, y + s); ctx.lineTo(x + q + s / 4, y + s); ctx.lineTo(x + q + s / 4 + s, y); ctx.lineTo(x + q + s, y); ctx.fill(); } }
    }
    drawDepot(t);
    // hedef hücreler
    var sealedSet = {}, pv = {}, pvSealed = {};
    G.sealedShown.forEach(function (ti) { sealedSet[ti] = 1; });
    if (G.plan) G.plan.forEach(function (ti, idx) { pv[ti] = idx + 1; });
    G.previewSealed.forEach(function (ti) { pvSealed[ti] = 1; });
    for (var ti = 0; ti < L.n; ti++) {
      var tg = L.targets[ti], x0 = G.ox + tg.c * s, y0 = G.oy + tg.r * s, color = col(tg.col);
      if (G.visual[ti]) { var age = t - (G.pops[ti] || -9); box(x0, y0, s, color, age < 0.28 ? 0.35 * (1 - age / 0.28) : 0); }
      else {
        ctx.fillStyle = cfg.ghost ? mix(color, GHOST_BASE, 0.45) : '#aab2c2'; ctx.fillRect(x0 + 1, y0 + 1, s - 2, s - 2);
        ctx.strokeStyle = 'rgba(0,0,0,.35)'; ctx.lineWidth = 1; ctx.strokeRect(x0 + 1.5, y0 + 1.5, s - 3, s - 3);
      }
    }
    // önizleme (ipucu ≥ 1): seçili rengin dalgasının dolduracağı hücreler, arkadan öne numaralı
    if (G.plan && G.status === 'idle') {
      var pc = col(G.selected), n = G.plan.length, showNum = s >= 13 && n <= 60;
      G.plan.forEach(function (ti2, idx) {
        var tg2 = L.targets[ti2], x1 = G.ox + tg2.c * s, y1 = G.oy + tg2.r * s;
        ctx.globalAlpha = 0.55; ctx.fillStyle = pc; ctx.fillRect(x1 + 1, y1 + 1, s - 2, s - 2); ctx.globalAlpha = 1;
        ctx.lineWidth = 2; ctx.strokeStyle = isDark(pc) ? '#fff' : '#111'; ctx.strokeRect(x1 + 1.5, y1 + 1.5, s - 3, s - 3);
        if (showNum) { ctx.fillStyle = isDark(pc) ? '#fff' : '#000'; ctx.font = '700 ' + Math.floor(s * 0.5) + 'px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(String(idx + 1), x1 + s / 2, y1 + s / 2 + 1); }
      });
    }
    // kilit uyarısı (ipucu 2): bu dalga erişilemez yapacak hücreler
    if (G.status === 'idle') G.previewSealed.forEach(function (ti3) { hatch(ti3, 'rgba(255,60,60,.95)', t, false); });
    // gerçek kilit (kayıp): erişilemeyen boş hücreler
    if (G.status === 'sealed') G.sealedShown.forEach(function (ti4) { hatch(ti4, 'rgba(255,40,40,1)', t, true); });
    // işçiler
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
      for (var k = 0; k < 3; k++) box(x - s * 0.8 + k * s * 0.55, y - s * 0.1, s * 0.5, col(k), 0);
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
      ctx.fillStyle = '#ff7a00'; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();                     // gövde (yelek)
      ctx.fillStyle = '#f4d7b0'; ctx.beginPath(); ctx.arc(x, y - r * 0.85, r * 0.55, 0, 7); ctx.fill();   // kafa
      ctx.fillStyle = '#ffd60a'; ctx.beginPath(); ctx.arc(x, y - r * 1.1, r * 0.6, Math.PI, 0); ctx.fill(); // baret
      ctx.strokeStyle = '#000'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.stroke();
      if (!done) box(x - s * 0.22, y - r * 2.3 - s * 0.08, s * 0.44, col(w.color), 0);                   // taşınan kutu
    });
  }

  // ---------------------------------------------------------------- dalga
  function send(ci) {
    if (G.status !== 'idle') return;
    var L = G.level, plan = L.plan(G.filled, ci);
    if (!plan.length) { toast('Bu renkten şu an erişilebilir kutu yok'); return; }
    var t0 = now(), routes = L.routes(G.filled, plan), before = G.filled, after = L.apply(G.filled, plan);
    G.history.push({ color: ci, before: before, n: plan.length });
    G.filled = after;
    var sealed = L.sealedCells(after), won = L.filledCount(after) === L.n;
    G.pending = { sealed: sealed, won: won };
    // işçi takvimi: varış sırası = yerleştirme sırası
    var v = 7 * cfg.speed, gap = 0.11 / cfg.speed, tr = routes.map(function (p) { return Math.max(1, p.length - 1) / v; }), T0 = 0.05;
    for (var i = 0; i < plan.length; i++) T0 = Math.max(T0, tr[i] - i * gap + 0.05);
    G.workers = plan.map(function (ti, i) { return { ti: ti, path: routes[i], depart: t0 + T0 + i * gap - tr[i], arrive: t0 + T0 + i * gap, travel: tr[i], color: ci, state: 0, doneAt: 0 }; });
    G.waveEnd = t0 + T0 + (plan.length - 1) * gap + 0.45;
    var a = G.cur, letter = L.letters[ci];
    a.tokens.push(letter);
    a.moves.push({ i: a.moves.length + 1, token: letter, t_ms: Date.now() - a.t0, decide_ms: Math.round((t0 - G.readyAt) * 1000), preview_switches: G.switches, placed: plan.length,
                   filled_after: L.filledCount(after), sealed_after: sealed.length > 0, preview_shown: cfg.hint >= 1 });
    G.selected = -1; G.plan = null; G.previewSealed = []; G.status = 'anim'; saveLog(); refresh();
  }
  function finishWave() {
    G.workers = []; G.readyAt = now(); G.switches = 0;
    var p = G.pending; G.pending = null;
    if (p.won) { G.status = 'won'; G.wonAt = now(); G.cur.outcome = 'won'; G.cur.t1 = Date.now();
      setMsg('Resim tamamlandı! ' + G.history.length + ' dalga. ' + (cfg.test ? '' : 'Yeniden başlatabilir ya da başka seviye seçebilirsin.'), 'good'); }
    else if (p.sealed.length) { G.status = 'sealed'; G.sealedShown = p.sealed; G.cur.sealed_at_move = G.cur.moves.length;
      setMsg('Kilitlendi: ' + p.sealed.length + ' boş hücreye artık girişten yol yok (kırmızı). Bu seviye bu hâliyle tamamlanamaz.' + (G.undoLeft > 0 ? ' Geri alabilirsin.' : ''), 'bad'); }
    else G.status = 'idle';
    if (G.status === 'idle') setMsg('Sıradaki renk? ' + (cfg.hint ? 'Bir renge bir kez bas: dalganın nereye gideceğini göster; aynı renge/Gönder\'e tekrar bas: gönder.' : ''), 'info');
    saveLog(); refresh();
  }
  function select(ci) {
    if (G.status !== 'idle') return;
    var L = G.level, reach = L.reachablePerColor(G.filled); if (reach[ci] <= 0) { toast('Bu renkten şu an erişilebilir kutu yok'); return; }
    if (cfg.hint === 0) { send(ci); return; }
    if (G.selected === ci) { send(ci); return; }
    G.selected = ci; G.switches++;
    G.plan = L.plan(G.filled, ci);
    G.previewSealed = cfg.hint >= 2 ? L.sealedCells(L.apply(G.filled, G.plan)) : [];
    var n = G.plan.length, name = G.palette.names[ci], text = 'Önizleme — ' + name + ': ' + n + ' kutu, arkadan öne (1 = en uzak). Göndermek için aynı renge ya da Gönder\'e bas.';
    if (cfg.hint >= 2) text += G.previewSealed.length ? ' ⚠ Bu dalga ' + G.previewSealed.length + ' boş hücreyi erişilemez yapar.' : ' Bu dalga hiçbir hücreyi hemen kapatmaz.';
    setMsg(text, cfg.hint >= 2 && G.previewSealed.length ? 'bad' : 'info'); refresh();
  }
  function undo() {
    if (G.undoLeft <= 0 || !G.history.length || G.status === 'anim' || G.status === 'won') return;
    var h = G.history.pop(); G.filled = h.before; G.visual = new Uint8Array(h.before); G.status = 'idle'; G.undoLeft--; G.sealedShown = []; G.plan = null; G.selected = -1; G.previewSealed = [];
    G.cur.tokens.push('U'); G.cur.moves.push({ i: G.cur.moves.length + 1, token: 'U', t_ms: Date.now() - G.cur.t0 }); G.readyAt = now(); G.switches = 0;
    setMsg('Son dalga geri alındı. Kalan geri alma: ' + G.undoLeft, 'info'); saveLog(); refresh();
  }
  function abandon() { if (G.cur && !G.cur.outcome) { G.cur.outcome = 'abandon'; G.cur.t1 = Date.now(); } nextLevel(); }
  function nextLevel() {
    if (!cfg.test) return;
    if (G.cur && !G.cur.outcome) { G.cur.outcome = 'abandon'; G.cur.t1 = Date.now(); }
    G.testIdx++;
    if (G.testIdx >= order.length) { showModal('<h3>Test bitti</h3><p>Teşekkürler. Lütfen kaydı indir ve araştırmacıya ver.</p><p><button onclick="window.CBGAME.downloadLog()">Kaydı indir</button></p>'); saveLog(); return; }
    loadLevel(order[G.testIdx]);
  }

  // ---------------------------------------------------------------- panel / butonlar
  function setMsg(t, cls) { var m = $('msg'); m.textContent = t; m.className = cls || 'info'; }
  var toastTimer = 0;
  function toast(t) { var e = $('toast'); e.textContent = t; e.classList.add('show'); clearTimeout(toastTimer); toastTimer = setTimeout(function () { e.classList.remove('show'); }, 1600); }
  function buildColorButtons() {
    var box = $('colorBtns'); box.innerHTML = '';
    G.palette.colors.forEach(function (c, i) {
      var b = document.createElement('button'); b.className = 'cbtn' + (isDark(c) ? ' dark' : ''); b.style.background = c; b.id = 'cb' + i; b.dataset.i = i;
      b.innerHTML = '<span>' + (i + 1) + ' · ' + G.palette.names[i] + '</span><small></small>';
      b.addEventListener('click', function () { select(i); }); box.appendChild(b);
    });
  }
  function refresh() {
    var L = G.level; if (!L) return;
    var seen = G.status === 'anim' ? G.visual : G.filled;   // animasyon sürerken oyuncunun GÖRDÜĞÜ durum
    var n = L.n, done = L.filledCount(seen), rem = L.remaining(seen), reach = L.reachablePerColor(seen), idle = G.status === 'idle';
    $('lvlTitle').textContent = cfg.test ? ('Seviye ' + (G.testIdx + 1) + ' / ' + order.length) : G.lv.name;
    $('lvlMeta').textContent = n + ' hücre · ' + L.K + ' renk · dalga başına W = ' + L.W + ' kutu · giriş hücresi: ' + L.entrances.length + (cfg.test ? '' : ' · ' + G.lv.id);
    var shown = done;
    $('progTxt').textContent = 'Yerleşen: ' + done + ' / ' + n + ' kutu (' + Math.round(100 * shown / n) + '%) · gönderilen dalga: ' + G.history.length;
    $('progBar').style.width = (100 * shown / n) + '%';
    var rows = '<tr><th></th><th>Kalan</th><th>≈Dalga</th><th>Erişilebilir</th></tr>';
    for (var i = 0; i < L.K; i++) {
      var lost = rem[i] - reach[i];
      rows += '<tr><td><span class="sw" style="background:' + col(i) + '"></span>' + G.palette.names[i] + '</td><td>' + rem[i] + '</td><td>' + Math.ceil(rem[i] / L.W) + '</td><td>' +
              reach[i] + (lost > 0 ? ' <span class="warn">⚠ ' + lost + ' erişilemez</span>' : '') + '</td></tr>';
    }
    $('stock').innerHTML = rows;
    var hist = ''; G.history.forEach(function (h) { hist += '<i style="background:' + col(h.color) + '" title="' + G.palette.names[h.color] + ': ' + h.n + ' kutu">' + h.n + '</i>'; });
    $('history').innerHTML = hist || '<span class="meta">henüz yok</span>';
    for (var k = 0; k < L.K; k++) {
      var b = $('cb' + k); b.disabled = !idle || reach[k] <= 0; b.classList.toggle('sel', G.selected === k);
      b.querySelector('small').textContent = 'kalan ' + rem[k] + ' · sonraki dalga ' + Math.min(L.W, reach[k]) + ' kutu';
    }
    $('sendBtn').disabled = !(idle && G.selected >= 0); $('sendBtn').style.display = cfg.hint === 0 ? 'none' : '';
    $('undoBtn').disabled = !(G.undoLeft > 0 && G.history.length && (G.status === 'idle' || G.status === 'sealed')); $('undoBtn').style.display = cfg.undo > 0 ? '' : 'none';
    $('undoBtn').textContent = 'Geri al (' + G.undoLeft + ')';
    var ab = $('abandonBtn'); ab.style.display = cfg.test ? '' : 'none'; ab.textContent = (G.status === 'won') ? 'Sonraki seviye' : 'Bu seviyeyi bırak';
    if (!cfg.test) devInfo();
  }
  function devInfo() {
    var s = G.lv.solver || {}, t = [];
    ['e_risky', 'e_crit', 'dens_risky', 'dh_exp_mean', 'dh_instant_share', 'abc_mean', 'filler_ratio', 'rnd0', 'win_undo1', 'win_undo2', 'waves'].forEach(function (k) { if (s[k] != null) t.push(k + ' = ' + s[k]); });
    $('devInfo').innerHTML = 'Çözücü ölçümü (araştırma; oyunda gösterilmez):<br>' + t.join(' · ') + '<br>' + (G.lv.note ? 'Not: ' + G.lv.note + '<br>' : '') + 'Kayıt: ' + LOG.attempts.length + ' deneme.';
  }
  function fillSelectors() {
    $('hintSel').value = String(cfg.hint); $('ghostChk').checked = cfg.ghost; $('speedSel').value = [1, 2, 4].indexOf(cfg.speed) >= 0 ? String(cfg.speed) : '1'; $('undoSel').value = String(cfg.undo);
    if (cfg.test) { $('lvlLbl').style.display = 'none'; $('dev').style.display = 'none'; $('parityBtn').style.display = 'none'; $('hintSel').parentNode.style.display = 'none'; $('ghostChk').parentNode.style.display = 'none'; $('undoLbl').style.display = 'none'; }
    if (!$('levelSel').options.length) {
      var groups = { hero: 'Hero (kedi, 216 hücre)', W: 'Isınma', A: 'A · anında hata', B: 'B · gecikmeli hata', C: 'C · zarfa yakın' }, html = '';
      ['hero', 'W', 'A', 'B', 'C'].forEach(function (g) {
        var items = LEVELS.filter(function (l) { return l.group === g; }); if (!items.length) return;
        html += '<optgroup label="' + groups[g] + '">' + items.map(function (l) { return '<option value="' + l.id + '">' + l.id + ' · ' + l.name + ' (' + l.cells + ')</option>'; }).join('') + '</optgroup>';
      });
      $('levelSel').innerHTML = html;
    }
    $('levelSel').value = G.lv.id;
  }

  // ---------------------------------------------------------------- kayıt
  function saveLog() { try { localStorage.setItem('cb_log_v0', JSON.stringify(LOG)); } catch (e) { /* yoksay */ } }
  function downloadLog() {
    LOG.meta.exported = new Date().toISOString();
    var blob = new Blob([JSON.stringify(LOG, null, 1)], { type: 'application/json' }), a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = 'renk_yerlestirme_kayit_' + (cfg.player || 'oyuncu') + '_' + Date.now() + '.json'; document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }

  // ---------------------------------------------------------------- parity paneli
  function showModal(html) { $('modalBody').innerHTML = html; $('modal').classList.add('show'); }
  function runParity() {
    var ok = 0, total = 0, bad = [], rows = '';
    VECTORS.levels.forEach(function (lv) {
      var L = new CB.Level(lv.grid, lv.W), lok = 0;
      lv.cases.forEach(function (c) {
        total++; var sim = L.simulate(c.sequence), same = sim.length === c.expected.length;
        for (var i = 0; same && i < sim.length; i++) same = JSON.stringify(sim[i].placed) === JSON.stringify(c.expected[i].placed) && !!sim[i].sealed === !!c.expected[i].sealed;
        if (same) { ok++; lok++; } else bad.push(lv.level_id + '/' + c.name);
      });
      rows += '<tr><td>' + lv.level_id + '</td><td>' + lv.cases.length + '</td><td>' + lok + '</td></tr>';
    });
    showModal('<h3>Parity testi: prototip çekirdeği ↔ Python çözücüsü</h3><p>Beklenen yerleştirmeler (hücre sırası dahil) ve kilitlenme durumu Python çözücüsünden (<code>research/parity.py</code>) üretildi ve bu sayfaya gömüldü; aşağıda tarayıcıdaki <code>engine.js</code> ile aynı dizileri oynatıp karşılaştırıyoruz.</p>' +
      '<p><b class="' + (ok === total ? 'ok' : 'warn') + '">' + ok + ' / ' + total + ' vaka birebir aynı</b> (' + VECTORS.levels.length + ' seviye)' + (bad.length ? '<br>Farklı: ' + bad.join(', ') : '') + '</p><table><tr><th>Seviye</th><th>Vaka</th><th>Eşleşen</th></tr>' + rows + '</table>');
    return { ok: ok, total: total, bad: bad };
  }

  // ---------------------------------------------------------------- döngü / olaylar
  function frame() {
    var t = now();
    if (G.status === 'anim') {
      G.workers.forEach(function (w) { if (w.state === 0 && t >= w.arrive) { w.state = 1; w.doneAt = t; G.visual[w.ti] = 1; G.pops[w.ti] = t; } });
      if (t - 0 >= G.waveEnd) { G.visual = new Uint8Array(G.filled); finishWave(); }
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
  $('hintSel').addEventListener('change', function () { cfg.hint = parseInt(this.value, 10); G.selected = -1; G.plan = null; G.previewSealed = []; newAttempt('restart'); });
  $('ghostChk').addEventListener('change', function () { cfg.ghost = this.checked; });
  $('speedSel').addEventListener('change', function () { cfg.speed = parseFloat(this.value); });
  $('undoSel').addEventListener('change', function () { cfg.undo = parseInt(this.value, 10); newAttempt('restart'); });
  window.addEventListener('resize', layout);
  window.addEventListener('keydown', function (e) {
    if (e.target && /select|input|textarea/i.test(e.target.tagName)) return;
    if (e.key >= '1' && e.key <= '9') { var i = parseInt(e.key, 10) - 1; if (i < G.level.K) select(i); }
    else if (e.key === 'Enter' || e.key === ' ') { if (G.selected >= 0) { e.preventDefault(); send(G.selected); } }
    else if (e.key === 'z' || e.key === 'Z') undo();
    else if (e.key === 'r' || e.key === 'R') newAttempt('restart');
  });
  if (window.ResizeObserver) new ResizeObserver(layout).observe($('boardWrap'));

  // otomasyon / araştırma API'si (tarayıcı testleri ve kayıt için)
  window.CBGAME = {
    send: function (letter) { var i = G.level.letters.indexOf(letter); if (cfg.hint === 0) send(i); else { G.selected = -1; select(i); select(i); } },
    select: function (letter) { select(G.level.letters.indexOf(letter)); },
    state: function () { return { status: G.status, filled: G.level.filledCount(G.filled), n: G.level.n, waves: G.history.length, level: G.lv.id, sealed: G.sealedShown.length, selected: G.selected, undoLeft: G.undoLeft }; },
    restart: function () { newAttempt('restart'); }, loadLevel: loadLevel, downloadLog: downloadLog, getLog: function () { return LOG; }, runParity: runParity,
    setCfg: function (o) { for (var k in o) cfg[k] = o[k]; fillSelectors(); newAttempt('restart'); }, undo: undo, nextLevel: nextLevel
  };

  // başlat
  var start = cfg.test ? order[0] : (qs.get('level') && byId[qs.get('level')] ? qs.get('level') : 'HERO2');
  G.testIdx = 0; loadLevel(start); requestAnimationFrame(frame);
})();

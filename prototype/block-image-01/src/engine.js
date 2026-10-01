/* block-image-01 — OYUN ÇEKİRDEĞİ (arayüzden bağımsız). Python referansı: tools/ref.py (parity: tests/parity.js).
 * Kurallar:
 *  • Izgara: 'E' giriş, '#' duvar, '.' zemin (ikisi de oyuncuya çizilmez), harf = hedef hücre (resmin bir bloğu). 4-komşuluk.
 *    Yürünebilir = zemin + giriş + BOŞ hedef hücre; dolan hedef KALICI engel. Hedef indeksleri satır-ana sıradadır.
 *  • Parça = sabit geometrik blok; resimdeki TEK hedefi aynı hücreleridir. Oyuncu yalnız hangi parçayı göndereceğini seçer.
 *  • El: 3 slot; her slotun elle yazılmış sabit kuyruğu. Gönderilen kartın yerine yalnız o slotun sıradaki parçası gelir.
 *  • Yerleşebilir ⇔ parçanın TÜM hedef hücreleri boş ve girişten erişilebilir.
 *  • place: hücreler en derinden başlayarak sıralanır; rota = girişten BFS en kısa yol (parça başı BFS); sonra parça kalıcı engel olur.
 *    Sonra: sealed (boş hücre erişilemez) · stuck (hiçbir kart yerleşemez) · won (hepsi dolu).
 */
(function (root, factory) { if (typeof module === 'object' && module.exports) module.exports = factory(); else root.BI = factory(); })(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  var DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  function Level(text, pieces, hand) {
    var rows = String(text).replace(/\s+$/, '').split('\n'), self = this;
    this.h = rows.length; this.w = Math.max.apply(null, rows.map(function (r) { return r.length; }));
    var n = this.h * this.w; this.kind = new Uint8Array(n); this.tIdx = new Int32Array(n).fill(-1); this.entrances = []; var cells = [];
    for (var r = 0; r < this.h; r++) for (var c = 0; c < this.w; c++) {
      var ch = c < rows[r].length ? rows[r][c] : '#', i = r * this.w + c;
      if (ch === '#') this.kind[i] = 0; else if (ch === '.') this.kind[i] = 1; else if (ch === 'E') { this.kind[i] = 2; this.entrances.push(i); } else { this.kind[i] = 3; cells.push({ r: r, c: c, cell: i }); }
    }
    cells.sort(function (a, b) { return a.r - b.r || a.c - b.c; });
    this.targets = cells.map(function (t, ti) { self.tIdx[t.cell] = ti; return t; }); this.n = this.targets.length;
    this.pieces = pieces.map(function (p, i) { return { i: i, id: p.id, cells: p.cells.map(function (x) { return self.tIdx[x[0] * self.w + x[1]]; }) }; });
    var pid = {}; this.pieces.forEach(function (p) { pid[p.id] = p.i; });
    this.hand = hand.map(function (q) { return q.map(function (id) { return pid[id]; }); });
    var cover = new Uint8Array(this.n); this.pieces.forEach(function (p) { p.cells.forEach(function (t) { cover[t]++; }); });
    for (var k = 0; k < this.n; k++) if (cover[k] !== 1) throw new Error('parçalar resmi tam kaplamıyor');
  }
  Level.prototype.newState = function () { return { filled: new Uint8Array(this.n), ptr: this.hand.map(function () { return 0; }) }; };
  Level.prototype.bfs = function (filled, wantParent) {
    var w = this.w, h = this.h, n = w * h, dist = new Int32Array(n).fill(-1), parent = wantParent ? new Int32Array(n).fill(-1) : null, q = new Int32Array(n), head = 0, tail = 0;
    for (var e = 0; e < this.entrances.length; e++) { dist[this.entrances[e]] = 0; q[tail++] = this.entrances[e]; }
    while (head < tail) {
      var u = q[head++], ur = (u / w) | 0, uc = u - ur * w;
      for (var d = 0; d < 4; d++) {
        var r = ur + DIRS[d][0], c = uc + DIRS[d][1]; if (r < 0 || c < 0 || r >= h || c >= w) continue;
        var v = r * w + c; if (dist[v] >= 0 || this.kind[v] === 0) continue; var ti = this.tIdx[v]; if (ti >= 0 && filled[ti]) continue;
        dist[v] = dist[u] + 1; if (parent) parent[v] = u; q[tail++] = v;
      }
    }
    return { dist: dist, parent: parent };
  };
  Level.prototype.cards = function (st) { return this.hand.map(function (q, s) { return st.ptr[s] < q.length ? q[st.ptr[s]] : null; }); };
  Level.prototype.feasible = function (filled, pi, b) { var cs = this.pieces[pi].cells; for (var i = 0; i < cs.length; i++) if (filled[cs[i]] || b.dist[this.targets[cs[i]].cell] < 0) return false; return true; };
  Level.prototype.options = function (st) { var b = this.bfs(st.filled), self = this; return this.cards(st).map(function (c) { return c === null ? null : self.feasible(st.filled, c, b); }); };
  Level.prototype.sealedCells = function (filled, b) { var out = []; for (var i = 0; i < this.n; i++) if (!filled[i] && b.dist[this.targets[i].cell] < 0) out.push(i); return out; };
  Level.prototype.filledCount = function (f) { var s = 0; for (var i = 0; i < this.n; i++) s += f[i]; return s; };
  Level.prototype.place = function (st, slot) {
    var c = this.cards(st)[slot]; if (c === null) return null;
    var b = this.bfs(st.filled, true); if (!this.feasible(st.filled, c, b)) return null;
    var T = this.targets, D = b.dist, order = this.pieces[c].cells.slice().sort(function (a, z) { return (D[T[z].cell] - D[T[a].cell]) || (a - z); }), steps = [];
    order.forEach(function (ti) { var path = [], cur = T[ti].cell; while (cur >= 0) { path.push(cur); cur = b.parent[cur]; } path.reverse(); steps.push({ ti: ti, route: path }); });
    var f = new Uint8Array(st.filled); order.forEach(function (ti) { f[ti] = 1; });
    var ptr = st.ptr.slice(); ptr[slot]++; var ns = { filled: f, ptr: ptr }, b2 = this.bfs(f), sealed = this.sealedCells(f, b2), won = this.filledCount(f) === this.n, stuck = false;
    if (!won && !sealed.length) { stuck = true; var cs = this.cards(ns); for (var j = 0; j < cs.length; j++) if (cs[j] !== null && this.feasible(f, cs[j], b2)) { stuck = false; break; } }
    return { piece: c, cells: order, steps: steps, state: ns, sealed: sealed, won: won, stuck: stuck };
  };
  Level.prototype.remaining = function (st) { var s = 0; this.hand.forEach(function (q, i) { s += q.length - st.ptr[i]; }); return s; };
  function routeSig(steps) { var m = 1000000007, h = 0; steps.forEach(function (s) { var a = 0; s.route.forEach(function (c, i) { a = (a + c * (i + 1)) % m; }); h = (h * 31 + a + s.route.length) % m; }); return h; }
  /* EL / KUYRUK MUHASEBESİ: her parça tam bir kez ya gönderilmiş (kuyruk önekinde) ya bekliyor (kuyruk sonekinde); el kartı = kuyruk başı. */
  Level.prototype.audit = function (st) {
    var self = this, err = [], seen = {}, sent = 0, rem = 0, nP = this.pieces.length, sentSet = {};
    this.hand.forEach(function (q, s) {
      if (st.ptr[s] < 0 || st.ptr[s] > q.length) err.push('slot ' + s + ': işaretçi aralık dışı');
      q.forEach(function (p, k) { if (seen[p]) err.push('çift: ' + self.pieces[p].id); seen[p] = 1; if (k < st.ptr[s]) { sent++; sentSet[p] = 1; } else rem++; });
    });
    if (Object.keys(seen).length !== nP) err.push('kayıp parça: kuyruklarda ' + Object.keys(seen).length + ' / ' + nP);
    if (sent + rem !== nP || rem !== nP - sent) err.push('muhasebe: gönderilen ' + sent + ' + kalan ' + rem + ' ≠ ' + nP);
    this.cards(st).forEach(function (c, s) { var q = self.hand[s]; if (c === null ? st.ptr[s] < q.length : c !== q[st.ptr[s]]) err.push('slot ' + s + ': el kartı kuyruk başı değil'); });
    this.pieces.forEach(function (p) { p.cells.forEach(function (ti) { if (!!st.filled[ti] !== !!sentSet[p.i]) err.push(p.id + ': hücre durumu gönderim durumuyla uyuşmuyor'); }); });
    return { ok: !err.length, errors: err, sent: sent, remaining: rem, total: nP, ids: this.cards(st).map(function (c) { return c === null ? null : self.pieces[c].id; }) };
  };
  /* Her slot için neden/ne olur: empty (kuyruk bitti) · blocked (yol kapalı) · seals/stuck (gönderirsen kaybedersin) · ok (devam edilebilir) · won. deadlock = hiçbir kart devam ettirmiyor. */
  Level.prototype.diagnose = function (st) {
    var self = this, opts = this.options(st), won = this.filledCount(st.filled) === this.n;
    var slots = this.cards(st).map(function (c, s) {
      if (c === null) return { slot: s, piece: null, state: 'empty' };
      if (!opts[s]) return { slot: s, piece: self.pieces[c].id, state: 'blocked' };
      var r = self.place(st, s); return { slot: s, piece: self.pieces[c].id, state: r.won ? 'won' : r.sealed.length ? 'seals' : r.stuck ? 'stuck' : 'ok' };
    });
    var cont = slots.filter(function (x) { return x.state === 'ok' || x.state === 'won'; }).length;
    return { slots: slots, continuable: cont, deadlock: !won && cont === 0 };
  };
  Level.prototype.simulate = function (seq) {
    var st = this.newState(), out = [], self = this;
    for (var k = 0; k < seq.length; k++) {
      var e = { slot: seq[k], cards: this.cards(st), legal: this.options(st).map(function (x) { return !!x; }) }, r = this.place(st, seq[k]);
      if (!r) { e.illegal = true; out.push(e); break; }
      e.cells = r.cells; e.rlen = r.steps.map(function (s) { return s.route.length; }); e.rsig = routeSig(r.steps); e.sealed = r.sealed.length > 0; e.stuck = r.stuck; e.won = r.won; out.push(e); st = r.state;
      if (e.sealed || e.stuck || e.won) break;
    }
    return out;
  };
  return { Level: Level, DIRS: DIRS };
});

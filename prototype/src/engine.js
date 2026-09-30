/* Renk-Yerleştirme prototipi — KURAL ÇEKİRDEĞİ (arayüzden bağımsız).
 *
 * Solver (research/puzzle_engine.py) ile birebir aynı kurallar:
 *   • Izgara: 'E' giriş, '#' duvar, '.' zemin (kalıcı açık), diğer her harf = hedef hücre (1 kutu).
 *   • Hareket: 4-komşuluk; işçi zemin + E + henüz DOLMAMIŞ hedef hücreler üzerinden yürür.
 *   • Dolan hedef hücre kalıcı engeldir.
 *   • Oyuncu yalnız RENK seçer. Miktar seviye parametresidir: sabit W.
 *   • Dalga = seçilen renkte, dalga BAŞINDA girişten erişilebilir boş hücreler arasından, (uzaklık azalan, satır, sütun)
 *     sırasıyla ilk W hücre ("en derinden başla"). Erişilebilir hücre W'den azsa o kadarı yerleşir; hiç yoksa hamle yasadışı.
 *   • Dalga atomiktir: durum anında değişir; animasyon yalnızca kozmetiktir.
 *   • Bir hedef hücre boşken girişten erişilemiyorsa seviye KAYIPTIR ("sealed").
 *   • Kazanma: tüm hedef hücreler dolu.
 * Not: bir dalgada "en derinden başla" sırası dalga başında tek BFS ile hesaplanır; bu, kutu-kutu yerleştirmeyle eşdeğerdir
 * (en derindeki hücreyi doldurmak aynı renkteki kalan hücrelerin uzaklığını/erişilebilirliğini değiştirmez).
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.CB = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  var DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];

  function Level(text, W) {
    var rows = String(text).replace(/\s+$/, '').split('\n');
    this.h = rows.length;
    this.w = Math.max.apply(null, rows.map(function (r) { return r.length; }));
    this.W = W;
    var n = this.h * this.w;
    this.kind = new Uint8Array(n);           // 0 duvar, 1 zemin, 2 giriş, 3 hedef
    this.tIdx = new Int32Array(n).fill(-1);  // hücre -> hedef indeksi
    this.entrances = [];
    var chars = {}, cells = [];
    for (var r = 0; r < this.h; r++) {
      for (var c = 0; c < this.w; c++) {
        var ch = c < rows[r].length ? rows[r][c] : '#', i = r * this.w + c;
        if (ch === '#') this.kind[i] = 0;
        else if (ch === '.') this.kind[i] = 1;
        else if (ch === 'E') { this.kind[i] = 2; this.entrances.push(i); }
        else { this.kind[i] = 3; cells.push({ r: r, c: c, ch: ch }); chars[ch] = true; }
      }
    }
    this.letters = Object.keys(chars).sort();              // solver: sorted(set(letters))
    var self = this;
    cells.sort(function (a, b) { return a.r - b.r || a.c - b.c; });
    this.targets = cells.map(function (t, ti) {
      t.ti = ti; t.col = self.letters.indexOf(t.ch); t.cell = t.r * self.w + t.c; self.tIdx[t.cell] = ti; return t;
    });
    this.n = this.targets.length;
    this.K = this.letters.length;
    this.counts = this.letters.map(function () { return 0; });
    this.targets.forEach(function (t) { self.counts[t.col]++; });
  }

  Level.prototype.newFilled = function () { return new Uint8Array(this.n); };

  // girişlerden çok-kaynaklı BFS; dist (erişilemez = -1). wantParent ise ebeveyn dizisi de döner.
  Level.prototype.bfs = function (filled, wantParent) {
    var w = this.w, h = this.h, n = w * h, dist = new Int32Array(n).fill(-1);
    var parent = wantParent ? new Int32Array(n).fill(-1) : null;
    var q = new Int32Array(n), head = 0, tail = 0;
    for (var e = 0; e < this.entrances.length; e++) { dist[this.entrances[e]] = 0; q[tail++] = this.entrances[e]; }
    while (head < tail) {
      var u = q[head++], ur = (u / w) | 0, uc = u - ur * w;
      for (var d = 0; d < 4; d++) {
        var r = ur + DIRS[d][0], c = uc + DIRS[d][1];
        if (r < 0 || c < 0 || r >= h || c >= w) continue;
        var v = r * w + c;
        if (dist[v] >= 0 || this.kind[v] === 0) continue;
        var ti = this.tIdx[v];
        if (ti >= 0 && filled[ti]) continue;
        dist[v] = dist[u] + 1; if (parent) parent[v] = u; q[tail++] = v;
      }
    }
    return { dist: dist, parent: parent };
  };

  // Seçilen renk için dalga planı: sıralı hedef indeksleri (en derinden başla).
  Level.prototype.plan = function (filled, color, bfsRes) {
    var b = bfsRes || this.bfs(filled), cand = [];
    for (var i = 0; i < this.n; i++) {
      var t = this.targets[i];
      if (t.col === color && !filled[i] && b.dist[t.cell] >= 0) cand.push(i);
    }
    var T = this.targets, D = b.dist;
    cand.sort(function (a, c) {
      var da = D[T[a].cell], dc = D[T[c].cell];
      return (dc - da) || (T[a].r - T[c].r) || (T[a].c - T[c].c);
    });
    return cand.slice(0, this.W);
  };

  // erişilemez boş hedef hücreler (kayıp göstergesi)
  Level.prototype.sealedCells = function (filled, bfsRes) {
    var b = bfsRes || this.bfs(filled), out = [];
    for (var i = 0; i < this.n; i++) if (!filled[i] && b.dist[this.targets[i].cell] < 0) out.push(i);
    return out;
  };

  Level.prototype.apply = function (filled, placed) {
    var f = new Uint8Array(filled); for (var i = 0; i < placed.length; i++) f[placed[i]] = 1; return f;
  };

  Level.prototype.remaining = function (filled) {
    var rem = this.counts.map(function () { return 0; });
    for (var i = 0; i < this.n; i++) if (!filled[i]) rem[this.targets[i].col]++;
    return rem;
  };
  Level.prototype.filledCount = function (filled) { var s = 0; for (var i = 0; i < this.n; i++) s += filled[i]; return s; };

  // erişilebilir boş hücre sayısı (renk başına) — "şu an yerleştirilebilir kutu" bilgisi
  Level.prototype.reachablePerColor = function (filled, bfsRes) {
    var b = bfsRes || this.bfs(filled), out = this.counts.map(function () { return 0; });
    for (var i = 0; i < this.n; i++) if (!filled[i] && b.dist[this.targets[i].cell] >= 0) out[this.targets[i].col]++;
    return out;
  };

  // animasyon rotaları: dalga başı BFS'inden her hedefe girişten en kısa yol (hücre indeks listesi)
  Level.prototype.routes = function (filled, placed) {
    var b = this.bfs(filled, true), self = this;
    return placed.map(function (ti) {
      var path = [], cur = self.targets[ti].cell;
      while (cur >= 0) { path.push(cur); cur = b.parent[cur]; }
      return path.reverse();
    });
  };

  // parity: renk dizisini oynat; her hamlede sıralı yerleşen hücreler ve kilit durumu
  Level.prototype.simulate = function (seq) {
    var filled = this.newFilled(), out = [], self = this;
    for (var k = 0; k < seq.length; k++) {
      var col = this.letters.indexOf(seq[k]);
      var placed = col < 0 ? [] : this.plan(filled, col);
      if (!placed.length) { out.push({ color: seq[k], placed: [], illegal: true }); break; }
      filled = this.apply(filled, placed);
      out.push({ color: seq[k], placed: placed.map(function (ti) { return [self.targets[ti].r, self.targets[ti].c]; }),
                 sealed: this.sealedCells(filled).length > 0 });
    }
    return out;
  };

  return { Level: Level, DIRS: DIRS };
});

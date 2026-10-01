/* PIXEL-ART KEDİ (96×96, sınırlı palet). Elle yazılmış piksel çizimi: yalnız tam piksellere boyayan ilkel şekiller (elips, çokgen, çizgi);
 * yumuşatma/vektör eğri yok. Her parça kendi 1 px koyu dış çizgisini alır; gölgeler 3 tonlu bantlar + dama dithering.
 * Oyun mantığının gizli gridi bu resmin dolu piksel maskesidir (tools/render_cat.js → tools/cat_cells.json). */
(function (root) {
  'use strict';
  var N = 96;
  var PAL = ['', '#4a2a1a', '#f0a04b', '#ffc57a', '#d9772c', '#b9561b', '#fff0d6', '#eed3a8', '#ff8fa6', '#e0607e', '#74d66a', '#2f9e4f', '#17120d', '#ffffff', '#c98a5a', '#fbe3b8'];
  // 1 çizgi · 2 kürk · 3 kürk açık · 4 kürk koyu · 5 çizgi/şerit · 6 krem · 7 krem koyu · 8 pembe · 9 pembe koyu · 10 göz yeşil · 11 göz koyu yeşil · 12 gözbebeği · 13 beyaz · 14 bıyık · 15 krem açık
  function pixels() {
    var cv = new Uint8Array(N * N);
    function layer() { return new Uint8Array(N * N); }
    function inEll(x, y, cx, cy, rx, ry) { var dx = (x + 0.5 - cx) / rx, dy = (y + 0.5 - cy) / ry; return dx * dx + dy * dy <= 1; }
    function inPoly(x, y, P) { var px = x + 0.5, py = y + 0.5, c = false; for (var i = 0, j = P.length - 1; i < P.length; j = i++) { var xi = P[i][0], yi = P[i][1], xj = P[j][0], yj = P[j][1]; if (((yi > py) !== (yj > py)) && (px < (xj - xi) * (py - yi) / (yj - yi) + xi)) c = !c; } return c; }
    function fill(L, test, col) { for (var y = 0; y < N; y++) for (var x = 0; x < N; x++) if (test(x, y)) L[y * N + x] = col; }
    function ellipse(L, cx, cy, rx, ry, col) { fill(L, function (x, y) { return inEll(x, y, cx, cy, rx, ry); }, col); }
    function poly(L, P, col) { fill(L, function (x, y) { return inPoly(x, y, P); }, col); }
    function line(L, x0, y0, x1, y1, col, th) { var n = Math.ceil(Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) * 2) + 1, h = (th || 1) / 2; for (var i = 0; i <= n; i++) { var x = x0 + (x1 - x0) * i / n, y = y0 + (y1 - y0) * i / n; for (var yy = Math.floor(y - h); yy <= Math.floor(y + h); yy++) for (var xx = Math.floor(x - h); xx <= Math.floor(x + h); xx++) if (xx >= 0 && yy >= 0 && xx < N && yy < N && (xx + 0.5 - x) * (xx + 0.5 - x) + (yy + 0.5 - y) * (yy + 0.5 - y) <= h * h + 0.2) L[yy * N + xx] = col; } }
    // 3 tonlu elips: açık (sol-üst), temel, koyu (sağ-alt), tonlar arasında dama dithering
    function shaded(L, cx, cy, rx, ry, c0, c1, c2) {
      fill(L, function (x, y) { return inEll(x, y, cx, cy, rx, ry); }, c1);
      fill(L, function (x, y) { if (!inEll(x, y, cx, cy, rx, ry)) return false; var d = ((x + 0.5 - cx + rx * 0.28) / (rx * 0.82)) * ((x + 0.5 - cx + rx * 0.28) / (rx * 0.82)) + ((y + 0.5 - cy + ry * 0.32) / (ry * 0.82)) * ((y + 0.5 - cy + ry * 0.32) / (ry * 0.82)); return d <= 0.55 || (d <= 0.75 && ((x + y) & 1) === 0); }, c0);
      fill(L, function (x, y) { if (!inEll(x, y, cx, cy, rx, ry)) return false; var d = ((x + 0.5 - cx + rx * 0.3) / (rx * 0.95)) * ((x + 0.5 - cx + rx * 0.3) / (rx * 0.95)) + ((y + 0.5 - cy + ry * 0.3) / (ry * 0.95)) * ((y + 0.5 - cy + ry * 0.3) / (ry * 0.95)); return d >= 1.12 || (d >= 0.98 && ((x + y) & 1) === 0); }, c2);
    }
    // bir parça katmanını 1 px koyu dış çizgiyle tuvale yaz
    function commit(L, outlineCol) {
      var out = layer();
      for (var y = 0; y < N; y++) for (var x = 0; x < N; x++) if (L[y * N + x]) {
        var edge = x === 0 || y === 0 || x === N - 1 || y === N - 1 || !L[y * N + x - 1] || !L[y * N + x + 1] || !L[(y - 1) * N + x] || !L[(y + 1) * N + x];
        out[y * N + x] = edge ? (outlineCol || 1) : L[y * N + x];
      }
      for (var i = 0; i < N * N; i++) if (out[i]) cv[i] = out[i];
    }
    function put(L, x, y, c) { if (x >= 0 && y >= 0 && x < N && y < N) L[y * N + x] = c; }

    // ---- kuyruk (arkada): kalın eğri, şeritli
    var T = layer(), P0 = [66, 84], P1 = [91, 92], P2 = [96, 63], P3 = [79, 54], pts = [];
    for (var i = 0; i <= 80; i++) { var t = i / 80, u = 1 - t; pts.push([u * u * u * P0[0] + 3 * u * u * t * P1[0] + 3 * u * t * t * P2[0] + t * t * t * P3[0], u * u * u * P0[1] + 3 * u * u * t * P1[1] + 3 * u * t * t * P2[1] + t * t * t * P3[1], i]); }
    pts.forEach(function (p) { ellipse(T, p[0], p[1], 5.6, 5.6, 2); });
    var arc = [0]; for (var q = 1; q < pts.length; q++) arc.push(arc[q - 1] + Math.hypot(pts[q][0] - pts[q - 1][0], pts[q][1] - pts[q - 1][1]));
    for (var ty = 0; ty < N; ty++) for (var tx = 0; tx < N; tx++) if (T[ty * N + tx]) {   // her kuyruk pikselini en yakın eğri noktasına göre halkalara ayır
      var bi = 0, bd = 1e9; for (var q2 = 0; q2 < pts.length; q2++) { var dd = (tx + 0.5 - pts[q2][0]) * (tx + 0.5 - pts[q2][0]) + (ty + 0.5 - pts[q2][1]) * (ty + 0.5 - pts[q2][1]); if (dd < bd) { bd = dd; bi = q2; } }
      var ring = Math.floor(arc[bi] / 4.6) % 2 === 1, rim = Math.sqrt(bd) >= 3.7 && (tx + 0.5 - pts[bi][0]) + (ty + 0.5 - pts[bi][1]) < 0;
      T[ty * N + tx] = ring ? 5 : (rim ? 3 : 2);
    }
    commit(T);
    // ---- gövde
    var B = layer(); shaded(B, 48, 69, 23, 22, 3, 2, 4);
    ellipse(B, 48, 73.5, 12.5, 16, 6); fill(B, function (x, y) { return B[y * N + x] === 6 && inEll(x, y, 48, 73.5, 12.5, 16) && !inEll(x, y, 46.5, 71.5, 10.5, 14) ; }, 7);
    [[27, 58, 33, 59.5], [26, 67, 33, 68], [27.5, 76, 34, 75], [69, 58, 63, 59.5], [70, 67, 63, 68], [68.5, 76, 62, 75]].forEach(function (s) { line(B, s[0], s[1], s[2], s[3], 5, 1.6); });
    commit(B);
    // ---- ön patiler
    [38, 58].forEach(function (cx) {
      var Pw = layer(); shaded(Pw, cx, 87.5, 9, 5.6, 13, 6, 7); [-3.2, 0, 3.2].forEach(function (d) { line(Pw, cx + d, 88, cx + d, 91.5, 7, 1); }); commit(Pw);
    });
    // ---- kulaklar
    [[[23, 34], [26, 4], [46, 18]], [[73, 34], [70, 4], [50, 18]]].forEach(function (tri, i) {
      var E = layer(); poly(E, tri, 2); fill(E, function (x, y) { return E[y * N + x] && inPoly(x, y, [[tri[0][0] + (i ? -3 : 3), tri[0][1] - 3], [tri[1][0] + (i ? -1 : 1), tri[1][1] + 3], [tri[1][0] + (i ? -1 : 1) + (i ? -9 : 9), tri[1][1] + 12]]); }, 3);
      var m = i ? -1 : 1, bx = i ? 96 : 0;
      fill(E, function (x, y) { return inPoly(x, y, [[bx + m * 29, 27], [bx + m * 29.5, 13.5], [bx + m * 40, 19.5]]); }, 8);
      fill(E, function (x, y) { return E[y * N + x] === 8 && !inPoly(x, y, [[bx + m * 29.5, 25.5], [bx + m * 30, 15.5], [bx + m * 37.5, 20.2]]); }, 9);
      commit(E);
    });
    // ---- kafa
    var Hd = layer(); shaded(Hd, 48, 37, 26, 21, 3, 2, 4);
    [[48, 17, 48, 25], [40, 18.5, 41.8, 26], [56, 18.5, 54.2, 26]].forEach(function (s) { line(Hd, s[0], s[1], s[2], s[3], 5, 1.7); });
    [[35, 46.5, 10, 7], [61, 46.5, 10, 7], [48, 48, 8.5, 6.5]].forEach(function (e) { ellipse(Hd, e[0], e[1], e[2], e[3], 6); });
    [[35, 46.5, 10, 7], [61, 46.5, 10, 7]].forEach(function (e) { fill(Hd, function (x, y) { return Hd[y * N + x] === 6 && inEll(x, y, e[0], e[1], e[2], e[3]) && !inEll(x, y, e[0] - 1, e[1] - 1.2, e[2] - 1.6, e[3] - 1.6); }, 7); });
    [[31, 43, 3, 1.6], [65, 43, 3, 1.6]].forEach(function (e) { ellipse(Hd, e[0], e[1], e[2], e[3], 8); });
    commit(Hd);
    // ---- yüz detayları (çizgi katmanı olmadan doğrudan)
    var D = layer();
    [37, 59].forEach(function (ex) {
      ellipse(D, ex, 36, 5.2, 6.4, 11); ellipse(D, ex, 36, 4.2, 5.4, 10); ellipse(D, ex, 38, 3.6, 3.4, 10);
      ellipse(D, ex, 36.5, 2.1, 4.6, 12); put(D, Math.round(ex - 2.5), 33, 13); put(D, Math.round(ex - 2.5), 34, 13); put(D, Math.round(ex - 1.5), 33, 13); put(D, Math.round(ex + 1.5), 39, 13);
    });
    poly(D, [[45, 42], [51, 42], [48, 45.8]], 8); line(D, 45, 41.6, 51, 41.6, 9, 1); put(D, 48, 45, 9);
    line(D, 48, 46, 48, 49, 1, 1); line(D, 48, 49, 44, 51.5, 1, 1); line(D, 48, 49, 52, 51.5, 1, 1); line(D, 44, 51.5, 41, 49.5, 1, 1); line(D, 52, 51.5, 55, 49.5, 1, 1);
    [[40, 45.5, 29, 43.5], [40, 48, 28.5, 50.5], [56, 45.5, 67, 43.5], [56, 48, 67.5, 50.5]].forEach(function (s) { line(D, s[0], s[1], s[2], s[3], 14, 1); });
    for (var i2 = 0; i2 < N * N; i2++) if (D[i2]) cv[i2] = D[i2];
    return { N: N, pal: PAL, idx: cv };
  }
  root.CB_ART = { N: N, pal: PAL, pixels: pixels };
})(typeof self !== 'undefined' ? self : this);

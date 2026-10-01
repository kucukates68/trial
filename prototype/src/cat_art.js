/* KEDİ ÇİZİMİ (vektör). Oyun mantığı bu çizimin 64x64 maskesini gizli grid olarak kullanır; oyuncu grid değil bu resmi görür.
 * Aynı fonksiyon (1) çalışma anında ekran çözünürlüğünde, (2) tools/render_cat.js ile maske/renk çıkarırken kullanılır. */
(function (root) {
  'use strict';
  var C = { fur: '#f2a14a', furHi: '#ffc479', furLo: '#d9772c', stripe: '#c4621f', cream: '#fff3dc', creamLo: '#f2dcb8', line: '#6a3a1c', pink: '#ff8fa6', eye: '#74d66a', eyeLo: '#2f9e4f' };
  function ell(ctx, x, y, rx, ry) { ctx.beginPath(); ctx.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2); }
  function rad(ctx, x, y, r, c0, c1) { var g = ctx.createRadialGradient(x - r * 0.25, y - r * 0.35, r * 0.1, x, y, r); g.addColorStop(0, c0); g.addColorStop(1, c1); return g; }
  function draw(ctx, S) {
    ctx.save(); ctx.scale(S, S); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    // kuyruk (arkada)
    ctx.beginPath(); ctx.moveTo(44, 56); ctx.bezierCurveTo(60, 60, 63, 42, 53, 36);
    ctx.strokeStyle = C.line; ctx.lineWidth = 8.6; ctx.stroke();
    ctx.strokeStyle = C.fur; ctx.lineWidth = 6.6; ctx.stroke();
    ctx.save(); ctx.setLineDash([1.6, 4.2]); ctx.lineCap = 'butt'; ctx.strokeStyle = C.stripe; ctx.lineWidth = 6.6; ctx.stroke(); ctx.restore();
    // gövde
    ell(ctx, 32, 46, 15.5, 14.5); ctx.fillStyle = rad(ctx, 32, 46, 18, C.furHi, C.fur); ctx.fill(); ctx.strokeStyle = C.line; ctx.lineWidth = 1.2; ctx.stroke();
    ell(ctx, 32, 49, 8.6, 11); ctx.fillStyle = rad(ctx, 32, 49, 12, C.cream, C.creamLo); ctx.fill();
    ctx.strokeStyle = C.stripe; ctx.lineWidth = 1.5;
    [[17.5, 41, 21.5, 42], [17, 46, 21.5, 46.5], [17.8, 51, 22, 50.5], [46.5, 41, 42.5, 42], [47, 46, 42.5, 46.5], [46.2, 51, 42, 50.5]].forEach(function (s) { ctx.beginPath(); ctx.moveTo(s[0], s[1]); ctx.lineTo(s[2], s[3]); ctx.stroke(); });
    // ön patiler
    [[25.5, 58.3], [38.5, 58.3]].forEach(function (p) {
      ell(ctx, p[0], p[1], 6, 3.7); ctx.fillStyle = rad(ctx, p[0], p[1], 7, '#ffffff', C.cream); ctx.fill(); ctx.strokeStyle = C.line; ctx.lineWidth = 1.1; ctx.stroke();
      ctx.strokeStyle = C.creamLo; ctx.lineWidth = 0.8; [-1.6, 1.6].forEach(function (d) { ctx.beginPath(); ctx.moveTo(p[0] + d, p[1] + 0.8); ctx.lineTo(p[0] + d, p[1] + 3); ctx.stroke(); });
    });
    // kulaklar
    [[[15.5, 22], [17.2, 3], [30.5, 12]], [[48.5, 22], [46.8, 3], [33.5, 12]]].forEach(function (t, i) {
      ctx.beginPath(); ctx.moveTo(t[0][0], t[0][1]); ctx.lineTo(t[1][0], t[1][1]); ctx.lineTo(t[2][0], t[2][1]); ctx.closePath();
      ctx.fillStyle = rad(ctx, t[1][0], t[1][1] + 6, 14, C.furHi, C.fur); ctx.fill(); ctx.strokeStyle = C.line; ctx.lineWidth = 1.2; ctx.stroke();
      var m = i ? -1 : 1, bx = i ? 64 : 0; ctx.beginPath(); ctx.moveTo(bx + m * 19.3, 18); ctx.lineTo(bx + m * 19.6, 8.6); ctx.lineTo(bx + m * 26.6, 12.6); ctx.closePath(); ctx.fillStyle = C.pink; ctx.fill();
    });
    // kafa
    ell(ctx, 32, 24.5, 17.5, 14); ctx.fillStyle = rad(ctx, 32, 24.5, 21, C.furHi, C.fur); ctx.fill(); ctx.strokeStyle = C.line; ctx.lineWidth = 1.2; ctx.stroke();
    ctx.strokeStyle = C.stripe; ctx.lineWidth = 1.5;
    [[32, 11.5, 32, 17], [26.8, 12.6, 28.4, 17.2], [37.2, 12.6, 35.6, 17.2]].forEach(function (s) { ctx.beginPath(); ctx.moveTo(s[0], s[1]); ctx.lineTo(s[2], s[3]); ctx.stroke(); });
    // yanaklar / burun bölgesi
    [[23.5, 31.2, 6.6, 4.6], [40.5, 31.2, 6.6, 4.6], [32, 32, 5.6, 4.4]].forEach(function (e) { ell(ctx, e[0], e[1], e[2], e[3]); ctx.fillStyle = C.cream; ctx.fill(); });
    ctx.globalAlpha = 0.5; [[21.5, 28.6], [42.5, 28.6]].forEach(function (b) { ell(ctx, b[0], b[1], 2.6, 1.5); ctx.fillStyle = C.pink; ctx.fill(); }); ctx.globalAlpha = 1;
    // gözler
    [24.5, 39.5].forEach(function (x) {
      ell(ctx, x, 23.8, 3.5, 4); ctx.fillStyle = rad(ctx, x, 23.8, 5, '#b8f5a0', C.eye); ctx.fill(); ctx.strokeStyle = C.eyeLo; ctx.lineWidth = 0.8; ctx.stroke();
      ell(ctx, x, 24.2, 1.5, 3.1); ctx.fillStyle = '#16200f'; ctx.fill();
      ctx.beginPath(); ctx.arc(x - 1, 22.4, 0.95, 0, 7); ctx.fillStyle = '#fff'; ctx.fill();
    });
    // burun, ağız, bıyık
    ctx.beginPath(); ctx.moveTo(30.2, 28.4); ctx.lineTo(33.8, 28.4); ctx.lineTo(32, 30.6); ctx.closePath(); ctx.fillStyle = C.pink; ctx.fill(); ctx.strokeStyle = C.line; ctx.lineWidth = 0.7; ctx.stroke();
    ctx.strokeStyle = C.line; ctx.lineWidth = 0.8; ctx.beginPath(); ctx.moveTo(32, 30.6); ctx.lineTo(32, 32.2); ctx.moveTo(32, 32.2); ctx.quadraticCurveTo(29.8, 34.2, 28.2, 32.7); ctx.moveTo(32, 32.2); ctx.quadraticCurveTo(34.2, 34.2, 35.8, 32.7); ctx.stroke();
    ctx.strokeStyle = '#8a6a50'; ctx.lineWidth = 0.55;
    [[27, 30.4, 20.5, 29.4], [27, 32, 20.2, 33.4], [37, 30.4, 43.5, 29.4], [37, 32, 43.8, 33.4]].forEach(function (s) { ctx.beginPath(); ctx.moveTo(s[0], s[1]); ctx.lineTo(s[2], s[3]); ctx.stroke(); });
    ctx.restore();
  }
  root.CB_ART = { w: 64, h: 64, draw: draw };
})(typeof self !== 'undefined' ? self : this);

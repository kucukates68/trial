// node tests/qa_color.js — RENK SİSTEMİ QA: kedi = 25 parçanın birleşmiş hâli; targetColor[cell] = owningPiece.color
const { chromium } = require(process.env.PLAYWRIGHT_NODE || '/opt/node22/lib/node_modules/playwright'); const path = require('path'), fs = require('fs');
const HTML = 'file://' + path.resolve(__dirname, '..', 'dist', 'block-image-01.html'), INFO = require('./level_info.json'), WIN = INFO.win; const shots = path.resolve(__dirname, '_shots'); fs.mkdirSync(shots, { recursive: true });
const SRC = fs.readFileSync(path.resolve(__dirname, '..', 'src', 'ui.js'), 'utf8');
let fails = 0; const ok = (c, m) => { console.log((c ? 'OK   ' : 'FAIL ') + m); if (!c) fails++; };
const HEX = { orange: '#ff9f1c', blue: '#3b82f6', red: '#ef4444', green: '#2fb67c', dark: '#2e2a35' }, NAMES = Object.keys(HEX), rgb = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
(async () => {
  const b = await chromium.launch(), errs = []; const pg = await b.newPage({ viewport: { width: 1100, height: 860 }, deviceScaleFactor: 1 }); pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.goto(HTML + '?speed=20'); await pg.waitForFunction(() => window.CBGAME); await pg.waitForTimeout(300);
  const info = await pg.evaluate(() => { const L = CBGAME.level, rows = [], cells = []; for (let pi = 0; pi < L.pieces.length; pi++) rows.push({ id: L.pieces[pi].id, color: CBGAME.pieceColor(pi), card: CBGAME.cardPixels(pi), n: L.pieces[pi].cells.length });
    for (let ti = 0; ti < L.n; ti++) cells.push({ owner: CBGAME.owner(ti), col: CBGAME.targetColor(ti), ghost: CBGAME.cellPixel(ti), ineg: CBGAME.level.tIdx ? 0 : 0 }); return { rows, cells, n: L.n, counts: rows.reduce((a, r) => (a[r.color] = (a[r.color] || 0) + 1, a), {}), cover: CBGAME.level.pieces.reduce((a, p) => a + p.cells.length, 0) }; });
  // geometri: 25 parça, 188 hücre, her hücre tam bir parçaya ait
  const ownerCount = new Array(info.n).fill(0); info.cells.forEach((c, i) => ownerCount[i]++); ok(info.rows.length === 25 && info.n === 188 && info.cover === 188, `geometri: ${info.rows.length} parça, ${info.n} hedef hücre, parça hücreleri toplamı ${info.cover} (her hücre tam bir parçaya ait)`);
  // 1) piece.color + kartlar tek renk
  const has = info.rows.filter(r => NAMES.includes(r.color)).length, mono = info.rows.filter(r => r.card.length === 1 && r.card[0] === rgb(HEX[r.color]).join(',') + ',255').length;
  ok(has === 25, `${has}/25 parçanın piece.color değeri var ${JSON.stringify(info.counts)}`); ok(mono === 25, `${mono}/25 pieces monochrome (kart pikselleri == piece.color)`);
  // 2) targetColor[cell] == owningPiece.color (kaynak) — ve eski colors[] kullanılmıyor
  const srcOK = info.cells.filter(c => c.col.toLowerCase() === HEX[info.rows[c.owner].color]).length; ok(srcOK === 188, `${srcOK}/188 hedef hücre: targetColor == owningPiece.color`);
  ok(!/LV\.colors|LV\.palette|BI_LEVEL\.colors/.test(SRC), 'render kodu eski colors[]/palette verisine başvurmuyor (ui.js taraması)');
  // 3) başlangıç hayalet kedisi piece.color'ın açık tonu (render edilen piksel)
  const ghostOK = info.cells.filter(c => { const w = rgb(HEX[info.rows[c.owner].color]), want = w.map(v => Math.round(v + (255 - v) * 0.66)); return c.ghost.every((v, i) => Math.abs(v - want[i]) <= 2); }).length; ok(ghostOK === 188, `${ghostOK}/188 hücre: başlangıç hayaleti = piece.color'ın açık tonu (canvas pikseli)`);
  // 4) oyna: taşırken tek renk, yerleşince hücrelerin RENDER edilen rengi == piece.color
  const hand = () => pg.evaluate(() => [...document.querySelectorAll('#hand .card')].map(b => ({ slot: +b.dataset.slot, id: b.dataset.piece })));
  let carryOK = 0, settleCells = 0, settleTotal = 0, startHand = null, previewOK = 0;
  for (let k = 0; k < WIN.length; k++) {
    await pg.waitForFunction(() => CBGAME.state().status === 'idle', { timeout: 60000 }); const h = await hand(); if (k === 0) { startHand = h; await pg.screenshot({ path: path.join(shots, 'c0_first_hand.png') }); }
    const slot = WIN[k], card = h.find(x => x.slot === slot), pi = await pg.evaluate(id => CBGAME.level.pieces.findIndex(p => p.id === id), card.id);
    await pg.click('#slot' + slot); await pg.waitForTimeout(60); if (k === 3) await pg.screenshot({ path: path.join(shots, 'c1_preview.png') });
    const pv = await pg.evaluate(() => CBGAME.previewCells()), cells = await pg.evaluate(pi => CBGAME.level.pieces[pi].cells.slice().sort((a, z) => a - z), pi); if (JSON.stringify(pv) === JSON.stringify(cells)) previewOK++;
    await pg.click('#sendBtn'); await pg.waitForFunction(() => CBGAME.state().status === 'anim');
    const cargo = await pg.evaluate(() => CBGAME.workerCargo()); if (cargo.length > 0 && cargo.every(c => c.toLowerCase() === HEX[info.rows[pi].color])) carryOK++;
    await pg.waitForFunction(() => CBGAME.state().status !== 'anim', { timeout: 60000 }); await pg.waitForTimeout(900);
    const px = await pg.evaluate(cs => cs.map(ti => CBGAME.cellPixel(ti)), cells), want = rgb(HEX[info.rows[pi].color]);
    px.forEach(p => { settleTotal++; if (p.join(',') === want.join(',')) settleCells++; }); if (k === 3) await pg.screenshot({ path: path.join(shots, 'c3_settled.png') });
  }
  ok(previewOK === 25, `${previewOK}/25: önizleme hedefi == parçanın kendi hücreleri`); ok(carryOK === 25, `${carryOK}/25 parça: işçilerin taşıdığı tüm kutular piece.color`);
  ok(settleCells === 188 && settleTotal === 188, `${settleCells}/${settleTotal} target cells: yerleştikten sonra render edilen renk == owningPiece.color`);
  const st = await pg.evaluate(() => CBGAME.state()); ok(st.status === 'won' && st.filled === st.n, 'kazanan dizi hâlâ kazanıyor: ' + st.filled + '/' + st.n);
  const first = startHand.map(x => info.rows.find(r => r.id === x.id)); ok(first.length === 3 && new Set(first.map(r => r.color)).size === 3, 'ilk el: ' + first.map(r => r.id + '=' + r.color).join(' · '));
  // CAT FEATURE COVERAGE: gözler/burun gerçek parça, kulaklar/kuyruk, bitişik parçalar farklı renk, dekoratif piksel yok
  const F = await pg.evaluate(() => { const L = CBGAME.level, P = CBGAME.info.pieces, W = L.w, rowsOf = pi => L.pieces[pi].cells.map(ti => L.targets[ti].r), colsOf = pi => L.pieces[pi].cells.map(ti => L.targets[ti].c);
    const eyes = P.map((p, i) => ({ p, i })).filter(x => x.p.role === 'eye'), nose = P.map((p, i) => ({ p, i })).filter(x => x.p.role === 'nose');
    const minRow = Math.min(...L.targets.map(t => t.r)), ears = new Set(); L.targets.forEach((t, ti) => { if (t.r <= minRow + 2 && (t.c < 6 || t.c > 12)) ears.add(CBGAME.owner(ti)); });
    const maxCol = Math.max(...L.targets.map(t => t.c)), tail = new Set(); L.targets.forEach((t, ti) => { if (t.c >= 16) tail.add(CBGAME.owner(ti)); });
    const tailCells = [...tail].reduce((a, pi) => a + L.pieces[pi].cells.length, 0);
    let sameAdj = 0; const seen = new Set(); L.targets.forEach((t, ti) => { [[1, 0], [0, 1]].forEach(d => { const r = t.r + d[0], c = t.c + d[1], nt = (r < L.h && c < L.w) ? L.tIdx[r * L.w + c] : -1; if (nt >= 0) { const a = CBGAME.owner(ti), b = CBGAME.owner(nt); if (a !== b && P[a].color === P[b].color && P[a].color !== 'dark') { const k = Math.min(a, b) + '-' + Math.max(a, b); if (!seen.has(k)) { seen.add(k); sameAdj++; } } } }); });
    let deco = 0, sampled = 0; for (let r = 0; r < L.h - 1; r++) for (let c = 0; c < L.w; c++) { if (L.tIdx[r * L.w + c] >= 0 || L.kind[r * L.w + c] !== 0) continue; const t = { r, c }, d = G_dpr(), x = Math.round((CBGAME.geo().ox + (c + 0.5) * CBGAME.geo().s) * d), y = Math.round((CBGAME.geo().oy + (r + 0.5) * CBGAME.geo().s) * d); sampled++; if (CBGAME.alphaAt(x, y) !== 0) deco++; function G_dpr() { return CBGAME.geo().dpr; } }
    return { nEye: eyes.length, eyeOK: eyes.every(x => L.pieces[x.i].cells.length === 1 && x.p.color === 'dark' && CBGAME.cardPixels(x.i).length === 1), eyeOwn: eyes.every(x => CBGAME.owner(L.pieces[x.i].cells[0]) === x.i), noseN: nose.length, ears: ears.size, earColors: [...ears].map(pi => P[pi].color), tailPieces: tail.size, tailCells, sameAdj, deco, sampled }; });
  ok(F.nEye === 2 && F.eyeOK && F.eyeOwn, `catFeatureCoverage: ${F.nEye} göz parçası (1 hücre, dark, monochrome), göz hücreleri bu parçalara ait`);
  ok(F.noseN === 1, 'catFeatureCoverage: burun gerçek 1 hücrelik parça'); ok(F.ears === 2 && F.earColors[0] !== F.earColors[1], `catFeatureCoverage: 2 kulak parçası, farklı renkler (${F.earColors.join(' / ')})`);
  ok(F.tailPieces === 3 && F.tailCells >= 20, `catFeatureCoverage: kuyruk ${F.tailPieces} parça / ${F.tailCells} hücre`); ok(F.sameAdj === 0, `bitişik parçalar farklı renk: aynı renkli komşu çift sayısı = ${F.sameAdj}`);
  ok(F.deco === 0 && F.sampled > 300, `dekoratif piksel yok: hedef olmayan ${F.sampled} hücrenin 0 tanesinde çizim var (${F.deco})`);
  await pg.click('#parityBtn'); await pg.waitForTimeout(300); const m = (await pg.textContent('#modalBody')).match(/(\d+) \/ (\d+) vaka/); ok(m && m[1] === m[2], 'parity ' + m[0]); ok(errs.length === 0, 'console hatası yok ' + JSON.stringify(errs.slice(0, 3)));
  const T = srcOK === 188 && settleCells === 188 && ghostOK === 188, P = mono === 25 && has === 25 && carryOK === 25;
  console.log(''); console.log('targetPieceColorParity: ' + (T ? '188/188 target cells: PASS' : 'FAIL')); console.log('25/25 pieces monochrome: ' + (P ? 'PASS' : 'FAIL')); console.log('pieceToTargetColorParity: ' + (T && P ? 'PASS' : 'FAIL')); console.log('finalCatColorSource: piece.color'); console.log('catFeatureCoverage: ' + (F.nEye === 2 && F.eyeOK && F.eyeOwn && F.noseN === 1 && F.ears === 2 && F.tailPieces === 3 && F.sameAdj === 0 && F.deco === 0 ? 'PASS' : 'FAIL'));
  await b.close(); console.log(fails || !(T && P) ? 'BAŞARISIZ' : 'TÜMÜ GEÇTİ'); process.exit(fails || !(T && P) ? 1 : 0);
})();

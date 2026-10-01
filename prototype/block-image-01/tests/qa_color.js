// node tests/qa_color.js — PARÇA RENGİ sistemi QA (25/25): elde = tek renk, taşınırken = tek renk, yerleşince = hedef resmin gerçek renkleri; renk hedeften bağımsız
const { chromium } = require(process.env.PLAYWRIGHT_NODE || '/opt/node22/lib/node_modules/playwright'); const path = require('path'), fs = require('fs');
const HTML = 'file://' + path.resolve(__dirname, '..', 'dist', 'block-image-01.html'), INFO = require('./level_info.json'), WIN = INFO.win; const shots = path.resolve(__dirname, '_shots'); fs.mkdirSync(shots, { recursive: true });
let fails = 0; const ok = (c, m) => { console.log((c ? 'OK   ' : 'FAIL ') + m); if (!c) fails++; };
(async () => {
  const b = await chromium.launch(), errs = []; const pg = await b.newPage({ viewport: { width: 1100, height: 860 }, deviceScaleFactor: 1 }); pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.goto(HTML + '?speed=20'); await pg.waitForFunction(() => window.CBGAME); await pg.waitForTimeout(300);
  const info = await pg.evaluate(() => { const L = CBGAME.level, hx = { orange: '#ff9f1c', blue: '#3b82f6', red: '#ef4444', green: '#2fb67c' }, rows = [];
    for (let pi = 0; pi < L.pieces.length; pi++) rows.push({ id: L.pieces[pi].id, color: CBGAME.pieceColor(pi), card: CBGAME.cardPixels(pi), tgt: CBGAME.targetColors(pi), want: CBGAME.hexToRgb(hx[CBGAME.pieceColor(pi)] || '#000000') });
    return { rows, palette: CBGAME.info.palette, counts: rows.reduce((a, r) => (a[r.color] = (a[r.color] || 0) + 1, a), {}) }; });
  const NAMES = ['orange', 'blue', 'red', 'green'], rgb = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
  // 1) piece.color var
  const has = info.rows.filter(r => NAMES.includes(r.color)).length; ok(has === 25, `1) ${has}/25 parçanın piece.color değeri var; dağılım ${JSON.stringify(info.counts)}`);
  // 2) kart: TÜM hücreler piece.color ile çiziliyor (kartta piece.color dışında tek bir opak piksel yok)
  const mono = info.rows.filter(r => r.card.length === 1 && r.card[0] === r.want.join(',') + ',255').length; ok(mono === 25, `2) ${mono}/25 kart tek renk: kart pikselleri == piece.color`);
  // 3) hedef renkleri bağımsız: piece.color hex'i hedef renkleri arasında yok; aynı baskın hedef rengine sahip parçalar farklı piece.color alabiliyor
  const noClash = info.rows.filter(r => r.tgt.every(t => t.toLowerCase() !== ({ orange: '#ff9f1c', blue: '#3b82f6', red: '#ef4444', green: '#2fb67c' })[r.color])).length;
  const dom = r => { const c = {}; r.tgt.forEach(t => c[t] = (c[t] || 0) + 1); return Object.keys(c).sort((a, z) => c[z] - c[a] || (a < z ? -1 : 1))[0]; };
  const groups = {}; info.rows.forEach(r => (groups[dom(r)] = groups[dom(r)] || new Set()).add(r.color)); const mixedGroup = Object.values(groups).some(s => s.size >= 2);
  const multiTarget = info.rows.filter(r => new Set(r.tgt).size >= 2).length; const paletteHexes = info.palette.map(x => x.toLowerCase()); const colourNotInImage = ['#ff9f1c', '#3b82f6', '#ef4444', '#2fb67c'].every(h => !paletteHexes.includes(h));
  ok(noClash === 25 && mixedGroup && colourNotInImage, `3) targetColorIndependent: ${noClash}/25 parçada hedef renkleri piece.color'dan farklı; aynı baskın hedef rengini taşıyan parçalar farklı piece.color alıyor (${mixedGroup}); ${multiTarget}/25 parçanın hedefi çok renkli`);
  // 4) yürüt: taşırken tek renk, yerleşince hedef resmin gerçek renkleri
  const hand = () => pg.evaluate(() => [...document.querySelectorAll('#hand .card')].map(b => ({ slot: +b.dataset.slot, id: b.dataset.piece })));
  let carryOK = 0, settleOK = 0, startHand = null; const startShot = [];
  for (let k = 0; k < WIN.length; k++) {
    await pg.waitForFunction(() => CBGAME.state().status === 'idle', { timeout: 60000 }); const h = await hand(); if (k === 0) { startHand = h; await pg.screenshot({ path: path.join(shots, 'c0_first_hand.png') }); }
    const slot = WIN[k], card = h.find(x => x.slot === slot); const pi = await pg.evaluate(id => CBGAME.level.pieces.findIndex(p => p.id === id), card.id);
    await pg.click('#slot' + slot); await pg.waitForTimeout(40); if (k === 3) await pg.screenshot({ path: path.join(shots, 'c1_preview.png') });
    await pg.click('#sendBtn'); await pg.waitForFunction(() => CBGAME.state().status === 'anim');
    const cargo = await pg.evaluate(() => CBGAME.workerCargo()), want = await pg.evaluate(pi => CBGAME.pieceColor(pi), pi), hex = { orange: '#ff9f1c', blue: '#3b82f6', red: '#ef4444', green: '#2fb67c' }[want];
    if (cargo.length > 0 && cargo.every(c => c.toLowerCase() === hex)) carryOK++;
    if (k === 3) { await pg.waitForTimeout(150); await pg.screenshot({ path: path.join(shots, 'c2_carry.png') }); }
    await pg.waitForFunction(() => CBGAME.state().status !== 'anim', { timeout: 60000 }); await pg.waitForTimeout(900);
    const cells = await pg.evaluate(pi => CBGAME.level.pieces[pi].cells, pi), tc = await pg.evaluate(pi => CBGAME.targetColors(pi), pi), px = await pg.evaluate(cs => cs.map(ti => CBGAME.cellPixel(ti)), cells);
    if (px.every((p, i) => p.join(',') === rgb(tc[i]).join(','))) settleOK++;
    if (k === 3) await pg.screenshot({ path: path.join(shots, 'c3_settled.png') });
  }
  ok(carryOK === 25, `taşınırken: ${carryOK}/25 parçada tüm işçi kutuları piece.color (tek renk)`);
  ok(settleOK === 25, `yerleşince: ${settleOK}/25 parçanın bütün hücreleri hedef resmin gerçek renklerinde (piksel okundu)`);
  const st = await pg.evaluate(() => CBGAME.state()); ok(st.status === 'won' && st.filled === st.n, 'kazanan dizi hâlâ kazanıyor: ' + st.filled + '/' + st.n);
  const first = startHand.map(x => info.rows.find(r => r.id === x.id).color); ok(first.length === 3 && new Set(first).size === 3, 'ilk el: ' + first.join(' · '));
  await pg.click('#parityBtn'); await pg.waitForTimeout(300); const m = (await pg.textContent('#modalBody')).match(/(\d+) \/ (\d+) vaka/); ok(m && m[1] === m[2], 'parity ' + m[0]); ok(errs.length === 0, 'console hatası yok ' + JSON.stringify(errs.slice(0, 3)));
  console.log(''); const allPass = has === 25 && mono === 25 && noClash === 25 && mixedGroup && colourNotInImage && carryOK === 25 && settleOK === 25;
  console.log('pieceColorMode: ' + (has === 25 && mono === 25 && carryOK === 25 && settleOK === 25 ? 'PASS' : 'FAIL')); console.log('25/25 monochrome pieces: ' + (mono === 25 && carryOK === 25 ? 'PASS' : 'FAIL')); console.log('targetColorIndependent: ' + (noClash === 25 && mixedGroup && colourNotInImage ? 'PASS' : 'FAIL'));
  await b.close(); console.log(fails || !allPass ? 'BAŞARISIZ' : 'TÜMÜ GEÇTİ'); process.exit(fails || !allPass ? 1 : 0);
})();

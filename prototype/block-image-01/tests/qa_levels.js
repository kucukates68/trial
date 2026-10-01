// node tests/qa_levels.js l02 → L02..L05 tarayıcı QA: kapsama, tek renk parça (veri/kart/hayalet/yerleşen/yük), tüm kartlar, kazanan+karışık dizi, tuzak → sealed, telefon
const { chromium } = require(process.env.PLAYWRIGHT_NODE || '/opt/node22/lib/node_modules/playwright'); const path = require('path'), fs = require('fs');
const ID = process.argv[2]; const HTML = 'file://' + path.resolve(__dirname, '..', 'dist', 'block-image-' + ID.toUpperCase() + '.html'), INFO = require('./level_info_' + ID + '.json'), SRC = fs.readFileSync(path.resolve(__dirname, '..', 'src', 'ui.js'), 'utf8');
const shots = path.resolve(__dirname, '_shots'); fs.mkdirSync(shots, { recursive: true });
let fails = 0; const ok = (c, m) => { console.log((c ? 'OK   ' : 'FAIL ') + m); if (!c) fails++; };
const near = (a, b, t) => Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]) + Math.abs(a[2] - b[2]) <= t;
const rgb = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
const idle = p => p.waitForFunction(() => ['idle', 'won', 'sealed', 'stuck'].includes(CBGAME.state().status), null, { timeout: 30000 });
const play = async (p, s) => { await p.evaluate(sl => CBGAME.select(sl), s); await p.evaluate(sl => CBGAME.select(sl), s); await p.waitForFunction(() => CBGAME.state().status !== 'anim', null, { timeout: 30000 }); };
async function fresh(b, vp) { const p = await b.newPage({ viewport: vp }); p.errs = []; p.on('pageerror', e => p.errs.push(String(e))); p.on('console', m => m.type() === 'error' && p.errs.push(m.text())); await p.goto(HTML); await p.waitForFunction(() => window.CBGAME); return p; }
(async () => {
  const b = await chromium.launch(); const p = await fresh(b, { width: 1280, height: 820 });
  const N = INFO.stats ? await p.evaluate(() => CBGAME.state().n) : 0, st0 = await p.evaluate(() => CBGAME.state()), NP = st0.pieces;
  const cov = await p.evaluate(() => { const L = CBGAME.level, c = new Uint8Array(L.n); L.pieces.forEach(pc => pc.cells.forEach(t => c[t]++)); let dup = 0, miss = 0; c.forEach(v => { if (v > 1) dup++; if (v === 0) miss++; }); return { dup, miss, n: L.n }; });
  ok(cov.dup === 0 && cov.miss === 0, ID + ': kapsama %100 · çift hedef 0 · eksik hedef 0 (' + cov.n + ' hücre, ' + NP + ' parça)');
  ok(!/ARTCOL|\.art\[|\['art'\]/.test(SRC) && !(await p.evaluate(() => 'art' in CBGAME.info.pieces[0])), 'piece.art yok / render kaynağı değil');
  const meta = await p.evaluate(() => CBGAME.info.pieces.map((pc, i) => ({ id: pc.id, color: pc.color, n: pc.cells.length, hex: CBGAME.pieceHex(i) })));
  ok(meta.every(m => typeof m.color === 'string' && /^#[0-9a-f]{6}$/i.test(m.hex)), NP + ' parçanın hepsinde tek piece.color'); ok(new Set(meta.map(m => m.color)).size < NP, 'doğal palet: ' + new Set(meta.map(m => m.color)).size + ' ad / ' + new Set(meta.map(m => m.hex)).size + ' hex (tüm parçalar farklı renk değil)');
  const cards = await p.evaluate(() => CBGAME.info.pieces.map((pc, i) => ({ id: pc.id, faces: CBGAME.cardFaces(i), hex: CBGAME.pieceHex(i) })));
  ok(cards.every(c => c.faces.length === 1 && near(c.faces[0].split(',').map(Number), rgb(c.hex), 6)), NP + '/' + NP + ' kart önizlemesi tek renk');
  const ghost = await p.evaluate(() => CBGAME.info.pieces.map((pc, i) => { const set = {}; CBGAME.level.pieces[i].cells.forEach(ti => set[CBGAME.cellPixel(ti).join(',')] = 1); return Object.keys(set).length; })); ok(ghost.every(n => n === 1), NP + '/' + NP + ' hayalet tek renk');
  // her kartın canvas render'ı: tüm kartları sırayla ele getir (kuyruk boyunca) — kazanan dizi sırasında kontrol
  let cardBad = [], allPrev = true, auditsOk = true, placedBad = [], cargoBad = [], seen = new Set(), cargoN = 0;
  for (let i = 0; i < INFO.win.length; i++) {
    await idle(p); const cardsNow = await p.evaluate(() => CBGAME.state().cards); cardsNow.forEach(c => c && seen.add(c));
    const fit = await p.evaluate(() => [...document.querySelectorAll('#hand .card')].filter(c => c.querySelector('canvas')).every(c => { const cv = c.querySelector('canvas'); const r = cv.getBoundingClientRect(); return r.width > 4 && r.height > 4 && r.width <= 140 && r.height <= 110; })); if (!fit) cardBad.push(i);
    const cardId = cardsNow[INFO.win[i]], pi = meta.findIndex(m => m.id === cardId);
    await p.evaluate(s => CBGAME.select(s), INFO.win[i]); const prev = await p.evaluate(() => CBGAME.previewCells());
    await p.evaluate(s => CBGAME.select(s), INFO.win[i]);
    if (i % 5 === 2) { await p.waitForTimeout(250); const cg = await p.evaluate(() => CBGAME.workerCargo()); cargoN++; if (!(cg.length > 0 && new Set(cg).size === 1 && cg[0].toLowerCase() === meta[pi].hex.toLowerCase())) cargoBad.push(cardId); }
    await p.waitForFunction(() => CBGAME.state().status !== 'anim', null, { timeout: 30000 });
    const dest = await p.evaluate(() => CBGAME.destCells()); if (JSON.stringify(prev) !== JSON.stringify(dest)) allPrev = false; auditsOk = auditsOk && await p.evaluate(() => CBGAME.handDiag().audit.ok);
    if (i < INFO.win.length - 1) { await p.waitForTimeout(760); const faces = await p.evaluate(ti => CBGAME.level.pieces[ti].cells.map(c => CBGAME.cellFace(c).join(',')), pi); if (!(new Set(faces).size === 1 && near(faces[0].split(',').map(Number), rgb(meta[pi].hex), 8))) placedBad.push(cardId); }
    if (i === Math.floor(INFO.win.length / 2)) await p.screenshot({ path: path.join(shots, ID + '_mid.png') });
  }
  const st = await p.evaluate(() => CBGAME.state()); ok(st.status === 'won' && st.filled === cov.n, 'kazanan dizi → ' + st.filled + '/' + cov.n + ' dolu, status=won'); ok(seen.size === NP, 'oyun boyunca ' + seen.size + '/' + NP + ' kartın hepsi elde göründü');
  ok(cardBad.length === 0, 'tüm el kartları render edildi ve kutuya sığdı'); ok(allPrev, 'önizleme = gerçek yerleşim (her hamle)'); ok(auditsOk, 'el/kuyruk muhasebesi (audit) tutarlı'); ok(placedBad.length === 0, 'yerleşen bloklar tek renk ' + JSON.stringify(placedBad.slice(0, 3))); ok(cargoBad.length === 0, 'işçi yükü tek renk (' + cargoN + ' örnek)');
  const fin = await p.evaluate(() => { const L = CBGAME.level, per = L.pieces.map(pc => new Set(pc.cells.map(ti => CBGAME.renderedFace(ti, false).join(','))).size), all = new Set(); for (let ti = 0; ti < L.n; ti++) all.add(CBGAME.renderedFace(ti, false).join(',')); return { per, d: all.size }; });
  ok(fin.per.every(n => n === 1), NP + '/' + NP + ' parçanın tüm blokları aynı render renginde (' + fin.d + ' farklı renk)'); await p.waitForTimeout(500); await p.screenshot({ path: path.join(shots, ID + '_won.png') });
  // karışık + ters kazanan diziler
  for (const [k, seq] of [['karışık', INFO.win_mixed], ['ters', INFO.win_reverse]]) { await p.evaluate(() => CBGAME.restart()); for (const s of seq) { await idle(p); await play(p, s); } await idle(p); const s2 = await p.evaluate(() => CBGAME.state()); ok(s2.status === 'won' && s2.filled === cov.n, k + ' kazanan dizi → won'); }
  // tuzak: en kısa kilitlenen yol → sealed
  await p.evaluate(() => CBGAME.restart()); for (const s of INFO.trap_seq) { await idle(p); await play(p, s); } await idle(p); await p.waitForTimeout(300); const ts = await p.evaluate(() => CBGAME.state()); ok(ts.status === 'sealed' || ts.status === 'stuck', 'tuzak yolu (' + INFO.trap_seq.length + ' hamle) → ' + ts.status); await p.screenshot({ path: path.join(shots, ID + '_trap.png') });
  await p.evaluate(() => CBGAME.restart()); ok((await p.evaluate(() => CBGAME.state())).status === 'idle', 'yeniden başlat çalışıyor');
  // telefon
  const p2 = await fresh(b, { width: 390, height: 844 }); for (let i = 0; i < 8; i++) { await idle(p2); await play(p2, INFO.win[i]); } await idle(p2); await p2.screenshot({ path: path.join(shots, ID + '_phone.png') });
  ok(await p2.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), 'telefonda yatay taşma yok'); const e = p.errs.concat(p2.errs); ok(e.length === 0, 'console hatası yok ' + JSON.stringify(e.slice(0, 2)));
  await b.close(); console.log(ID + ': ' + (fails ? 'BAŞARISIZ ' + fails : 'TÜMÜ GEÇTİ')); process.exit(fails ? 1 : 0);
})();

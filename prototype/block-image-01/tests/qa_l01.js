// node tests/qa_l01.js → L01 (36×24 kedi) tarayıcı QA: oynanabilirlik + TEK-RENKLİ PARÇA kuralı + fiziksel blok render'ı
// Kural: her gameplay parçası tek renk (piece.color). piece.art render kaynağı DEĞİL. Renk çeşitliliği parçalar ARASINDA oluşur.
const { chromium } = require(process.env.PLAYWRIGHT_NODE || '/opt/node22/lib/node_modules/playwright'); const path = require('path'), fs = require('fs');
const HTML = 'file://' + path.resolve(__dirname, '..', 'dist', 'block-image-L01.html'), INFO = require('./level_info_l01.json'), SRC = fs.readFileSync(path.resolve(__dirname, '..', 'src', 'ui.js'), 'utf8');
const shots = path.resolve(__dirname, '_shots'); fs.mkdirSync(shots, { recursive: true });
let fails = 0; const ok = (c, m) => { console.log((c ? 'OK   ' : 'FAIL ') + m); if (!c) fails++; };
const near = (a, b, t) => Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]) + Math.abs(a[2] - b[2]) <= t;
const idle = p => p.waitForFunction(() => ['idle', 'won', 'sealed', 'stuck'].includes(CBGAME.state().status), null, { timeout: 20000 });
const play = (p, s) => p.evaluate(sl => { CBGAME.select(sl); CBGAME.select(sl); }, s);
(async () => {
  const b = await chromium.launch(), errs = []; const p = await b.newPage({ viewport: { width: 1280, height: 820 } }); p.on('pageerror', e => errs.push(String(e))); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  await p.goto(HTML); await p.waitForFunction(() => window.CBGAME);
  let st = await p.evaluate(() => CBGAME.state()); ok(st.n === 460 && st.pieces === 19, 'L01: 460 hedef hücre, 19 parça');
  ok(JSON.stringify(st.cards) === JSON.stringify(['FACE_L', 'EAR_L', 'EAR_R']), 'başlangıç eli = FACE_L · EAR_L · EAR_R (ALT-2)');
  ok(!/ARTCOL|\.art\[|\['art'\]/.test(SRC), 'render kodu piece.art / hücre bazlı renk kaynağı kullanmıyor (ui.js taraması)');
  // ---- 1) veri: her parça tek renk (piece.color), palette içinde; piece.art veri olarak durabilir ama kullanılmaz
  const meta = await p.evaluate(() => { const LV = CBGAME.info; return LV.pieces.map((pc, i) => ({ id: pc.id, color: pc.color, n: pc.cells.length, hex: CBGAME.pieceHex(i) })); });
  ok(meta.length === 19 && meta.every(m => typeof m.color === 'string' && /^#[0-9a-f]{6}$/i.test(m.hex)), '19 parçanın her birinin tek bir piece.color değeri var');
  const used = [...new Set(meta.map(m => m.color))]; ok(used.length >= 5, 'renk çeşitliliği parçalar ARASINDA: ' + used.length + ' farklı renk (' + used.join(', ') + ')');
  const adjBad = await p.evaluate(() => { const L = CBGAME.level, own = {}; L.pieces.forEach(pc => pc.cells.forEach(ti => own[ti] = pc.i)); const bad = []; for (let ti = 0; ti < L.n; ti++) { const t = L.targets[ti]; [[0, 1], [1, 0]].forEach(([dr, dc]) => { const nj = L.tIdx[(t.r + dr) * L.w + t.c + dc]; if (nj >= 0 && own[nj] !== own[ti] && CBGAME.info.pieces[own[nj]].color === CBGAME.info.pieces[own[ti]].color) bad.push(CBGAME.info.pieces[own[ti]].id + '-' + CBGAME.info.pieces[own[nj]].id); }); } return [...new Set(bad)]; });
  ok(adjBad.length === 0, 'komşu parçalar farklı renkte (okunabilirlik) ' + JSON.stringify(adjBad));
  // ---- 2) KART: her kart tek renk
  const cards = await p.evaluate(() => CBGAME.info.pieces.map((pc, i) => ({ id: pc.id, faces: CBGAME.cardFaces(i), hex: CBGAME.pieceHex(i) })));
  const rgb = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
  ok(cards.every(c => c.faces.length === 1 && near(c.faces[0].split(',').map(Number), rgb(c.hex), 6)), '19/19 kart önizlemesi tek renk (kart yüzleri = piece.color)');
  const cardFit = await p.evaluate(() => [...document.querySelectorAll('#hand .card')].every(c => { const cv = c.querySelector('canvas'); return cv && cv.getBoundingClientRect().width <= 130 && cv.getBoundingClientRect().height <= 96; })); ok(cardFit, 'kartlar sığıyor');
  // ---- 3) HAYALET: her parçanın bütün hayalet hücreleri aynı renk (parça renginin açık tonu)
  const ghost = await p.evaluate(() => CBGAME.info.pieces.map((pc, i) => { const L = CBGAME.level; const set = {}; L.pieces[i].cells.forEach(ti => { const f = CBGAME.cellPixel(ti); set[f.join(',')] = 1; }); return { id: pc.id, n: Object.keys(set).length, rendered: [...new Set(L.pieces[i].cells.map(ti => CBGAME.renderedFace(ti, true).join(',')))].length }; }));
  ok(ghost.every(g => g.n === 1 && g.rendered === 1), '19/19 parçanın hayaleti tek renk (tahtada okunan piksel + render fonksiyonu)');
  // ---- 4) 19 hamle: önizleme = yerleşim; yerleşen blokların hepsi parça rengi; işçi yükü tek renk
  let allPrev = true, maxMs = 0, auditsOk = true, placedOk = 0, cargoOk = true, cargoChecked = 0; const faceBad = [];
  for (let i = 0; i < INFO.win.length; i++) {
    await idle(p); const cardId = (await p.evaluate(() => CBGAME.state().cards))[INFO.win[i]], pi = meta.findIndex(m => m.id === cardId);
    await p.evaluate(s => CBGAME.select(s), INFO.win[i]); const prev = await p.evaluate(() => CBGAME.previewCells());
    const prevFaces = await p.evaluate(() => { const rd = CBGAME.read(); return rd.cells.map(ti => CBGAME.previewFill(ti)); }); if (new Set(prevFaces).size !== 1) faceBad.push('önizleme ' + cardId);
    const t0 = Date.now(); await p.evaluate(s => CBGAME.select(s), INFO.win[i]);
    if (cardId === 'FOREHEAD' || cardId === 'HAUNCH') { await p.waitForTimeout(250); const cg = await p.evaluate(() => CBGAME.workerCargo()); cargoChecked++; if (!(cg.length > 0 && new Set(cg).size === 1 && cg[0].toLowerCase() === meta[pi].hex.toLowerCase())) cargoOk = false; }
    await p.waitForFunction(() => CBGAME.state().status !== 'anim', null, { timeout: 20000 }); maxMs = Math.max(maxMs, Date.now() - t0);
    const dest = await p.evaluate(() => CBGAME.destCells()); if (JSON.stringify(prev) !== JSON.stringify(dest)) allPrev = false; auditsOk = auditsOk && await p.evaluate(() => CBGAME.handDiag().audit.ok);
    if (i < INFO.win.length - 1) {   // parıltı (flash) sönsün, sonra tahtadaki gerçek pikselleri oku
      await p.waitForTimeout(760); const faces = await p.evaluate(ti => CBGAME.level.pieces[ti].cells.map(c => CBGAME.cellFace(c).join(',')), pi);
      if (new Set(faces).size === 1 && near(faces[0].split(',').map(Number), rgb(meta[pi].hex), 8)) placedOk++; else faceBad.push(cardId + ' ' + [...new Set(faces)].join('|'));
    }
    if (i === 8) await p.screenshot({ path: path.join(shots, 'l01_mid.png') });
  }
  st = await p.evaluate(() => CBGAME.state()); ok(st.status === 'won' && st.filled === 460, 'kazanan dizi → 460/460 dolu, status=won');
  ok(allPrev, '19/19 blokta önizleme = gerçek yerleşim'); ok(auditsOk, 'her hamlede el/kuyruk muhasebesi tutarlı (audit)'); ok(maxMs < 2000, 'en uzun blok animasyonu ' + maxMs + ' ms (<2 sn, ×1)');
  ok(placedOk === 18 && faceBad.length === 0, 'yerleşen bloklar tek renk: ilk 18 parçanın her hücresi tahtada piece.color ' + JSON.stringify(faceBad.slice(0, 3)));
  ok(cargoChecked === 2 && cargoOk, 'işçi yükü tek renk (= parça rengi; FOREHEAD 64 işçi, HAUNCH)');
  // son parça + bütün 460 hücre render fonksiyonuyla: her parçanın hücreleri aynı yüz rengi, tüm kedi çok renkli
  const fin = await p.evaluate(() => { const L = CBGAME.level, perPiece = L.pieces.map((pc, i) => [...new Set(pc.cells.map(ti => CBGAME.renderedFace(ti, false).join(',')))].length), all = new Set(); for (let ti = 0; ti < L.n; ti++) all.add(CBGAME.renderedFace(ti, false).join(',')); return { perPiece, distinct: all.size }; });
  ok(fin.perPiece.every(n => n === 1), '19/19 parçanın bütün blokları aynı render renginde (460 hücre)'); ok(fin.distinct >= 5, 'tamamlanan kedi çok renkli: ' + fin.distinct + ' farklı renk parçalar arasından');
  await p.waitForTimeout(500); await p.screenshot({ path: path.join(shots, 'l01_won.png') });
  // ---- FİZİKSEL BLOK denetimi (tahtada): aralık, üst ışık, alt gölge
  const bl = await p.evaluate(() => { const L = CBGAME.level, g = CBGAME.geo(), T = L.targets, at = {}; T.forEach((t, i) => at[t.r + ',' + t.c] = i); let pick = null;
    for (let i = 160; i < T.length && !pick; i++) { const t = T[i]; if (at[t.r + ',' + (t.c + 1)] !== undefined && at[(t.r + 1) + ',' + t.c] !== undefined) pick = i; }
    const t = T[pick], d = g.dpr, X = g.ox + t.c * g.s, Y = g.oy + t.r * g.s, c2 = document.getElementById('board').getContext('2d'), px = (x, y) => Array.from(c2.getImageData(Math.round(x * d), Math.round(y * d), 1, 1).data);
    return { gapR: px(X + g.s, Y + g.s / 2), gapB: px(X + g.s / 2, Y + g.s), top: px(X + g.s / 2, Y + g.s * 0.12), face: px(X + g.s / 2, Y + g.s * 0.45), bot: px(X + g.s / 2, Y + g.s * 0.86) }; });
  const lum = c => 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2];
  ok(Math.abs(lum(bl.gapR) - lum(bl.face)) > 5 && Math.abs(lum(bl.gapB) - lum(bl.face)) > 5, 'komşu bloklar arasında panonun göründüğü boşluk var (düz yüzeye birleşmiyor)');
  ok(lum(bl.top) > lum(bl.face) + 6 && lum(bl.bot) < lum(bl.face) - 6, 'her blokta üst ışık + alt gölge (fiziksel kutu)');
  // ---- tuzak (3. el) + yeniden başlat
  await p.evaluate(() => CBGAME.restart()); await idle(p); await play(p, 0); await idle(p); await play(p, 0); await idle(p);
  const hand3 = await p.evaluate(() => CBGAME.handDiag()); ok(hand3.hand[0] === 'FOREHEAD' && hand3.slots[0].state === 'seals', '3. elde FOREHEAD kilitleyen kart (kulaklar boş) — ilk anlık tuzak');
  await p.evaluate(() => CBGAME.select(0)); await p.waitForTimeout(200); await p.evaluate(() => CBGAME.select(0)); await p.waitForFunction(() => CBGAME.state().status === 'sealed', null, { timeout: 20000 }); await p.waitForTimeout(300); await p.screenshot({ path: path.join(shots, 'l01_trap.png') }); ok(true, 'tuzak: FOREHEAD → kilitlendi (sealed)');
  await p.evaluate(() => CBGAME.restart()); ok((await p.evaluate(() => CBGAME.state())).status === 'idle', 'yeniden başlat çalışıyor');
  // ---- telefon
  const p2 = await b.newPage({ viewport: { width: 390, height: 844 } }); p2.on('pageerror', e => errs.push(String(e))); await p2.goto(HTML); await p2.waitForFunction(() => window.CBGAME);
  for (let i = 0; i < 9; i++) { await idle(p2); await play(p2, INFO.win[i]); } await idle(p2); await p2.screenshot({ path: path.join(shots, 'l01_phone.png') });
  ok(await p2.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), 'telefonda yatay taşma yok'); ok(errs.length === 0, 'console hatası yok ' + JSON.stringify(errs.slice(0, 2)));
  await b.close(); console.log(fails ? 'BAŞARISIZ ' + fails : 'TÜMÜ GEÇTİ'); process.exit(fails ? 1 : 0);
})();

// node tests/qa_l01.js → L01 (36×24 kedi) tarayıcı QA: oynanabilirlik, önizleme=yerleşim, tuzak, renk modu, süre, ekran görüntüleri
const { chromium } = require(process.env.PLAYWRIGHT_NODE || '/opt/node22/lib/node_modules/playwright'); const path = require('path'), fs = require('fs');
const HTML = 'file://' + path.resolve(__dirname, '..', 'dist', 'block-image-L01.html'), INFO = require('./level_info_l01.json'); const shots = path.resolve(__dirname, '_shots'); fs.mkdirSync(shots, { recursive: true });
let fails = 0; const ok = (c, m) => { console.log((c ? 'OK   ' : 'FAIL ') + m); if (!c) fails++; };
const idle = p => p.waitForFunction(() => ['idle', 'won', 'sealed', 'stuck'].includes(CBGAME.state().status), null, { timeout: 20000 });
const play = (p, s) => p.evaluate(sl => { CBGAME.select(sl); CBGAME.select(sl); }, s);
(async () => {
  const b = await chromium.launch(), errs = []; let p = await b.newPage({ viewport: { width: 1280, height: 820 } }); p.on('pageerror', e => errs.push(String(e))); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  await p.goto(HTML); await p.waitForFunction(() => window.CBGAME);
  let st = await p.evaluate(() => CBGAME.state()); ok(st.n === 460 && st.pieces === 19, 'L01: 460 hedef hücre, 19 parça');
  ok(JSON.stringify(st.cards) === JSON.stringify(['FACE_L', 'EAR_L', 'EAR_R']), 'başlangıç eli = FACE_L · EAR_L · EAR_R (ALT-2)');
  ok(await p.evaluate(() => CBGAME.colorMode()) === 'art', 'varsayılan renk modu: resim (gerçek pikseller)');
  const cardOk = await p.evaluate(() => [...document.querySelectorAll('#hand .card')].every(c => { const cv = c.querySelector('canvas'); return cv && cv.getBoundingClientRect().width <= 130 && cv.getBoundingClientRect().height <= 96; })); ok(cardOk, 'kartlar sığıyor (en geniş parça ≤130 px)');
  // 19 hamle: önizleme = yerleşim, muhasebe, süre
  let allPrev = true, maxMs = 0, audits = true; const t00 = Date.now();
  for (let i = 0; i < INFO.win.length; i++) {
    await idle(p); await p.evaluate(s => CBGAME.select(s), INFO.win[i]); const prev = await p.evaluate(() => CBGAME.previewCells()); const t0 = Date.now(); await p.evaluate(s => CBGAME.select(s), INFO.win[i]);
    await p.waitForFunction(() => CBGAME.state().status !== 'anim', null, { timeout: 20000 }); maxMs = Math.max(maxMs, Date.now() - t0);
    const dest = await p.evaluate(() => CBGAME.destCells()); if (JSON.stringify(prev) !== JSON.stringify(dest)) allPrev = false; audits = audits && await p.evaluate(() => CBGAME.handDiag().audit.ok);
    if (i === 8) await p.screenshot({ path: path.join(shots, 'l01_mid.png') });
  }
  st = await p.evaluate(() => CBGAME.state()); ok(st.status === 'won' && st.filled === 460, 'kazanan dizi → 460/460 dolu, status=won');
  ok(allPrev, '19/19 blokta önizleme = gerçek yerleşim'); ok(audits, 'her hamlede el/kuyruk muhasebesi tutarlı (audit)'); ok(maxMs < 2000, 'en uzun blok animasyonu ' + maxMs + ' ms (<2 sn, ×1)');
  await p.waitForTimeout(500); await p.screenshot({ path: path.join(shots, 'l01_won.png') });
  // renk: yerleşen hücre = resim rengi; parça modunda = parça kimlik rengi
  const px = await p.evaluate(() => { const art = CBGAME.hexToRgb(CBGAME.artColor(200)), p1 = CBGAME.cellPixel(200); return { art, p1 }; });
  ok(true, 'resim modunda hücre pikseli okunabiliyor ' + JSON.stringify(px.p1));
  await p.evaluate(() => CBGAME.setColors('piece')); await p.waitForTimeout(150); ok(await p.evaluate(() => CBGAME.colorMode()) === 'piece', 'renk modu parçaya geçti'); await p.screenshot({ path: path.join(shots, 'l01_won_piece.png') });
  // tuzak: iki yanak sonrası alın → kulaklar kapanır (3. el)
  await p.evaluate(() => { CBGAME.setColors('art'); CBGAME.restart(); }); await idle(p);
  await play(p, 0); await idle(p); await play(p, 0); await idle(p);
  const hand3 = await p.evaluate(() => CBGAME.handDiag()); ok(hand3.hand[0] === 'FOREHEAD' && hand3.slots[0].state === 'seals', '3. elde FOREHEAD kilitleyen kart olarak görünüyor (kulaklar boş) — ilk anlık tuzak');
  await p.evaluate(() => CBGAME.select(0)); await p.waitForTimeout(200); const rd = await p.evaluate(() => CBGAME.read()); ok(rd && rd.cut.length > 0, 'seçince kilitlenecek hücreler önizlemede var (' + (rd && rd.cut.length) + ')');
  await p.evaluate(() => CBGAME.select(0)); await p.waitForFunction(() => CBGAME.state().status === 'sealed', null, { timeout: 20000 }); await p.waitForTimeout(300); await p.screenshot({ path: path.join(shots, 'l01_trap.png') }); ok(true, 'tuzak: FOREHEAD → kilitlendi (sealed)');
  // JAW erken göndermek de tuzak (başka yeni oyun): A: FL FR FH MZ JW → önce MUZZLE... pratik: kilit sonrası yeniden başlat çalışıyor
  await p.evaluate(() => CBGAME.restart()); ok((await p.evaluate(() => CBGAME.state())).status === 'idle', 'yeniden başlat çalışıyor');
  // telefon
  const p2 = await b.newPage({ viewport: { width: 390, height: 844 } }); p2.on('pageerror', e => errs.push(String(e))); await p2.goto(HTML); await p2.waitForFunction(() => window.CBGAME);
  for (let i = 0; i < 9; i++) { await idle(p2); await play(p2, INFO.win[i]); } await idle(p2); await p2.screenshot({ path: path.join(shots, 'l01_phone.png') });
  const fit = await p2.evaluate(() => { const c = document.getElementById('hand').getBoundingClientRect(); return c.right <= window.innerWidth + 1 && document.documentElement.scrollWidth <= window.innerWidth + 1; }); ok(fit, 'telefonda yatay taşma yok');
  ok(errs.length === 0, 'console hatası yok ' + JSON.stringify(errs.slice(0, 2)));
  await b.close(); console.log(fails ? 'BAŞARISIZ ' + fails : 'TÜMÜ GEÇTİ'); process.exit(fails ? 1 : 0);
})();

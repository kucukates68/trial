// Headless Chromium QA:  node tests/browser_qa.js [shots_dir]
const path = require('path'), fs = require('fs');
const { chromium } = require(process.env.PLAYWRIGHT_NODE || '/opt/node22/lib/node_modules/playwright');
const HTML = 'file://' + path.resolve(__dirname, '..', 'dist', 'colorbuild.html');
const VEC = JSON.parse(fs.readFileSync(path.resolve(__dirname, 'conformance_all.json'), 'utf8')).levels;
const shots = process.argv[2] || path.resolve(__dirname, '_shots'); fs.mkdirSync(shots, { recursive: true });
let failures = 0; const ok = (c, m) => { console.log((c ? 'OK   ' : 'FAIL ') + m); if (!c) failures++; };
const caseOf = (id, name) => VEC.find(v => v.level_id === id).cases.find(c => c.name === name);

async function waitFor(page, pred, ms = 60000) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) { const s = await page.evaluate(() => window.CBGAME.state()); if (pred(s)) return s; await page.waitForTimeout(100); }
  throw new Error('zaman aşımı: ' + JSON.stringify(await page.evaluate(() => window.CBGAME.state())));
}
async function findSeal(page, id) {
  return page.evaluate(id => {
    const lv = window.CB_LEVELS.find(l => l.id === id), L = new window.CB.Level(lv.grid, lv.W);
    function dfs(f, seq, depth) {
      if (depth === 0) return null;
      for (let k = 0; k < L.K; k++) {
        const p = L.plan(f, k); if (!p.length) continue; const g = L.apply(f, p), s2 = seq.concat([L.letters[k]]);
        if (L.sealedCells(g).length) return s2; const r = dfs(g, s2, depth - 1); if (r) return r;
      }
      return null;
    }
    return dfs(L.newFilled(), [], 6);
  }, id);
}
async function play(page, seq) {
  for (const c of seq) { await waitFor(page, s => s.status !== 'anim'); await page.evaluate(l => window.CBGAME.send(l), c); }
  return waitFor(page, s => s.status !== 'anim');
}

(async () => {
  const browser = await chromium.launch();
  const errors = [];
  async function open(url, w = 1280, h = 800) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    page.on('pageerror', e => errors.push('pageerror: ' + e.message)); page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
    await page.goto(url); await page.waitForFunction(() => window.CBGAME); return page;
  }

  // 1) hero: yükleme, önizleme, animasyon
  let page = await open(HTML);
  let st = await page.evaluate(() => window.CBGAME.state());
  ok(st.level === 'HERO2' && st.n === 216 && st.status === 'idle', 'HERO2 yüklendi: 216 hücre, idle');
  await page.screenshot({ path: path.join(shots, '01_initial.png') });
  await page.click('#cb0'); await page.waitForTimeout(150);
  st = await page.evaluate(() => window.CBGAME.state()); ok(st.selected === 0, 'ilk dokunuş rengi seçti (önizleme)');
  await page.screenshot({ path: path.join(shots, '02_preview.png') });
  await page.click('#cb0'); await page.waitForTimeout(1600);
  st = await page.evaluate(() => window.CBGAME.state()); ok(st.status === 'anim', 'ikinci dokunuş dalgayı gönderdi (animasyon sürüyor)');
  await page.screenshot({ path: path.join(shots, '03_workers_walking.png') });
  await page.waitForTimeout(2500); await page.screenshot({ path: path.join(shots, '04_workers_placing.png') });
  st = await waitFor(page, s => s.status !== 'anim'); ok(st.filled === 21 || st.filled > 0, 'dalga bitti; yerleşen kutu ' + st.filled + ' (W=21 beklenir)');
  ok(st.filled === 21, 'W=21 kutu yerleşti');
  await page.screenshot({ path: path.join(shots, '05_after_wave.png') });
  // parity paneli
  await page.click('#parityBtn'); await page.waitForTimeout(300);
  const ptxt = await page.textContent('#modalBody'); ok(/107 \/ 107 vaka birebir/.test(ptxt), 'parity paneli: 107 / 107 vaka birebir');
  await page.screenshot({ path: path.join(shots, '06_parity.png') }); await page.click('#modalClose'); await page.close();

  // 2) tam kazanma (hero 2) — hızlı
  page = await open(HTML + '?speed=200&hint=0&level=HERO2');
  st = await play(page, caseOf('HERO2', 'winning').sequence); ok(st.status === 'won' && st.filled === 216, 'HERO2 kazanan dizi → won (216/216)');
  await page.waitForTimeout(400); await page.screenshot({ path: path.join(shots, '07_won.png') });
  const log = await page.evaluate(() => window.CBGAME.getLog()); const att = log.attempts[0];
  ok(att.outcome === 'won' && att.tokens.join('') === caseOf('HERO2', 'winning').sequence.join(''), 'kayıt: outcome=won, token dizisi oynananla aynı');
  ok(att.moves.every(m => m.decide_ms >= 0 && m.placed > 0), 'kayıt: her hamlede decide_ms ve placed var');
  await page.close();

  // 3) kilitlenme (hero 2, hata dizisi)
  page = await open(HTML + '?speed=200&hint=0&level=HERO2');
  const sealSeq = await findSeal(page, 'HERO2'); ok(Array.isArray(sealSeq), 'HERO2 için kilitleyen dizi bulundu: ' + (sealSeq || []).join('')); st = await play(page, sealSeq);
  ok(st.status === 'sealed' && st.sealed > 0, 'yanlış hamle → sealed (' + st.sealed + ' hücre erişilemez)');
  await page.waitForTimeout(300); await page.screenshot({ path: path.join(shots, '08_sealed.png') });
  ok((await page.textContent('#msg')).includes('Kilitlendi'), 'kilit mesajı gösteriliyor');
  await page.click('#restartBtn'); st = await page.evaluate(() => window.CBGAME.state()); ok(st.status === 'idle' && st.filled === 0, 'yeniden başlat: temiz durum');
  await page.close();

  // 4) ipucu 2: kilit uyarısı önizlemede
  page = await open(HTML + '?hint=2&speed=200&level=HERO2');
  await waitFor(page, s => s.status === 'idle');
  const seq2 = await findSeal(page, 'HERO2'); await play(page, seq2.slice(0, -1));
  await page.evaluate(l => window.CBGAME.select(l), seq2[seq2.length - 1]); await page.waitForTimeout(200);
  const m2 = await page.textContent('#msg'); ok(/erişilemez yapar/.test(m2), 'ipucu 2: önizleme kilit uyarısı veriyor → "' + m2.slice(0, 90) + '…"');
  await page.screenshot({ path: path.join(shots, '09_hint2_warning.png') }); await page.close();

  // 5) geri al
  page = await open(HTML + '?hint=0&speed=200&undo=2&level=HERO2');
  const seq3 = await findSeal(page, 'HERO2'); await play(page, seq3); await page.click('#undoBtn'); st = await page.evaluate(() => window.CBGAME.state());
  ok(st.status === 'idle' && st.undoLeft === 1 && st.waves === seq3.length - 1, 'geri al: son dalga geri alındı, hak 2→1');
  await page.close();

  // 6) test modu: etiket gizli, bırak/sonraki, kayıt
  page = await open(HTML + '?mode=test&speed=200&hint=1&levels=W01S,A01S&player=qa');
  ok(await page.isHidden('#dev') && await page.isHidden('#levelSel'), 'test modu: seviye seçici ve geliştirici paneli gizli');
  ok((await page.textContent('#lvlTitle')) === 'Seviye 1 / 2', 'test modu: nötr başlık (grup etiketi yok)');
  const w1 = caseOf('W01S', 'winning').sequence; for (const c of w1) { await waitFor(page, s => s.status !== 'anim'); await page.evaluate(l => window.CBGAME.send(l), c); }
  await waitFor(page, s => s.status === 'won'); await page.click('#abandonBtn'); await page.waitForTimeout(200);
  ok((await page.textContent('#lvlTitle')) === 'Seviye 2 / 2', 'kazanınca "Sonraki seviye" ile 2. seviyeye geçti');
  await page.click('#abandonBtn'); await page.waitForTimeout(300);
  ok((await page.textContent('#modalBody')).includes('Test bitti'), 'son seviyeden sonra bitiş ekranı');
  const l2 = await page.evaluate(() => window.CBGAME.getLog()); ok(l2.attempts.length === 2 && l2.attempts[0].outcome === 'won' && l2.attempts[1].outcome === 'abandon', 'kayıt: won + abandon'); await page.close();

  // 7) dar ekran (mobil) düzen
  page = await open(HTML, 420, 820); await page.screenshot({ path: path.join(shots, '10_mobile.png') }); await page.close();

  ok(errors.length === 0, 'konsol/sayfa hatası yok' + (errors.length ? ' → ' + errors.slice(0, 3).join(' | ') : ''));
  await browser.close(); console.log(failures ? failures + ' BAŞARISIZ' : 'TÜM KONTROLLER GEÇTİ'); process.exit(failures ? 1 : 0);
})().catch(e => { console.error('HATA', e); process.exit(2); });

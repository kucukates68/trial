// node tests/qa_hand.js → EL / KUYRUK tutarlılığı + yasal seçenek denetimi + çözücü↔UI (motor) eşleşmesi
global.self = global; const BI = require('../src/engine.js'), fs = require('fs'); const info = JSON.parse(fs.readFileSync(__dirname + '/level_info.json'));
global.window = {}; eval(fs.readFileSync(__dirname + '/../src/level.js', 'utf8')); const LV = window.BI_LEVEL, L = new BI.Level(LV.grid, LV.pieces, LV.hand);
const N = LV.pieces.length, res = []; const rep = (name, ok, extra) => { res.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (extra ? '  — ' + extra : '')); };
const key = st => Buffer.from(st.filled).toString('hex') + '|' + st.ptr.join(',');
// 1) bütün ulaşılabilir durumlar (her yasal hamle): muhasebe + el=kuyruk başı + çıkmaz taraması
const seen = new Map(); let audits = 0, auditBad = [], dead = [], doomed = [], emptyWithQueue = 0, minCont = 9, maxDepth = 0;
const win = new Map(); // durum → kazanılabilir mi (kesin DP)
function rec(st) {
  const k = key(st); if (win.has(k)) return win.get(k);
  const a = L.audit(st); audits++; if (!a.ok) auditBad.push(a.errors[0]); if (a.remaining !== N - L.hand.reduce((s, q, i) => s + st.ptr[i], 0)) auditBad.push('kalan');
  L.cards(st).forEach((c, s) => { if (c === null && st.ptr[s] < L.hand[s].length) emptyWithQueue++; });
  const d = L.diagnose(st); let w = false;
  d.slots.forEach(x => { if (x.state === 'blocked' && L.cards(st)[x.slot] === null) auditBad.push('boş+illegal karışımı'); });
  for (let s = 0; s < 3; s++) { const c = L.cards(st)[s]; if (c === null || !L.options(st)[s]) continue; const r = L.place(st, s); if (r.won) w = true; else if (!r.sealed.length && !r.stuck) { if (rec(r.state)) w = true; } }
  win.set(k, w); if (!w) doomed.push(k); if (d.deadlock) dead.push(k); if (!d.deadlock) minCont = Math.min(minCont, d.continuable);
  return w;
}
const rootWin = rec(L.newState());
rep('25/25 piece accounting', auditBad.length === 0 && audits > 100, audits + ' ulaşılabilir durumda kalan = ' + N + ' − gönderilen; her parça tam 1 kuyrukta/elde');
const ids = LV.hand.flat(); rep('no missing piece', new Set(ids).size === N && LV.pieces.every(p => ids.includes(p.id)), ids.length + ' kuyruk girişi / ' + N + ' parça');
rep('no duplicate piece', ids.length === new Set(ids).size);
rep('hand/queue consistency', auditBad.length === 0 && emptyWithQueue === 0, 'el = kuyruk başı; slot yalnız kuyruğu bitince boş (' + emptyWithQueue + ' ihlal)');
rep('LEGAL OPTION CHECK: ulaşılabilir hiçbir durumda çıkmaz/kayıp-durum yok', rootWin && dead.length === 0 && doomed.length === 0, 'çıkmaz ' + dead.length + ', kazanılamaz ulaşılabilir durum ' + doomed.length + ', en az devam ettirilebilir kart sayısı ' + minCont);
// 2) çözücü kazanan dizileri: motor eli = kuyruk başı, her adım yasal, sonunda kazanır
let okSeq = true, detail = [];
for (const name of ['win', 'win_mixed']) {
  let st = L.newState(), won = false;
  info[name].forEach((slot, i) => {
    const exp = L.hand.map((q, s) => st.ptr[s] < q.length ? L.pieces[q[st.ptr[s]]].id : null), a = L.audit(st);
    if (JSON.stringify(a.ids) !== JSON.stringify(exp) || !a.ok || !L.options(st)[slot]) { okSeq = false; detail.push(name + '@' + i); return; }
    const r = L.place(st, slot); st = r.state; if (r.won) won = true; if (r.sealed.length || r.stuck) okSeq = false;
  }); if (!won) okSeq = false;
}
rep('solver/UI parity', okSeq && JSON.stringify(info.hand) === JSON.stringify(LV.hand), 'kazanan diziler (win, win_mixed) 25 adımda el=kuyruk başı, yasal, kazanır ' + detail.join(','));
console.log(res.every(Boolean) ? 'HEPSİ GEÇTİ' : 'BAŞARISIZ'); process.exit(res.every(Boolean) ? 0 : 1);

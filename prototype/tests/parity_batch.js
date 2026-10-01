// node tests/parity_batch.js  → engine.js DLevel ↔ tools/batch_ref.py (literal hücre-hücre referans) vektörleri
global.self = global; const CB = require('../src/engine.js'), V = require('./image_vectors.json'); let ok = 0, tot = 0;
for (const lv of V.levels) {
  const L = new CB.DLevel(lv.grid, lv.batch.zones, lv.batch.hand);
  for (const c of lv.cases) { tot++; const t0 = Date.now(), sim = L.simulate(c.sequence), same = JSON.stringify(sim) === JSON.stringify(c.expected); if (same) ok++; else console.log('FARKLI', lv.level_id, c.name); console.log((same ? 'OK   ' : 'FAIL '), lv.level_id, c.name, 'adım', sim.length, Date.now() - t0, 'ms'); }
}
console.log(ok + ' / ' + tot + ' vaka birebir'); process.exit(ok === tot ? 0 : 1);

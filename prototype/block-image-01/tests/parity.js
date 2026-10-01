// node tests/parity.js  → src/engine.js ↔ tools/ref.py vektörleri
global.self = global; const BI = require('../src/engine.js'), V = require(process.argv[2] ? require('path').resolve(process.argv[2]) : './vectors.json'); let ok = 0, tot = 0;
for (const lv of V) { const L = new BI.Level(lv.grid, lv.pieces, lv.hand);
  for (const c of lv.cases) { tot++; const sim = L.simulate(c.sequence), same = JSON.stringify(sim) === JSON.stringify(c.expected); if (same) ok++; console.log(same ? 'OK   ' : 'FAIL ', lv.level_id, c.name, 'adım', sim.length); } }
console.log(ok + ' / ' + tot + ' vaka birebir'); process.exit(ok === tot ? 0 : 1);

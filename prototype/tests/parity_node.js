// Prototip çekirdeğini solver test vektörleriyle çalıştırır ve parity.py'nin beklediği iz biçiminde yazar.
//   node tests/parity_node.js <vectors.json> <out_traces.json>
const fs = require('fs'), path = require('path');
const CB = require(path.join(__dirname, '..', 'src', 'engine.js'));
const vec = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const traces = vec.levels.map(function (lv) {
  const L = new CB.Level(lv.grid, lv.W);
  return { level_id: lv.level_id, cases: lv.cases.map(function (c) { return { name: c.name, moves: L.simulate(c.sequence) }; }) };
});
fs.writeFileSync(process.argv[3], JSON.stringify({ traces: traces }));
console.log('izler yazıldı:', process.argv[3], '| seviye', traces.length, '| vaka', traces.reduce(function (a, t) { return a + t.cases.length; }, 0));

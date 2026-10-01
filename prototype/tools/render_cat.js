// node tools/render_cat.js → tools/cat_cells.json (NxN dolu-piksel maskesi + renk) + tests/_shots/cat_art.png (8x büyütülmüş önizleme). Tek kaynak: src/cat_art.js
const fs = require('fs'), path = require('path'), vm = require('vm');
const ctx = { self: {}, window: {} }; vm.createContext(ctx); vm.runInContext(fs.readFileSync(path.resolve(__dirname, '../src/cat_art.js'), 'utf8'), ctx);
const A = ctx.self.CB_ART, px = A.pixels(), N = px.N;
const cells = Array.from(px.idx, (v) => (v ? v : 0));
fs.writeFileSync(path.resolve(__dirname, 'cat_cells.json'), JSON.stringify({ N, idx: Array.from(px.idx), pal: px.pal }));
console.log('N', N, 'dolu piksel', cells.filter(Boolean).length, 'renk', new Set(cells.filter(Boolean)).size);
// önizleme PNG (bağımsız minimal PNG yazıcı)
const zlib = require('zlib'), S = 8, W = N * S, raw = Buffer.alloc((W * 4 + 1) * W);
const hex = (h) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
for (let y = 0; y < W; y++) { raw[y * (W * 4 + 1)] = 0; for (let x = 0; x < W; x++) { const v = px.idx[((y / S) | 0) * N + ((x / S) | 0)], c = v ? hex(px.pal[v]) : [238, 241, 246], o = y * (W * 4 + 1) + 1 + x * 4; raw[o] = c[0]; raw[o + 1] = c[1]; raw[o + 2] = c[2]; raw[o + 3] = 255; } }
function crc(b) { let c, t = []; for (let n = 0; n < 256; n++) { c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } let r = 0xffffffff; for (const x of b) r = t[(r ^ x) & 255] ^ (r >>> 8); return (r ^ 0xffffffff) >>> 0; }
function chunk(t, d) { const l = Buffer.alloc(4); l.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t), d]), c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([l, td, c]); }
const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(W, 0); ihdr.writeUInt32BE(W, 4); ihdr[8] = 8; ihdr[9] = 6;
fs.mkdirSync(path.resolve(__dirname, '../tests/_shots'), { recursive: true });
fs.writeFileSync(path.resolve(__dirname, '../tests/_shots/cat_art.png'), Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]));

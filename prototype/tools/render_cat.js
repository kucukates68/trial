// node tools/render_cat.js → tools/cat_cells.json (64x64 maske + hücre rengi; tek kaynak: src/cat_art.js) + tests/_shots/cat_art.png
const { chromium } = require(process.env.PLAYWRIGHT_NODE || '/opt/node22/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const b = await chromium.launch(), pg = await b.newPage();
  await pg.setContent('<canvas id=c></canvas>');
  await pg.addScriptTag({ content: fs.readFileSync(path.resolve(__dirname, '../src/cat_art.js'), 'utf8') });
  const out = await pg.evaluate(() => {
    const S = 8, W = 64 * S, c = document.getElementById('c'); c.width = W; c.height = W; const g = c.getContext('2d', { willReadFrequently: true });
    CB_ART.draw(g, S); const d = g.getImageData(0, 0, W, W).data, cells = [];
    for (let r = 0; r < 64; r++) for (let q = 0; q < 64; q++) {
      let a = 0, R = 0, G = 0, B = 0, n = S * S;
      for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) { const i = ((r * S + y) * W + q * S + x) * 4, al = d[i + 3] / 255; a += al; R += d[i] * al; G += d[i + 1] * al; B += d[i + 2] * al; }
      cells.push(a / n >= 0.5 ? [Math.round(R / a), Math.round(G / a), Math.round(B / a)] : null);
    }
    return { cells, png: c.toDataURL('image/png') };
  });
  fs.writeFileSync(path.resolve(__dirname, 'cat_cells.json'), JSON.stringify(out.cells));
  fs.mkdirSync(path.resolve(__dirname, '../tests/_shots'), { recursive: true });
  fs.writeFileSync(path.resolve(__dirname, '../tests/_shots/cat_art.png'), Buffer.from(out.png.split(',')[1], 'base64'));
  console.log('hücre', out.cells.filter(Boolean).length); await b.close();
})();

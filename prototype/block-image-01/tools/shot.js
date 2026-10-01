// node tools/shot.js in.html out.png [w h]  — HTML → PNG (Playwright)
const { chromium } = require(process.env.PLAYWRIGHT_NODE || '/opt/node22/lib/node_modules/playwright');
(async () => { const [, , inp, out, w, h] = process.argv; const b = await chromium.launch(), p = await b.newPage({ viewport: { width: +w || 1100, height: +h || 640 } }); await p.goto('file://' + require('path').resolve(inp)); await p.screenshot({ path: out, fullPage: true }); await b.close(); })();

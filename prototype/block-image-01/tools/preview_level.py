"""python3 tools/preview_level.py tools/lXX_source.json out.png — parçalar (tek renk) + sınırlar + isimler; yan tarafta boyut listesi"""
import json, sys, os, subprocess
src = json.load(open(sys.argv[1])); out = sys.argv[2]; cell = 20; W, H = 36, 24
own = {}; col = {}
hexmap = src['colorHex']
for p in src['pieces']:
    for r, c in p['cells']: own[(c, r)] = p['id']
    col[p['id']] = hexmap[p['color']]
rects = []; cent = {}
for (x, y), n in own.items():
    rects.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>' % (x * cell, y * cell, cell, cell, col[n]))
    if own.get((x + 1, y)) != n: rects.append('<rect x="%d" y="%d" width="2" height="%d" fill="#fff"/>' % ((x + 1) * cell - 1, y * cell, cell))
    if own.get((x, y + 1)) != n: rects.append('<rect x="%d" y="%d" width="%d" height="2" fill="#fff"/>' % (x * cell, (y + 1) * cell - 1, cell))
for p in src['pieces']:
    cs = [(c, r) for r, c in p['cells']]; mx = sum(x for x, y in cs) / len(cs); my = sum(y for x, y in cs) / len(cs); c = min(cs, key=lambda q: (q[0] - mx) ** 2 + (q[1] - my) ** 2)
    rects.append('<text x="%.1f" y="%.1f" font-size="9" text-anchor="middle" fill="#fff" stroke="#000" stroke-width="2.4" paint-order="stroke" font-family="sans-serif" font-weight="700">%s</text>' % ((c[0] + .5) * cell, (c[1] + .5) * cell + 3, p['id']))
for (x, y) in [tuple(f) for f in src.get('floor', [])]: rects.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#0001" stroke="#999" stroke-dasharray="2 2"/>' % (x * cell, y * cell, cell, cell))
ex, ey = src['entrance'][1], src['entrance'][0]; rects.append('<ellipse cx="%d" cy="%d" rx="30" ry="10" fill="#4a3322"/>' % ((ex + .5) * cell, (ey + .3) * cell))
sizes = sorted(((len(p['cells']), p['id']) for p in src['pieces']), reverse=True)
html = '<body style="margin:0;background:#e6d9bd;font-family:sans-serif"><div style="display:flex;gap:16px;padding:10px"><svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">%s</svg><div style="font-size:11px;columns:2;width:230px">%s</div></div></body>' % (W * cell, (H + 1) * cell, ''.join(rects), ''.join('<div>%s %d</div>' % (n, s) for s, n in sizes))
tmp = out + '.html'; open(tmp, 'w').write(html); subprocess.check_call(['node', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shot.js'), tmp, out, '1020', '560']); os.remove(tmp)

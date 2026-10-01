import json, os, sys, subprocess
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); sys.path.insert(0, os.path.join(H, '..'))
from labkit import Board, Analysis
import candidates as C, explain as E
ROOT = os.path.join(H, '..', '..'); OUT = os.path.join(ROOT, 'design', 'lab'); os.makedirs(OUT, exist_ok=True)
def svg(cid):
    title, rows, q, colors, note, labels = C.CANDS[cid]; B = Board(rows); s = 28; W = B.w * s; Hh = B.h * s; out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="sans-serif">' % (W, Hh + 24, W, Hh + 24), '<rect width="100%" height="100%" fill="#f4ecd8"/>']
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            x, y = c * s, r * s
            if ch in '#': continue
            if ch == '.': out.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#e9dfc6"/>' % (x, y, s, s))
            elif ch == 'E': out.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#7a5a36"/><text x="%d" y="%d" font-size="12" fill="#fff" text-anchor="middle">giriş</text>' % (x, y, s, s, x + s / 2, y + s / 2 + 4))
            else: out.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="#fff" stroke-width="1"/>' % (x, y, s, s, colors[ch]))
    for n, cs in B.cells.items():
        r = sum(p[0] for p in cs) / len(cs); c = sum(p[1] for p in cs) / len(cs)
        out.append('<text x="%.1f" y="%.1f" font-size="12" font-weight="700" fill="#111" stroke="#fff" stroke-width="3" paint-order="stroke" text-anchor="middle">%s</text>' % ((c + .5) * s, (r + .5) * s + 4, labels[n]))
    out.append('</svg>'); return '\n'.join(out)
def png(cid):
    p = os.path.join(OUT, cid + '_map.svg'); open(p, 'w', encoding='utf-8').write(svg(cid))
    js = "const {chromium}=require('/opt/node22/lib/node_modules/playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();await p.goto('file://%s');const el=await p.$('svg');await el.screenshot({path:'%s'});await b.close()})()" % (p, p.replace('.svg', '.png'))
    open('/tmp/claude-0/-home-user-trial/309a846e-36ea-5c76-a60b-b8e84c53c4f6/scratchpad/mp.js', 'w').write(js); subprocess.run(['node', '/tmp/claude-0/-home-user-trial/309a846e-36ea-5c76-a60b-b8e84c53c4f6/scratchpad/mp.js'], check=True)
if __name__ == '__main__':
    sol = ['# SPOILER — adayların kazanan dizileri (oynamadan önce açma)\n']
    for cid in C.CANDS:
        png(cid); title, rows, q, colors, note, labels = C.CANDS[cid]; info = json.load(open(os.path.join(ROOT, 'tests', 'level_info_%s.json' % cid)))
        lv, L = E.load(cid); memo, root = L.analyse(); lst = []
        def rec(st, seq):
            if len(lst) >= 6: return
            for m in memo[st][3]:
                if not m[1]: continue
                if m[4] == 'won': lst.append(seq + [m[0] + 1])
                else: rec(m[5], seq + [m[0] + 1])
        rec(L.new_state(), [])
        sol.append('## %s — %d kazanan sıra (ilk 6): kart/slot numaralarıyla\n' % (title, root[2]))
        for s in lst: sol.append('- ' + ' '.join(str(x) for x in s))
        sol.append('')
    open(os.path.join(OUT, 'SOLUTIONS_SPOILER.md'), 'w', encoding='utf-8').write('\n'.join(sol)); print('ok')

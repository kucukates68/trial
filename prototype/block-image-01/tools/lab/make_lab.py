"""Deney adayı üretici: python3 tools/lab/make_lab.py → src/level_x0N.js, src/vectors_x0N.js, tests/*_x0N.json, dist/block-image-X0N.html, design/lab/xN_map.svg
Mekanik değişmez: ref.py referansı ile kesin çözücü; labkit hızlı çözücüsüyle çapraz doğrulama."""
import json, os, sys, random
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); sys.path.insert(0, os.path.join(H, '..'))
from labkit import Board, Analysis
from ref import Level
import templates as T
ROOT = os.path.join(H, '..', '..')
PAL = dict(A='#e8833a', B='#d9a441', C='#c4572e', D='#b8793a', ONE='#4f8fd6', TWO='#3aa6a6', THREE='#6a74d6', p='#9fc4ee', q='#9ad8d4', r='#b7bdf0', l='#5aa469', u='#8fcf8a', R3='#7bbf6a', k='#7a6ad6', K='#d66aa6', X='#8a5fd0', Dd='#e6c14a', v='#4f8fd6', w='#6aa6e6', a='#e8833a', b='#d9a441', c='#c4572e', d='#b8793a', m='#5aa469', n='#8fcf8a')
def build(cid, title, rows, queues0, colors, note, labels=None):
    B = Board(rows); names = B.names; assert sorted(sum(queues0, [])) == names, (sorted(sum(queues0, [])), names)
    labels = labels or {n: n for n in names}; queues = [[labels[x] for x in q] for q in queues0]
    GRID = '\n'.join(''.join('a' if (ch not in '#.E') else ch for ch in r) for r in rows)
    pieces = [dict(id=labels[n], cells=[list(p) for p in sorted(B.cells[n])], color='c_' + n) for n in names]
    colorHex = {'c_' + n: colors[n] for n in names}
    L = Level(GRID, [dict(id=p['id'], cells=p['cells']) for p in pieces], queues); memo, root = L.analyse(); stats = L.stats(); assert root[0], 'çözülemez'
    A = Analysis(B, queues0); f = A.features(); assert f['orders'] == stats['winning_orders'], ('ref ↔ lab uyuşmuyor', f['orders'], stats['winning_orders'])
    def walk(prefer):
        st = L.new_state(); seq = []; k = 0
        while True:
            win, p, cnt, moves = memo[st]; good = [m for m in moves if m[1]]; pref = [m for m in good if prefer(k, m)]; m = (pref or good)[0]; seq.append(m[0]); k += 1
            if m[4] == 'won': return seq
            st = m[5]
    winA = walk(lambda k, m: True); winB = walk(lambda k, m: m[0] == k % 3); winC = walk(lambda k, m: m[0] == (2 - k % 3))
    rng = random.Random(5); cases = [dict(name='winning', sequence=winA), dict(name='winning_mixed', sequence=winB), dict(name='winning_reverse', sequence=winC)]
    trap_seq = None; best = 99
    for i in range(30):
        st = L.new_state(); sq = []
        while True:
            opts = [s for s in range(3) if L.cards(st)[s] is not None and L.options(st)[s]]
            if not opts: break
            s = rng.choice(opts); sq.append(s); r = L.place(st, s)
            if r['won'] or r['sealed'] or r['stuck']:
                if (r['sealed'] or r['stuck']) and len(sq) < best: best = len(sq); trap_seq = list(sq)
                break
            st = r['state']
        cases.append(dict(name='random%d' % i, sequence=sq))
    cases.append(dict(name='illegal_empty', sequence=[0] * 30))
    for c in cases: c['expected'] = L.simulate(c['sequence'])
    lv = dict(id=cid.upper(), name=title, title=title, style='blocks', colorHex=colorHex, w=B.w, h=B.h, grid=GRID, cells=sum(len(p['cells']) for p in pieces), pieces=pieces, hand=queues, pattern='', stats=stats)
    tg = '######\nE.AAAA\n######'; tp = [dict(id='T1', cells=[[1, 2], [1, 3]]), dict(id='T2', cells=[[1, 4], [1, 5]])]; TL = Level(tg, tp, [['T2'], ['T1'], []])
    vec = [dict(level_id=cid.upper(), grid=GRID, pieces=[dict(id=p['id'], cells=p['cells']) for p in pieces], hand=queues, cases=cases), dict(level_id='TOY', grid=tg, pieces=tp, hand=[['T2'], ['T1'], []], cases=[dict(name='toy_far_first', sequence=[0, 1], expected=TL.simulate([0, 1]))])]
    S = os.path.join(ROOT, 'src'); Tt = os.path.join(ROOT, 'tests'); lid = cid.lower()
    open(os.path.join(S, 'level_%s.js' % lid), 'w', encoding='utf-8').write('window.BI_LEVEL = ' + json.dumps(lv, ensure_ascii=False, separators=(',', ':')) + ';\n')
    open(os.path.join(S, 'vectors_%s.js' % lid), 'w', encoding='utf-8').write('window.BI_VECTORS = ' + json.dumps(vec, separators=(',', ':')) + ';\n')
    json.dump(vec, open(os.path.join(Tt, 'vectors_%s.json' % lid), 'w'), separators=(',', ':'))
    f2 = {k: v for k, v in f.items() if k not in ('example',)}
    json.dump(dict(hand=queues, win=winA, win_mixed=winB, win_reverse=winC, trap_seq=trap_seq, stats=stats, fast=f2, colors={p['id']: p['color'] for p in pieces}), open(os.path.join(Tt, 'level_info_%s.json' % lid), 'w'), indent=1, default=str)
    os.system('python3 %s %s' % (os.path.join(ROOT, 'tools', 'build.py'), lid))
    return B, A, f, stats, winA
CANDS = {}
def cand(cid, title, rows, queues, colors, note=''): CANDS[cid] = (title, rows, queues, colors, note)
if __name__ == '__main__':
    import candidates; ids = sys.argv[1:] or list(candidates.CANDS)
    for cid in ids:
        title, rows, q, colors, note, labels = candidates.CANDS[cid]; B, A, f, stats, win = build(cid, title, rows, q, colors, note, labels); print(cid, 'orders', f['orders'], 'p_random', stats['p_random'], 'wins', ''.join('ABC'[s] for s in win))

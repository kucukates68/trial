"""Genel blok-seviye üretici (L02+): python3 tools/make_level_blocks.py l02
Girdi : tools/<id>_source.json  (id, name, title, entrance, floor, pieces[{id,color,cells[r,c]}], colorHex, style, hand)
Çıktı : src/level_<id>.js, src/vectors_<id>.js, tests/vectors_<id>.json, tests/level_info_<id>.json
Doğrulama: Python referansı (ref.py) kesin çözücü + lvlkit hızlı çözücü çapraz kontrol (winning_orders, p_random, durum sayısı birebir)."""
import json, os, sys, random, time
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from ref import Level
from lvlkit import Canvas, Geo, report, validate, stats_line

LID = sys.argv[1].lower(); SRC = json.load(open(os.path.join(H, LID + '_source.json'), encoding='utf-8'))
W, HH = 36, 24; ER, EC = SRC['entrance']
rows = [['#'] * W for _ in range(HH + 1)]
for (x, y) in [tuple(f) for f in SRC.get('floor', [])]: rows[y][x] = '.'
for p in SRC['pieces']:
    for r, c in p['cells']: rows[r][c] = 'a'
rows[ER][EC] = 'E'
GRID = '\n'.join(''.join(r) for r in rows)
pieces = [dict(id=p['id'], cells=p['cells'], color=p['color']) for p in SRC['pieces']]
hand = SRC['hand']; ids = [p['id'] for p in pieces]
assert sorted(sum(hand, [])) == sorted(ids), 'kuyruklar parçaları tam bir kez içermeli'
cells_total = sum(len(p['cells']) for p in pieces); assert len({tuple(c) for p in pieces for c in p['cells']}) == cells_total, 'çakışan hücre var'
assert all(p['color'] in SRC['colorHex'] for p in pieces), 'her parça tek renk (piece.color) ve colorHex içinde olmalı'

cv = Canvas(); cv.entrance = (EC, ER); cv.floor = {tuple(f) for f in SRC.get('floor', [])}
for p in SRC['pieces']: cv.piece(p['id'], p['color'], [(c, r) for r, c in p['cells']])
errs, adj = validate(cv); assert not errs, errs
geo = Geo(cv); fast = report(geo, hand)

t0 = time.time(); L = Level(GRID, pieces, hand); memo, root = L.analyse(); stats = L.stats(); print('ref çözücü %.1f sn:' % (time.time() - t0), json.dumps(stats))
assert root[0], 'çözülemez'
assert stats['winning_orders'] == fast['winning_orders'] and abs(stats['p_random'] - fast['p_random']) < 1e-4 and stats['n_states'] >= 1, ('ref ↔ hızlı çözücü uyuşmuyor', stats, fast['winning_orders'], fast['p_random'])
print('ref ↔ hızlı çözücü: winning_orders %d, p_random %.5f birebir' % (fast['winning_orders'], fast['p_random']))

def walk(prefer):
    st = L.new_state(); seq = []; k = 0
    while True:
        win, p, cnt, moves = memo[st]; good = [m for m in moves if m[1]]; pref = [m for m in good if prefer(k, m)]; m = (pref or good)[0]; seq.append(m[0]); k += 1
        if m[4] == 'won': return seq
        st = m[5]
winA = walk(lambda k, m: True); winB = walk(lambda k, m: m[0] == k % 3); winC = walk(lambda k, m: m[0] == (2 - k % 3))
rng = random.Random(11); cases = [dict(name='winning', sequence=winA), dict(name='winning_mixed', sequence=winB), dict(name='winning_reverse', sequence=winC)]
trap_seq = None; best_len = 999
for i in range(24):
    st = L.new_state(); sq = []
    while True:
        opts = [s for s in range(3) if L.cards(st)[s] is not None and L.options(st)[s]]
        if not opts: break
        s = rng.choice(opts); sq.append(s); r = L.place(st, s)
        if r['won'] or r['sealed'] or r['stuck']:
            if r['sealed'] and len(sq) < best_len: best_len = len(sq); trap_seq = list(sq)
            break
        st = r['state']
    cases.append(dict(name='random%d' % i, sequence=sq))
cases.append(dict(name='illegal_empty', sequence=[0] * 60))
for c in cases: c['expected'] = L.simulate(c['sequence'])
# en kısa kilitlenen yol (BFS, tüm yasal hamleler) — QA tuzak testi için
from collections import deque
q = deque([(L.new_state(), [])]); seen = set(); shortest = None
while q and shortest is None:
    st, sq = q.popleft(); key = st
    if key in seen: continue
    seen.add(key)
    for s in range(3):
        if L.cards(st)[s] is None or not L.options(st)[s]: continue
        r = L.place(st, s)
        if r['sealed']: shortest = sq + [s]; break
        if not r['won'] and not r['stuck']: q.append((r['state'], sq + [s]))
n_seal = sum(1 for c in cases if any(e.get('sealed') for e in c['expected'])); print('vaka', len(cases), '| kilitlenen vaka', n_seal, '| en kısa kilitlenen yol', len(shortest or []), 'hamle')
tg = '######\nE.AAAA\n######'; tp = [dict(id='T1', cells=[[1, 2], [1, 3]]), dict(id='T2', cells=[[1, 4], [1, 5]])]
TL = Level(tg, tp, [['T2'], ['T1'], []]); toy = [dict(name='toy_far_first', sequence=[0, 1], expected=TL.simulate([0, 1]))]
lv = dict(id=SRC['id'], name=SRC['name'], title=SRC['title'], style=SRC.get('style', 'blocks'), colorHex=SRC['colorHex'], w=W, h=HH + 1, grid=GRID, cells=cells_total, pieces=pieces, hand=hand, pattern=SRC.get('pattern', ''), stats=stats)
S = os.path.join(H, '..', 'src'); T = os.path.join(H, '..', 'tests')
open(os.path.join(S, 'level_%s.js' % LID), 'w', encoding='utf-8').write('window.BI_LEVEL = ' + json.dumps(lv, ensure_ascii=False, separators=(',', ':')) + ';\n')
vec = [dict(level_id=SRC['id'], grid=GRID, pieces=[dict(id=p['id'], cells=p['cells']) for p in pieces], hand=hand, cases=cases), dict(level_id='TOY', grid=tg, pieces=tp, hand=[['T2'], ['T1'], []], cases=toy)]
open(os.path.join(S, 'vectors_%s.js' % LID), 'w', encoding='utf-8').write('window.BI_VECTORS = ' + json.dumps(vec, separators=(',', ':')) + ';\n')
json.dump(vec, open(os.path.join(T, 'vectors_%s.json' % LID), 'w'), separators=(',', ':'))
fast_out = {k: v for k, v in fast.items()}
json.dump(dict(hand=hand, win=winA, win_mixed=winB, win_reverse=winC, trap_seq=shortest, stats=stats, fast=fast_out, size=stats_line(cv), colors={p['id']: p['color'] for p in pieces}), open(os.path.join(T, 'level_info_%s.json' % LID), 'w'), indent=1)
print('yazıldı:', LID, '| kazanan hat', ''.join('ABC'[s] for s in winA))

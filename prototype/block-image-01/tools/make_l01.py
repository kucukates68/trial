"""L01 — 36×24 piksel-art kedi (460 hücre, 19 parça, kuyruk ALT-2).
Kaynak veri: tools/l01_source.json (hücre → parça + resim rengi; parça kimlik rengi; el kuyrukları).
Bu betik: oyun verisi (src/level_l01.js) + Python referansı ile kesin çözücü ölçümü + parity vektörleri (src/vectors_l01.js, tests/vectors_l01.json, tests/level_info_l01.json).
Mekanik değişmez (ref.py / engine.js); burada yalnızca veri ve doğrulama üretilir."""
import json, os, sys, random
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from ref import Level

SRC = json.load(open(os.path.join(H, 'l01_source.json'), encoding='utf-8'))
W, HH = SRC['w'], SRC['h']; ER, EC = SRC['entrance']                       # giriş: hedef alanın 1 satır altı (satır 24, sütun 18)
rows = [['#'] * W for _ in range(HH + 1)]
for p in SRC['pieces']:
    for r, c in p['cells']: rows[r][c] = 'a'
rows[ER][EC] = 'E'
GRID = '\n'.join(''.join(r) for r in rows)
pieces = [dict(id=p['id'], cells=p['cells'], color=p['color'], art=p['art']) for p in SRC['pieces']]
hand = SRC['hand']
ids = [p['id'] for p in pieces]
assert sorted(sum(hand, [])) == sorted(ids), 'kuyruklar parçaları tam bir kez içermeli'
assert sum(len(p['cells']) for p in pieces) == 460
assert all(isinstance(p['color'], str) and p['color'] in SRC.get('colorHex', {}) for p in pieces), 'her parça tek renk (piece.color) ve palette içinde olmalı'

L = Level(GRID, [dict(id=p['id'], cells=p['cells']) for p in pieces], hand)
memo, root = L.analyse(); assert root[0], 'çözülemez'
stats = L.stats(); print('çözücü:', json.dumps(stats))
assert stats['trap_delayed'] == 0, 'gecikmeli tuzak olmamalı'

def walk(prefer):
    st = L.new_state(); seq = []; k = 0
    while True:
        win, p, cnt, moves = memo[st]; good = [m for m in moves if m[1]]; pref = [m for m in good if prefer(k, m)]; m = (pref or good)[0]; seq.append(m[0]); k += 1
        if m[4] == 'won': return seq
        st = m[5]
winA = walk(lambda k, m: True); winB = walk(lambda k, m: m[0] == k % 3); winC = walk(lambda k, m: m[0] == (2 - k % 3))
rng = random.Random(7)
cases = [dict(name='winning', sequence=winA), dict(name='winning_mixed', sequence=winB), dict(name='winning_reverse', sequence=winC)]
for i in range(14):       # rastgele yasal oyunlar (tuzaklara giren yollar dahil)
    st = L.new_state(); sq = []
    while True:
        opts = [s for s in range(3) if L.cards(st)[s] is not None and L.options(st)[s]]
        if not opts: break
        s = rng.choice(opts); sq.append(s); r = L.place(st, s)
        if r['won'] or r['sealed'] or r['stuck']: break
        st = r['state']
    cases.append(dict(name='random%d' % i, sequence=sq))
cases.append(dict(name='illegal_empty', sequence=[0] * 40))
for c in cases: c['expected'] = L.simulate(c['sequence'])
n_seal = sum(1 for c in cases if any(e.get('sealed') for e in c['expected'])); print('vaka', len(cases), '| kilitlenen (tuzak) vaka', n_seal)

tg = '######\nE.AAAA\n######'; tp = [dict(id='T1', cells=[[1, 2], [1, 3]]), dict(id='T2', cells=[[1, 4], [1, 5]])]
TL = Level(tg, tp, [['T2'], ['T1'], []]); toy = [dict(name='toy_far_first', sequence=[0, 1], expected=TL.simulate([0, 1]))]
lv = dict(id='L01', name='L01 — Kedi', title='L01 · kedi 36×24', style=SRC.get('style', 'blocks'), colorHex=SRC.get('colorHex', {}), w=W, h=HH + 1, grid=GRID, cells=460, pieces=pieces, hand=hand, pattern=SRC['pattern'], stats=stats)
S = os.path.join(H, '..', 'src'); T = os.path.join(H, '..', 'tests')
open(os.path.join(S, 'level_l01.js'), 'w', encoding='utf-8').write('window.BI_LEVEL = ' + json.dumps(lv, ensure_ascii=False, separators=(',', ':')) + ';\n')
vec = [dict(level_id='L01', grid=GRID, pieces=[dict(id=p['id'], cells=p['cells']) for p in pieces], hand=hand, cases=cases), dict(level_id='TOY', grid=tg, pieces=tp, hand=[['T2'], ['T1'], []], cases=toy)]
open(os.path.join(S, 'vectors_l01.js'), 'w', encoding='utf-8').write('window.BI_VECTORS = ' + json.dumps(vec, separators=(',', ':')) + ';\n')
json.dump(vec, open(os.path.join(T, 'vectors_l01.json'), 'w'), separators=(',', ':'))
json.dump(dict(hand=hand, win=winA, win_mixed=winB, win_reverse=winC, stats=stats, colors={p['id']: p['color'] for p in pieces}), open(os.path.join(T, 'level_info_l01.json'), 'w'), indent=1)
print('yazıldı: src/level_l01.js, src/vectors_l01.js, tests/vectors_l01.json, tests/level_info_l01.json | kazanan hat', ''.join('ABC'[s] for s in winA))

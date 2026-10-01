"""block-image-01 — CAT ART PASS: el çizimi kedi (188 hücre, 25 parça). Kedi = parçaların birleşmiş hâli; hedef rengi = sahibi parçanın rengi.
ART (aşağıda) her hücreyi sahibi parçanın HARFİYLE yazar; harf = parça. Gözler (e,f) ve burun (n) 1 hücrelik GERÇEK parçalardır; kuyruk 3 parçalık ince bir kıvrımdır.
Renkler (turuncu/mavi/kırmızı/yeşil + göz/burun için 'dark') level tasarımı olarak atanır: bitişik parçalar farklı renk (4-boyama), kulaklar farklı, her kuyrukta ≥3 renk.
Mekanik değişmez (ref.py / engine.js). Bu betik: seviye + kesin DP + parity vektörleri + karar yoğunluğu üretir."""
import json, os, sys, random
from collections import deque
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from ref import Level

BOARD = 24; R0, C0 = 1, 2
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
ART = [
    ".a...........b......",
    ".aa.........bb......",
    ".aaa.......bbb......",
    ".ccccccddddddd......",
    ".ccccccddddddd......",
    ".jjjekkkkkflll......",
    ".jjjjkkkkkllll......",
    ".jjjjmmnmmllll......",
    "..jjjmmmmmlll.VVV...",
    "...qqqqqqqqq..VVV...",
    "..sssuuuuuttt...VV..",
    "..sssvvvvvttt...UU..",
    "..wwwwyyyxxxx...UU..",
    "..wwwwyyyxxxx...UU..",
    "..wwwwzzzxxxxTTTUU..",
    "..ppppzzzrrrrTTTTTT.",
]
ROLE = {'e': 'eye', 'f': 'eye', 'n': 'nose'}
COLORS = ['orange', 'blue', 'red', 'green']

cellsmap = {}
for r, row in enumerate(ART):
    assert len(row) == 20, (r, len(row))
    for c, ch in enumerate(row):
        if ch != '.': cellsmap[(r + R0, c + C0)] = ch
letters = sorted({v for v in cellsmap.values()}, key=lambda ch: min(p for p, v in cellsmap.items() if v == ch))
assert len(cellsmap) == 188 and len(letters) == 25, (len(cellsmap), len(letters))
pieces_cells = {ch: sorted(p for p, v in cellsmap.items() if v == ch) for ch in letters}
for ch, cs in pieces_cells.items():            # her parça bağlı olmalı
    seen = {cs[0]}; q = deque([cs[0]])
    while q:
        u = q.popleft()
        for dr, dc in DIRS:
            v = (u[0] + dr, u[1] + dc)
            if v in cs and v not in seen: seen.add(v); q.append(v)
    assert len(seen) == len(cs), ('parça bağlı değil', ch)
ID = {ch: 'B%02d' % (i + 1) for i, ch in enumerate(letters)}
E = (BOARD - 1, C0 + 7); lastcat = max(r for r, c in cellsmap if c == E[1]); FLOOR = [(r, E[1]) for r in range(lastcat + 1, BOARD - 1)]
grid = [['#'] * BOARD for _ in range(BOARD)]
for r, c in cellsmap: grid[r][c] = 'A'
for r, c in FLOOR: grid[r][c] = '.'
grid[E[0]][E[1]] = 'E'; GRID = '\n'.join(''.join(r) for r in grid)
adj = {ch: set() for ch in letters}
for (r, c), ch in cellsmap.items():
    for dr, dc in DIRS:
        o = cellsmap.get((r + dr, c + dc))
        if o and o != ch: adj[ch].add(o); adj[o].add(ch)

def valid_order():
    first = {cellsmap[(r, c)] for (r, c) in cellsmap if any((r + dr, c + dc) in set(FLOOR) for dr, dc in DIRS)}
    disc = []; seen = set(first); q = deque(sorted(first))
    while q:
        u = q.popleft(); disc.append(u)
        for v in sorted(adj[u]):
            if v not in seen: seen.add(v); q.append(v)
    return disc[::-1]

def patterns(order):
    rank = {ch: k for k, ch in enumerate(order)}; P = {}
    P['round_robin'] = [[ch for ch in order if rank[ch] % 3 == k] for k in range(3)]
    P['blocks2'] = [sorted([order[i] for i in range(len(order)) if (i // 2) % 3 == k], key=lambda ch: rank[ch]) for k in range(3)]
    P['thirds'] = [order[0:8], order[8:16], order[16:]]
    P['blocks3'] = [sorted([order[i] for i in range(len(order)) if (i // 3) % 3 == k], key=lambda ch: rank[ch]) for k in range(3)]
    return P

def colour(hand_ch, memo, Lv):
    """4-boyama (bitişik parçalar farklı), gözler/burun 'dark'; kulaklar farklı; her kuyrukta ≥3 renk; ilk elde 3 farklı renk; 3 kartın farklı renk olma oranı maksimum."""
    free = [ch for ch in letters if ch not in ROLE]; best = None; states = list(memo.keys()); pid = {ID[ch]: i for i, ch in enumerate(letters)}
    for seed in range(3000):
        rng = random.Random(seed); order = free[:]; rng.shuffle(order); col = {}
        def bt(i):
            if i == len(order): return True
            ch = order[i]; opts = COLORS[:]; rng.shuffle(opts)
            for c in opts:
                if any(col.get(o) == c for o in adj[ch]): continue
                if ch in ('a', 'b') and col.get('b' if ch == 'a' else 'a') == c: continue
                col[ch] = c
                if bt(i + 1): return True
                del col[ch]
            return False
        if not bt(0): continue
        for ch, r in ROLE.items(): col[ch] = 'dark'
        cnt = {c: sum(1 for ch in free if col[ch] == c) for c in COLORS}
        if min(cnt.values()) < 3 or max(cnt.values()) > 8: continue
        if any(len({col[ch] for ch in q}) < 3 for q in hand_ch): continue
        heads0 = [col[letters[h]] for h in Lv.cards(Lv.new_state()) if h is not None]
        if len(set(heads0)) < 3: continue
        sc = sum(len({col[letters[h]] for h in Lv.cards(st) if h is not None}) / max(1, len([h for h in Lv.cards(st) if h is not None])) for st in states) / len(states)
        if best is None or sc > best[0]: best = (sc, seed, dict(col))
    assert best, 'renk ataması bulunamadı'; return best

def build_pieces(col):
    return [dict(id=ID[ch], cells=[list(p) for p in pieces_cells[ch]], color=col[ch], role=ROLE.get(ch)) for ch in letters]

if __name__ == '__main__':
    order = valid_order(); print('hücre', len(cellsmap), 'parça', len(letters), 'boyutlar', {ID[ch]: len(pieces_cells[ch]) for ch in letters})
    pats = patterns(order); res = {}
    tmp_pieces = [dict(id=ID[ch], cells=[list(p) for p in pieces_cells[ch]]) for ch in letters]; ix = {ch: i for i, ch in enumerate(letters)}
    for name, qs in pats.items():
        hand = [[ID[ch] for ch in q] for q in qs]; Lv = Level(GRID, tmp_pieces, hand); s = Lv.stats(); res[name] = (s, qs, hand); print(name, [len(q) for q in qs], json.dumps(s))
    pick = sys.argv[1] if len(sys.argv) > 1 else 'blocks2'; s, qs, hand = res[pick]; Lv = Level(GRID, tmp_pieces, hand); memo, root = Lv.analyse(); assert root[0], 'çözülemez'
    sc, cseed, col = colour(qs, memo, Lv); pieces = build_pieces(col)
    print('renkler:', {c: sum(1 for p in pieces if p['color'] == c) for c in COLORS + ['dark']}, 'ortalama farklı-renk oranı', round(sc, 3), 'tohum', cseed)
    L = Level(GRID, pieces, hand)
    def walk(prefer):
        st = L.new_state(); seq = []; k = 0
        while True:
            win, p, cnt, moves = memo[st]; good = [m for m in moves if m[1]]; pref = [m for m in good if prefer(k, m)]; m = (pref or good)[0]; seq.append(m[0]); k += 1
            if m[4] == 'won': return seq
            st = m[5]
    winA = walk(lambda k, m: True); winB = walk(lambda k, m: m[0] == k % 3)
    rng = random.Random(3); cases = [dict(name='winning', sequence=winA), dict(name='winning_mixed', sequence=winB)]
    for i in range(10):
        st = L.new_state(); sq = []
        while True:
            opts = [sl for sl in range(3) if L.cards(st)[sl] is not None and L.options(st)[sl]]
            if not opts: break
            sl = rng.choice(opts); sq.append(sl); r = L.place(st, sl)
            if r['won'] or r['sealed'] or r['stuck']: break
            st = r['state']
        cases.append(dict(name='hand_random%d' % i, sequence=sq))
    cases.append(dict(name='illegal_empty', sequence=[0] * 40))
    for c in cases: c['expected'] = L.simulate(c['sequence'])
    tg = '######\nE.AAAA\n######'; tp = [dict(id='T1', cells=[[1, 2], [1, 3]]), dict(id='T2', cells=[[1, 4], [1, 5]])]
    TL = Level(tg, tp, [['T2'], ['T1'], []]); toy = [dict(name='toy_far_first', sequence=[0, 1], expected=TL.simulate([0, 1])), dict(name='toy_illegal', sequence=[2], expected=TL.simulate([2]))]
    TL2 = Level(tg, tp, [['T1'], ['T2'], []]); toy2 = [dict(name='toy_near_first_seals', sequence=[0], expected=TL2.simulate([0]))]; assert any(e.get('sealed') for e in toy2[0]['expected'])
    lv = dict(id='cat-02', name='Blok Resim 01 — Kedi', w=BOARD, h=BOARD, grid=GRID, cells=len(cellsmap), pieces=pieces, hand=hand, pattern=pick, stats=s)
    S = os.path.join(H, '..', 'src')
    open(os.path.join(S, 'level.js'), 'w', encoding='utf-8').write('window.BI_LEVEL = ' + json.dumps(lv, ensure_ascii=False) + ';\n')
    vec = [dict(level_id=lv['id'], grid=GRID, pieces=pieces, hand=hand, cases=cases), dict(level_id='TOY', grid=tg, pieces=tp, hand=[['T2'], ['T1'], []], cases=toy), dict(level_id='TOY2', grid=tg, pieces=tp, hand=[['T1'], ['T2'], []], cases=toy2)]
    open(os.path.join(S, 'vectors.js'), 'w', encoding='utf-8').write('window.BI_VECTORS = ' + json.dumps(vec) + ';\n')
    json.dump(vec, open(os.path.join(H, '..', 'tests', 'vectors.json'), 'w'))
    json.dump(dict(hand=hand, win=winA, win_mixed=winB, stats=s, order=[ID[ch] for ch in order], colors={p['id']: p['color'] for p in pieces}), open(os.path.join(H, '..', 'tests', 'level_info.json'), 'w'), indent=1)
    # kontrol: karar yoğunluğu (kazanan hatlar boyunca)
    rng2 = random.Random(1); decs = []
    for _ in range(400):
        st = L.new_state(); dec = 0
        while True:
            win, p, cnt, moves = memo[st]; good = [m for m in moves if m[1]]; bad = [m for m in moves if not m[1]]
            if good and bad: dec += 1
            m = rng2.choice(good)
            if m[4] == 'won': break
            st = m[5]
        decs.append(dec)
    print('yazıldı; seçilen', pick, json.dumps(s)); print('kazanan hat', winA); print('kazanan hatlarda ortalama karar', round(sum(decs) / len(decs), 2), 'min', min(decs), 'maks', max(decs))

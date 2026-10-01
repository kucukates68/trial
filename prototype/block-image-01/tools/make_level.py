"""block-image-01: TEK elle hazırlanmış seviye (genel üretici değil). 96×96 pixel-art kedi → 20×20 küçük blok resmi (tools/downsample.py) → 24×24 tahta.
Resim, 6–11 hücrelik geometrik BLOKLARA bölünür (satır-ana büyütme, kompakt şekil tercihi; tek bir tohumla sabit); her blok resmin kendi renkli hücrelerinden oluşur
ve resimdeki tek hedefi budur. El: 3 slot, kuyruklar 'girişten blok-komşuluk BFS'inin tersi' geçerli sıranın alt dizisi (⇒ çözülebilir; kesin DP ile doğrulanır)."""
import json, os, sys, random
from collections import deque
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from downsample import downsample, PAL
from ref import Level

N = 20; BOARD = 24; R0, C0 = 1, 2
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
art = downsample(N, 0.45, 0.18)
# en büyük bağlı bileşen
left = set(art); comps = []
while left:
    s = next(iter(left)); comp = {s}; q = deque([s]); left.discard(s)
    while q:
        u = q.popleft()
        for dr, dc in DIRS:
            v = (u[0] + dr, u[1] + dc)
            if v in left: left.discard(v); comp.add(v); q.append(v)
    comps.append(comp)
cat = max(comps, key=len); art = {p: art[p] for p in cat}
cells = {(r + R0, c + C0): v for (r, c), v in art.items()}                 # tahta koordinatları
E = (BOARD - 1, C0 + N // 2); lastcat = max(r for r, c in cells if c == E[1]); FLOOR = [(r, E[1]) for r in range(lastcat + 1, BOARD - 1)]
grid = [['#'] * BOARD for _ in range(BOARD)]
for r, c in cells: grid[r][c] = 'A'
for r, c in FLOOR: grid[r][c] = '.'
grid[E[0]][E[1]] = 'E'; GRID = '\n'.join(''.join(r) for r in grid)
TG = sorted(cells)                                                         # hedef sırası (satır-ana) = motordakiyle aynı
COLORS = [PAL[cells[p]] for p in TG]

def bbox(sh):
    rs = [p[0] for p in sh]; cs = [p[1] for p in sh]; return max(rs) - min(rs) + 1, max(cs) - min(cs) + 1

def tile(rng, sizes):
    lft = set(cells); pcs = []
    while lft:
        start = min(lft, key=lambda v: (sum(((v[0] + dr, v[1] + dc) in lft) for dr, dc in DIRS), v)); size = rng.choice(sizes); shape = [start]; sset = {start}
        while len(shape) < size:
            cand = {(r + dr, c + dc) for r, c in shape for dr, dc in DIRS} & lft - sset
            if not cand: break
            def sc(v): h, w = bbox(shape + [v]); return (max(h, w), h * w, rng.random())
            b = min(cand, key=sc); shape.append(b); sset.add(b)
        pcs.append(shape); lft -= sset
    # küçük artıkları komşuyla birleştir
    changed = True
    while changed:
        changed = False
        for i, p in enumerate(pcs):
            if len(p) < 5:
                nb = [j for j, q in enumerate(pcs) if j != i and len(q) + len(p) <= 13 and any((r + dr, c + dc) in set(q) for r, c in p for dr, dc in DIRS)]
                if nb:
                    j = min(nb, key=lambda j: len(pcs[j])); pcs[j] = pcs[j] + p; pcs.pop(i); changed = True; break
    return pcs

def shape_key(sh):
    r0 = min(p[0] for p in sh); c0 = min(p[1] for p in sh); return tuple(sorted((r - r0, c - c0) for r, c in sh))

def good_tiling(pcs):
    if not (18 <= len(pcs) <= 25): return None
    if any(len(p) < 5 or len(p) > 13 for p in pcs): return None
    comp = []
    for p in pcs:
        h, w = bbox(p); 
        if max(h, w) > 7: return None
        comp.append(len(p) / (h * w))
    if min(comp) < 0.42: return None
    return sum(comp) / len(comp) + 0.02 * len({shape_key(p) for p in pcs})

def best_tiling():
    best = None
    for seed in range(400):
        rng = random.Random(seed); pcs = tile(rng, (6, 7, 8, 9, 10)); sc = good_tiling(pcs)
        if sc is not None and (best is None or sc > best[0]): best = (sc, seed, pcs)
    assert best, 'uygun bölme bulunamadı'; return best

def centroid(p): return sum(r for r, c in p) / len(p), sum(c for r, c in p) / len(p)

def build():
    sc, seed, pcs = best_tiling()
    pcs.sort(key=lambda p: min(p))                       # kimlik: satır-ana ilk hücreye göre
    pieces = [dict(id='B%02d' % (i + 1), cells=[list(x) for x in sorted(p)]) for i, p in enumerate(pcs)]
    return seed, pieces

def valid_order(L, pieces):
    cp = {}
    for i, p in enumerate(pieces):
        for r, c in p['cells']: cp[(r, c)] = i
    adj = {i: set() for i in range(len(pieces))}
    for (r, c), i in cp.items():
        for dr, dc in ((1, 0), (0, 1)):
            j = cp.get((r + dr, c + dc))
            if j is not None and j != i: adj[i].add(j); adj[j].add(i)
    fl = set(FLOOR); first = {cp[(r, c)] for (r, c) in cp if any((r + dr, c + dc) in fl for dr, dc in DIRS)}
    disc = []; seen = set(first); q = deque(sorted(first))
    while q:
        u = q.popleft(); disc.append(u)
        for v in sorted(adj[u]):
            if v not in seen: seen.add(v); q.append(v)
    return disc[::-1]

def patterns(pieces, order):
    rank = {j: k for k, j in enumerate(order)}; cen = [centroid([tuple(x) for x in p['cells']]) for p in pieces]
    def lane(j):
        r, c = cen[j]
        if r < R0 + 9: return 0                        # baş ve kulaklar
        if c >= C0 + 15: return 2                      # kuyruk
        return 1                                       # gövde, patiler
    P = {}
    P['anatomy'] = [sorted([j for j in range(len(pieces)) if lane(j) == k], key=lambda j: rank[j]) for k in range(3)]
    P['round_robin'] = [[j for j in order if rank[j] % 3 == k] for k in range(3)]
    P['thirds'] = [order[0:len(order) // 3], order[len(order) // 3: 2 * len(order) // 3], order[2 * len(order) // 3:]]
    P['blocks2'] = [sorted([order[i] for i in range(len(order)) if (i // 2) % 3 == k], key=lambda j: rank[j]) for k in range(3)]
    return P


COLOR_NAMES = ['orange', 'blue', 'red', 'green']; COLOR_COUNTS = [6, 6, 6, 7]

def assign_colors(L, pieces, hand, memo):
    """Her PARÇANIN kendi rengi (level tasarımcısı verisi): turuncu 6, mavi 6, kırmızı 6, yeşil 7. Hedef resimden TÜRETİLMEZ, slota bağlı DEĞİLDİR, çözüme bağlı DEĞİLDİR.
    Yalnız görsel kolaylık: sabit tohumlu karıştırma + 'erişilebilir eller'de 3 kartın farklı renk olma oranını artıran seçim; her kuyrukta 4 rengin de bulunması şart (renk slotu belli etmesin)."""
    states = list(memo.keys()); n = len(pieces); base = [c for c, k in zip(range(4), COLOR_COUNTS) for _ in range(k)]; best = None
    for seed in range(4000):
        rng = random.Random(seed); cols = base[:]; rng.shuffle(cols)
        if any(len({cols[L.pid[x]] for x in q}) < 4 for q in hand): continue
        if [cols[h] for h in L.cards(L.new_state())] != [0, 1, 2]: continue   # ilk el: turuncu · mavi · kırmızı (yalnız başlangıç; sonraki eller serbest)
        sc = 0.0
        for st in states:
            heads = [c for c in L.cards(st) if c is not None]; sc += len({cols[h] for h in heads}) / max(1, len(heads))
        sc /= len(states)
        if best is None or sc > best[0]: best = (sc, seed, cols)
    sc, seed, cols = best
    for i, p in enumerate(pieces): p['color'] = COLOR_NAMES[cols[i]]
    print('parça renkleri:', {c: sum(1 for p in pieces if p['color'] == c) for c in COLOR_NAMES}, 'ortalama farklı-renk oranı (3 kart):', round(sc, 3), 'tohum', seed)

if __name__ == '__main__':
    seed, pieces = build()
    print('hücre', len(TG), 'blok', len(pieces), 'boyutlar', sorted(len(p['cells']) for p in pieces), 'tohum', seed, 'farklı şekil', len({shape_key([tuple(x) for x in p['cells']]) for p in pieces}))
    L0 = Level(GRID, pieces, [[], [], []]) if False else None
    order = valid_order(None, pieces); print('geçerli sıra', [pieces[j]['id'] for j in order])
    pats = patterns(pieces, order); res = {}
    for name, qs in pats.items():
        hand = [[pieces[j]['id'] for j in q] for q in qs]; L = Level(GRID, pieces, hand)
        s = L.stats(); st = L.new_state(); trap0 = sum(1 for sl in range(3) if L.cards(st)[sl] is not None and L.place(st, sl)['sealed'])
        res[name] = (s, hand, trap0); print(name, [len(q) for q in qs], json.dumps(s), 'ilk elde tuzak:', trap0)
    pick = sys.argv[1] if len(sys.argv) > 1 else 'anatomy'
    s, hand, trap0 = res[pick]; L = Level(GRID, pieces, hand)
    # kazanan hat (geçerli sıra) + serpiştirilmiş kazanan hat (DP)
    memo, root = L.analyse(); assert root[0], 'çözülemez'
    assign_colors(L, pieces, hand, memo)
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
    # sentetik: stuck / yerleşemez kuralını sınar (oynanmaz)
    tg = '######\nE.AAAA\n######'; tp = [dict(id='T1', cells=[[1, 2], [1, 3]]), dict(id='T2', cells=[[1, 4], [1, 5]]), dict(id='T3', cells=[[1, 3], [1, 4]])]
    TL = Level(tg, tp[:2], [['T2'], ['T1'], []]); toy = [dict(name='toy_far_first', sequence=[0, 1], expected=TL.simulate([0, 1])), dict(name='toy_illegal', sequence=[2], expected=TL.simulate([2]))]
    TL2 = Level(tg, tp[:2], [['T1'], ['T2'], []]); toy += [dict(name='toy_near_first_seals', sequence=[0], expected=TL2.simulate([0]))]
    assert any(e.get('sealed') for c in toy for e in c['expected']), 'sentetik sealed yok'
    pal_used = sorted(set(cells.values())); cmap = {v: i for i, v in enumerate(pal_used)}
    lv = dict(id='cat-01', name='Blok Resim 01 — Kedi', w=BOARD, h=BOARD, grid=GRID, cells=len(TG), palette=[PAL[v] for v in pal_used], colors=[cmap[cells[p]] for p in TG],
              pieces=pieces, hand=hand, pattern=pick, stats=s)
    S = os.path.join(H, '..', 'src')
    open(os.path.join(S, 'level.js'), 'w', encoding='utf-8').write('window.BI_LEVEL = ' + json.dumps(lv, ensure_ascii=False) + ';\n')
    vec = [dict(level_id=lv['id'], grid=GRID, pieces=pieces, hand=hand, cases=cases), dict(level_id='TOY', grid=tg, pieces=tp[:2], hand=[['T2'], ['T1'], []], cases=toy[:2]), dict(level_id='TOY2', grid=tg, pieces=tp[:2], hand=[['T1'], ['T2'], []], cases=toy[2:])]
    open(os.path.join(S, 'vectors.js'), 'w', encoding='utf-8').write('window.BI_VECTORS = ' + json.dumps(vec) + ';\n')
    json.dump(vec, open(os.path.join(H, '..', 'tests', 'vectors.json'), 'w'))
    json.dump(dict(hand=hand, win=winA, win_mixed=winB, stats=s, order=[pieces[j]['id'] for j in order]), open(os.path.join(H, '..', 'tests', 'level_info.json'), 'w'), indent=1)
    print('yazıldı; seçilen', pick, json.dumps(s)); print('kazanan hat', winA); print('serpiştirilmiş', winB)

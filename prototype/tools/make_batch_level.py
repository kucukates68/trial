"""CAT96 GÖNDERİ seviyesi (yalnız bu seviye için elle kurulmuş veri; genel üretici DEĞİL).
Hedef: 96×96 pixel-art kedinin 4227 dolu pikseli (tools/cat_cells.json). Kediyi 10 anatomik BÖLGE'ye ayırıyoruz (kulaklar, baş, yüz, boyun/omuz, göğüs/yan,
karın, patiler, kuyruk üst/alt). Bir gönderi = (bölge, adet): bölgenin erişilebilir en derin pikselinden büyüyen bağlı küme (bkz. batch_ref.choose_batch).
Bölge sınırları elle yerleştirilmiş tohumlardan (Dijkstra) türetilir; gönderi kuyrukları 3 slot (baş / gövde / kuyruk+ayak şeritleri) için elle seçilmiş boyut döngüleridir.
Kuyruklar, 'girişten bölge-komşuluk BFS'inin tersi' geçerli sıranın alt dizisidir ⇒ seviye kesin çözülebilir (kesin DP ile ayrıca doğrulanır)."""
import json, os, sys, heapq, math, random
from collections import deque
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from batch_ref import BLevel, check_equivalence

cj = json.load(open(os.path.join(H, 'cat_cells.json'))); N = cj['N']
cat = {(i // N, i % N) for i, c in enumerate(cj['idx']) if c}
E = (N - 1, N // 2); lastcat = max(r for r, c in cat if c == E[1]); FLOOR = [(r, E[1]) for r in range(lastcat + 1, N - 1)]
grid = [['#'] * N for _ in range(N)]
for r, c in cat: grid[r][c] = 'A'
for r, c in FLOOR: grid[r][c] = '.'
grid[E[0]][E[1]] = 'E'; GRID = '\n'.join(''.join(r) for r in grid)

SEEDS = [('earL', 32, 14), ('earR', 64, 14), ('forehead', 48, 22), ('headTopL', 33, 26), ('headTopR', 63, 26), ('eyeL', 36, 36), ('eyeR', 60, 36),
         ('cheekL', 30, 46), ('cheekR', 66, 46), ('muzzle', 48, 46), ('chin', 48, 56), ('shoulderL', 32, 60), ('shoulderR', 64, 60), ('chest', 48, 68),
         ('flankL', 28, 72), ('flankR', 68, 72), ('belly', 48, 80), ('rumpL', 32, 84), ('pawL', 39, 88), ('pawR', 57, 88),
         ('tailBase', 72, 86), ('tailMid', 87, 78), ('tailUp', 87, 66), ('tailTip', 80, 56)]
ZONES = [('earL', ['earL']), ('earR', ['earR']), ('head', ['forehead', 'headTopL', 'headTopR', 'eyeL', 'eyeR']), ('face', ['cheekL', 'cheekR', 'muzzle']),
         ('neck', ['chin', 'shoulderL', 'shoulderR']), ('chest', ['chest', 'flankL', 'flankR']), ('belly', ['belly', 'rumpL']), ('paws', ['pawL', 'pawR']),
         ('tailUp', ['tailUp', 'tailTip']), ('tailLow', ['tailMid', 'tailBase'])]
LANES = [['earL', 'earR', 'head', 'face'], ['neck', 'chest', 'belly', 'paws'], ['tailUp', 'tailLow']]     # slot 0 = baş, slot 1 = gövde, slot 2 = kuyruk
LANE_SIZES = [[132, 108, 156, 120, 96], [96, 78, 114, 90, 72], [60, 48, 72, 54, 42]]                           # slot başına gönderi boyutu döngüsü (bölge sınırında son gönderi kalanı alır)
def wgt(r, c): return 1 + 0.7 * math.sin(c * 0.62 + r * 0.37) * math.cos(r * 0.51 - c * 0.29)

def regions():
    owner = {}; pq = []
    for k, (nm, x, y) in enumerate(SEEDS):
        p = min(cat, key=lambda q: (q[0] - y) ** 2 + (q[1] - x) ** 2); heapq.heappush(pq, (0.0, k, p))
    while pq:
        d, k, p = heapq.heappop(pq)
        if p in owner: continue
        owner[p] = k
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v = (p[0] + dr, p[1] + dc)
            if v in cat and v not in owner: heapq.heappush(pq, (d + wgt(*v), k, v))
    return owner

owner = regions(); name2zone = {}
for zi, (zn, regs) in enumerate(ZONES):
    for rn in regs: name2zone[[s[0] for s in SEEDS].index(rn)] = zi
tg = sorted(cat); ZONE = [name2zone[owner[p]] for p in tg]; ZN = [z[0] for z in ZONES]
zsize = [ZONE.count(i) for i in range(len(ZONES))]

def split(S, sizes, minlast=24):
    out = []; i = 0
    while S > 0:
        k = sizes[i % len(sizes)]; i += 1
        if S - k < minlast: k = S
        out.append(k); S -= k
    return out

def build_hand(order_idx):
    """order_idx: bölge indekslerinin geçerli (kazandıran) sırası. Slot kuyruğu = o slotun bölgeleri bu sırayla, her biri boyut döngüsüyle bölünmüş."""
    hand = []
    for lane, sizes in zip(LANES, LANE_SIZES):
        zs = sorted((ZN.index(z) for z in lane), key=lambda z: order_idx.index(z)); q = []; carry = 0
        for z in zs:
            for k in split(zsize[z], sizes[carry % len(sizes):] + sizes[:carry % len(sizes)]): q.append([z, k])
            carry += 1
        hand.append(q)
    return hand

def valid_zone_order():
    adj = {i: set() for i in range(len(ZONES))}
    for t, nb in enumerate(TNB):
        for u in nb:
            if ZONE[t] != ZONE[u]: adj[ZONE[t]].add(ZONE[u]); adj[ZONE[u]].add(ZONE[t])
    first = {ZONE[t] for t in range(len(tg)) if any((tg[t][0] + dr, tg[t][1] + dc) in set(FLOOR) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    disc = []; seen = set(first); q = deque(sorted(first))
    while q:
        u = q.popleft(); disc.append(u)
        for v in sorted(adj[u]):
            if v not in seen: seen.add(v); q.append(v)
    return disc[::-1]

if __name__ == '__main__':
    tof = {p: i for i, p in enumerate(tg)}
    TNB = [[tof[(r + dr, c + dc)] for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (r + dr, c + dc) in tof] for (r, c) in tg]
    print('hücre', len(tg), 'bölge boyutları', dict(zip(ZN, zsize)))
    order = valid_zone_order(); print('geçerli bölge sırası', [ZN[z] for z in order])
    hand = build_hand(order); print('kuyruk uzunlukları', [len(q) for q in hand], 'toplam', sum(k for q in hand for _, k in q))
    for s, q in enumerate(hand): print(' slot', s, [(ZN[z], k) for z, k in q][:6], '...')
    L = BLevel(GRID, ZONE, hand)
    # geçerli sıra: bölgeleri sırayla, her bölgenin gönderilerini kuyruk sırasıyla yolla; hiçbiri mühürlemeden bitmeli
    st = L.new_state(); seq = []; ptr = [0, 0, 0]; won = False
    allb = []
    for z in order:
        for s in range(3):
            for qi, (zz, k) in enumerate(hand[s]):
                if zz == z: allb.append((s, qi))
    for s, qi in allb:
        assert ptr[s] == qi, ('kuyruk sırası geçerli sırayla uyumsuz', s, qi, ptr)
        r = L.dispatch_fast(st, s); assert r is not None and not r['sealed'] and not r['stuck'] or (r and r['won']), ('geçerli sıra çalışmıyor', s, qi, ZN[hand[s][qi][0]], r and (len(r['sealed']), r['stuck']))
        seq.append(s); st = r['state']; ptr[s] += 1
    assert r['won']; print('geçerli sıra OK:', len(seq), 'gönderi')
    print('literal = hızlı yol:', check_equivalence(L, random.Random(5)), 'rasgele durumda doğrulandı')
    stats = L.stats(); print('kesin çözücü:', json.dumps(stats))
    memo, _root = L.analyse(); mixed = []; stm = L.new_state(); k = 0
    while True:   # üçlü döngüyle serpiştirilmiş (her slottan sırayla) başka bir KAZANAN hat: slotlar arası karar anlarını gösterir
        win, p, cnt, moves = memo[stm]; good = [m for m in moves if m[1]]; pref = [m for m in good if m[0] == k % 3]; m = (pref or good)[0]; mixed.append(m[0]); k += 1
        if m[4] == 'won': break
        stm = m[5]
    print('serpiştirilmiş kazanan hat:', len(mixed), 'gönderi')
    lv = dict(id='CAT96', name='Pixel kedi — gönderi inşası', grid=GRID, art=True, w=N, h=N, cells=len(tg), batch=dict(zones=ZONE, zone_names=ZN, hand=hand),
              palette=dict(colors=['#f2a14a'], names=['Gönderi']), stats=stats)
    # parity vektörleri: kazanan dizi + el-uyumlu rasgele oyunlar + yasadışı (literal hücre-hücre referans)
    rng = random.Random(21); cases = [dict(name='winning', sequence=seq), dict(name='winning_mixed', sequence=mixed)]
    for i in range(5):
        st = L.new_state(); sq = []
        while True:
            opts = [s for s, o in enumerate(L.options(st)) if o is not None]
            if not opts: break
            s = rng.choice(opts); sq.append(s); r = L.dispatch_fast(st, s)
            if r['won'] or r['sealed'] or r['stuck']: break
            st = r['state']
        cases.append(dict(name='hand_random%d' % i, sequence=sq))
    cases.append(dict(name='illegal_empty_slot', sequence=[0] * 40))
    for c in cases: c['expected'] = L.simulate(c['sequence'])
    S = os.path.join(H, '..', 'src')
    open(os.path.join(S, 'levels_image.js'), 'w', encoding='utf-8').write('window.CB_LEVELS.push(' + json.dumps(lv, ensure_ascii=False) + ');\n')
    vec = dict(level_id=lv['id'], grid=GRID, batch=lv['batch'], cases=cases)
    open(os.path.join(S, 'vectors_image.js'), 'w', encoding='utf-8').write('window.CB_VECTORS.levels.push(' + json.dumps(vec) + ');\n')
    # oyuncu seviyesinde (toplam adet = hücre sayısı) stuck/yerleşemez hiç oluşmaz; kuralı sınamak için küçük SENTETİK vektör seviyesi (oynanmaz)
    toy_grid = '##############\nE.AAAAAAAAAA##\n##############'; toy_hand = [[[0, 4], [0, 4]], [[0, 5]], []]
    TL = BLevel(toy_grid, [0] * 10, toy_hand); tcases = []
    for nm, sq in [('toy_stuck_after_two', [0, 0]), ('toy_stuck_after_three', [1, 0]), ('toy_illegal_empty_slot', [2]), ('toy_won_never', [1, 0, 0])]:
        tcases.append(dict(name=nm, sequence=sq, expected=TL.simulate(sq)))
    assert any(e.get('stuck') for c in tcases for e in c['expected']), 'sentetik seviyede stuck üretilemedi'
    tvec = dict(level_id='TOY_STUCK', grid=toy_grid, batch=dict(zones=[0] * 10, hand=toy_hand), cases=tcases)
    open(os.path.join(S, 'vectors_image.js'), 'a', encoding='utf-8').write('window.CB_VECTORS.levels.push(' + json.dumps(tvec) + ');\n')
    json.dump(dict(levels=[vec, tvec]), open(os.path.join(H, '..', 'tests', 'image_vectors.json'), 'w'))
    json.dump(dict(hand=hand, zone_names=ZN, win_seq=seq, win_seq_mixed=mixed, stats=stats), open(os.path.join(H, '..', 'tests', 'image_level_info.json'), 'w'))
    print('yazıldı: CAT96 gönderi seviyesi; vaka', len(cases))

"""Yüksek çözünürlüklü RESİM seviyesi (elle yazılmış tek kedi): 64x64 gizli grid + 24 organik bölge (parça) + 3 slotlu el.
Gizli grid, kedi çiziminin (src/cat_art.js) maskesidir (tools/cat_cells.json ← node tools/render_cat.js).
Bölgeler ELLE yerleştirilmiş 24 tohum noktasından büyütülür (düzensiz/organik sınır için hafif sabit gürültülü Dijkstra); üretici/arama yoktur.
Her parçanın hedef bölgesi SABİT (piece.fixed): olası tek konum o bölgedir; bölgedeki her hücre boş + girişten erişilebilir olmalı.
El: 3 slot, her slotun elle belirlenmiş sabit kuyruğu (queue); gönderilen kartın yerine yalnız o slotun sıradaki parçası gelir."""
import json, os, sys, heapq, math, random
from collections import deque, Counter
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from piece_ref import PLevel

_cj = json.load(open(os.path.join(H, 'cat_cells.json'))); N = _cj['N']
cat = {(i // N, i % N) for i, c in enumerate(_cj['idx']) if c}
# en büyük 4-bağlantılı bileşen
comps = []; left = set(cat)
while left:
    s = next(iter(left)); comp = {s}; q = deque([s]); left.discard(s)
    while q:
        u = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v = (u[0] + dr, u[1] + dc)
            if v in left: left.discard(v); comp.add(v); q.append(v)
    comps.append(comp)
cat = max(comps, key=len); assert len(cat) >= 3000

# giriş: alt orta; görünmez zemin sütunu
E = (N - 1, N // 2); lastcat = max(r for r, c in cat if c == E[1]); FLOOR = [(r, E[1]) for r in range(lastcat + 1, N - 1)]
grid = [['#'] * N for _ in range(N)]
for r, c in cat: grid[r][c] = 'A'
for r, c in FLOOR:
    assert (r, c) not in cat; grid[r][c] = '.'
grid[E[0]][E[1]] = 'E'

# ---- elle yerleştirilmiş tohumlar (x=sütun, y=satır) → bölgeler
SEEDS = [('earL', 32, 14), ('earR', 64, 14), ('forehead', 48, 22), ('headTopL', 33, 26), ('headTopR', 63, 26), ('eyeL', 36, 36), ('eyeR', 60, 36),
         ('cheekL', 30, 46), ('cheekR', 66, 46), ('muzzle', 48, 46), ('chin', 48, 56), ('shoulderL', 32, 60), ('shoulderR', 64, 60), ('chest', 48, 68),
         ('flankL', 28, 72), ('flankR', 68, 72), ('belly', 48, 80), ('rumpL', 32, 84), ('pawL', 39, 88), ('pawR', 57, 88),
         ('tailBase', 72, 86), ('tailMid', 87, 78), ('tailUp', 87, 66), ('tailTip', 80, 56)]
def snap(x, y):
    best = min(cat, key=lambda p: (p[0] - y) ** 2 + (p[1] - x) ** 2); return best
def wgt(r, c): return 1 + 0.7 * math.sin(c * 0.62 + r * 0.37) * math.cos(r * 0.51 - c * 0.29)   # düzensiz (piksel kümesi gibi) sınırlar
dist = {}; owner = {}; pq = []
for k, (nm, x, y) in enumerate(SEEDS):
    p = snap(x, y); heapq.heappush(pq, (0.0, k, p))
while pq:
    d, k, p = heapq.heappop(pq)
    if p in owner: continue
    owner[p] = k
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        v = (p[0] + dr, p[1] + dc)
        if v in cat and v not in owner: heapq.heappush(pq, (d + wgt(*v), k, v))
assert len(owner) == len(cat)
regions = {k: sorted(p for p, kk in owner.items() if kk == k) for k in range(len(SEEDS))}
for k, rc in regions.items(): assert len(rc) >= 40, (SEEDS[k][0], len(rc))
pieces = [dict(id='P%02d' % (k + 1), ch='A', cells=[list(p) for p in rc], fixed=True, name=SEEDS[k][0]) for k, rc in regions.items()]
GRID = '\n'.join(''.join(r) for r in grid)
L = PLevel(GRID, [{k: v for k, v in p.items() if k != 'name'} for p in pieces])
pid = {p['id']: i for i, p in enumerate(pieces)}

# ---- geçerli (kazandıran) sıra: girişten parça-komşuluk BFS'inin TERSİ ("en uzaktan başla")
cell_piece = {tuple(c): i for i, p in enumerate(pieces) for c in p['cells']}
adj = {i: set() for i in range(len(pieces))}
for (r, c), i in cell_piece.items():
    for dr, dc in ((1, 0), (0, 1)):
        j = cell_piece.get((r + dr, c + dc))
        if j is not None and j != i: adj[i].add(j); adj[j].add(i)
first = {cell_piece[(r, c)] for (r, c) in cat if any((r + dr, c + dc) in set(FLOOR) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
disc = []; seen = set(first); q = deque(sorted(first))
while q:
    u = q.popleft(); disc.append(u)
    for v in sorted(adj[u]):
        if v not in seen: seen.add(v); q.append(v)
order = disc[::-1]
st = (0, 0)
for j in order:
    r = L.place(st, j); assert r is not None and not r['sealed'], ('geçersiz sıra', pieces[j]['id']); st = r['state']
assert r['won']
rank = {j: k for k, j in enumerate(order)}

# ---- el kuyrukları (3 slot): her kuyruk geçerli sıranın ALT DİZİSİ ⇒ seviye kesin çözülebilir
def dp(queues):
    memo = {}; place_cache = {}
    def mask_of(ptr):
        f = 0; u = 0
        return None
    def rec(ptr, state):
        key = ptr
        if key in memo: return memo[key]
        heads = [queues[k][ptr[k]] for k in range(3) if ptr[k] < len(queues[k])]
        out = []
        for k in range(3):
            if ptr[k] >= len(queues[k]): continue
            j = queues[k][ptr[k]]; res = L.place(state, j); np = list(ptr); np[k] += 1
            if res['won']: out.append((j, 1, 1.0, 'won', 1))
            elif res['sealed'] or res['stuck']: out.append((j, 0, 0.0, 'sealed', 0))
            else:
                sub = rec(tuple(np), res['state']); out.append((j, sub[0], sub[1], 'cont', sub[2]))
        win = any(o[1] for o in out); p = sum(o[2] for o in out) / len(out) if out else 0.0
        cnt = sum(o[4] for o in out)
        memo[key] = (win, p, cnt, out); return memo[key]
    root = rec((0, 0, 0), (0, 0))
    return memo, root
def metrics(queues):
    memo, root = dp(queues); dec = 0; inst = 0; delay = 0; free = 0
    seen = set(); stack = [(0, 0, 0)]
    while stack:
        ptr = stack.pop()
        if ptr in seen: continue
        seen.add(ptr); win, p, cnt, out = memo[ptr]
        if not win: continue
        wins = [o for o in out if o[1]]; losers = [o for o in out if not o[1]]
        if losers and wins: dec += 1; inst += sum(1 for o in losers if o[3] == 'sealed'); delay += sum(1 for o in losers if o[3] != 'sealed')
        elif len(wins) == len(out) and len(out) > 1: free += 1
        for k in range(3):
            if ptr[k] < len(queues[k]):
                j = queues[k][ptr[k]]
                if any(o[0] == j and o[1] and o[3] == 'cont' for o in out):
                    np = list(ptr); np[k] += 1; stack.append(tuple(np))
    return dict(solvable=bool(root[0]), p_random=round(root[1], 5), winning_orders=root[2], decision_states=dec, free_states=free, trap_instant=inst, trap_delayed=delay, n_states=len(memo))

def by_rank(js): return sorted(js, key=lambda j: rank[j])
NAMES = {p['name']: i for i, p in enumerate(pieces)}
PATTERNS = {
    'round_robin': lambda: [by_rank([j for j in order if rank[j] % 3 == k]) for k in range(3)],
    'anatomy': lambda: [by_rank([NAMES[n] for n in ns]) for ns in (
        ['earL', 'earR', 'forehead', 'headTopL', 'headTopR', 'eyeL', 'eyeR', 'cheekL'],
        ['cheekR', 'muzzle', 'chin', 'shoulderL', 'shoulderR', 'chest', 'flankL', 'flankR'],
        ['belly', 'rumpL', 'pawL', 'pawR', 'tailBase', 'tailMid', 'tailUp', 'tailTip'])],
    'rank_thirds': lambda: [order[0:8], order[8:16], order[16:24]],
    'blocks3': lambda: [by_rank([order[i] for i in range(24) if (i // 3) % 3 == k]) for k in range(3)],
}
def build(pattern='anatomy'):
    from piece_ref import make_vectors  # noqa (yalnız bağımlılık denetimi)
    queues = PATTERNS[pattern](); stats = metrics(queues); memo, root = dp(queues); rng = random.Random(11)
    lv = dict(id='CAT96', name='Pixel kedi — resim inşası', grid=GRID, art=True, w=N, h=N, cells=L.n,
              pieces=pieces, hand=[[pieces[j]['id'] for j in q] for q in queues], pattern=pattern,
              palette=dict(colors=['#f2a14a'], names=['Parça']), stats=stats)
    # parity vektörleri (motor düzeyi): kazanan dizi, el-uyumlu rasgele oyunlar, serbest sıralı rasgele oyunlar, yasadışı tekrar
    cases = []
    def win_seq():
        ptr = (0, 0, 0); seq = []
        while True:
            win, p, cnt, out = memo[ptr]; ch = [o for o in out if o[1]]; o = rng.choice(ch); seq.append(o[0])
            if o[3] == 'won': return seq
            k = [kk for kk in range(3) if ptr[kk] < len(queues[kk]) and queues[kk][ptr[kk]] == o[0]][0]
            ptr = tuple(ptr[i] + (1 if i == k else 0) for i in range(3))
    for i in range(2): cases.append(dict(name=f'winning{i}', sequence=win_seq()))
    for i in range(6):   # el-uyumlu rasgele
        ptr = [0, 0, 0]; st = (0, 0); seq = []
        while True:
            ks = [k for k in range(3) if ptr[k] < len(queues[k])]
            if not ks: break
            k = rng.choice(ks); j = queues[k][ptr[k]]; seq.append(j); res = L.place(st, j); ptr[k] += 1
            if res['won'] or res['sealed'] or res['stuck']: break
            st = res['state']
        cases.append(dict(name=f'hand_random{i}', sequence=seq))
    for i in range(4):   # serbest sıra (el kısıtı yok)
        js = list(range(24)); rng.shuffle(js); cases.append(dict(name=f'free_random{i}', sequence=js[:rng.randint(1, 8)]))
    cases.append(dict(name='illegal_repeat', sequence=[0, 0]))
    for c in cases: c['expected'] = L.simulate(c['sequence'])
    S = os.path.join(H, '..', 'src')
    open(os.path.join(S, 'levels_image.js'), 'w', encoding='utf-8').write('window.CB_LEVELS.push(' + json.dumps(lv, ensure_ascii=False) + ');\n')
    vec = dict(level_id=lv['id'], grid=GRID, pieces=[{k: v for k, v in p.items() if k != 'name'} for p in pieces], cases=cases)
    open(os.path.join(S, 'vectors_image.js'), 'w', encoding='utf-8').write('window.CB_VECTORS.levels.push(' + json.dumps(vec) + ');\n')
    json.dump(dict(levels=[vec]), open(os.path.join(H, '..', 'tests', 'image_vectors.json'), 'w'))
    json.dump(dict(queues=lv['hand'], order=[pieces[j]['id'] for j in order], stats=stats), open(os.path.join(H, '..', 'tests', 'image_level_info.json'), 'w'), indent=1)
    print('yazıldı: CAT96', L.n, 'hücre', L.P, 'parça; vaka', len(cases), json.dumps(stats))
    print('el kuyrukları', lv['hand'])


if __name__ == '__main__':
    pick = sys.argv[1] if len(sys.argv) > 1 else None
    if pick == 'build': build(sys.argv[2] if len(sys.argv) > 2 else 'anatomy'); sys.exit(0)
    print('hücre', L.n, 'parça', L.P, 'parça boyutları', sorted(len(p['cells']) for p in pieces))
    print('geçerli sıra', [pieces[j]['name'] for j in order])
    res = {}
    for name, fn in PATTERNS.items():
        if pick and name != pick and pick != 'all': continue
        qs = fn(); assert sorted(sum(qs, [])) == list(range(24))
        res[name] = metrics(qs); print(name, json.dumps(res[name]), flush=True)

import sys, itertools, random, json
sys.path.insert(0, '.')
from labkit import *
def splits(n, sizes):
    return sizes
def search(B, sizes=None, limit=None, seed=1):
    n = B.n; names = B.names
    if sizes is None: base = n // 3; sizes = [base + (1 if i < n % 3 else 0) for i in range(3)]
    perms = itertools.permutations(names); out = []
    if limit:
        rnd = random.Random(seed); perms = (rnd.sample(names, n) for _ in range(limit))
    seen = set()
    for pm in perms:
        q = [list(pm[:sizes[0]]), list(pm[sizes[0]:sizes[0] + sizes[1]]), list(pm[sizes[0] + sizes[1]:])]
        key = tuple(sorted(tuple(x) for x in q))
        if key in seen: continue
        seen.add(key)
        A = Analysis(B, q); f = A.features()
        if not f['solvable']: continue
        f['queues'] = q; out.append(f)
    return out
def score(f):
    if f.get('start_safe') != 3: return -1
    c = f['start_closes']; allc = sum(1 for v in c.values() if v)
    s = 0
    s += 10 * allc                                   # her ilk hamle başka bir kartı kapatıyor
    s += 6 * min(f['start_win_moves'], 2)            # ≥2 kazanan ilk hamle
    s += 3 * min(f.get('deepsurv', 0), 5) + (4 if f['fork'] else 0)
    s += min(f['infl'], 6) + min(f['fork'], 4)
    s += 10 * max(0, 1 - abs(f['safe_win'] - 0.5) * 2)       # 1-hamle güvenli ajan tek başına yetmesin (≈%50)
    s += 2 * min(f['midsurv'], 4) - 2 * max(0, f['surv_max'] - 4)    # sonuç 1-3 hamle sonra belli olsun
    if f['orders'] < 2: s -= 20
    return s
if __name__ == '__main__':
    pass

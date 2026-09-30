"""Algorithmic colour maps on a fixed geometry + colour-structure descriptors.

CM1  large contiguous blobs (farthest-point Voronoi)
CM2  roughly balanced colours (equal-size angular sectors)
CM3  one dominant colour + (k-1) small compact patches (~12% each)
CM4  few colour transitions (unequal vertical bands, left->right)
CM5  many colour transitions ((r+2c) mod k: every neighbouring pair differs)
CM6  same colour split into >=3 separate islands (5-6 Voronoi seeds mapped 0,1,0,2,0[,3])
CM7  colour order along (ring) depth alternates: 2k equal-count bands cycling
CM8  colour order along (ring) depth constant: k equal-count bands outer->inner
CM9  constant order along row depth (k equal-count bands top->bottom)   [bottom/top-entrance proxy]
CM10 alternating order along row depth (2k bands cycling)
"""
from __future__ import annotations
import math
from collections import deque, Counter

CM_NAMES = ['CM1', 'CM2', 'CM3', 'CM4', 'CM5', 'CM6', 'CM7', 'CM8', 'CM9', 'CM10']
CM_DESC = {
    'CM1': 'büyük bitişik bölgeler', 'CM2': 'dengeli renkler', 'CM3': 'tek baskın + küçük yamalar',
    'CM4': 'az geçiş (dikey bantlar)', 'CM5': 'çok geçiş (her komşu farklı)', 'CM6': 'aynı renk çok ada',
    'CM7': 'derinlikte sıra değişken', 'CM8': 'derinlikte sıra sabit',
    'CM9': 'satır-derinlikte sabit', 'CM10': 'satır-derinlikte değişken'}


def _nbrs(cells):
    S = set(cells)
    return {c: [(c[0] + dr, c[1] + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (c[0] + dr, c[1] + dc) in S]
            for c in cells}


def _ring_depth(cells):
    S = set(cells)
    d = {}
    q = deque()
    for c in cells:
        if any((c[0] + dr, c[1] + dc) not in S for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            d[c] = 1
            q.append(c)
    nb = _nbrs(cells)
    while q:
        u = q.popleft()
        for v in nb[u]:
            if v not in d:
                d[v] = d[u] + 1
                q.append(v)
    return d


def _d2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _farthest_seeds(cells, m, start_rank=0):
    n = len(cells)
    cr = sum(r for r, c in cells) / n
    cc = sum(c for r, c in cells) / n
    order = sorted(cells, key=lambda x: (-((x[0] - cr) ** 2 + (x[1] - cc) ** 2), x))
    seeds = [order[min(start_rank, len(order) - 1)]]
    while len(seeds) < m:
        best = max(cells, key=lambda x: (min(_d2(x, s) for s in seeds), [-x[0], -x[1]]))
        seeds.append(best)
    return seeds


def _voronoi(cells, seeds):
    lab = {}
    for c in cells:
        lab[c] = min(range(len(seeds)), key=lambda i: (_d2(c, seeds[i]), i))
    return lab


def _bands(order, fractions):
    n = len(order)
    cum = []
    a = 0.0
    for f in fractions:
        a += f
        cum.append(a)
    lab = {}
    for i, c in enumerate(order):
        x = (i + 0.5) / n
        k = 0
        while k < len(cum) - 1 and x > cum[k]:
            k += 1
        lab[c] = k
    return lab


def _components(lab, nb):
    seen = set()
    comps = Counter()
    for c in lab:
        if c in seen:
            continue
        col = lab[c]
        comps[col] += 1
        stack = [c]
        seen.add(c)
        while stack:
            u = stack.pop()
            for v in nb[u]:
                if v not in seen and lab[v] == col:
                    seen.add(v)
                    stack.append(v)
    return comps


def generate(mask, cm: str, k: int = 3) -> dict:
    cells = sorted(mask)
    n = len(cells)
    nb = _nbrs(cells)
    cr = sum(r for r, c in cells) / n
    cc = sum(c for r, c in cells) / n
    if cm == 'CM1':
        return _voronoi(cells, _farthest_seeds(cells, k))
    if cm == 'CM2':
        order = sorted(cells, key=lambda x: (math.atan2(x[0] - cr, x[1] - cc), _d2(x, (cr, cc)), x))
        return {c: min(k - 1, i * k // n) for i, c in enumerate(order)}
    if cm == 'CM3':
        rd = _ring_depth(cells)
        lab = {c: 0 for c in cells}
        p = max(3, round(0.12 * n))
        seeds = []
        s1 = max(cells, key=lambda x: (rd[x], [-x[0], -x[1]]))
        seeds.append(s1)
        bnd = [c for c in cells if rd[c] == 1]
        if k >= 3:
            seeds.append(max(bnd, key=lambda x: (_d2(x, s1), [-x[0], -x[1]])))
        while len(seeds) < k - 1:
            seeds.append(max(cells, key=lambda x: (min(_d2(x, s) for s in seeds), [-x[0], -x[1]])))
        seeds = seeds[:k - 1]
        for j, sd in enumerate(seeds, start=1):
            if lab[sd] != 0:
                cand = [c for c in cells if lab[c] == 0]
                sd = min(cand, key=lambda x: (_d2(x, sd), x))
            got = {sd}
            q = deque([sd])
            lab[sd] = j
            while q and len(got) < p:
                u = q.popleft()
                for v in sorted(nb[u]):
                    if lab[v] == 0 and v not in got and len(got) < p:
                        lab[v] = j
                        got.add(v)
                        q.append(v)
        return lab
    if cm == 'CM4':
        order = sorted(cells, key=lambda x: (x[1], x[0]))
        fr = [0.40, 0.35, 0.25] if k == 3 else [0.35, 0.25, 0.20, 0.20]
        return _bands(order, fr)
    if cm == 'CM5':
        return {c: (c[0] + 2 * c[1]) % k for c in cells}
    if cm == 'CM6':
        m = 6
        mp = [0, 1, 0, 2, 0, 1] if k == 3 else [0, 1, 0, 2, 0, 3]
        best, bestc, bestlab = None, -1, None
        for start in range(10):
            seeds = _farthest_seeds(cells, m, start)
            seeds = sorted(seeds, key=lambda x: (math.atan2(x[0] - cr, x[1] - cc), x))   # neighbours around the centroid differ in colour
            vor = _voronoi(cells, seeds)
            lab = {c: mp[v] for c, v in vor.items()}
            comps = _components(lab, nb)
            if len(set(lab.values())) == k and comps[0] > bestc:
                best, bestc, bestlab = lab, comps[0], lab
            if bestc >= 3:
                break
        return bestlab if bestlab is not None else lab
    if cm in ('CM7', 'CM8'):
        rd = _ring_depth(cells)
        order = sorted(cells, key=lambda x: (rd[x], math.atan2(x[0] - cr, x[1] - cc), x))
        if cm == 'CM8':
            return {c: min(k - 1, i * k // n) for i, c in enumerate(order)}
        return {c: (i * 2 * k // n) % k for i, c in enumerate(order)}
    if cm in ('CM9', 'CM10'):
        order = sorted(cells, key=lambda x: (x[0], x[1]))
        if cm == 'CM9':
            return {c: min(k - 1, i * k // n) for i, c in enumerate(order)}
        return {c: (i * 2 * k // n) % k for i, c in enumerate(order)}
    raise KeyError(cm)


# ------------------------------------------------------------------ descriptors
def _entropy(counts):
    n = sum(counts)
    return -sum((c / n) * math.log2(c / n) for c in counts if c)


def seq_stats(seq):
    """transition statistics of a colour sequence."""
    n = len(seq)
    if n < 2:
        return dict(trans=0, trans_per_cell=0.0, runs=1, mean_run=float(n))
    tr = sum(1 for a, b in zip(seq, seq[1:]) if a != b)
    runs = tr + 1
    return dict(trans=tr, trans_per_cell=tr / n, runs=runs, mean_run=n / runs)


def colormap_descriptors(lab: dict, k: int) -> dict:
    cells = sorted(lab)
    n = len(cells)
    nb = _nbrs(cells)
    counts = [sum(1 for v in lab.values() if v == i) for i in range(k)]
    p = [c / n for c in counts]
    comps = _components(lab, nb)
    edges = 0
    diff = 0
    for u in cells:
        for v in nb[u]:
            if u < v:
                edges += 1
                if lab[u] != lab[v]:
                    diff += 1
    obs_t = diff / max(edges, 1)
    exp_t = 1 - sum(x * x for x in p)
    rd = _ring_depth(cells)
    order = sorted(cells, key=lambda x: (rd[x], x))
    rs = seq_stats([lab[c] for c in order])
    return dict(
        cm_counts='/'.join(map(str, counts)), cm_dominant=max(p), cm_entropy=_entropy(counts),
        cm_entropy_norm=_entropy(counts) / math.log2(k),
        cm_comp_total=sum(comps.values()), cm_comp_max=max(comps.values()),
        cm_comp_mean=sum(comps.values()) / k,
        cm_trans_sp=obs_t, cm_clustering=(1 - obs_t / exp_t) if exp_t > 1e-9 else 0.0,
        ring_trans=rs['trans'], ring_trans_per_cell=rs['trans_per_cell'], ring_runs=rs['runs'],
        ring_mean_run=rs['mean_run'], ring_layers=max(rd.values()),
    )


def entrance_descriptors(L):
    """descriptors that depend on the access geometry (initial reach depth of every target)."""
    d0 = L.depth_profile()
    if any(x < 0 for x in d0):
        return dict(n_unreach=sum(1 for x in d0 if x < 0))
    order = sorted(range(L.n), key=lambda ti: (d0[ti], ti))
    seq = [L.tcolor[ti] for ti in order]
    st = seq_stats(seq)
    maxd = max(d0) or 1
    wt = 0.0
    for i in range(len(seq) - 1):
        if seq[i] != seq[i + 1]:
            wt += d0[order[i]] / maxd
    cut = sorted(d0)[int(0.8 * (L.n - 1))]
    deep = [L.tcolor[ti] for ti in range(L.n) if d0[ti] >= cut]
    dc = Counter(deep)
    return dict(n_unreach=0, ent_maxdepth=maxd, ent_meandepth=sum(d0) / L.n,
                ent_trans=st['trans'], ent_trans_per_cell=st['trans_per_cell'],
                ent_trans_per_wave=st['trans'] / max(L.waves_nominal, 1),
                ent_runs=st['runs'], ent_mean_run=st['mean_run'], ent_wtrans=wt,
                ent_wtrans_per_cell=wt / L.n,
                deep_colors=len(dc), deep_entropy=_entropy(list(dc.values())))


# ------------------------------------------------------------ region-colouring ablation
def region_partition(mask, R):
    """R farthest-point Voronoi regions; returns (cell->region, region adjacency set)."""
    cells = sorted(mask)
    seeds = _farthest_seeds(cells, R, 0)
    vor = _voronoi(cells, seeds)
    nb = _nbrs(cells)
    adj = set()
    for u in cells:
        for v in nb[u]:
            if vor[u] != vor[v]:
                adj.add((min(vor[u], vor[v]), max(vor[u], vor[v])))
    return vor, adj


def proper_colorings(R, adj, k, cap=4000):
    """all colourings of region graph with k colours, adjacent regions differ, every colour used,
    colour of region 0 fixed to 0 (removes label symmetry)."""
    nbrs = {i: set() for i in range(R)}
    for a, b in adj:
        nbrs[a].add(b); nbrs[b].add(a)
    out = []
    col = [-1] * R
    def rec(i, used):
        if len(out) >= cap:
            return
        if i == R:
            if used == k:
                out.append(tuple(col))
            return
        for c in range(min(k, used + 1)):        # canonical labelling (first-use order)
            if all(col[j] != c for j in nbrs[i] if j < i):
                col[i] = c
                rec(i + 1, max(used, c + 1))
        col[i] = -1
    rec(0, 0)
    return out


def region_labels(mask, R, k, idx, sample=40, seed=7):
    """idx-th (pseudo-randomly sampled) proper colouring of an R-region partition; None if out of range."""
    import random
    vor, adj = region_partition(mask, R)
    cols = proper_colorings(R, adj, k)
    if not cols:
        return None
    rng = random.Random(seed * 1000 + R)
    rng.shuffle(cols)
    cols = cols[:sample]
    if idx >= len(cols):
        return None
    return {c: cols[idx][vor[c]] for c in vor}


def region_count(mask, R, k, sample=40):
    vor, adj = region_partition(mask, R)
    return min(len(proper_colorings(R, adj, k)), sample)

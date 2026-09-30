"""Dominance-based colour-dependency descriptors (structure only; no solver, independent of W).

x must be placed before y  <=>  y dominates x (every entrance path to x passes through y).
Colour-level graph: edge cx -> cy  if some x (colour cx) is dominated by some y (colour cy != cx).
"""
import json, os, sys, itertools
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from puzzle_engine import Level
from run_experiments import make_labels, OUT
from puzzle_access import build_grid
import pandas as pd


def has_cycle(K, edges):
    adj = {i: [b for a, b in edges if a == i] for i in range(K)}
    state = {}
    def dfs(u):
        state[u] = 1
        for v in adj[u]:
            if state.get(v) == 1: return True
            if state.get(v) is None and dfs(v): return True
        state[u] = 2
        return False
    return any(state.get(i) is None and dfs(i) for i in range(K))


def dep_desc(args):
    src, cm, k, layout, scale, n = args
    try:
        lab = make_labels(src, cm, k, scale, n)
        if lab is None:
            return None
        L = Level(build_grid(lab, layout), 1)
        d0 = L.bfs(0)
        if any(d0[L.tnode[ti]] < 0 for ti in range(L.n)):
            return dict(src=src, cm=cm, k=k, layout=layout, scale=scale, syn_n=n, dep_unreach=True)
        dom = [[] for _ in range(L.n)]        # dom[y] = cells dominated by y
        for y in range(L.n):
            d = L.bfs(1 << y)
            dom[y] = [x for x in range(L.n) if x != y and d[L.tnode[x]] < 0]
        pairs = set(); shadowed = set(); same = 0; cross = 0
        for y in range(L.n):
            for x in dom[y]:
                if L.tcolor[x] != L.tcolor[y]:
                    pairs.add((L.tcolor[x], L.tcolor[y])); shadowed.add(x); cross += 1
                else:
                    same += 1
        K = L.K
        bidir = sum(1 for a, b in itertools.combinations(range(K), 2) if (a, b) in pairs and (b, a) in pairs)
        return dict(src=src, cm=cm, k=k, layout=layout, scale=scale, syn_n=n, dep_unreach=False,
                    dep_edges=len(pairs), dep_density=len(pairs) / (K * (K - 1)), dep_bidir=bidir,
                    dep_cycle=bool(has_cycle(K, pairs)), dep_shadow_frac=len(shadowed) / L.n,
                    dep_cross_per_cell=cross / L.n, dep_same_per_cell=same / L.n,
                    dep_maxdom=max(len(x) for x in dom) / L.n)
    except Exception as e:
        return dict(src=src, cm=cm, k=k, layout=layout, scale=scale, syn_n=n, dep_error=repr(e))


def main():
    keys = set()
    for name in ['broad', 'ab4', 'synth', 'size', 'wsweep', 'region']:
        p = os.path.join(OUT, f'{name}.jsonl')
        for line in open(p):
            r = json.loads(line)
            keys.add((r['src'], r['cm'], r['k'], r['layout'], r.get('scale', 1), r.get('syn_n', 0)))
    keys = sorted(keys)
    print(len(keys), 'unique structures', flush=True)
    with Pool(4) as pool:
        rows = [r for r in pool.imap_unordered(dep_desc, keys, chunksize=8) if r]
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, 'dep_descriptors.csv'), index=False)
    print(df.shape, 'errors', df.get('dep_error', pd.Series(dtype=object)).notna().sum())


if __name__ == '__main__':
    main()

"""Factorial / ablation sweeps for the colour-placement puzzle.  Output: results/<exp>.jsonl (+csv).

usage: python3 run_experiments.py <exp> [--procs 4] [--limit N]
  broad   8 silhouettes x 10 colour maps x 18 access layouts x 3 wave bins   (k=3)
  ab4     same factorial (subset of layouts) with k=4 colours for paired 3-vs-4 comparison
  synth   synthetic square pictures x 18 layouts x W sweep
  size    same colour structure, small/medium/large (integer upscale of the coloured picture)
  wsweep  real silhouettes: full W sweep on a colour-map x layout subset
  refine  high-resolution sweep around the most interesting broad-sweep regions (needs broad results)
"""
from __future__ import annotations
import json, math, os, sys, time, argparse, itertools
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from puzzle_engine import analyze
from puzzle_shapes import SILHOUETTES, silhouette, synthetic, SYNTH_NAMES, scale_mask_colors
from puzzle_colormaps import CM_NAMES, generate, colormap_descriptors, entrance_descriptors, region_labels, region_count
from puzzle_access import LAYOUTS, FAMILY, ONE_PER_FAMILY, build_grid, family_of, neighbours

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
BINS = {'w07_10': (7, 10, 8.5), 'w11_15': (11, 15, 13), 'w16_20': (16, 20, 18)}


def waves_for(counts, W):
    return sum(math.ceil(c / W) for c in counts)


def pick_W(counts, bin_name):
    lo, hi, tgt = BINS[bin_name]
    best = None
    for W in range(1, max(counts) + 1):
        w = waves_for(counts, W)
        if lo <= w <= hi:
            key = (abs(w - tgt), W)
            if best is None or key < best[0]:
                best = (key, W)
    return None if best is None else best[1]


def make_labels(src, cm, k, scale=1, n=8, seed=0):
    if src in SILHOUETTES:
        lab = generate(silhouette(src), cm, k)
    elif src.startswith('syn:'):
        lab = synthetic(src[4:], n, k, seed)
    elif src.startswith('reg:'):
        _, shp, R, idx = src.split(':')
        lab = region_labels(silhouette(shp), int(R), k, int(idx))
    else:
        raise KeyError(src)
    if scale > 1:
        lab = scale_mask_colors(lab, scale)
    return lab


def job(a):
    exp, src, cm, k, layout, binname, W, scale, n = a
    t0 = time.time()
    row = dict(exp=exp, src=src, cm=cm, k=k, layout=layout, family=family_of(layout), bin=binname,
               scale=scale, syn_n=n)
    try:
        lab = make_labels(src, cm, k, scale, n)
        row.update(colormap_dict(lab, k))
        counts = [sum(1 for v in lab.values() if v == i) for i in range(k)]
        if W is None:
            W = pick_W(counts, binname)
        if W is None:
            row.update(skipped=True, reason='no W in bin')
            return row
        grid = build_grid(lab, layout)
        res = analyze(grid, W, sims=1200, seed=hash((src, cm, layout, W)) & 0xffff, want_desc=entrance_descriptors,
                      extra=bool(os.environ.get('PUZZLE_EXTRA')))
        row.update(res)
        _bigint_fix(row)
    except Exception as e:                                  # keep sweep alive, record failure
        row.update(error=repr(e))
    row['sec'] = round(time.time() - t0, 3)
    return row


def _bigint_fix(row):
    for key in ('seq_raw', 'seq_canon'):
        v = row.get(key)
        if isinstance(v, int):
            row['log10_' + key] = math.log10(v) if v > 0 else 0.0
            if v > 2 ** 53:
                row[key] = float(v)


def colormap_dict(lab, k):
    return colormap_descriptors(lab, k)


# ------------------------------------------------------------------ job lists
def jobs_broad(k=3, layouts=None, exp='broad'):
    layouts = layouts or list(LAYOUTS)
    J = []
    for src in SILHOUETTES:
        for cm in CM_NAMES:
            for layout in layouts:
                for b in BINS:
                    J.append((exp, src, cm, k, layout, b, None, 1, 0))
    return J


def jobs_ab4():
    L = ['OPEN', 'COR1', 'BOT1', 'BOT3', 'SPL1', 'SPB1', 'SPB3', 'MUL1', 'MUL4']
    return jobs_broad(4, L, 'ab4') + jobs_broad(3, L, 'ab3')


def jobs_synth():
    J = []
    Wl = {8: [1, 2, 3, 4, 5, 6, 8, 10, 12, 16], 6: [1, 2, 3, 4, 6, 9]}
    for n, ws in Wl.items():
        for name in SYNTH_NAMES:
            for layout in LAYOUTS:
                for W in ws:
                    J.append(('synth', 'syn:' + name, 'SYN', 3, layout, f'W{W}', W, 1, n))
    return J


def jobs_size():
    J = []
    # (a) synthetic n=4 base, integer upscales -> 16/64/144/256 cells, same colour topology
    L = ['OPEN', 'COR1', 'BOT1', 'SPL1', 'SPB1', 'MUL1']
    for name in ['rows3', 'rings', 'rings_alt', 'checker3', 'quadrants', 'mrf3', 'sandwich', 'tiles2']:
        for s, n in ((1, 4), (2, 4), (3, 4), (4, 4)):
            for layout in L:
                for b in ('w07_10', 'w11_15'):
                    J.append(('size', 'syn:' + name, 'SYN', 3, layout, b, None, s, n))
    # (b) real silhouettes x1 vs x2 (colour picture upscaled)
    for src in SILHOUETTES:
        for cm in ['CM1', 'CM5', 'CM7', 'CM8']:
            for s in (1, 2):
                for layout in L:
                    for b in ('w07_10', 'w11_15'):
                        J.append(('size', src, cm, 3, layout, b, None, s, 0))
    return J


def jobs_wsweep():
    J = []
    Ws = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 20, 24]
    L = ['OPEN', 'COR1', 'BOT1', 'SPL1', 'SPB1', 'MUL1']
    for src in SILHOUETTES:
        for cm in ['CM1', 'CM3', 'CM5', 'CM7', 'CM8']:
            for layout in L:
                for W in Ws:
                    J.append(('wsweep', src, cm, 3, layout, f'W{W}', W, 1, 0))
    return J


def jobs_region():
    J = []
    L = ['OPEN', 'COR1', 'BOT1', 'SPL1', 'SPB1', 'MUL1']
    for shp in SILHOUETTES:
        m = silhouette(shp)
        for R in (3, 4, 5, 6, 8, 10, 12, 16):
            nc = region_count(m, R, 3)
            for idx in range(nc):
                for layout in L:
                    for b in ('w07_10', 'w11_15'):
                        J.append(('region', f'reg:{shp}:{R}:{idx}', 'REG', 3, layout, b, None, 1, 0))
    return J


def _refine_regions(top):
    import pandas as pd
    df = pd.read_json(os.path.join(OUT, 'broad.jsonl'), lines=True)
    df = df[df['solv'] == True].copy()
    df['yield'] = ((df['greedy_deep'] == False) & (df['dens_risky'] >= 0.25)).astype(float)
    g = df.groupby(['src', 'cm', 'layout']).agg(y=('yield', 'mean'), r=('dens_risky', 'mean'), n=('yield', 'size')).reset_index()
    g = g[g.n >= 2].sort_values(['y', 'r'], ascending=False).head(top)
    return g


def jobs_refine(top=48):
    """all W (1..32) in the `top` regions with highest puzzle yield in the broad sweep."""
    g = _refine_regions(top)
    Ws = list(range(1, 33))
    return [('refine', r.src, r.cm, 3, r.layout, f'W{W}', W, 1, 0) for _, r in g.iterrows() for W in Ws]


def jobs_refine_layout(top=24):
    """single-port perturbations of the best layouts, 3 wave bins."""
    g = _refine_regions(top)
    J = []
    for _, r in g.iterrows():
        for lay in [r.layout] + neighbours(r.layout):
            for b in BINS:
                J.append(('refine_layout', r.src, r.cm, 3, lay, b, None, 1, 0))
    return J


EXPS = {'region': jobs_region, 'broad': jobs_broad, 'ab4': jobs_ab4, 'synth': jobs_synth, 'size': jobs_size,
        'wsweep': jobs_wsweep, 'refine': jobs_refine, 'refine_layout': jobs_refine_layout}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exp')
    ap.add_argument('--procs', type=int, default=4)
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    J = EXPS[a.exp]()
    if a.limit:
        J = J[::max(1, len(J) // a.limit)][:a.limit]
    path = os.path.join(OUT, f"{a.exp}{os.environ.get('PUZZLE_TAG', '')}.jsonl")
    print(a.exp, len(J), 'jobs ->', path, flush=True)
    t0 = time.time()
    with Pool(a.procs) as pool, open(path, 'w') as f:
        for i, r in enumerate(pool.imap_unordered(job, J, chunksize=2)):
            f.write(json.dumps(r, default=lambda x: float(x) if hasattr(x, '__float__') else str(x)) + '\n')
            if i % 250 == 0:
                f.flush()
                print(i, round(time.time() - t0), flush=True)
    print('done', len(J), round(time.time() - t0), 's', flush=True)


if __name__ == '__main__':
    main()

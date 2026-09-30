"""colour-level order tightness from the solver itself: whole-colour waves (W=inf).
ord_valid      number of valid colour orders (of K!)
ord_valid_frac share of colour permutations that solve the level
ord_first_safe share of colours that can be sent first without dooming the level"""
import os, sys, itertools, math
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from puzzle_engine import Level
from run_experiments import make_labels, OUT
from puzzle_access import build_grid
import pandas as pd


def desc(args):
    src, cm, k, layout, scale, n = args
    try:
        lab = make_labels(src, cm, k, scale, n)
        if lab is None:
            return None
        L = Level(build_grid(lab, layout), 10 ** 6)
        full = L.full
        valid = 0
        first_ok = set()
        for perm in itertools.permutations(range(L.K)):
            s = 0
            ok = True
            for c in perm:
                sealed, mv = L.info(s)
                nxt = dict(mv).get(c)
                if sealed or nxt is None:
                    ok = False
                    break
                s = nxt
            if ok and s == full:
                valid += 1
                first_ok.add(perm[0])
        return dict(src=src, cm=cm, k=k, layout=layout, scale=scale, syn_n=n, ord_valid=valid,
                    ord_valid_frac=valid / math.factorial(L.K), ord_first_safe=len(first_ok) / L.K)
    except Exception as e:
        return dict(src=src, cm=cm, k=k, layout=layout, scale=scale, syn_n=n, ord_error=repr(e))


if __name__ == '__main__':
    d = pd.read_csv(os.path.join(OUT, 'dep_descriptors.csv'))
    keys = list(d[['src', 'cm', 'k', 'layout', 'scale', 'syn_n']].itertuples(index=False, name=None))
    with Pool(4) as p:
        rows = [r for r in p.imap_unordered(desc, keys, chunksize=16) if r]
    o = pd.DataFrame(rows)
    m = d.merge(o, on=['src', 'cm', 'k', 'layout', 'scale', 'syn_n'])
    m.to_csv(os.path.join(OUT, 'dep_descriptors.csv'), index=False)
    print(m.shape, m.filter(like='ord_').describe().round(2).to_string())

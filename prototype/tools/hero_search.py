"""Hero level candidates: hand-coloured cat (orange / black / white) scaled x2 = 216 target cells, SINGLE entrance.
Measures each (access layout, W) with the research solver so the choice is evidence-based.
This is dev tooling (imports ../../research); the shipped HTML is standalone.
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'research'))
import pandas as pd
from puzzle_engine import analyze
from puzzle_access import build_grid, LAYOUTS
from puzzle_shapes import scale_mask_colors

CAT = [".OO..OO.",
       ".OKWWKO.",
       "OOWWWWOO",
       "OWKWWKWO",
       "OWWWWWWO",
       "OWWKKWWO",
       ".OWWWWO.",
       ".OOWWOO."]
LET = {'O': 0, 'K': 1, 'W': 2}          # letters A=orange, B=black, C=white in the level file


def cat_labels(scale=2):
    lab = {(r, c): LET[ch] for r, row in enumerate(CAT) for c, ch in enumerate(row) if ch != '.'}
    return scale_mask_colors(lab, scale) if scale > 1 else lab


def waves(counts, W):
    return sum(math.ceil(c / W) for c in counts)


if __name__ == '__main__':
    lab = cat_labels(2)
    counts = [sum(1 for v in lab.values() if v == i) for i in range(3)]
    print('hücre', len(lab), 'renk sayıları (turuncu/siyah/beyaz)', counts)
    single = ['BOT1', 'BOT2', 'BOT3', 'COR1', 'COR2', 'COR3']
    rows = []
    for lay in single:
        g = build_grid(lab, lay)
        for W in range(8, 31):
            wv = waves(counts, W)
            if not 9 <= wv <= 22: continue
            r = analyze(g, W, extra=True, sims=800)
            if not r.get('solv'):
                rows.append(dict(layout=lay, W=W, waves=wv, solv=False)); continue
            rows.append(dict(layout=lay, W=W, waves=wv, solv=True, greedy_fail=not r['greedy_deep'], e_risky=r['e_risky'], e_crit=r['e_crit'], dens=r['dens_risky'],
                             filler=r['filler_ratio'], dh=r['dh_exp_mean'], instant=r['dh_instant_share'], abc=r['abc_mean'], rnd0=r['rnd0'], undo1=r['win_undo1'],
                             first_safe=f"{r['first_safe']}/{r['first_legal']}", rec1=r['rec1']))
    df = pd.DataFrame(rows)
    pd.set_option('display.width', 220); pd.set_option('display.max_rows', 300)
    print(df.round(3).to_string(index=False))
    df.to_csv(os.path.join(HERE, 'hero_search.csv'), index=False)

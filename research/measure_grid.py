"""Measure ANY grid (e.g. the real 244-cell cat prototype) with the full metric set.

grid file: plain text, one row per line.  E = entrance, # = wall, . = permanent open floor, every other
character = a colour (E is reserved).  Example letters: O K W for orange/black/white.

usage:
  python3 measure_grid.py cat244.txt                 # picks W values giving 7-20 waves
  python3 measure_grid.py cat244.txt --W 12 16 20    # explicit W list
  python3 measure_grid.py cat244.txt --csv out.csv
Envelope flags use benchmark_reference.json as COMPARISON ranges only (not targets).
"""
import argparse, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
from puzzle_engine import analyze, Level

HERE = os.path.dirname(os.path.abspath(__file__))
REF = {c['id']: c for c in json.load(open(f'{HERE}/benchmark_reference.json'))['claims']}
DIMS = [('action_space', 'visible_mean', 1.0), ('critical_decisions', 'e_risky', 1.0), ('recovery_horizon', 'dh_exp_mean', 1.0),
        ('total_moves', 'e_moves', 5.0), ('filler_ratio', 'filler_ratio', 0.05), ('trap_timing', 'trap_timing', 0.05)]


def flags(r):
    out = {}
    for cid, col, tm in DIMS:
        lo, hi = REF[cid]['range']
        t = max(0.25 * (hi - lo), tm)
        x = r.get(col)
        out[cid] = 'nan' if x is None or (isinstance(x, float) and math.isnan(x)) else ('core' if lo <= x <= hi else ('tol' if lo - t <= x <= hi + t else ('below' if x < lo else 'above')))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('grid'); ap.add_argument('--W', type=int, nargs='*'); ap.add_argument('--csv')
    a = ap.parse_args()
    g = open(a.grid).read().rstrip('\n')
    L = Level(g, 1)
    print(f"hedef hücre: {L.n} | renkler: {dict(zip(L.letters, L.cnt))} | giriş hücresi: {len(L.ent)}")
    d0 = L.depth_profile()
    if any(x < 0 for x in d0):
        print("UYARI: girişten erişilemeyen hedef hücre var:", sum(1 for x in d0 if x < 0)); return
    Ws = a.W
    if not Ws:
        Ws = sorted({w for w in range(1, L.n + 1) if 7 <= sum(math.ceil(c / w) for c in L.cnt) <= 20})
    rows = []
    for W in Ws:
        r = analyze(g, W, extra=True)
        if not r.get('solv'):
            print(f"W={W}: çözümsüz/atlandı", {k: r.get(k) for k in ('skipped', 'n_states')}); continue
        r['W'] = W; rows.append(r)
    if not rows:
        return
    df = pd.DataFrame(rows)
    cols = ['W', 'waves_nominal', 'e_moves', 'e_meaningful', 'e_risky', 'e_crit', 'e_forced', 'dens_risky', 'filler_ratio', 'dh_exp_mean', 'dh_instant_share', 'latent_doom_mass',
            'blind_progress_mean', 'abc_mean', 'abc_max_dag', 'visible_mean', 'mbf_mean', 'cpr_risky', 'trap_timing', 'regret_max', 'rec1', 'greedy_deep', 'rnd0', 'win_undo1', 'win_undo2']
    print(df[cols].round(3).to_string(index=False))
    print("\nzarf bayrakları (core/tol/below/above; hedef değil):")
    for r in rows:
        print(f"  W={r['W']:>3}", flags(r))
    if a.csv:
        df.to_csv(a.csv, index=False); print("yazıldı:", a.csv)


if __name__ == '__main__':
    main()

"""Headline numbers + machine-readable summary (results/summary.json)."""
import json, warnings
import pandas as pd, numpy as np
warnings.filterwarnings('ignore')
from analysis_common import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
b = load('broad'); ball = load('broad', solvable=False)
b['puzzle_yield'] = ((b.greedy_fail == 1) & (b.dens_risky >= 0.25)).astype(float)
out = {}
# variance shares
for r in ['dens_risky', 'dens_meaningful', 'e_risky', 'greedy_fail', 'puzzle_yield']:
    t, r2 = anova_eta(b, r, ['src', 'cm', 'layout', 'bin'])
    out['eta2_' + r] = {k: round(float(v), 3) for k, v in t['eta2'].items()}
    out['eta2_' + r]['R2'] = round(float(r2), 3)
print("Puzzle verimi (greedy başarısız & dens_risky>=0.25) η²:", out['eta2_puzzle_yield'])
# solvability
out['solvable_share_by_cm'] = ball.groupby('cm').solv.mean().round(3).to_dict()
out['solvable_share_by_family'] = ball.groupby('family').solv.mean().round(3).to_dict()
out['solvable_share_by_shape'] = ball.groupby('src').solv.mean().round(3).to_dict()
print("çözülebilir pay CM:", out['solvable_share_by_cm'])
# many cells but few decisions
b['risky_per100'] = 100 * b.e_risky / b.cells
g = b.groupby(['cm', 'family']).agg(cells=('cells', 'mean'), e_risky=('e_risky', 'mean'), e_meaningful=('e_meaningful', 'mean'), risky_per100=('risky_per100', 'mean'),
                                     dens_risky=('dens_risky', 'mean'), greedy_fail=('greedy_fail', 'mean'), n=('cells', 'size')).round(2)
low = g.sort_values('e_risky').head(12)
print("\nEn az riskli karar (hücre sayısı ~aynı; CM×erişim):"); print(low.to_string())
hi = g.sort_values('e_risky', ascending=False).head(8)
print("\nEn çok riskli karar:"); print(hi.to_string())
save(g, 'cm_x_family_decision_summary')
big = b[b.cells >= 90]
print("\n>=90 hücre (rabbit, landscape) içinde CM × OPEN ortalama e_risky / dens_risky:")
print(big[big.family == 'OPEN'].groupby('cm')[['cells', 'e_risky', 'dens_risky']].mean().round(2).to_string())
out['low_decision_combos'] = low.reset_index().to_dict('records')
out['high_decision_combos'] = hi.reset_index().to_dict('records')
json.dump(out, open(f'{RES}/summary.json', 'w'), indent=1, default=float)
print("kaydedildi:", f'{RES}/summary.json')

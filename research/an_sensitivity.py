"""Sensitivity of the conclusions to the MEANINGFUL-SAFE threshold delta (spread of random-continuation win prob)."""
import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
from analysis_common import *
pd.set_option('display.width', 250)
names = {'0.02': 'broad_delta0.02', '0.05': 'broad', '0.10': 'broad_delta0.10', '0.20': 'broad_delta0.20'}
D = {k: load(v) for k, v in names.items()}
base = D['0.05']
rows = []
for k, d in D.items():
    d = d.copy()
    d['comp_ok'] = 1
    m = d.e_moves.replace(0, np.nan)
    t_, r2 = anova_eta(d, 'dens_meaningful', ['src', 'cm', 'layout', 'bin'])
    t2, r22 = anova_eta(d, 'dens_risky', ['src', 'cm', 'layout', 'bin'])
    rows.append(dict(delta=k, n=len(d),
                     share_free=(d.e_free / m).mean(), share_meansafe=(d.e_meansafe / m).mean(),
                     share_trap=(d.e_trap / m).mean(), share_crit=(d.e_crit / m).mean(),
                     dens_meaningful=d.dens_meaningful.mean(), dens_risky=d.dens_risky.mean(),
                     eta2_cm_meaningful=t_.loc['cm', 'eta2'], eta2_layout_meaningful=t_.loc['layout', 'eta2'],
                     eta2_src_meaningful=t_.loc['src', 'eta2'], eta2_bin_meaningful=t_.loc['bin', 'eta2'],
                     eta2_cm_risky=t2.loc['cm', 'eta2'], eta2_layout_risky=t2.loc['layout', 'eta2'],
                     eta2_src_risky=t2.loc['src', 'eta2']))
T = pd.DataFrame(rows).round(3)
print(T.T.to_string()); save(T.set_index('delta'), 'sensitivity_delta')
key = ['src', 'cm', 'layout', 'bin']
j = base.set_index(key)[['dens_risky', 'dens_meaningful']].join(D['0.20'].set_index(key)[['dens_risky', 'dens_meaningful']], rsuffix='_d20', how='inner')
print("\ndens_risky delta'dan bağımsız mı? max |fark| =", float((j.dens_risky - j.dens_risky_d20).abs().max()))
print("dens_meaningful korelasyonu (δ=0.05 vs 0.20):", round(j[['dens_meaningful', 'dens_meaningful_d20']].corr().iloc[0, 1], 3))

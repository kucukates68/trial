import pandas as pd, numpy as np
from analysis_common import *
pd.set_option('display.width',250);pd.set_option('display.max_columns',40)
d=load('synth',solvable=False)
d['pat']=d.src.str[4:]
print("satır",len(d),"çözülebilir",round(d.solv.mean(),3))
print("\nÇözülebilirlik desene göre:",d.groupby('pat').solv.mean().round(2).to_dict())
s=d[d.solv].copy()
s['waves']=s['waves_nominal']
# restrict to comparable game length: 7-16 waves
t=s[(s.waves>=7)&(s.waves<=16)]
print("7-16 dalga aday:",len(t))
cols=['cm_comp_total','cm_trans_sp','cm_clustering','ent_trans_per_cell','dens_risky','dens_meaningful','e_risky','greedy_fail','regret_max','win_undo2']
g=t.groupby('pat')[cols].mean().round(3).sort_values('dens_risky')
print(g.to_string());save(g,'synth_by_pattern_waves7_16')
# family x pattern heat
h=t.pivot_table(index='pat',columns='family',values='dens_risky',aggfunc='mean').round(2)
print("\nDeseni x erişim ailesi: dens_risky");print(h.to_string());save(h,'synth_pattern_x_family_dens_risky')
h2=t.pivot_table(index='pat',columns='family',values='solv',aggfunc='size')
# ANOVA on synth (same geometry: 8x8 square), pattern x layout x W
u=s[s.syn_n==8].copy();u['Wc']=u['W'].astype(str)
for r in ['dens_risky','dens_meaningful','e_risky','greedy_fail']:
    tab,r2=anova_eta(u,r,['pat','layout','Wc'])
    print(f"\nANOVA η² (8x8, tek geometri) resp={r} R2={r2:.2f}");print(tab['eta2'].round(3).to_string())
# orthogonal contrasts: same geometry, same counts, different depth order
pairs=[('rows3','rows_alt'),('rings','rings_alt'),('cols3','rows3'),('mrf0','mrf8'),('checker3','diag3')]
print("\nKontrast çiftleri (7-16 dalga, tüm erişimler): dens_risky / greedy_fail / cm_comp_total / ent_trans_per_cell")
for a,b in pairs:
    for p in (a,b):
        x=t[t.pat==p]
        print(f"  {p:10} n={len(x):4d} comps={x.cm_comp_total.mean():5.1f} entTr={x.ent_trans_per_cell.mean():.2f} dens_risky={x.dens_risky.mean():.3f} greedyFail={x.greedy_fail.mean():.2f} solv_share_in_all={d[d.pat==p].solv.mean():.2f}")
    print('  --')
# clustering dose (mrf0..mrf8)
print("\nKümelenme dozu (MRF yumuşatma geçişi):")
for p in ['mrf0','mrf1','mrf3','mrf8']:
    x=t[t.pat==p];print(f"  {p}: comps={x.cm_comp_total.mean():.1f} clustering={x.cm_clustering.mean():.2f} entTr={x.ent_trans_per_cell.mean():.2f} dens_risky={x.dens_risky.mean():.3f} dens_meaningful={x.dens_meaningful.mean():.3f} greedyFail={x.greedy_fail.mean():.2f} solv={d[d.pat==p].solv.mean():.2f}")

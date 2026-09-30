import pandas as pd, numpy as np
from analysis_common import *
pd.set_option('display.width',250);pd.set_option('display.max_columns',40)
b=load('broad')
b['log10_canon_pm']=b['log_seq_canon_per_move']
resps=['dens_meaningful','dens_risky','e_meaningful','e_risky','e_crit','risk','regret_max','greedy_fail','log10_canon_pm']
rows=[]
for r in resps:
    t,r2=anova_eta(b,r,['src','cm','layout','bin'])
    t['resp']=r;t['R2']=r2;rows.append(t.reset_index().rename(columns={'index':'term'}))
A=pd.concat(rows)
piv=A.pivot(index='term',columns='resp',values='eta2').round(3)
order=['src','cm','layout','bin','src:cm','src:layout','src:bin','cm:layout','cm:bin','layout:bin','Residual']
print("η² (toplam SS payı), tek-seviye: n=",len(b))
print(piv.loc[order,resps].to_string())
save(piv.loc[order,resps],'anova_eta2_broad_src_cm_layout_bin')
# access family vs layout-within-family
b['fam']=b['family']
t,_=anova_eta(b,'dens_risky',['src','cm','fam','bin'])
print("\nfamily (6) sürümü dens_risky:");print(t['eta2'].round(3).to_string())
# 'geometry' = access ; 'color' = cm ; silhouette = src ; decomposition into main / interaction
for r in ['dens_meaningful','dens_risky','e_risky','risk','greedy_fail']:
    t,r2=anova_eta(b,r,['src','cm','layout','bin'])
    main=t.loc[['src','cm','layout','bin'],'eta2'].sum();inter=t.drop(['src','cm','layout','bin','Residual'])['eta2'].sum()
    print(f"{r:16} ana etkiler {main:.3f} | 2'li etkileşimler {inter:.3f} | 3+ kalan {t.loc['Residual','eta2']:.3f} | R2 {r2:.3f}")

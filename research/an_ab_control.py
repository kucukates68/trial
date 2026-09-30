import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
from analysis_common import *
import statsmodels.formula.api as smf
pd.set_option('display.width',250)
dep=pd.read_csv(f'{RES}/dep_descriptors.csv')
a=pd.concat([load('ab4',solvable=False)]);a=a[a.solv]
a=a.merge(dep,on=['src','cm','k','layout','scale','syn_n'],how='left')
a['comp_per_cell']=a.cm_comp_total/a.cells
key=['src','cm','layout','bin']
j=a[a.k==3].set_index(key).join(a[a.k==4].set_index(key),lsuffix='_3',rsuffix='_4',how='inner').reset_index()
for fac in ['layout']:
    j['family']=j['family_3']
    dd=j.assign(de=j.e_risky_4-j.e_risky_3,dt=j.e_trap_4-j.e_trap_3,dc=j.e_crit_4-j.e_crit_3,dd=j.dens_risky_4-j.dens_risky_3)
    print("erişim ailesi bazında 4-3 farkı:");print(dd.groupby('family')[['de','dt','dc','dd']].mean().round(2).to_string())
print("\nHavuzlu regresyon (ab3+ab4 tüm satırlar), k katsayısı yapı kontrolleriyle:")
for y in ['e_risky','e_trap','e_crit','dens_risky','e_meaningful','greedy_fail']:
    m0=smf.ols(f'{y} ~ C(k)+np.log(waves_nominal)+C(family)',data=a).fit()
    m1=smf.ols(f'{y} ~ C(k)+np.log(waves_nominal)+C(family)+cm_clustering+comp_per_cell+cm_dominant+cm_entropy_norm+ord_valid_frac',data=a).fit()
    m2=smf.ols(f'{y} ~ C(k)+np.log(waves_nominal)+C(family)+cm_clustering+comp_per_cell+cm_dominant+cm_entropy_norm+ord_valid_frac+ent_trans_per_cell+deep_entropy',data=a).fit()
    print(f"  {y:14} k4-k3: yalnız dalga+erişim kontrolü {m0.params['C(k)[T.4]']:+.3f} | + renk yapısı ve sıra sıkılığı {m1.params['C(k)[T.4]']:+.3f} (p={m1.pvalues['C(k)[T.4]']:.2g}) | + geçiş {m2.params['C(k)[T.4]']:+.3f}")
# same ord-tightness matched: compare k=3 vs k=4 within ord_valid_frac buckets
a['ordb']=pd.cut(a.ord_valid_frac,[-.01,0,.34,.67,1.0],labels=['0','≤1/3','≤2/3','>2/3'])
print("\nAynı renk-sırası sıkılığı kovasında k=3 vs k=4:");print(a.pivot_table(index='ordb',columns='k',values=['dens_risky','e_risky','e_crit','e_trap'],aggfunc='mean',observed=True).round(2).to_string())

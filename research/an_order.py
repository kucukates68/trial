import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
from analysis_common import *
import statsmodels.api as sm
pd.set_option('display.width',250);pd.set_option('display.max_columns',40)
dep=pd.read_csv(f'{RES}/dep_descriptors.csv')
def merged(name,solvable=True):
    d=load(name,solvable=solvable)
    for c in ('scale','syn_n'):
        if c not in d:d[c]=0 if c=='syn_n' else 1
    return d.merge(dep,on=['src','cm','k','layout','scale','syn_n'],how='left')
b=merged('broad');b['comp_per_cell']=b.cm_comp_total/b.cells
b['ord_bin']=pd.cut(b.ord_valid_frac,[-0.01,0.0,0.34,0.67,0.99,1.0],labels=['0 (renk-sırası çözümsüz)','≤1/3','≤2/3','<1','1 (hepsi geçerli)'])
print("n",len(b))
g=b.groupby('ord_bin',observed=True)[['dens_risky','dens_meaningful','e_risky','greedy_fail','risk','regret_max','win_undo2']].agg('mean').round(3);g['n']=b.groupby('ord_bin',observed=True).size()
print("\nW=∞ renk-sırası sıkılığı -> karar yapısı (W=bin değerinde çözülebilir adaylar):");print(g.to_string());save(g,'order_tightness_buckets')
print("\nKorelasyon dens_risky ~",b[['ord_valid_frac','ord_first_safe','cm_clustering','comp_per_cell','ent_trans_per_cell','dep_shadow_frac']].corrwith(b.dens_risky).round(2).to_dict())
fam=pd.get_dummies(b.family,drop_first=True).astype(float)
def r2(cols,y):
    X=sm.add_constant(pd.concat([b[cols],fam],axis=1)) if cols else sm.add_constant(fam)
    return sm.OLS(b[y],X).fit().rsquared
cmc=['cm_clustering','comp_per_cell','cm_dominant','cm_entropy_norm'];trc=['ent_trans_per_cell','ent_wtrans_per_cell','ent_mean_run','deep_entropy'];dpc=['dep_density','dep_shadow_frac','dep_cross_per_cell','dep_maxdom']
ordc=['ord_valid_frac','ord_first_safe']
for y in ['dens_risky','dens_meaningful','e_risky','greedy_fail']:
    print(f"\n{y}: erişim={r2([],y):.3f} | +renk-sırası sıkılığı={r2(ordc,y):.3f} | +renk istatistiği={r2(cmc,y):.3f} | sıra+renk ist.={r2(ordc+cmc,y):.3f} | hepsi(sıra+renk+geçiş+bağımlılık)={r2(ordc+cmc+trc+dpc,y):.3f}")
y='dens_risky';allc=ordc+cmc+trc+dpc
Z=(b[allc]-b[allc].mean())/b[allc].std().replace(0,1);Xf=sm.add_constant(pd.concat([Z,fam],axis=1));yf=(b[y]-b[y].mean())/b[y].std()
full=sm.OLS(yf,Xf).fit();rows=[]
for c in allc:
    m2=sm.OLS(yf,Xf.drop(columns=[c])).fit();rows.append((c,full.params[c],full.rsquared-m2.rsquared))
D=pd.DataFrame(rows,columns=['var','std_beta','drop1_dR2']).sort_values('drop1_dR2',ascending=False)
print("\nTek-tek çıkarma (dens_risky), R2=%.3f"%full.rsquared);print(D.round(3).to_string(index=False));D.to_csv(f'{SUM}/drop_one_with_order.csv',index=False)
# region ablation within-R
r=merged('region');r['R']=r.src.str.split(':').str[2].astype(int)
r['grp']=r.src.str.split(':').str[1]+'_'+r.R.astype(str)+'_'+r.layout+'_'+r.bin
r=r[r.groupby('grp')['dens_risky'].transform('size')>=4]
dc=r['dens_risky']-r.groupby('grp')['dens_risky'].transform('mean')
print("\nBölge ablasyonu GRUP İÇİ korelasyon (R sabit):")
for c in ['ord_valid_frac','ord_first_safe','dep_shadow_frac','ent_trans_per_cell','cm_entropy_norm']:
    cc=r[c]-r.groupby('grp')[c].transform('mean');print(f"  {c:18} r={np.corrcoef(cc.fillna(0),dc)[0,1]:.3f}")
# synthetic contrasts
sy=merged('synth');sy=sy[(sy.waves_nominal>=7)&(sy.waves_nominal<=16)]
t=sy.groupby(sy.src.str[4:])[['ord_valid_frac','ord_first_safe','cm_comp_total','ent_trans_per_cell','dens_risky']].mean().round(3).sort_values('dens_risky');print("\nSentetik desen:");print(t.to_string())
